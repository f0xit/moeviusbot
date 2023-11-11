import datetime as dt
import logging
from typing import Optional, Sequence

import discord
from discord.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot import Bot
from tools.check_tools import SpecialUser, is_special_user
from tools.converter_tools import DtString
from tools.embed_tools import EmbedBuilder
from tools.event_tools import Event, EventType
from tools.view_tools import EventButtonAction, ViewBuilder


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(Reminder(bot))
    logging.info("Cog: Reminder loaded.")


class Reminder(commands.Cog, name="Events"):
    """Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten,
    beizutreten oder deren Status abzufragen.

    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP,
    wenn du mehr darüber wissen willst."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.session = Session(self.bot.db_engine, autoflush=True)
        self.upcoming_events = self.get_upcoming_events()
        self.time_now = ""
        self.reminder_checker.start()
        logging.info("Reminder initialized.")

    async def cog_load(self):
        logging.info("Finding stream channel...")

        chan_id = int(self.bot.settings["channels"]["stream"])
        stream_channel = self.bot.main_guild.get_channel(chan_id)

        if not isinstance(stream_channel, discord.TextChannel):
            logging.error("Stream channel not found!")
            raise RuntimeError("Stream channel found. [ID: %s]", chan_id)

        self.stream_channel = stream_channel
        logging.info("Stream channel found. [ID: %s] %s", stream_channel.id, stream_channel.name)

    async def cog_unload(self) -> None:
        self.reminder_checker.cancel()
        self.session.close()
        logging.info("Reminder unloaded.")

    def get_upcoming_events(self) -> Sequence[Event]:
        events = self.session.execute(select(Event)).scalars.all()
        logging.info("Updated list of upcoming events. Amount: %s", events.count)
        return events

    async def save_event_in_db(self, event: Event) -> None:
        self.session.add(event)
        self.session.commit()
        logging.info("Inserted event into DB: %s", event)

        self.upcoming_events = self.get_upcoming_events()

    async def mark_event_as_announced(self, event: Event) -> None:
        event.announced = True
        self.session.commit()

        logging.info("Event updated (announced): %s", event)

        self.upcoming_events = self.get_upcoming_events()

    async def mark_event_as_started(self, event: Event) -> None:
        event.started = True
        self.session.commit()

        logging.info("Event updated (started): %s", event)

        self.upcoming_events = self.get_upcoming_events()

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
            await ctx.send("Es wurde kein Stream angekündigt, Krah Krah!")
            return

        embed = EmbedBuilder.upcoming_events(self.upcoming_events)

        await ctx.send("Hier sind die angekündigten Streams:", embed=embed)

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS])
    @_stream.command(name="add", brief="Fügt ein Stream Event hinzu.")
    @discord.app_commands.rename(time="zeitpunkt", title="titel", description="beschreibung")
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

        event = Event(
            type=EventType.STREAM,
            title=title,
            description=description,
            time=time,
            creator=ctx.author.id,
        )

        embed = EmbedBuilder.single_stream_announcement(event)
        view = ViewBuilder.confirm_event_preview()
        preview = await ctx.send("Stimmt das so?", embed=embed, view=view, ephemeral=True)
        await view.wait()

        match view.performed_action:
            case EventButtonAction.SAVE:
                await self.save_event_in_db(event)

                await ctx.send(
                    "Alles klar, das Event wurde gespeichert, Krah Krah!", ephemeral=True
                )
            case EventButtonAction.ANNOUNCE:
                await self.save_event_in_db(event)

                await self.stream_channel.send(
                    embed=EmbedBuilder.single_stream_announcement(event),
                    view=ViewBuilder.join_single_event(),
                )
                await self.mark_event_as_announced(event)

                await ctx.send(
                    "Alles klar, das Event wurde gespeichert und angekündigt , Krah Krah!",
                    ephemeral=True,
                )
            case EventButtonAction.ABORT:
                await ctx.send("Alles klar, Krah Krah! Was möchtest du ändern?", ephemeral=True)

        await preview.edit(view=None)

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

            logging.info("Ein Event beginnt: %s!", event.type)

            await self.stream_channel.send(
                f"Oh, ist es denn schon {event.time.strftime('%H:%M')} Uhr? "
                "Dann ab auf https://www.twitch.tv/schnenko/ ... ",
                embed=EmbedBuilder.stream_running(event),
            )

            await self.mark_event_as_started(event)

    @reminder_checker.before_loop
    async def before_reminder_loop(self):
        logging.debug("Waiting for reminder time checker..")
        await self.bot.wait_until_ready()
        logging.info("Reminder time checker started!")
