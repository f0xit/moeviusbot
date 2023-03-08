'''Cog for miscellaneous fun commands'''
import logging
import math
import random
import re

import discord
from bs4 import BeautifulSoup
from discord.ext import commands

from bot import Bot
from tools.json_tools import DictFile
from tools.request_tools import async_request_html
from tools.textfile_tools import lines_from_textfile


async def setup(bot: Bot) -> None:
    '''Setup function for the cog.'''
    await bot.add_cog(Misc(bot))
    logging.info('Cog loaded: Misc.')


class Misc(commands.Cog, name='Sonstiges'):
    '''This cog includes some miscellaneous fun commands'''

    def __init__(self, bot: Bot):
        self.bot = bot
        self.fragen = lines_from_textfile('fragen.txt')
        self.bible = lines_from_textfile('moevius-bibel.txt')
        self.responses = DictFile('responses')

    async def cog_unload(self) -> None:
        logging.info('Cog unloaded: Misc.')

    @commands.command(
        name='ps5',
        brief='Vergleicht die erste Zahl aus der vorherigen Nachricht mit dem  Preis einer PS5.'
    )
    async def _ps5(self, ctx: commands.Context):
        '''Vergleicht die erste Zahl aus der vorherigen Nachricht mit dem  Preis einer PS5.'''

        ps5_url = 'https://direct.playstation.com/de-de/buy-consoles/playstation5-console'
        ps5_soup = BeautifulSoup(await async_request_html(ps5_url), 'html.parser')

        price_tag = ps5_soup.find_all('span', class_='product-price')[0]
        price_sup_tag = ps5_soup.find_all('sup', class_='product-price-sup')[1]

        if price_tag is None or price_sup_tag is None:
            return

        ps5_price = float(price_tag.text) + float(price_sup_tag.text) / 100

        message = [msg async for msg in ctx.channel.history(limit=2)][1].content

        if (re_match := re.search(r"\d+(,\d+)?", message)) is None:
            return

        number = float(re_match.group(0).replace(',', '.'))

        quot_ps5 = number / ps5_price

        if quot_ps5 < 1:
            await ctx.send(
                f'Wow, das reicht ja gerade mal für {round(quot_ps5*100)}% einer PS5.'
            )
        else:
            await ctx.send(
                f'Wow, das reicht ja gerade mal für {math.floor(quot_ps5)} '
                f'{"PS5" if math.floor(quot_ps5) == 1 else "PS5en"}.'
            )

    @commands.command(
        name='frage',
        aliases=['f'],
        brief='Stellt eine zufällige Frage.'
    )
    async def _frage(self, ctx: commands.Context):
        '''Stellt eine zufällige Frage.'''

        if self.fragen is None:
            return

        frage = random.choice(self.fragen)

        await ctx.send(
            embed=discord.Embed(
                title=f'Frage an {ctx.author.display_name}',
                colour=discord.Colour(0xff00ff),
                description=frage
            )
        )

        logging.info('%s requested a question', ctx.author.name)
        logging.debug(frage)

    @commands.command(
        name='bibel',
        aliases=['bi'],
        brief='Präsentiert die Weisheiten des Krächzers.'
    )
    async def _bibel(self, ctx: commands.Context):
        '''Präsentiert die Weisheiten des Krächzers.'''

        if self.bible is None:
            return

        quote = random.choice(self.bible)

        await ctx.send(
            embed=discord.Embed(
                title='Das Wort unseres Herrn, Krah Krah!',
                colour=discord.Colour(0xff00ff),
                description=quote
            )
        )

        logging.info('%s requested a bible quote', ctx.author.name)
        logging.debug(quote)

    @commands.command(
        name='ult',
        aliases=['Q', 'q'],
        brief='Die ultimative Fähigkeit von Mövius dem Krächzer.'
    )
    async def _ult(self, ctx: commands.Context) -> None:
        '''Platzhalter: Das Ult-Kommando ist aktuell deaktiviert'''

        await ctx.send(
            'Die Ult ist aktuell deaktiviert, bitte bleiben Sie in der Leitung, Krah Krah!'
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        '''Listens for words in the responses-file and replies as defined.'''

        if message.author == self.bot.user:
            return

        # Requests from file
        if message.content[1:] in self.responses['req']:
            response = self.responses['req'][message.content[1:]]
            for res in response['res']:
                await message.channel.send(res.format(**locals(), **globals()))
            logging.info(response['log'].format(**locals(), **globals()))

        # Responses from file
        else:
            for key in self.responses['res']:
                if re.search(key, message.content):
                    response = self.responses['res'][key]
                    for res in response['res']:
                        await message.channel.send(
                            content=res.format(**locals(), **globals()), tts=False
                        )
                    logging.info(response['log'].format(
                        **locals(), **globals()))
