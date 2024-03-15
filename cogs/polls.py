"""Cog for polls"""

import logging
from string import ascii_lowercase
from typing import Optional

import discord
from discord.ext import commands

from bot import Bot
from tools.check_tools import SpecialUser, is_special_user
from tools.embed_tools import PollEmbed
from tools.json_tools import DictFile
from tools.view_tools import PollView


def convert_choices_to_list(choices_str) -> list[tuple[str, str]]:
    return list(
        zip(ascii_lowercase, [name for name in map(str.strip, choices_str.split(";")) if name])
    )


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    await bot.add_cog(Polls(bot))
    logging.info("Cog loaded: Polls.")


class Polls(commands.Cog, name="Umfragen"):
    """This cog includes commands for building polls"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @commands.hybrid_group(name="poll", fallback="start")
    @discord.app_commands.rename(
        title="titel",
        description="beschreibung",
        choices_str="antworten",
    )
    @discord.app_commands.describe(
        title="Titel der Umfrage",
        description="Optionale Beschreibung",
        choices_str="Antwortmöglichkeiten, getrennt mit Semikolon",
    )
    async def _poll(
        self,
        ctx: commands.Context,
        title: str,
        description: Optional[str],
        choices_str: str,
    ) -> None:
        await ctx.defer()

        choices = convert_choices_to_list(choices_str)

        if len(choices) < 2:
            await ctx.send(
                "Bitte gib mindestens 2 Antwortmöglichkeiten an. Beispiel: Apfel; Birne; Krah Krah!",
                ephemeral=True,
            )
            return

        try:
            polls = DictFile("polls")
            new_poll_id = str(max(map(int, polls)) + 1)
        except ValueError:
            new_poll_id = "0"

        new_poll = {
            "title": title,
            "description": description,
            "choices": dict(choices),
            "votes": {},
        }

        polls.update({new_poll_id: new_poll})

        embed = PollEmbed(new_poll_id, new_poll)
        view = PollView(new_poll_id, choices)

        await ctx.send(embed=embed, view=view)
