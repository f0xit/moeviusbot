import os
import re
import random
import math
import logging
import datetime as dt
from PIL import Image
import discord
from discord.ext import commands, tasks
from bot import Bot
from tools.dt_tools import get_local_timezone


async def setup(bot: Bot) -> None:
    await bot.add_cog(Gartic(bot))
    logging.info("Cog: Gartic geladen.")


class Gartic(commands.Cog, name='Gartic'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.daily_gartic.start()

    async def cog_unload(self) -> None:
        self.daily_gartic.cancel()

    @commands.command(
        name='gartic',
        brief='Zeigt ein zufälliges Gartic-Gemälde aus dem Archiv.'
    )
    async def generate_random_painting(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel = None
    ) -> None:
        try:
            raw_rounds = os.listdir("gartic")
            rounds = []

            for round in raw_rounds:
                if re.match(r"^\d{3}$", round):
                    rounds.append(round)

            round = random.choice(rounds)
        except Exception as e:
            logging.error(e)

        try:
            raw_stories = os.listdir(f"gartic/{round}")
            stories = []

            for story in raw_stories:
                if re.match(r"^album_.*\.gif$", story):
                    stories.append(story)

            story = random.choice(stories)
        except Exception as e:
            logging.error(e)

        try:
            story_gif = Image.open(f"gartic/{round}/{story}")

            position = random.randint(0, math.floor(story_gif.n_frames/2) - 1)
        except Exception as e:
            logging.error(e)

        try:
            story_gif.seek(2*position)
            story_gif.save("gartic_text.png")
            story_gif.seek(2*position + 1)
            story_gif.save("gartic_image.png")

            output_image = Image.new(
                'RGB', (story_gif.width, 2*story_gif.height))

            image_top = Image.open("gartic_text.png")
            image_bottom = Image.open("gartic_image.png")

            output_image.paste(im=image_top, box=(0, 0))
            output_image.paste(im=image_bottom, box=(0, story_gif.height))

            output_image.save("gartic_output.png")

            if channel is None:
                await ctx.send(
                    file=discord.File('gartic_output.png')
                )
            else:
                await channel.send(
                    "Guten Abend, Krah Krah! Hier kommt das tägliche "
                    + "Highlight aus dem Gartic Phone-Archiv, Krah Krah!",
                    file=discord.File('gartic_output.png')
                )

        except Exception as e:
            logging.error(e)

    @commands.command(
        name='pick',
        brief='Zeigt ein spezifisches Gartic-Gemälde aus dem Archiv.'
    )
    async def pick(
        self,
        ctx: commands.Context,
        round: str,
        album: int,
        position: int
    ) -> None:
        raw_stories = os.listdir(f"gartic/{round}")
        stories = []

        for story in raw_stories:
            if re.match(r"^album_.*\.gif$", story):
                stories.append(story)

        output_image = Image.open(f"gartic/{round}/{stories[int(album)]}")
        output_image.seek(2*int(position)+1)
        output_image.save("gartic_output.png")

        await ctx.send(
            file=discord.File('gartic_output.png')
        )

    @tasks.loop(time=dt.time(19, 30, tzinfo=get_local_timezone()))
    async def daily_gartic(self) -> None:
        gartic_channel = 815702384688234538
        try:
            await self.generate_random_painting(
                None,
                channel=self.bot.get_channel(gartic_channel)
            )
        except Exception as exc_msg:
            logging.error(
                'ERROR: Kein Gartic-Image des Tages: %s', exc_msg
            )

    @daily_gartic.before_loop
    async def _before_gartic_loop(self):
        logging.debug('Waiting for daily gartic loop...')
        await self.bot.wait_until_ready()
        logging.debug('Daily gartic loop running!')
