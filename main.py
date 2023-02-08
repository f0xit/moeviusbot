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
from tools.py_version_tools import check_python_version
from tools.textfile_tools import lines_from_textfile

check_python_version()

STARTUP_TIME = dt.datetime.now()
LOG_TOOL = LoggerTools(level="DEBUG")


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
            await ctx.send('Fehler: Extension konnte nicht gefunden werden!')
            logging.warning('Extension not existing: %s', extension)
        except commands.ExtensionAlreadyLoaded:
            await ctx.send('Fehler: Extension bereits geladen!')
            logging.warning('Extension already loaded: %s', extension)
        except commands.NoEntryPointError:
            await ctx.send('Fehler: Extension hat keine Setup-Funktion!')
            logging.warning('Extension has no setup function: %s', extension)
        except commands.ExtensionFailed:
            await ctx.send('Fehler: Extension Setup fehlgeschlagen!')
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
            await ctx.send('Fehler: Extension konnte nicht gefunden werden!')
            logging.warning('Extension not existing: %s', extension)
        except commands.ExtensionNotLoaded:
            await ctx.send('Fehler: Extension nicht geladen!')
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

    @is_super_user()
    @_bot.command(
        name='pull',
        aliases=['-p']
    )
    async def _git_pull(self, ctx: commands.Context) -> None:
        console_output = subprocess.check_output(
            'git pull', shell=True
        ).strip().decode('ascii')

        await ctx.send(f'```{console_output}```')

    @is_super_user()
    @_bot.command(
        name='log',
        aliases=['-l']
    )
    async def _show_log(self, ctx: commands.Context, page: int = 1, file: str = '') -> None:
        chunk_size = 15

        path = 'logs/moevius.log'
        if file:
            path += '.' + file

        log_lines = lines_from_textfile(path)
        if log_lines is None:
            await ctx.send(
                'Dieses Log-File scheint es nicht zu geben, Krah Krah! Format: YYYY_MM_DD'
            )
            return

        number_of_pages = len(log_lines) // chunk_size + 1

        if not 1 <= page <= number_of_pages:
            await ctx.send(
                f'Diese Seite gibt es nicht, Krah Krah! Bereich: 1 bis {number_of_pages}')
            return

        log_lines.reverse()

        page -= 1
        log_output = log_lines[(chunk_size*page):(chunk_size)*(page + 1)]
        log_output.reverse()

        await ctx.send(
            f'{path[5:]} - Seite {page + 1}/{number_of_pages}:\n```{"".join(log_output)}```'
        )

    @_bot.command(
        name='version',
        aliases=['-v']
    )
    async def _version(self, ctx: commands.Context) -> None:
        console_output = subprocess.check_output(
            'git describe --tags', shell=True
        ).strip().decode('ascii')

        version_string = ''
        try:
            res = console_output.split('-')
            version_string = res[0].removeprefix('v')
            if len(res) >= 2:
                version_string += f'.\nTag is {res[1]} commits behind.'
                version_string += f' Currently running commit {res[2][1:]}'

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
    async def _reload_bot(self, ctx: commands.Context) -> None:
        if ctx.prefix == '?':
            return

        logging.warning('%s hat einen Reload gestartet.', ctx.author.name)
        await ctx.send('Reload wird gestartet.')

        self.bot.load_files_into_attrs()
        await self.bot.analyze_guild()

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
        await self.bot.analyze_guild()

        await asyncio.gather(*map(
            self.bot.load_extension,
            [
                f"cogs.{filename[:-3]}" for filename in os.listdir('./cogs')
                if (filename.endswith('.py')
                    and not filename.startswith('__')
                    and f"cogs.{filename[:-3]}" not in self.bot.extensions.keys())
            ]
        ))

        await self.bot.tree.sync()

        logging.info('Bot ready!')
        startup_duration = (dt.datetime.now() - STARTUP_TIME).total_seconds()
        logging.debug('Startup took %.4f seconds.', startup_duration)

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

        if (hans := self.bot.get_user(247117682875432960)) is None:
            return

        await hans.send(
            f"```*ERROR*\n{ctx.author.name}\n{ctx.message.content}\n{error}```"
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        logging.info(
            'New channel created: [ID:%s] %s', channel.id, channel.name
        )
        await self.bot.analyze_guild()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        logging.info('Channel deleted: [ID:%s] %s', channel.id, channel.name)
        await self.bot.analyze_guild()

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
        await self.bot.analyze_guild()


def main() -> None:
    load_dotenv()

    if (discord_token := os.getenv('DISCORD_TOKEN')) is None:
        sys.exit('Discord token not found! Please check your .env file!')
    else:
        logging.info('Discord token loaded successfully.')

    moevius = Bot()
    asyncio.run(moevius.add_cog(Administration(moevius)))
    moevius.run(discord_token)


if __name__ == "__main__":
    main()
