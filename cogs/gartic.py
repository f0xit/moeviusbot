"""Cog for the faith point mechanic"""

import datetime as dt
import logging
import math
import random
import re
from pathlib import Path

import discord
from discord.ext import commands, tasks
from PIL import Image

from bot import Bot
from tools.dt_tools import get_local_timezone


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(Gartic(bot))
    logging.info("Cog loaded: Gartic.")


async def generate_random_painting() -> None:
    """Generates a combination of prompt and drawing from a random gartic phone game."""

    gartic_path = Path("gartic")
    cache_path = Path("cache")

    gartic_round = random.SystemRandom().choice(
        [directory for directory in gartic_path.iterdir() if re.match(r"^\d{3}$", directory.name)]
    )

    gartic_story = random.SystemRandom().choice(
        [file for file in gartic_round.iterdir() if re.match(r"^album_.*\.gif$", file.name)]
    )

    story_gif = Image.open(gartic_story)
    position = random.SystemRandom().randint(0, math.floor(story_gif.n_frames / 2) - 1)

    story_gif.seek(2 * position)
    story_gif.save(cache_path / "gartic_text.png")
    story_gif.seek(2 * position + 1)
    story_gif.save(cache_path / "gartic_image.png")

    output_image = Image.new("RGB", (story_gif.width, 2 * story_gif.height))

    image_top = Image.open(cache_path / "gartic_text.png")
    image_bottom = Image.open(cache_path / "gartic_image.png")

    output_image.paste(im=image_top, box=(0, 0))
    output_image.paste(im=image_bottom, box=(0, story_gif.height))

    output_image.save(cache_path / "gartic_output.png")


class Gartic(commands.Cog, name="Gartic"):
    """This cog includes everything related to the gartic mechanic"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        if not (cache_path := Path("cache")).exists():
            cache_path.mkdir()
            logging.warning("Created cache directory")

        self.daily_gartic.start()

    async def cog_unload(self) -> None:
        self.daily_gartic.cancel()
        logging.info("Cog unloaded: Gartic.")

    @commands.command(name="gartic", brief="Zeigt ein zufälliges Gartic-Gemälde aus dem Archiv.")
    async def _gartic(self, ctx: commands.Context) -> None:
        """Zeigt ein zufälliges Gartic-Gemälde aus dem Archiv."""

        await generate_random_painting()

        await ctx.send(file=discord.File("cache/gartic_output.png"))

    @tasks.loop(time=dt.time(19, 30, tzinfo=get_local_timezone()))
    async def daily_gartic(self) -> None:
        """Posts a daily gartic image to the right channel."""

        await generate_random_painting()

        channel = self.bot.get_channel(815702384688234538)

        if channel is None or not isinstance(channel, discord.TextChannel):
            return

        await channel.send(
            "Guten Abend, Krah Krah! Hier kommt das tägliche Highlight aus dem Gartic Phone-Archiv, Krah Krah!",
            file=discord.File("cache/gartic_output.png"),
        )

    @daily_gartic.before_loop
    async def _before_gartic_loop(self) -> None:
        logging.debug("Waiting for daily gartic loop...")
        await self.bot.wait_until_ready()
        logging.debug("Daily gartic loop running!")
