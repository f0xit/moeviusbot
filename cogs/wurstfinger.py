"""Cog for text correction and the opposite"""

import logging
from typing import TYPE_CHECKING

from autocorrect import Speller
from discord.ext import commands

from tools.text_tools import schnenkify

if TYPE_CHECKING:
    from bot import Bot


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(Wurstfinger(bot))
    logging.info("Cog loaded: Wurstfinger.")


class Wurstfinger(commands.Cog, name="Wurstfinger"):
    """This cog contains command for text correction and the opposite"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.speller = Speller()

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Wurstfinger.")

    @commands.command(name="schnenk", aliases=["Schnenk"])
    async def _schnenk(self, ctx: commands.Context, percent: int = 5) -> None:
        message = [message async for message in ctx.channel.history(limit=2)][1].content
        schnenk = schnenkify(message=message, percent=percent)

        await ctx.send(f"Oder wie Schnenk es sagen würde:\n{schnenk} Krah Krah!")

    @commands.command(name="wurstfinger")
    async def _wurstfinger(self, ctx: commands.Context) -> None:
        message = [msg async for msg in ctx.channel.history(limit=2)][1].content
        correction = self.speller(message)

        await ctx.send(f"Meintest du vielleicht: {correction}")
        logging.info('Wurstfinger: "%s" → "%s".', message, correction)
