import datetime as dt
import functools
import logging
from typing import Optional, Sequence

import discord
from discord.ext import commands, tasks
from sqlalchemy.orm import Session

from bot import Bot
from tools.check_tools import SpecialUser, is_special_user
from tools.converter_tools import DtString
from tools.embed_tools import EmbedBuilder
from tools.event_tools import Event, EventType
from tools.view_tools import EventButtonAction, ViewBuilder

ANNOY_IDS = [232561052573892608]


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(Reminder(bot))
    logging.info("Cog: Reminder loaded!")


def refresh_upcoming_events():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(self, *args, **kw):
            await func(self, *args, **kw)
            logging.debug("Decorator fired for event list refresh.")
            self.upcoming_events = await Event.get_upcoming_events(self.session)

        return wrapped

    return wrapper


class Reminder(commands.Cog, name="Events"):
    """Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten,
    beizutreten oder deren Status abzufragen.

    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP,
    wenn du mehr darüber wissen willst."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.session = Session(self.bot.db_engine, autoflush=True)
        self.upcoming_events: Sequence[Event] = []
        self.time_now = ""
        self.reminder_checker.start()

        logging.info("Cog: Reminder initialized!")

    async def cog_load(self):
        self.upcoming_events = await Event.get_upcoming_events(self.session)

        chan_id = int(self.bot.settings["channels"]["stream"])
        logging.debug("Finding stream channel with [ID#%s] ...", chan_id)

        stream_channel = self.bot.main_guild.get_channel(chan_id)

        if not isinstance(stream_channel, discord.TextChannel):
            logging.error("Stream channel not found!")
            raise RuntimeError("Stream channel not found! [ID#%s]", chan_id)

        self.stream_channel = stream_channel
        logging.info("Stream channel found. [ID#%s] %s", stream_channel.id, stream_channel.name)

    async def cog_unload(self) -> None:
        self.reminder_checker.cancel()
        self.session.close()
        logging.info("Cog: Reminder unloaded!")

    @refresh_upcoming_events()
    async def save_event_in_db(self, event: Event) -> None:
        self.session.add(event)
        self.session.commit()
        logging.info("Inserted event into DB: %s", event)

    @refresh_upcoming_events()
    async def mark_event_as_announced(self, event: Event) -> None:
        event.announced = True
        logging.info("Event updated (announced): %s", event)

        self.session.commit()

    @refresh_upcoming_events()
    async def mark_events_as_announced(self, events: Sequence[Event]) -> None:
        for event in events:
            event.announced = True
            logging.info("Event updated (announced): %s", event)

        self.session.commit()

    @refresh_upcoming_events()
    async def mark_event_as_started(self, event: Event) -> None:
        event.started = True
        self.session.commit()

        logging.info("Event updated (started): %s", event)

    @commands.hybrid_group(
        name="stream",
        fallback="show",
        brief="Infos und Einstellungen zum aktuellen Stream-Reminder.",
    )
    async def _stream(self, ctx: commands.Context) -> None:
        """Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine
        Einstellungen anpassen"""

        await ctx.defer()

        if not (self.upcoming_events):
            await ctx.send("Es wurde noch kein Stream angekündigt, Krah Krah!")
            logging.info("Upcoming stream requested but none is announced.")
            return

        embed = EmbedBuilder.upcoming_events(self.upcoming_events)

        await ctx.send("Hier sind die angekündigten Streams:", embed=embed)
        logging.info("Displayed upcoming and announced streams.")

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS])
    @_stream.command(name="add", brief="Fügt ein Stream Event hinzu.")
    @discord.app_commands.rename(time="Zeitpunkt", title="Titel", description="Beschreibung")
    @discord.app_commands.describe(
        time="HH:MM oder TT.MM. HH:MM",
        title="Optionaler Titel",
        description="Optionale Beschreibung",
    )
    async def _add_stream(
        self,
        ctx: commands.Context,
        time: DtString,
        title: Optional[str] = "",
        description: Optional[str] = "",
    ) -> None:
        await ctx.defer()
        logging.info("New stream proposed by %s...", ctx.author.id)

        event = Event(
            type=EventType.STREAM,
            title=title,
            description=description,
            time=time,
            creator=ctx.author.id,
        )
        logging.debug("Proposed stream: %s", repr(event))

        embed = EmbedBuilder.single_stream_announcement(event)
        view = ViewBuilder.confirm_event_preview()
        preview = await ctx.send(
            "Stimmt das so, Krah Krah?",
            embed=embed,
            view=view,
            ephemeral=True,
        )
        logging.debug("Preview displayed for %s.", ctx.author.id)

        logging.debug("Waiting for user input...")
        await view.wait()

        logging.info("User action on preview: %s", view.performed_action)
        match view.performed_action:
            case EventButtonAction.SAVE:
                await self.save_event_in_db(event)

            case EventButtonAction.ANNOUNCE:
                await self.save_event_in_db(event)

                await self.stream_channel.send(
                    embed=EmbedBuilder.single_stream_announcement(event),
                    view=ViewBuilder.join_single_event(),
                )
                await self.mark_event_as_announced(event)

        await preview.edit(view=None)
        logging.debug("Preview buttons removed.")

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS])
    @commands.hybrid_group(name="announce", fallback="list", brief="Zeigt unangekündigte Events.")
    async def _announce_event(self, ctx: commands.Context) -> None:
        await ctx.defer()
        logging.info("List of unannounced streams requested by %s...", ctx.author.id)

        events_to_announce = await Event.get_events_to_announce(self.session)

        await ctx.send(
            embed=EmbedBuilder.events_to_be_announced(events_to_announce), ephemeral=True
        )

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS])
    @_announce_event.command(name="next", brief="Kündigt Stream Events an.")
    async def _announce_next_event(
        self,
        ctx: commands.Context,
    ) -> None:
        await ctx.defer()
        logging.info("Announcement of next stream requested by %s...", ctx.author.id)

        if (output_channel := self.bot.channels["stream"]) is None:
            await ctx.send(
                "Fehler! Es gibt keinen gültigen Streaming-Channel, Krah Krah!",
                ephemeral=True,
            )
            logging.error("No streaming channel found!")
            raise RuntimeError("No streaming channel found!")

        if (event := (await Event.get_events_to_announce(self.session))[0]) is None:
            await ctx.send(
                "Es gibt keine Streams, die angekündigt werden können, Krah Krah!",
                ephemeral=True,
            )
            logging.debug("No streams found to be announced.")
            return

        await output_channel.send(embed=EmbedBuilder.single_stream_announcement(event))
        await self.mark_event_as_announced(event)
        await ctx.send("Ich habe das Event angekündigt, Krah Krah!", ephemeral=True)

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS])
    @_announce_event.command(name="week", brief="Kündigt Stream Events an.")
    async def _announce_this_week_events(
        self, ctx: commands.Context, description: Optional[str]
    ) -> None:
        await ctx.defer()

        if (output_channel := self.bot.channels["stream"]) is None:
            await ctx.send(
                "Fehler! Es gibt keinen gültigen Streaming-Channel, Krah Krah!",
                ephemeral=True,
            )
            logging.error("No streaming channel found!")
            raise RuntimeError("No streaming channel found!")

        if not (events := (await Event.get_week_events_to_announce(self.session))):
            await ctx.send(
                "Es gibt diese Woche keine Streams, die angekündigt werden können, Krah Krah!",
                ephemeral=True,
            )
            logging.debug("No streams found to be announced.")
            return

        if description is None:
            description = ""

        await output_channel.send(embed=EmbedBuilder.week_streams_announcement(events, description))
        await self.mark_events_as_announced(events)
        await ctx.send("Ich habe die Events angekündigt, Krah Krah!", ephemeral=True)

    @commands.hybrid_command(name="join", aliases=["j"], brief="Tritt einem Event bei.")
    async def _join(self, ctx: commands.Context) -> None:
        """Wenn ein Reminder eingerichtet wurde, kannst du ihm mit diesem Kommando beitreten.

        Stehst du auf der Teilnehmerliste, wird der Bot dich per Erwähnung benachrichtigen,
        wenn das Event beginnt oder siche etwas ändern sollte."""

    @tasks.loop(seconds=5.0)
    async def reminder_checker(self):
        dt_ftm = "%d_%m_%H_%M"

        if self.time_now == dt.datetime.now().strftime(dt_ftm):
            return

        self.time_now = dt.datetime.now().strftime(dt_ftm)

        for event in self.upcoming_events:
            if event.time.strftime(dt_ftm) != self.time_now:
                continue

            logging.info("Event starting: [ID#]%s with type %s!", event.id, event.type)

            await self.stream_channel.send(
                f"Oh, ist es denn schon {event.time.strftime('%H:%M')} Uhr? "
                "Dann ab auf https://www.twitch.tv/schnenko/ ... ",
                embed=EmbedBuilder.stream_running(event),
            )

            await self.mark_event_as_started(event)
            logging.info("Event announced [ID#]%s!", event.id)

    @reminder_checker.before_loop
    async def before_reminder_loop(self):
        logging.debug("Waiting for reminder time checker..")
        await self.bot.wait_until_ready()
        logging.info("Reminder time checker started!")
