"""This module contains the bot class that inherits from discord's default bot."""

import logging

import discord
from discord.ext import commands

from tools.db_tools import create_engine
from tools.json_tools import DictFile


class Bot(commands.Bot):
    """This bot class expands the default discord bot with attributes and
    functions needed in this project.
    """

    def __init__(self) -> None:
        super().__init__(("!", "?"), intents=discord.Intents.all())

        self.load_files_into_attrs()
        self.db_engine = create_engine()

        logging.info("Bot initialized!")

    def load_files_into_attrs(self) -> None:
        """This function fills the bot's attributes with data from files."""

        self.settings = DictFile("settings")
        self.channels: dict[str, discord.TextChannel | None] = {}

    async def set_main_guild(self) -> None:
        """This function analyzes the the channels in the discord guild
        specified in the bot's settings as 'server_id' and stores them in the
        bot's channels-attribute.

        Raises:
            RuntimeError: When no guild is found.
        """

        logging.info("Finding guild [ID#%s]...", self.settings["server_id"])

        if (guild := self.get_guild(int(self.settings["server_id"]))) is None:
            logging.critical("Guild not found!")
            raise RuntimeError("Guild not found!")

        self.main_guild = guild
        logging.info("Guild found! [ID#%s] %s", self.main_guild.id, self.main_guild.name)
