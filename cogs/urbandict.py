"""Cog for the urban dictionary command"""
import json
import logging
from typing import Tuple
from urllib.parse import quote as urlquote

import discord
from bs4 import BeautifulSoup, NavigableString
from discord.ext import commands
from result import Err, Ok, Result, UnwrapError

from bot import Bot
from tools.request_tools import async_request_html


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


async def request_ud_definition(term: str) -> Result[Tuple[str, str], str]:
    """Uses the urban dictionary API and returns the first definition
    and the corresponding example sentence."""

    api_url = "http://api.urbandictionary.com/v0/define?term="

    try:
        data = json.loads((await async_request_html(format_url(api_url, term))).unwrap())
    except UnwrapError as err_msg:
        return Err(f"API-Request failed: {err_msg}")

    if not data["list"]:
        return Ok(("", ""))

    first_result: dict[str, str] = data["list"][0]

    definition = first_result["definition"].translate({ord(c): None for c in "[]"})
    example = first_result["example"].translate({ord(c): None for c in "[]"})

    return Ok((definition, example))


async def request_try_these(term: str) -> Result[list[str], str]:
    """Scrapes the urban dictionary website to find existing definitions,
    when the search term doesn't have one."""

    page_url = "https://www.urbandictionary.com/define.php?term="

    try:
        soup = BeautifulSoup(
            (await async_request_html(format_url(page_url, term), 404)).unwrap(), "html.parser"
        )
    except UnwrapError as err_msg:
        return Err(f"API-Request failed: {err_msg}")

    if not (div := soup.find("div", class_="try-these")):
        return Err("No try-these found.")

    if isinstance(div, NavigableString):
        return Err("Div is navigable string, should be tag.")

    if not (items := div.find_all("li")[:10]):
        return Err("Could not find list items.")

    return Ok([item.text for item in items])


class UrbanDict(commands.Cog, name="UrbanDict"):
    """Urban dictionary cog."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: UrbanDict.")

    @commands.command(name="urbandict", aliases=["ud"], brief="Durchforstet das Urban Dictionary")
    async def _urbandict(self, ctx: commands.Context, *args):
        term = " ".join(args)

        logging.info("%s looked for %s in the Urban Dictionary.", ctx.author.name, term)

        try:
            definition, example = (await request_ud_definition(term)).unwrap()

        except UnwrapError as err_msg:
            logging.error(err_msg)
            return

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

        try:
            try_these = (await request_try_these(term)).unwrap()
        except UnwrapError as err_msg:
            logging.info("No definition found: %s", err_msg)
            await ctx.send("Dazu kann ich nun wirklich gar nichts sagen, Krah Krah!")
            return

        await ctx.send(
            content="Hey, ich habe habe dazu nichts gefunden, aber versuch's doch mal hiermit:",
            embed=discord.Embed(
                title=f"Suchvorschläge für {term.title()}",
                colour=discord.Colour(0xFF00FF),
                description="\n".join(try_these),
            ),
        )
