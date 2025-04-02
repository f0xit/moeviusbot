"""Cog for random quote generation"""

from __future__ import annotations

import datetime as dt
import logging
import time
from typing import TYPE_CHECKING

import discord
import markovify
from discord.ext import commands, tasks

from tools.check_tools import is_super_user
from tools.dt_tools import get_local_timezone
from tools.embed_tools import QuoteEmbed
from tools.textfile_tools import lines_from_textfile, lines_to_textfile

if TYPE_CHECKING:
    from bot import Bot


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    quote_cog = Quote(bot)

    await quote_cog.build_markov()

    await bot.add_cog(quote_cog)
    logging.info("Cog loaded: Quote.")


class Quote(commands.Cog, name="Quote"):
    """This cog includes commands for random quote generation"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.quote_by = ""
        self.text_model = None
        self.daily_quote.start()

    async def cog_unload(self) -> None:
        self.daily_quote.cancel()
        logging.info("Cog unloaded: Quote.")

    async def build_markov(self, size: int = 3) -> bool:
        """Generates a markov model from the channel_messages.txt file.

        Args:
            size (int, optional): The number of words per slice in the model. Defaults to 3.

        Returns:
            bool: Is True, if the generation was successful, and False, if the generation failed."""

        start_time = time.time()

        if not (channel_messages := await lines_from_textfile("channel_messages.txt")):
            logging.error("No channel messages found!")
            return False

        self.quote_by = channel_messages.pop(0)
        self.text_model = markovify.NewlineText("\n".join(channel_messages), state_size=size)

        logging.info("Generation finished. Size: %s Duration: %s", size, time.time() - start_time)
        return True

    async def send_quote(
        self,
        channel: discord.TextChannel | discord.DMChannel,
        /,
        content: str | None = None,
        title: str = "Zitat",
        tries: int = 3000,
    ) -> None:
        """Posts a random quote into a discord channel using an embed.

        Args:
            channel (discord.TextChannel): A discord text channel.
            content (str | None, optional): Message above the embed. Defaults to None.
            title (str, optional): The title of the posted embed. Defaults to 'Zitat'.
            tries (int, optional): Tries the markov model uses to find a quote. Defaults to 3000.
        """

        if self.text_model is None:
            return

        quote = self.text_model.make_sentence(tries=tries)

        if quote is None:
            logging.warning("No quote found!")
            await channel.send(
                "Ich habe wirklich alles versucht, aber ich konnte einfach kein Zitat finden, Krah Krah!"
            )
            return

        quote = quote.replace(">", "")

        await channel.send(content=content, embed=QuoteEmbed(title, quote, self.quote_by))

        logging.info("Quote successful.")
        logging.debug("%s - Author: %s", quote, self.quote_by)

    @commands.group(name="zitat", aliases=["z"], brief="Zitiert eine weise Persönlichkeit.")
    async def _quote(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is not None or not isinstance(ctx.channel, discord.TextChannel | discord.DMChannel):
            return

        logging.info("%s requested a quote by %s.", ctx.author.name, self.quote_by)

        await self.send_quote(ctx.channel)

    @is_super_user()
    @_quote.command(
        name="downloadHistory",
        aliases=["dh"],
        brief="Besorgt sich die nötigen Daten für den Zitategenerator. "
        "ACHTUNG: Kann je nach Limit einige Sekunden bis Minuten dauern.",
    )
    async def _download_history(self, ctx: commands.Context, member: discord.Member, lim: int = 1000) -> None:
        quote_by = member.display_name

        await ctx.send(
            f"History Download: Lade pro Channel maximal {lim} "
            f"Nachrichten von {quote_by} herunter, "
            "Krah Krah! Das kann einen Moment dauern, Krah Krah!"
        )
        logging.info(
            "%s starts downloading the messages by %s, limit per channel: %s.",
            ctx.author.name,
            quote_by,
            lim,
        )

        start_time = time.time()
        sentences = [quote_by]

        if (rammgut := self.bot.get_guild(323922215584268290)) is None:
            return

        number_of_channels = len(channels := rammgut.text_channels)

        for channel in channels:
            try:
                async for msg in channel.history(limit=lim):
                    if msg.author != member:
                        continue

                    sentences.extend(msg for msg in msg.content.split(". ") if msg)
            except discord.Forbidden as exc_msg:
                number_of_channels -= 1
                logging.warning("Can't read channel %s: %s", channel.name, str(exc_msg))
                continue

        number_of_sentences = len(sentences) - 1
        await lines_to_textfile("channel_messages.txt", sentences)

        await ctx.send(
            f"History Download abgeschlossen! {number_of_sentences} Sätze in {number_of_channels} "
            f"Channels von Author {quote_by} heruntergeladen. Dauer: {(time.time() - start_time)}"
        )
        logging.info(
            "History Download complete! %s sentences in %s channels by author %s. Duration: %s",
            number_of_sentences,
            number_of_channels,
            quote_by,
            time.time() - start_time,
        )

    @is_super_user()
    @_quote.command(name="build_markov", aliases=["bm"], brief="Generiert das Modell für zufällige Zitate.")
    async def _build_markov(self, ctx: commands.Context, size: int = 3) -> None:
        """Generiert das Modell für zufällige Zitate."""

        await ctx.send("Markov Update wird gestartet.")
        await self.build_markov(size)
        await ctx.send("Markov Update abgeschlossen.")

    @tasks.loop(time=dt.time(9, tzinfo=get_local_timezone()))
    async def daily_quote(self) -> None:
        """Loop to generate a daily quote at 9 AM"""

        logging.info("It's 9 AM, time for a daily quote!")

        if (channel := self.bot.get_channel(580143021790855178)) is None:
            logging.warning("Channel for daily quote not found!")
            return

        if not isinstance(channel, discord.TextChannel | discord.DMChannel):
            return

        await self.send_quote(channel, content="Guten Morgen, Krah Krah!", title="Zitat des Tages")

    @daily_quote.before_loop
    async def _before_daily_quote(self) -> None:
        logging.debug("Waiting for daily quote loop...")
        await self.bot.wait_until_ready()
        logging.info("Daily quote loop running!")
