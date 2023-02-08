'''Cog for the faith point mechanic'''
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
    '''Setup function for the cog.'''
    await bot.add_cog(Gartic(bot))
    logging.info('Cog: Gartic geladen.')


async def generate_random_painting() -> None:
    '''Generates a combination of prompt and drawing from a random gartic phone game.'''

    gartic_rounds = [
        round for round in os.listdir("gartic")
        if re.match(r"^\d{3}$", round)
    ]

    gartic_round = random.choice(gartic_rounds)

    gartic_stories = [
        story for story in os.listdir(f"gartic/{gartic_round}")
        if re.match(r"^album_.*\.gif$", story)
    ]

    gartic_story = random.choice(gartic_stories)

    story_gif = Image.open(f"gartic/{gartic_round}/{gartic_story}")

    position = random.randint(0, math.floor(story_gif.n_frames/2) - 1)

    story_gif.seek(2*position)
    story_gif.save("gartic_text.png")
    story_gif.seek(2*position + 1)
    story_gif.save("gartic_image.png")

    output_image = Image.new(
        'RGB', (story_gif.width, 2*story_gif.height)
    )

    image_top = Image.open("gartic_text.png")
    image_bottom = Image.open("gartic_image.png")

    output_image.paste(im=image_top, box=(0, 0))
    output_image.paste(im=image_bottom, box=(0, story_gif.height))

    output_image.save("gartic_output.png")


class Gartic(commands.Cog, name='Gartic'):
    '''This cog includes everything related to the gartic mechanic'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.daily_gartic.start()

    async def cog_unload(self) -> None:
        self.daily_gartic.cancel()

    @commands.command(
        name='gartic',
        brief='Zeigt ein zufälliges Gartic-Gemälde aus dem Archiv.'
    )
    async def _gartic(
        self,
        ctx: commands.Context
    ) -> None:
        '''Zeigt ein zufälliges Gartic-Gemälde aus dem Archiv.'''

        await generate_random_painting()

        await ctx.send(
            file=discord.File('gartic_output.png')
        )

    @tasks.loop(time=dt.time(19, 30, tzinfo=get_local_timezone()))
    async def daily_gartic(self) -> None:
        '''Posts a daily gartic image to the right channel.'''

        await generate_random_painting()

        channel = self.bot.get_channel(815702384688234538)

        if channel is None or not isinstance(channel, discord.TextChannel):
            return

        await channel.send(
            "Guten Abend, Krah Krah! Hier kommt das tägliche "
            + "Highlight aus dem Gartic Phone-Archiv, Krah Krah!",
            file=discord.File('gartic_output.png')
        )

    @daily_gartic.before_loop
    async def _before_gartic_loop(self):
        logging.debug('Waiting for daily gartic loop...')
        await self.bot.wait_until_ready()
        logging.debug('Daily gartic loop running!')
