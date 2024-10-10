"""Cog for polls"""

import datetime as dt
import logging
from typing import Literal, Optional

import discord
from discord.ext import commands
from discord.ext.commands import BadArgument
from discord.utils import escape_markdown

from bot import Bot
from tools.check_tools import SpecialUser, is_special_user
from tools.converter_tools import convert_choices_to_list, convert_str_to_dt
from tools.dt_tools import get_local_timezone


def emoji_from_asciilo(ch: str) -> str:
    """Transforms lowercase ascii chars into corresponding regional indicator."""
    return chr(0x1F1E6 + ord(ch) - 97)


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    await bot.add_cog(Polls(bot))
    logging.info("Cog loaded: Polls.")


class Poll(discord.Poll):
    def __init__(
        self,
        question: str,
        duration: dt.timedelta,
        choices: list[tuple[str, str]],
        *,
        multiple: bool,
    ) -> None:
        super().__init__(escape_markdown(question), duration, multiple=multiple)

        for ch, text in choices:
            self.add_answer(text=text, emoji=emoji_from_asciilo(ch))


class Polls(commands.Cog, name="Umfragen"):
    """This cog includes commands for building polls"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Polls.")

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @commands.hybrid_group(name="poll", fallback="start")
    @discord.app_commands.rename(
        question="frage",
        choices_str="antworten",
        description="beschreibung",
        end_str="endzeitpunkt",
        multi_str="mehrfachantwort",
    )
    @discord.app_commands.describe(
        question="Was möchtest du fragen?",
        choices_str="Antwortmöglichkeiten, getrennt mit Semikolon",
        description="Optionale Beschreibung",
        end_str="HH:MM oder DD.MM. HH:MM",
        multi_str="Standard: Ja",
    )
    async def _poll(
        self,
        ctx: commands.Context,
        question: str,
        choices_str: str,
        description: Optional[str],
        end_str: Optional[str],
        multi_str: Optional[Literal["Ja", "Nein"]],
    ) -> None:
        await ctx.defer()

        try:
            if end_str is None:
                duration = dt.timedelta(weeks=2)
            else:
                duration = await convert_str_to_dt(end_str) - dt.datetime.now(get_local_timezone())
        except BadArgument:
            await ctx.send("Datum nicht erkannt. Bitte verwende HH:MM oder DD.MM. HH:MM, Krah Krah!", ephemeral=True)
            return

        multiple = multi_str is None or multi_str == "Ja"

        try:
            choices = convert_choices_to_list(choices_str)
        except BadArgument:
            await ctx.send("Bitte gib mindestens 2 Antwortmöglichkeiten an, Krah Krah!", ephemeral=True)
            return

        await ctx.send(description, poll=Poll(question, duration, choices, multiple=multiple))

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @_poll.command(name="stop")
    @discord.app_commands.rename(msg="nachricht")
    @discord.app_commands.describe(msg="Nachricht mit der Umfrage")
    async def _poll_stop(self, ctx: commands.Context, msg: discord.Message) -> None:
        await msg.end_poll()

        await ctx.send("Umfrage wurde gestoppt, Krah Krah!", ephemeral=True)
