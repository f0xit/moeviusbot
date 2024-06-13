"""Cog for miscellaneous fun commands"""

from __future__ import annotations

import logging
import math
import random
import re
from enum import Enum
from typing import TYPE_CHECKING

import discord
from bs4 import BeautifulSoup
from discord.ext import commands

from tools.json_tools import DictFile
from tools.request_tools import async_request_html
from tools.textfile_tools import lines_from_textfile

if TYPE_CHECKING:
    from bot import Bot


class ListType(Enum):
    """Enum of available list types"""

    NONE = 0
    QUESTION = 1
    BIBLE = 2


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    misc_cog = Misc(bot)
    await misc_cog.load_all_lists_from_file()
    await bot.add_cog(misc_cog)
    logging.info("Cog loaded: Misc.")


class Misc(commands.Cog, name="Sonstiges"):
    """This cog includes some miscellaneous fun commands"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.fragen: list[str] = []
        self.bible: list[str] = []
        self.responses = DictFile("responses")

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Misc.")

    async def load_all_lists_from_file(self) -> None:
        """Asynchronously loading the files for fragen and bible into their corresponding lists."""

        self.fragen = await lines_from_textfile("fragen.txt")
        self.bible = await lines_from_textfile("moevius-bibel.txt")

        logging.info("Files loaded. Fragen: %s - Bible: %s", len(self.fragen), len(self.bible))

    @commands.command(
        name="ps5",
        brief="Vergleicht die erste Zahl aus der vorherigen Nachricht mit dem  Preis einer PS5.",
    )
    async def _ps5(self, ctx: commands.Context) -> None:
        """Vergleicht die erste Zahl aus der vorherigen Nachricht mit dem  Preis einer PS5."""

        message = [msg async for msg in ctx.channel.history(limit=2)][1].content

        if (re_match := re.search(r"\d+(,\d+)?", message)) is None:
            logging.error("No number found in message!")
            return

        try:
            number = float(re_match.group(0).replace(",", "."))
        except ValueError:
            logging.exception("Unable to parse float!")
            return

        ps5_url = "https://direct.playstation.com/de-de/buy-consoles/playstation5-console"

        ps5_soup = BeautifulSoup(await async_request_html(ps5_url), "html.parser")

        price_tag = ps5_soup.find_all("span", class_="product-price")[0]
        price_sup_tag = ps5_soup.find_all("sup", class_="product-price-sup")[1]

        if price_tag is None or price_sup_tag is None:
            logging.error("Price Tag for PS5 not found on website!")
            return

        ps5_price = float(price_tag.text) + float(price_sup_tag.text) / 100

        quot_ps5 = number / ps5_price

        if quot_ps5 < 1:
            await ctx.send(f"Wow, das reicht ja gerade mal für {round(quot_ps5*100)}% einer PS5.")
        else:
            await ctx.send(
                f'Wow, das reicht ja gerade mal für {math.floor(quot_ps5)} '
                f'{"PS5" if math.floor(quot_ps5) == 1 else "PS5en"}.'
            )

    async def embed_random_item(self, ctx: commands.Context, choice: ListType = ListType.NONE) -> str | None:
        """Sends a Discord embed with a random item from a chosen list."""

        match choice:
            case ListType.NONE:
                return None

            case ListType.QUESTION:
                if not self.fragen:
                    self.fragen = await lines_from_textfile("fragen.txt")

                description = random.SystemRandom().choice(self.fragen)
                title = f"Frage an {ctx.author.display_name}"

            case ListType.BIBLE:
                if not self.bible:
                    self.fragen = await lines_from_textfile("moevius-bibel.txt")

                description = random.SystemRandom().choice(self.bible)
                title = "Das Wort unseres Herrn, Krah Krah!"

        await ctx.send(embed=discord.Embed(title=title, colour=discord.Colour(0xFF00FF), description=description))

        return description

    @commands.command(name="frage", aliases=["f"], brief="Stellt eine zufällige Frage.")
    async def _frage(self, ctx: commands.Context) -> None:
        """Stellt eine zufällige Frage."""

        logging.info("%s requested a question", ctx.author.name)

        if item := await self.embed_random_item(ctx, ListType.QUESTION) is None:
            logging.error("Could not send a question!")
            return

        logging.debug(item)

    @commands.command(name="bibel", aliases=["bi"], brief="Präsentiert die Weisheiten des Krächzers.")
    async def _bibel(self, ctx: commands.Context) -> None:
        """Präsentiert die Weisheiten des Krächzers."""

        logging.info("%s requested a bible quote", ctx.author.name)

        if item := await self.embed_random_item(ctx, ListType.BIBLE) is None:
            logging.error("Could not send a bible quote!")
            return

        logging.debug(item)

    @commands.command(name="ult", aliases=["Q", "q"], brief="Die ultimative Fähigkeit von Mövius dem Krächzer.")
    async def _ult(self, ctx: commands.Context) -> None:
        """Platzhalter: Das Ult-Kommando ist aktuell deaktiviert"""

        await ctx.send("Die Ult ist aktuell deaktiviert, bitte bleiben Sie in der Leitung, Krah Krah!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listens for words in the responses-file and replies as defined."""

        if message.author == self.bot.user:
            return

        # Requests from file
        if message.content[1:] in self.responses["req"]:
            response = self.responses["req"][message.content[1:]]
            for res in response["res"]:
                await message.channel.send(res.format(**locals(), **globals()))
            logging.info(response["log"].format(**locals(), **globals()))

        # Responses from file
        else:
            for key in self.responses["res"]:
                if re.search(key, message.content):
                    response = self.responses["res"][key]
                    for res in response["res"]:
                        await message.channel.send(content=res.format(**locals(), **globals()), tts=False)
                    logging.info(response["log"].format(**locals(), **globals()))
