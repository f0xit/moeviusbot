import datetime as dt
import logging

import discord
from discord.ext import commands, tasks

from bot import Bot
from tools.converter_tools import convert_str_to_dt
from tools.dt_tools import get_local_timezone
from tools.event_tools import Event, EventManager, EventType

ANNOY_IDS = [232561052573892608]


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
        self.events = EventManager()
        self.time_now = dt.datetime.now(get_local_timezone())

        self.reminder_checker.start()
        logging.info("Reminder initialized.")

    async def cog_unload(self) -> None:
        self.reminder_checker.cancel()
        logging.info("Reminder unloaded.")

    # Commands
    @commands.hybrid_group(
        name="stream",
        fallback="show",
        brief="Infos und Einstellungen zum aktuellen Stream-Reminder.",
    )
    async def _stream(self, ctx: commands.Context) -> None:
        """Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine
        Einstellungen anpassen"""

    @_stream.command(
        name="add",
        brief="Fügt ein Stream Event hinzu.",
    )
    async def _add_stream(
        self, ctx: commands.Context, time: str, game: str = ""
    ) -> None:
        """Fügt ein Stream Event hinzu."""

        new_dt = await convert_str_to_dt(time)

        new_event = self.events.add_event(
            Event(
                event_type=EventType.STREAM,
                event_title="Schnenko nervt!",
                event_dt=new_dt,
                event_members=[ctx.author.id],
                event_game=game,
            )
        )

        if (output_channel := self.bot.channels[str(new_event.event_type)]) is None:
            return

        await output_channel.send(
            f"**Macht euch bereit für einen Stream!**\n"
            f"Wann? {new_event.event_dt} Uhr\n"
            f"Was? {new_event.event_game}\n"
            "Gebt mir ein !join, Krah Krah!"
        )

        await ctx.send(
            f"Stream wurde angekündigt! ID: {new_event.event_id}", ephemeral=True
        )

    @tasks.loop(seconds=5.0)
    async def reminder_checker(self) -> None:
        if self.time_now.strftime("%H:%M") == dt.datetime.now(
            tz=get_local_timezone()
        ).strftime("%H:%M"):
            return

        self.time_now = dt.datetime.now(tz=get_local_timezone())

        for event in self.events.upcoming_events:
            if event.event_dt <= self.time_now:
                continue

            members = " ".join([f"<@{member_id}>" for member_id in event.event_members])

            output_channel = self.bot.channels["stream"]
            if not isinstance(output_channel, discord.TextChannel):
                return

            await output_channel.send(
                f"Oh, ist es denn schon {event.event_dt} Uhr? "
                "Dann ab auf https://www.twitch.tv/schnenko/ ... "
                "der Stream fängt an, Krah Krah! "
                f"Heute mit von der Partie: {members}",
                tts=False,
            )

    @reminder_checker.before_loop
    async def before_reminder_loop(self) -> None:
        logging.debug("Waiting for reminder time checker..")
        await self.bot.wait_until_ready()
        logging.info("Reminder time checker started!")
