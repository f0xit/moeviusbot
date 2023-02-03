import os
import sys
import getopt
import logging
import subprocess
import random
import re
import datetime as dt
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from event import Event
from myfunc import strfdelta
from bot import Bot
from tools.logger_tools import LoggerTools
from tools.check_tools import is_super_user

major_version, minor_version, micro_version, _, _ = sys.version_info
if (major_version, minor_version) < (3, 11):
    sys.exit("Wrong Python version. Please use at least 3.11.")

STARTUP_TIME = dt.datetime.now()
LOG_TOOL = LoggerTools(level="DEBUG")

try:
    options, arguments = getopt.getopt(sys.argv[1:], "l:", ["loglevel="])
except getopt.GetoptError:
    sys.exit("Option error.")
for option, argument in options:
    match option:
        case '-l' | '--loglevel':
            LOG_TOOL.set_log_level(argument)

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

if discord_token is None:
    sys.exit('Discord token not found! Please check your .env file!')
else:
    logging.info('Discord token loaded successfully.')

moevius = Bot()


class Administration(commands.Cog, name='Administration'):
    '''Diese Kategorie erfordert bestimmte Berechtigungen'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @is_super_user()
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

    @_bot.command(
        name='reload',
        aliases=['-r']
    )
    async def _reload(self, ctx: commands.Context) -> None:
        logging.warning('%s hat einen Reload gestartet.', ctx.author.name)
        await ctx.send('Reload wird gestartet.')

        self.bot.load_files_into_attrs()
        self.bot.analyze_guild()

    async def load_ext(self, ctx: commands.Context, extension: str) -> None:
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

    @ is_super_user()
    @ commands.group(
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

    @ _extensions.command(
        name='load',
        aliases=['-l'],
        brief='Lädt eine Extension in den Bot.'
    )
    async def _load(self, ctx: commands.Context, extension: str) -> None:
        await self.load_ext(ctx, extension)

    @ _extensions.command(
        name='unload',
        aliases=['-u'],
        brief='Entfernt eine Extension aus dem Bot.'
    )
    async def _unload(self, ctx: commands.Context, extension: str) -> None:
        await self.unload_ext(ctx, extension)

    @ _extensions.command(
        name='reload',
        aliases=['-r'],
        brief='Lädt eine Extension neu.'
    )
    async def _reload(self, ctx: commands.Context, extension: str) -> None:
        await self.unload_ext(ctx, extension)
        await self.load_ext(ctx, extension)


@ moevius.event
async def on_message(message: discord.Message) -> None:
    if message.author == moevius.user:
        return

    # Requests from file
    if message.content[1:] in moevius.responses['req'].keys():
        response = moevius.responses['req'][message.content[1:]]
        for res in response['res']:
            await message.channel.send(res.format(**locals(), **globals()))
        logging.info(response['log'].format(**locals(), **globals()))

    # Responses from file
    else:
        for key in moevius.responses['res'].keys():
            if re.search(key, message.content):
                response = moevius.responses['res'][key]
                for res in response['res']:
                    await message.channel.send(
                        content=res.format(**locals(), **globals()), tts=False
                    )
                logging.info(response['log'].format(**locals(), **globals()))

    await moevius.process_commands(message)


@ moevius.event
async def on_ready() -> None:
    moevius.analyze_guild()

    for filename in os.listdir('./cogs'):
        if (filename.endswith('.py')
                and not filename.startswith('__')
                and f"cogs.{filename[:-3]}" not in moevius.extensions.keys()):
            await moevius.load_extension(f"cogs.{filename[:-3]}")

    await moevius.add_cog(Administration(moevius))


@ moevius.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    logging.error("%s - %s - %s", ctx.author.name, ctx.message.content, error)
    await moevius.get_user(247117682875432960).send(
        f"```*ERROR*\n{ctx.author.name}\n{ctx.message.content}\n{error}```"
    )


@ moevius.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel) -> None:
    logging.info('New channel created: [ID:%s] %s', channel.id, channel.name)
    moevius.analyze_guild()


@ moevius.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel) -> None:
    logging.info('Channel deleted: [ID:%s] %s', channel.id, channel.name)
    moevius.analyze_guild()


@ moevius.event
async def on_guild_channel_update(
    before: discord.abc.GuildChannel,
    after: discord.abc.GuildChannel
) -> None:
    logging.info('Channel updated: [ID:%s] %s > %s',
                 after.id, before.name, after.name)
    moevius.analyze_guild()


if __name__ == "__main__":
    moevius.run(discord_token)
