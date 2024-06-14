"""Cog for polls"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from tools.check_tools import SpecialUser, is_special_user
from tools.converter_tools import convert_choices_to_list
from tools.embed_tools import PollEmbed
from tools.json_tools import DictFile
from tools.view_tools import PollView

if TYPE_CHECKING:
    from bot import Bot


MIN_CHOICES = 2


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    await bot.add_cog(Polls(bot))
    logging.info("Cog loaded: Polls.")


async def stop_poll(msg: discord.Message, polls: dict, poll_id: str) -> None:
    """Stops a running poll by deactivating the buttons of the given messsage."""

    choices = polls[poll_id]["choices"]
    votes = polls[poll_id]["votes"]

    view = PollView().deactivate_buttons_from_collection(choices, votes)

    await msg.edit(view=view)
    view.stop()


class Polls(commands.Cog, name="Umfragen"):
    """This cog includes commands for building polls"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.re_poll_button = re.compile(
            r"^moevius\:poll\:(?P<poll_id>\d+)\:choice\:(?P<choice>\w)\:iteration:(?P<iteration>\d+)$"
        )

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Polls.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.interactions.Interaction) -> None:
        """Poll interaction listener. Reacts to interactions that match the custom_id format for polls."""

        if interaction is None or interaction.data is None or "custom_id" not in interaction.data:
            logging.debug("Interaction empty or no custom_id.")
            return

        await interaction.response.defer()

        if (interaction_match := self.re_poll_button.match(interaction.data["custom_id"])) is None:
            logging.debug("Empty regex Match from custom_id. Not relevant for polls.")
            return

        poll_id, choice_id, iter_str = interaction_match.groups()

        polls = DictFile("polls")
        votes = polls[poll_id]["votes"]
        choices = polls[poll_id]["choices"]
        user_id = str(interaction.user.id)
        iteration = int(iter_str)

        if user_id not in votes:
            votes[user_id] = [choice_id]
        elif choice_id not in votes[user_id]:
            votes[user_id].append(choice_id)
        else:
            votes[user_id].remove(choice_id)

        polls.save()

        if interaction.message is None:
            logging.error("Message not found in interaction.")
            return

        view = PollView().buttons_from_collection(choices, votes, poll_id, iteration)

        await interaction.followup.edit_message(interaction.message.id, view=view)

        await interaction.followup.send("Stimmabgabe erfolgreich!", ephemeral=True)

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
        description: str | None,
        choices_str: str,
    ) -> None:
        await ctx.defer()

        choices = convert_choices_to_list(choices_str)

        if len(choices) < MIN_CHOICES:
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
        view = PollView().buttons_from_choices(new_poll_id, choices)
        msg = await ctx.send(
            "Eine neue Umfrage, Krah Krah! Mehrfachauswahl erlaubt. "
            "Klicke um abszutimmen oder um deine Stimme zurückzunehmen.",
            embed=embed,
            view=view,
        )

        new_poll["message_id"] = str(msg.id)
        polls.update({new_poll_id: new_poll})

    @is_special_user([SpecialUser.SCHNENK, SpecialUser.HANS, SpecialUser.ZUGGI])
    @_poll.command(name="stop")
    @discord.app_commands.rename(poll_id="umfragen_id")
    @discord.app_commands.describe(poll_id="ID der Umfrage")
    async def _poll_stop(self, ctx: commands.Context, poll_id: str) -> None:
        await ctx.defer(ephemeral=True)

        polls = DictFile("polls")

        if poll_id not in polls:
            await ctx.send("Fehler! Poll ID nicht gefunden!", ephemeral=True)
            logging.warning("Poll ID not found!")
            return

        if (msg := (await ctx.fetch_message(int(polls[poll_id]["message_id"])))) is None:
            await ctx.send("Fehler! Nachricht mit Poll nicht gefunden!", ephemeral=True)
            logging.warning("Message not found!")
            return

        await stop_poll(msg, polls, poll_id)

        await ctx.send("Poll deaktiviert!", ephemeral=True)
