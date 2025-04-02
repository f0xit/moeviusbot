"""Cog for the urban dictionary command"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from urllib.parse import quote as urlquote

import discord
from bs4 import BeautifulSoup, NavigableString
from discord.ext import commands

from tools.request_tools import async_request_html

if TYPE_CHECKING:
    from bot import Bot


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    await bot.add_cog(UrbanDict(bot))
    logging.info("Cog loaded: UrbanDict.")


def format_url(url: str, term: str) -> str:
    """Formats the url combined with a serch term.

    Args:
        url (str): The url, needs to end with ?term=
        term (str): The search term.

    Returns:
        str: The formatted url including the search term
    """

    return url + urlquote(term.replace(" ", "+"))


async def request_ud_definition(term: str) -> tuple[str, str]:
    """Uses the urban dictionary API and returns the first definition
    and the corresponding example sentence."""

    api_url = "http://api.urbandictionary.com/v0/define?term="

    data = json.loads(await async_request_html(format_url(api_url, term)))

    if not data["list"]:
        return ("", "")

    first_result: dict[str, str] = data["list"][0]

    definition = first_result["definition"].translate({ord(c): None for c in "[]"})
    example = first_result["example"].translate({ord(c): None for c in "[]"})

    return (definition, example)


async def request_try_these(term: str) -> list[str]:
    """Scrapes the urban dictionary website to find existing definitions,
    when the search term doesn't have one."""

    page_url = "https://www.urbandictionary.com/define.php?term="

    soup = BeautifulSoup((await async_request_html(format_url(page_url, term), 404)), "html.parser")

    if not (div := soup.find("div", class_="try-these")):
        msg = "No try-these found."
        raise OSError(msg)

    if isinstance(div, NavigableString):
        msg = "Div is navigable string, should be tag."
        raise OSError(msg)

    if not (items := div.find_all("li")[:10]):
        msg = "Could not find list items."
        raise OSError(msg)

    return [item.text for item in items]


class UrbanDict(commands.Cog, name="UrbanDict"):
    """Urban dictionary cog."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: UrbanDict.")

    @commands.command(name="urbandict", aliases=["ud"], brief="Durchforstet das Urban Dictionary")
    async def _urbandict(self, ctx: commands.Context, *args: str) -> None:
        term = " ".join(args)

        logging.info("%s looked for %s in the Urban Dictionary.", ctx.author.name, term)

        definition, example = await request_ud_definition(term)

        if definition:
            logging.debug("Definition found.")

            await ctx.send(
                embed=discord.Embed(
                    title=f"{term.title()}",
                    colour=discord.Colour(0xFF00FF),
                    url=format_url("https://www.urbandictionary.com/define.php?term=", term),
                    description=f"{definition}\n\n*{example}*",
                )
            )

            return

        logging.debug("No definition found, but a list of try-these.")

        try_these = await request_try_these(term)

        await ctx.send(
            content="Hey, ich habe habe dazu nichts gefunden, aber versuch's doch mal hiermit:",
            embed=discord.Embed(
                title=f"Suchvorschläge für {term.title()}",
                colour=discord.Colour(0xFF00FF),
                description="\n".join(try_these),
            ),
        )
