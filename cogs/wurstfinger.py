'''Cog for text correction and the opposite'''
import logging
import random
import re
import time
from discord.ext import commands
from autocorrect import Speller
from bot import Bot


async def setup(bot: Bot) -> None:
    '''Setup function for the cog.'''
    await bot.add_cog(Wurstfinger(bot))
    logging.info("Cog: Wurstfinger geladen.")


class Wurstfinger(commands.Cog, name='Wurstfinger'):
    '''This cog contains command for text correction and the opposite'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.speller = Speller()

        self.substitute = {
            'q': ['w', 'a'],
            'w': ['e', 's', 'a', 'q'],
            'e': ['r', 'd', 's', 'w'],
            'r': ['t', 'f', 'd', 'e'],
            't': ['z', 'g', 'f', 'e'],
            'z': ['u', 'h', 'g', 't'],
            'u': ['i', 'j', 'h', 'z'],
            'i': ['o', 'k', 'j', 'u'],
            'o': ['p', 'l', 'k', 'i'],
            'p': ['ü', 'ö', 'l', 'o'],
            'ü': ['ä', 'ö', 'p'],
            'a': ['q', 'w', 's', 'y'],
            's': ['w', 'e', 'd', 'x', 'y', 'a'],
            'd': ['e', 'r', 'f', 'c', 'x', 's'],
            'f': ['r', 't', 'g', 'v', 'c', 'd'],
            'g': ['t', 'z', 'h', 'b', 'v', 'f'],
            'h': ['z', 'u', 'j', 'n', 'b', 'g'],
            'j': ['u', 'i', 'k', 'm', 'n', 'h'],
            'k': ['i', 'o', 'l', 'm', 'j'],
            'l': ['o', 'p', 'ö', 'k'],
            'ö': ['p', 'ü', 'ä', 'l'],
            'ä': ['ü', 'ö'],
            'y': ['a', 's', 'x'],
            'x': ['s', 'd', 'c', 'y'],
            'c': ['d', 'f', 'v', 'x'],
            'v': ['f', 'g', 'b', 'c'],
            'b': ['g', 'h', 'n', 'v'],
            'n': ['h', 'j', 'm', 'b'],
            'm': ['j', 'k', 'n'],
            ' ': ['c', 'v', 'b', 'n', 'm']
        }

        logging.debug("Wurstfinger-Settings geladen.")

    @commands.command(
        name='schnenk',
        aliases=['Schnenk']
    )
    async def _schnenk(self, ctx: commands.Context, percent: int = 5) -> None:
        output = ""
        message = [message async for message in ctx.channel.history(limit=2)][1].content

        for character in message:
            uppercase = False

            if re.match(r'^[A-Z]$', character):
                uppercase = True
            elif re.match(r'^[1-9]$', character):
                output += character
                continue

            try:
                if random.randint(1, round(100/max(min(percent, 100), 1))) == 1:
                    character = random.choice(
                        self.substitute[character.lower()])
                    if uppercase:
                        character = character.upper()
            except KeyError:
                pass
            finally:
                output += character

        await ctx.send(f"Oder wie Schnenk, es sagen würde:\n{output} Krah Krah!")

    @commands.command(
        name='wurstfinger'
    )
    async def _wurstfinger(self, ctx: commands.Context) -> None:
        start_time = time.time()

        message = [msg async for msg in ctx.channel.history(limit=2)][1].content
        correction = self.speller(message)

        logging.info(
            'Wurstfinger: "%s" → "%s", Dauer: %s',
            message,
            correction,
            time.time() - start_time
        )

        await ctx.send(f"Meintest du vielleicht: {correction}")
