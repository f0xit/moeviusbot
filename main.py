import asyncio
import os
import sys
import logging
import subprocess
import datetime as dt
from dotenv import load_dotenv
import discord
from discord.ext import commands
from myfunc import strfdelta
from bot import Bot
from tools.logger_tools import LoggerTools
from tools.check_tools import is_super_user
from tools.py_version_tool import check_python_version

check_python_version()

STARTUP_TIME = dt.datetime.now()
LOG_TOOL = LoggerTools(level="DEBUG")

load_dotenv()
if (DISCORD_TOKEN := os.getenv('DISCORD_TOKEN')) is None:
    sys.exit('Discord token not found! Please check your .env file!')
else:
    logging.info('Discord token loaded successfully.')


class Administration(commands.Cog, name='Administration'):
    '''Diese Kategorie erfordert bestimmte Berechtigungen'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def load_ext(self, ctx: commands.Context, extension: str) -> None:
        '''Tries to load the given extension.

        Args:
            ctx (commands.Context): Invocation context. Needed for feedback message.
            extension (str): Name of the extension located in the cogs directory.
        '''
        try:
            await self.bot.load_extension(f'cogs.{extension}')
            await ctx.send('Die Extension wurde geladen.')
            logging.info('Extension loaded: %s', extension)
        except commands.ExtensionNotFound:
            await ctx.send(f'Fehler: Extension konnte nicht gefunden werden!')
            logging.warning('Extension not existing: %s', extension)
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f'Fehler: Extension bereits geladen!')
            logging.warning('Extension already loaded: %s', extension)
        except commands.NoEntryPointError:
            await ctx.send(f'Fehler: Extension hat keine Setup-Funktion!')
            logging.warning('Extension has no setup function: %s', extension)
        except commands.ExtensionFailed:
            await ctx.send(f'Fehler: Extension Setup fehlgeschlagen!')
            logging.warning('Extension setup failed: %s', extension)

    async def unload_ext(self, ctx: commands.Context, extension: str) -> None:
        '''Tries to unload the given extension.

        Args:
            ctx (commands.Context): Invocation context. Needed for feedback message.
            extension (str): Name of the extension located in the cogs directory.
        '''
        try:
            await self.bot.unload_extension(f'cogs.{extension}')
            await ctx.send('Die Extension wurde entfernt.')
            logging.info('Extension unloaded: %s', extension)
        except commands.ExtensionNotFound:
            await ctx.send(f'Fehler: Extension konnte nicht gefunden werden!')
            logging.warning('Extension not existing: %s', extension)
        except commands.ExtensionNotLoaded:
            await ctx.send(f'Fehler: Extension nicht geladen!')
            logging.warning('Extension not loaded: %s', extension)

    @commands.group(
        name='bot',
        aliases=['b'],
        brief='Kann den Bot steuern.'
    )
    async def _bot(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                'Was möchtest du mit dem Bot anfangen? '
                'Mit !help bot siehst du, welche Optionen verfügbar sind.'
            )

    @_bot.command(
        name='version',
        aliases=['-v']
    )
    async def _version(self, ctx: commands.Context) -> None:
        console_output = subprocess.check_output(
            'git describe --tags', shell=True
        ).strip().decode('ascii')

        try:
            res = console_output.split('-')
            version_string = ' '.join(res[:2]).title()
            if len(res) >= 2:
                version_string += f'.\nTag is {res[2]} commits behind.'
                version_string += f' Currently running commit {res[3][1:]}'

            await ctx.send(f'Bot läuft auf Version {version_string}')
            logging.info('Version %s', version_string)
        except IndexError:
            logging.error(
                'Something is wrong with the version string: %s', console_output
            )
            await ctx.send(f'Bot läuft auf Version {console_output}')
            logging.info('Version %s', version_string)

    @_bot.command(
        name='uptime',
        aliases=['-u']
    )
    async def _uptime(self, ctx: commands.Context) -> None:
        uptime = (dt.datetime.now() - STARTUP_TIME)
        uptimestr = strfdelta(
            uptime, '{days} Tage {hours}:{minutes}:{seconds}')

        await ctx.send(f'Uptime: {uptimestr} seit {STARTUP_TIME.strftime("%Y.%m.%d %H:%M:%S")}')
        logging.info(
            'Uptime: %s seit %s',
            uptimestr,
            STARTUP_TIME.strftime('%Y.%m.%d %H:%M:%S')
        )

    @is_super_user()
    @_bot.command(
        name='reload',
        aliases=['-r']
    )
    async def _reload(self, ctx: commands.Context) -> None:
        if ctx.prefix == '?':
            return

        logging.warning('%s hat einen Reload gestartet.', ctx.author.name)
        await ctx.send('Reload wird gestartet.')

        self.bot.load_files_into_attrs()
        self.bot.analyze_guild()

    @is_super_user()
    @commands.group(
        name='extensions',
        aliases=['ext'],
        brief='Verwaltet die Extensions des Bots.'
    )
    async def _extensions(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is not None:
            return

        await ctx.send(
            'Aktuell sind folgende Extensions geladen:\n'
            ', '.join(self.bot.extensions.keys())
        )
        await ctx.send('Mit !help ext siehst du, welche Optionen verfügbar sind.')
        logging.info(
            'Extensions active: %s',
            ', '.join(self.bot.extensions.keys())
        )

    @is_super_user()
    @_extensions.command(
        name='load',
        aliases=['-l'],
        brief='Lädt eine Extension in den Bot.'
    )
    async def _load(self, ctx: commands.Context, extension: str) -> None:
        if ctx.prefix == '?':
            return

        await self.load_ext(ctx, extension)

    @is_super_user()
    @_extensions.command(
        name='unload',
        aliases=['-u'],
        brief='Entfernt eine Extension aus dem Bot.'
    )
    async def _unload(self, ctx: commands.Context, extension: str) -> None:
        if ctx.prefix == '?':
            return

        await self.unload_ext(ctx, extension)

    @is_super_user()
    @_extensions.command(
        name='reload',
        aliases=['-r'],
        brief='Lädt eine Extension neu.'
    )
    async def _reload(self, ctx: commands.Context, extension: str) -> None:
        if ctx.prefix == '?':
            return

        await self.unload_ext(ctx, extension)
        await self.load_ext(ctx, extension)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.analyze_guild()

        for filename in os.listdir('./cogs'):
            if (filename.endswith('.py')
                    and not filename.startswith('__')
                    and f"cogs.{filename[:-3]}" not in self.bot.extensions.keys()):
                await self.bot.load_extension(f"cogs.{filename[:-3]}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user:
            return

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        logging.error(
            "%s - %s - %s",
            ctx.author.name, ctx.message.content, error
        )
        await self.bot.get_user(247117682875432960).send(
            f"```*ERROR*\n{ctx.author.name}\n{ctx.message.content}\n{error}```"
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        logging.info(
            'New channel created: [ID:%s] %s', channel.id, channel.name
        )
        self.bot.analyze_guild()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        logging.info('Channel deleted: [ID:%s] %s', channel.id, channel.name)
        self.bot.analyze_guild()

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel
    ) -> None:
        logging.info(
            'Channel updated: [ID:%s] %s > %s',
            after.id, before.name, after.name
        )
        self.bot.analyze_guild()


if __name__ == "__main__":
    moevius = Bot()
    asyncio.run(moevius.add_cog(Administration(moevius)))
    moevius.run(DISCORD_TOKEN)
