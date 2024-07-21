"""Cog for polls"""

import datetime as dt
import logging
from typing import Optional

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


class Polls(commands.Cog, name="Umfragen"):
    """This cog includes commands for building polls"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Polls.")

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @commands.hybrid_group(name="poll", fallback="start")
    @discord.app_commands.rename(
        title="titel",
        description="beschreibung",
        choices_str="antworten",
        ends_at_str="endzeitpunkt",
    )
    @discord.app_commands.describe(
        title="Titel der Umfrage",
        description="Optionale Beschreibung",
        choices_str="Antwortmöglichkeiten, getrennt mit Semikolon",
        ends_at_str="HH:MM oder DD.MM. HH:MM",
    )
    async def _poll(
        self,
        ctx: commands.Context,
        title: str,
        description: Optional[str],
        choices_str: str,
        ends_at_str: Optional[str],
    ) -> None:
        await ctx.defer()

        if ends_at_str is None:
            timedelta_to_end = dt.timedelta(weeks=2)
        else:
            try:
                end_date = await convert_str_to_dt(ends_at_str)
                timedelta_to_end = end_date - dt.datetime.now(get_local_timezone())
            except BadArgument:
                await ctx.send(
                    "Datum nicht erkannt. Bitte verwende HH:MM oder DD.MM. HH:MM, Krah Krah!",
                    ephemeral=True,
                )
            return

        new_poll = discord.Poll(
            escape_markdown(title),
            duration=timedelta_to_end,
            multiple=True,
        )

        try:
            for ch, text in convert_choices_to_list(choices_str):
                new_poll.add_answer(text=text, emoji=emoji_from_asciilo(ch))
        except BadArgument:
            await ctx.send(
                "Bitte gib mindestens 2 Antwortmöglichkeiten an. Beispiel: Apfel; Birne; Krah Krah!",
                ephemeral=True,
            )
            return

        await ctx.send(description, poll=new_poll)

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @_poll.command(name="stop")
    @discord.app_commands.rename(poll_id="umfragen_id")
    @discord.app_commands.describe(poll_id="ID der Umfrage")
    async def _poll_stop(self, ctx: commands.Context, msg: discord.Message) -> None:
        await msg.end_poll()

        await ctx.send("Umfrage wurde gestoppt, Krah Krah!", ephemeral=True)

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @_poll.command(name="info")
    @discord.app_commands.rename(poll_id="umfragen_id")
    @discord.app_commands.describe(poll_id="ID der Umfrage")
    async def _poll_info(self, ctx: commands.Context, msg: discord.Message) -> None:
        if msg.poll is None:
            return

        output = []

        for answer in msg.poll.answers:
            output.append(str(answer.emoji) + ", ".join([str(voter) async for voter in answer.voters()]))

        await ctx.send("Bisher wurde so abgestimmt: ```" + "\n".join(output) + "```")
