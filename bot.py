"""This module contains the bot class that inherits from discord's default bot."""

import logging

import discord
from discord.ext import commands

from tools.json_tools import DictFile


class Bot(commands.Bot):
    """This bot class expands the default discord bot with attributes and
    functions needed in this project.
    """

    def __init__(self) -> None:
        super().__init__(("!", "?"), intents=discord.Intents.all())

        self.load_files_into_attrs()

        logging.info("Bot initialized!")

    def load_files_into_attrs(self) -> None:
        """This function fills the bot's attributes with data from files."""

        self.settings = DictFile("settings")
        self.squads = DictFile("squads")
        self.channels: dict[str, discord.TextChannel | None] = {}

    async def analyze_guild(self) -> None:
        """This function analyzes the the channels in the discord guild
        specified in the bot's settings as 'server_id' and stores them in the
        bot's channels-attribute.

        Raises:
            RuntimeError: When no guild is found.
        """

        logging.info("Finding guild with ID:%s...", self.settings["server_id"])

        if (guild := self.get_guild(int(self.settings["server_id"]))) is None:
            raise RuntimeError("Guild not found!")

        logging.info("Guild found! [ID:%s] %s", guild.id, guild.name)

        logging.info("Analyzing channels...")

        categories = {
            None if cat[0] is None else cat[0].name: cat[1] for cat in guild.by_category()
        }

        try:
            self.channels["stream"] = next(
                chan
                for chan in categories[None]
                if chan.name == self.settings["channels"]["stream"]
                and chan.type == discord.ChannelType.text
            )
        except KeyError as err_msg:
            logging.warning("Category not found. Stream channel should be here. %s", err_msg)
            self.channels["stream"] = None
        except IndexError as err_msg:
            logging.warning(
                "Stream channel not found. Name in settings is %s. %s",
                self.settings["channels"]["stream"],
                err_msg,
            )
            self.channels["stream"] = None

        if self.channels["stream"] is None:
            logging.error("Stream channel not found!")
            return

        logging.info(
            "Stream channel found. [ID: %s] %s",
            self.channels["stream"].id,
            self.channels["stream"].name,
        )

        try:
            self.channels.update(
                {
                    chan.name: chan
                    for chan in list(categories["Spiele"])
                    if chan.type == discord.ChannelType.text
                }
            )
        except KeyError as err_msg:
            logging.warning('Category "Spiele" not found. %s', err_msg)

        logging.info("Channels found. %s", ",".join(self.channels.keys()))

        for name in self.channels:
            if name == "stream":
                continue

            if name not in self.squads:
                self.squads[name] = {}
                logging.info("Created empty squad for new game channel %s", name)
                continue

            logging.debug("Squad found: %s", ",".join(self.squads[name].keys()))

        logging.info("Channel analysis completed!")
