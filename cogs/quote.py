import logging
import random
import datetime as dt
import time
from typing import Tuple
import discord
from discord.ext import commands, tasks
import markovify
from bot import Bot
from tools.dt_tools import get_local_timezone
from tools.textfile_tools import lines_from_textfile, lines_to_textfile
from tools.check_tools import is_super_user


async def setup(bot: Bot) -> None:
    await bot.add_cog(Quote(bot))
    logging.info("Cog: Quote loaded.")


def build_markov(size: int = 3) -> Tuple[str, markovify.NewlineText]:
    """Generates a markov model from the channel_messages.txt file and
    returns it.

    Args:
        size (int, optional):
            The number of words per slice in the model. Defaults to 3.

    Returns:
        Tuple[str, markovify.NewlineText]:
            The first item contains the author of the messages, the second
            item is the model itself.
    """

    logging.debug('Markov build started with size %s...', size)
    start_time = time.time()

    channel_messages = lines_from_textfile('channel_messages.txt')
    author = channel_messages.pop(0)

    model = markovify.NewlineText(
        '\n'.join(channel_messages), state_size=size
    )

    logging.info(
        'Markov generation finished. Size: %s Duration: %s',
        size,
        time.time() - start_time
    )

    return author, model


class Quote(commands.Cog, name='Quote'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.quote_by, self.text_model = build_markov()
        self.daily_quote.start()

    async def cog_unload(self) -> None:
        self.daily_quote.cancel()

    async def send_quote(
        self,
        channel: discord.TextChannel,
        /,
        content: str | None = None,
        title: str = 'Zitat',
        tries: int = 3000
    ) -> None:
        '''Posts a random quote into a discord channel using an embed.

        Args:
            channel (discord.TextChannel): A discord text channel.
            content (str | None, optional): Message above the embed. Defaults to None.
            title (str, optional): The title of the posted embed. Defaults to 'Zitat'.
            tries (int, optional): Tries the markov model uses to find a quote. Defaults to 3000.
        '''
        quote = self.text_model.make_sentence(tries=tries)

        if quote is None:
            logging.warning('No quote found!')
            await channel.send(
                'Ich habe wirklich alles versucht, aber ich konnte einfach '
                'kein Zitat finden, Krah Krah!'
            )
            return

        quote = quote.replace('>', '')

        await channel.send(
            content=content,
            embed=discord.Embed(
                title=title,
                colour=discord.Colour(0xff00ff),
                description=quote,
                timestamp=dt.datetime.utcfromtimestamp(
                    random.randint(0, int(dt.datetime.now().timestamp()))
                )
            ).set_footer(text=self.quote_by)
        )

        logging.info('Quote successful.')
        logging.debug('%s - Author: %s', quote, self.quote_by)

    @commands.group(
        name='zitat',
        aliases=['z'],
        brief='Zitiert eine weise Persönlichkeit.'
    )
    async def _quote(self, ctx: commands.Context):
        if ctx.invoked_subcommand is not None:
            return

        logging.info(
            '%s requested a quote by %s.',
            ctx.author.name,
            self.quote_by
        )

        await self.send_quote(ctx.channel)

    @is_super_user()
    @_quote.command(
        name='downloadHistory',
        aliases=['dh'],
        brief='Besorgt sich die nötigen Daten für den Zitategenerator. '
        'ACHTUNG: Kann je nach Limit einige Sekunden bis Minuten dauern.'
    )
    async def _download_history(
        self, ctx: commands.Context, member: discord.Member, lim: int = 1000
    ) -> None:
        quote_by = member.display_name

        await ctx.send(
            f'History Download: Lade pro Channel maximal {lim} '
            f'Nachrichten von {quote_by} herunter, '
            'Krah Krah! Das kann einen Moment dauern, Krah Krah!'
        )
        logging.info(
            '%s starts downloading the messages by %s, limit per channel: %s.',
            ctx.author.name,
            quote_by,
            lim
        )

        start_time = time.time()
        sentences = [quote_by]

        rammgut = self.bot.get_guild(323922215584268290)  # Hard coded Rammgut

        number_of_channels = len(channels := rammgut.text_channels)

        for channel in channels:
            try:
                async for msg in channel.history(limit=lim):
                    if msg.author != member:
                        continue

                    sentences.extend(
                        msg for msg in msg.content.split('. ') if msg
                    )
            except discord.Forbidden as exc_msg:
                number_of_channels -= 1
                logging.warning(
                    'Can\'t read channel %s: %s',
                    channel.name,
                    str(exc_msg)
                )
                continue

        number_of_sentences = len(sentences) - 1
        lines_to_textfile('channel_messages.txt', sentences)

        await ctx.send(
            f'History Download abgeschlossen! {number_of_sentences} Sätze in {number_of_channels} '
            f'Channels von Author {quote_by} heruntergeladen. Dauer: {(time.time() - start_time)}'
        )
        logging.info(
            'History Download complete! %s sentences in %s '
            'channels by author %s. Duration: %s',
            number_of_sentences,
            number_of_channels,
            quote_by,
            time.time() - start_time
        )

    @is_super_user()
    @_quote.command(
        name='build_markov',
        aliases=['bm'],
        brief='Generiert das Modell für zufällige Zitate.'
    )
    async def _build_markov(self, ctx: commands.Context, size: int = 3) -> None:
        await ctx.send('Markov Update wird gestartet.')

        self.quote_by, self.text_model = build_markov(size)
        await ctx.send('Markov Update abgeschlossen.')

    @tasks.loop(time=dt.time(9, tzinfo=get_local_timezone()))
    async def daily_quote(self) -> None:
        logging.info('It\'s 9 AM, time for a daily quote!')

        if (channel := self.bot.get_channel(580143021790855178)) is None:
            logging.warning('Channel for daily quote not found!')
            return

        await self.send_quote(
            channel,
            ontent='Guten Morgen, Krah Krah!',
            title='Zitat des Tages'
        )

    @daily_quote.before_loop
    async def _before_daily_quote(self):
        logging.debug('Waiting for daily quote loop...')
        await self.bot.wait_until_ready()
        logging.debug('Daily quote loop running!')
