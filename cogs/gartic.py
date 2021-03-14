import os
import re
import random
import math
from PIL import Image
import discord
from discord.ext import commands

from myfunc import log, load_file, gcts

CHANNEL = 815702384688234538

def setup(bot):
    bot.add_cog(Gartic(bot))
    log("Cog: Gartic geladen.")

class Gartic(commands.Cog, name='Gartic'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='gartic',
        brief='Zeigt ein zufälliges Gartic-Gemälde aus dem Archiv.'
    )
    async def generate_random_painting(self, ctx, channel = None):
        raw_rounds = os.listdir("gartic")
        rounds = []

        for round in raw_rounds:
            if re.match(r"^\d{3}$", round):
                rounds.append(round)

        round = random.choice(rounds)


        raw_stories = os.listdir(f"gartic/{round}")
        stories = []

        for story in raw_stories:
            if re.match(r"^album_\w*.gif$", story):
                stories.append(story)

        story = random.choice(stories)


        story_gif = Image.open(f"gartic/{round}/{story}")

        position = random.randint(0, math.floor(story_gif.n_frames/2) - 1)

        story_gif.seek(2*position)
        story_gif.save("gartic_text.png")
        story_gif.seek(2*position + 1)
        story_gif.save("gartic_image.png")

        output_image = Image.new('RGB', (story_gif.width, 2*story_gif.height))

        image_top = Image.open("gartic_text.png")
        image_bottom = Image.open("gartic_image.png")

        output_image.paste(im=image_top, box=(0, 0))
        output_image.paste(im=image_bottom, box=(0, story_gif.height))

        output_image.save("gartic_output.png")

        if channel == None:
            await ctx.send(
                file=discord.File('gartic_output.png')
            )
        else:
            await channel.send(
                "Guten Abend, Krah Krah! Hier kommt das tägliche Highlight aus dem Gartic Phone-Archiv, Krah Krah!",
                file=discord.File('gartic_output.png')
            )
