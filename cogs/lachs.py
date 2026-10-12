"""Cog for random quote generation"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import discord
import markovify
from discord.ext import commands

from tools.check_tools import is_super_user
from tools.embed_tools import QuoteEmbed
from tools.text_tools import schnenkify
from tools.textfile_tools import lines_from_textfile

if TYPE_CHECKING:
    from bot import Bot


async def setup(bot: Bot) -> None:
    quote_cog = Lachs(bot)

    await quote_cog.build_markov()

    await bot.add_cog(quote_cog)
    logging.info("Cog loaded: Lachs.")


class Lachs(commands.Cog, name="Lachs"):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.text_model = None

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Lachs.")

    async def build_markov(self, size: int = 3) -> bool:
        start_time = time.time()

        if not (lines := await lines_from_textfile("lachs.txt")):
            logging.error("No lines found!")
            return False

        self.text_model = markovify.NewlineText("\n".join(lines), state_size=size)

        logging.info("Generation finished. Size: %s Duration: %s", size, time.time() - start_time)
        return True

    async def salmon_status(
        self,
        channel: discord.TextChannel | discord.DMChannel,
        /,
        content: str | None = None,
        title: str = "Wie geht's dem Lachs?",
    ) -> None:
        if self.text_model is None:
            return

        salmon_status = self.text_model.make_sentence_with_start("Der Lachs", tries=100, test_output=False)
        schnenkified = schnenkify(salmon_status, percent=1)

        await channel.send(content=content, embed=QuoteEmbed(title, schnenkified, "Kochstudio by Schnenko"))

        logging.info("Lachs successful.")

    @commands.group(name="lachs", aliases=["z"], brief="Zitiert eine weise Persönlichkeit.")
    async def _lachs(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is not None or not isinstance(ctx.channel, discord.TextChannel | discord.DMChannel):
            return

        await self.salmon_status(ctx.channel)

    @is_super_user()
    @_lachs.command(name="build_markov", aliases=["bm"], brief="Generiert das Modell für zufällige Lachs Updates.")
    async def _build_markov(self, ctx: commands.Context, size: int = 3) -> None:
        """Generiert das Modell für zufällige Zitate."""

        await ctx.send("Markov Update wird gestartet.")
        await self.build_markov(size)
        await ctx.send("Markov Update abgeschlossen.")
