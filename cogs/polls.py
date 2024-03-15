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


async def stop_poll(msg: discord.Message) -> None:
    view = discord.ui.View()

    for item in msg.components:
        if not isinstance(item, discord.ui.Button):
            continue
        item.disabled = True
        view.add_item(item)

    await msg.edit(view=view)
    view.stop()


class Polls(commands.Cog, name="Umfragen"):
    """This cog includes commands for building polls"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.poll_messages: list[discord.Message] = []

    async def cog_unload(self) -> None:
        for msg in self.poll_messages:
            await stop_poll(msg)

        logging.info("Cog unloaded: Polls.")

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

        embed = PollEmbed(new_poll_id, new_poll)
        view = PollView(new_poll_id, choices)

        msg = await ctx.send(embed=embed, view=view)

        new_poll["message_id"] = str(msg.id)
        polls.update({new_poll_id: new_poll})

        self.poll_messages.append(msg)

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @_poll.command(name="stop")
    @discord.app_commands.rename(
        poll_id="umfragen_id",
        message_id="nachrichten_id",
    )
    @discord.app_commands.describe(
        poll_id="ID der Umfrage",
        message_id="ID der Nachricht mit der Umfrage",
    )
    async def _poll_stop(
        self,
        ctx: commands.Context,
        poll_id: Optional[str],
        message_id: Optional[str],
    ) -> None:
        if poll_id is None and message_id is None:
            return

        await ctx.defer()

        if message_id is None:
            polls = DictFile("polls")

            if poll_id not in polls:
                return

            message_id = str(polls[poll_id]["message_id"])

        msg = await ctx.fetch_message(int(message_id))

        if msg is None:
            return

        await stop_poll(msg)

        await ctx.send("Deaktiviert!", ephemeral=True)
