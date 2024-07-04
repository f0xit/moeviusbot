"""Main file of the Moevius Discord Bot"""

import asyncio
import datetime as dt
import logging
import os
import subprocess
import sys

import discord
from discord.abc import GuildChannel
from discord.ext import commands
from dotenv import load_dotenv

from bot import Bot
from tools.check_tools import is_super_user
from tools.dt_tools import strfdelta
from tools.logger_tools import LoggerTools
from tools.py_version_tools import check_python_version
from tools.textfile_tools import lines_from_textfile

check_python_version()

STARTUP_TIME = dt.datetime.now()
LOG_TOOL = LoggerTools(level="DEBUG")
discord.utils.setup_logging(root=False)

MOEVIUS = Bot()


class Administration(commands.Cog, name="Administration"):
    """Diese Kategorie erfordert bestimmte Berechtigungen"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def load_ext(self, ctx: commands.Context, extension: str) -> None:
        """Tries to load the given extension.

        Args:
            ctx (commands.Context): Invocation context. Needed for feedback message.
            extension (str): Name of the extension located in the cogs directory."""

        try:
            await self.bot.load_extension(f"cogs.{extension}")
            await ctx.send("Die Extension wurde geladen.")
            logging.info("Extension loaded: %s", extension)
        except commands.ExtensionNotFound:
            await ctx.send("Fehler: Extension konnte nicht gefunden werden!")
            logging.warning("Extension not existing: %s", extension)
        except commands.ExtensionAlreadyLoaded:
            await ctx.send("Fehler: Extension bereits geladen!")
            logging.warning("Extension already loaded: %s", extension)
        except commands.NoEntryPointError:
            await ctx.send("Fehler: Extension hat keine Setup-Funktion!")
            logging.warning("Extension has no setup function: %s", extension)
        except commands.ExtensionFailed:
            await ctx.send("Fehler: Extension Setup fehlgeschlagen!")
            logging.warning("Extension setup failed: %s", extension)

    async def unload_ext(self, ctx: commands.Context, extension: str) -> None:
        """Tries to unload the given extension.

        Args:
            ctx (commands.Context): Invocation context. Needed for feedback message.
            extension (str): Name of the extension located in the cogs directory."""

        try:
            await self.bot.unload_extension(f"cogs.{extension}")
            await ctx.send("Die Extension wurde entfernt.")
            logging.info("Extension unloaded: %s", extension)
        except commands.ExtensionNotFound:
            await ctx.send("Fehler: Extension konnte nicht gefunden werden!")
            logging.warning("Extension not existing: %s", extension)
        except commands.ExtensionNotLoaded:
            await ctx.send("Fehler: Extension nicht geladen!")
            logging.warning("Extension not loaded: %s", extension)

    @commands.group(name="bot", aliases=["b"], brief="Kann den Bot steuern.")
    async def _bot(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            return

    @is_super_user()
    @_bot.command(name="pull", aliases=["-p"])
    async def _git_pull(self, ctx: commands.Context) -> None:
        """Pullt die neusten Commits aus dem Github-Repo."""

        console_output = (
            subprocess.check_output(  # noqa: S603
                ["git", "pull"]  # noqa: S607
            )
            .strip()
            .decode("ascii")
        )

        await ctx.send(f"```{console_output}```")

    @is_super_user()
    @_bot.command(name="sync", aliases=["-s"])
    async def _sync_tree(self, ctx: commands.Context) -> None:
        """Synchronisiert den Command Tree"""

        cmds = await self.bot.tree.sync()

        await ctx.send(f"Synced:\n```{cmds}```")

    @is_super_user()
    @_bot.command(name="log", aliases=["-l"])
    async def _show_log(self, ctx: commands.Context, page: int = 1, file: str = "") -> None:
        """Zeigt das neuste bzw. ein bestimmtes Logfile an. Die Seiten können mit dem page-Argument
        gewechselt werden."""

        chunk_size = 15

        path = f"logs/moevius.log.{file}" if file else "logs/moevius.log"

        if not (log_lines := (await lines_from_textfile(path))):
            await ctx.send("Dieses Log-File scheint es nicht zu geben, Krah Krah! Format: YYYY_MM_DD")
            return

        number_of_pages = len(log_lines) // chunk_size + 1

        if not 1 <= page <= number_of_pages:
            await ctx.send(f"Diese Seite gibt es nicht, Krah Krah! Bereich: 1 bis {number_of_pages}")
            return

        log_lines.reverse()

        page -= 1
        log_output = log_lines[(chunk_size * page) : (chunk_size) * (page + 1)]
        log_output.reverse()

        await ctx.send(f'{path[5:]} - Seite {page + 1}/{number_of_pages}:\n```{"".join(log_output)}```')

    @_bot.command(name="version", aliases=["-v"])
    async def _version(self, ctx: commands.Context) -> None:
        """Gibt Auskunft darüber, welche Version des Bots aktuell installiert ist.

        Achtung: Eventuell muss der Bot komplett neu gestartet werden, damit nachträgliche
        Änderungen wirksam werden."""

        console_output = (
            subprocess.check_output(  # noqa: S603
                ["git", "describe", "--tags"]  # noqa: S607
            )
            .strip()
            .decode("ascii")
        )

        try:
            res = console_output.split("-")
            version_string = res[0].removeprefix("v")

            if len(res) >= 2:
                version_string += f".\nTag is {res[1]} commits behind. Currently running commit {res[2][1:]}"

            await ctx.send(f"Bot läuft auf Version {version_string}")
            logging.info("Version %s", version_string)

        except IndexError:
            await ctx.send(f"**Fehler!** {console_output}")
            logging.error("Something is wrong with the version string: %s", console_output)

    @_bot.command(name="uptime", aliases=["-u"])
    async def _uptime(self, ctx: commands.Context) -> None:
        """Gibt Auskunft darüber, wie lange der Bot seit dem letzten Start läuft."""

        uptime = dt.datetime.now() - STARTUP_TIME
        uptime_str = strfdelta(uptime)

        await ctx.send(f'Uptime: {uptime_str} seit {STARTUP_TIME.strftime("%Y.%m.%d %H:%M:%S")}')

    @is_super_user()
    @_bot.command(name="reload", aliases=["-r"])
    async def _reload_bot(self, ctx: commands.Context) -> None:
        """Lädt Teile des Bots neu. Das bedeutet im Detail:

        1) Die Settings-Datei wird neu geladen.
        2) Der Server wird neu analysiert.

        Achtung: Dieser Befehl startet nicht wirklich das Programm neu. Auch werden geladene
        Extensions nicht neu geladen. Bitte dafür den entsprechenden Befehl benutzen."""

        logging.warning("%s hat einen Reload gestartet.", ctx.author.name)
        await ctx.send("Reload wird gestartet.")

        self.bot.load_files_into_attrs()
        await self.bot.analyze_guild()

    @commands.group(name="extensions", aliases=["ext"], brief="Verwaltet die Extensions des Bots.")
    async def _extensions(self, ctx: commands.Context) -> None:
        """Verwaltet die Extensions des Bots. Ein Aufruf ohne Unterbefehle zeigt die aktuell
        geladenen Extensions an."""

        if ctx.invoked_subcommand is not None:
            return

        await ctx.send("Aktuell sind folgende Extensions geladen:\n" + ", ".join(self.bot.extensions.keys()))

    @is_super_user()
    @_extensions.command(name="load", aliases=["-l"], brief="Lädt eine Extension in den Bot.")
    async def _load(self, ctx: commands.Context, extension: str) -> None:
        """'Lädt die Extension mit den angegebenen Namen in den Bot."""

        await self.load_ext(ctx, extension)

    @is_super_user()
    @_extensions.command(name="unload", aliases=["-u"], brief="Entfernt eine Extension aus dem Bot.")
    async def _unload(self, ctx: commands.Context, extension: str) -> None:
        """'Entfernt die Extension mit den angegebenen Namen aus dem Bot."""

        await self.unload_ext(ctx, extension)

    @is_super_user()
    @_extensions.command(name="reload", aliases=["-r"], brief="Lädt eine Extension neu.")
    async def _reload(self, ctx: commands.Context, extension: str) -> None:
        """Lädt eine Extension mit dem angegebenen Namen neu.

        Achtung: Sollte die Extension nicht geladen sein, wirft das Kommando einen Fehler.
        Dieser kann im Normalfall ignoriert werden."""

        await self.unload_ext(ctx, extension)
        await self.load_ext(ctx, extension)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """This function is called when the bot is ready. The following actions are executed:

        1) Analyze the guild.
        2) Gather the cogs in the corresponding directory and load them.
        3) Sync the command tree.

        Additionally, the elapsed time since startup is logged."""

        await self.bot.analyze_guild()

        await asyncio.gather(
            *map(
                self.bot.load_extension,
                [
                    f"cogs.{filename[:-3]}"
                    for filename in os.listdir("./cogs")
                    if (
                        filename.endswith(".py")
                        and not filename.startswith("__")
                        and f"cogs.{filename[:-3]}" not in self.bot.extensions
                    )
                ],
            )
        )

        logging.info("Bot ready!")

        startup_duration = (dt.datetime.now() - STARTUP_TIME).total_seconds()
        logging.info("Startup took %.4f seconds.", startup_duration)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """This function iiss callled when a command raises an error.'
        The following actions are executed:

        1) Logging the context and the error
        2) Sending a private message with the same content to the owner of the bot"""

        logging.error("%s - %s - %s", ctx.author.name, ctx.message.content, error)

        if (hans := self.bot.get_user(247117682875432960)) is None:
            return

        await hans.send(f"```*ERROR*\n{ctx.author.name}\n{ctx.message.content}\n{error}```")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: GuildChannel) -> None:
        """Re-analizes the guild if a channel is added."""

        logging.info("New channel created: [ID:%s] %s", channel.id, channel.name)
        await self.bot.analyze_guild()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel) -> None:
        """Re-analizes the guild if a channel is deleted."""

        logging.info("Channel deleted: [ID:%s] %s", channel.id, channel.name)
        await self.bot.analyze_guild()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, bef: GuildChannel, aft: GuildChannel) -> None:
        """Re-analizes the guild if a channel is updated."""

        logging.info("Channel updated: [ID:%s] %s > %s", aft.id, bef.name, aft.name)
        await self.bot.analyze_guild()


async def main() -> None:
    """The main function to start the discord bot. The following actions are executed:

    1) load the .env file for the API Token (exits if not found)
    2) initialize the Bot object which inherits from discord.ext.commands.Bot
    3) add the cog with the admin functions to the bot
    4) connect the bot to the Discord-API."""

    load_dotenv()

    if (discord_token := os.getenv("DISCORD_TOKEN")) is None:
        sys.exit("Discord token not found! Please check your .env file!")
    else:
        logging.info("Discord token loaded successfully.")

    await MOEVIUS.add_cog(Administration(MOEVIUS))
    await MOEVIUS.start(discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopping Moevius ...")
        asyncio.run(MOEVIUS.close())
        logging.info("Moevius stopped. Good night.")
        sys.exit(130)
