import os
import sys
import getopt
import logging
import subprocess
import random
import re
import datetime as dt
import math
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from event import Event
from myfunc import strfdelta
from bot import Bot
from tools.logger_tools import LoggerTools


async def setup(bot: Bot) -> None:
    await bot.add_cog(Misc(bot))
    logging.info("Cog: Misc loaded.")


class Misc(commands.Cog, name='Sonstiges'):
    '''Ein paar spaßige Kommandos für zwischendurch.'''

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        name='ps5',
        brief='Vergleicht die erste Zahl aus der vorherigen Nachricht mit dem  Preis einer PS5.'
    )
    async def _ps5(self, ctx: commands.Context):
        ps5_price = 499

        history = [msg async for msg in ctx.channel.history(limit=2)]
        message = history[1].content

        number = float(
            re.search(r"\d+(,\d+)?", message).group(0).replace(',', '.')
        )

        quot_ps5 = number / ps5_price

        if quot_ps5 < 1:
            await ctx.send(f"Wow, das reicht ja gerade mal für {round(quot_ps5*100)}% einer PS5.")
        else:
            await ctx.send(
                f"Wow, das reicht ja gerade mal für {math.floor(quot_ps5)} "
                f"{'PS5' if math.floor(quot_ps5) == 1 else 'PS5en'}."
            )

    @commands.command(
        name='frage',
        aliases=['f'],
        brief='Stellt eine zufällige Frage.'
    )
    async def _frage(self, ctx: commands.Context):
        frage = random.choice(self.bot.fragen)

        embed = discord.Embed(
            title=f"Frage an {ctx.author.display_name}",
            colour=discord.Colour(0xff00ff),
            description=frage
        )

        await ctx.send(embed=embed)
        logging.info(
            "%s hat eine Frage verlangt. Sie lautet: %s",
            ctx.author.name,
            frage
        )

    @commands.command(
        name='bibel',
        aliases=['bi'],
        brief='Präsentiert die Weisheiten des Krächzers.'
    )
    async def _bibel(self, ctx: commands.Context):
        quote = random.choice(self.bot.bible)

        embed = discord.Embed(
            title="Das Wort unseres Herrn, Krah Krah!",
            colour=discord.Colour(0xff00ff),
            description=quote
        )

        await ctx.send(embed=embed)
        logging.info(
            "%s hat ein Bibel-Zitat verlangt. Es lautet: %s",
            ctx.author.name,
            quote
        )

    @commands.command(
        name='ult',
        aliases=['Q', 'q'],
        brief='Die ultimative Fähigkeit von Mövius dem Krächzer.'
    )
    async def _ult(self, ctx: commands.Context, *args) -> None:
        '''Platzhalter: Das Ult-Kommando ist aktuell deaktiviert'''

        await ctx.send(
            'Die Ult ist aktuell deaktiviert, bitte bleiben Sie in der Leitung, Krah Krah!'
        )
