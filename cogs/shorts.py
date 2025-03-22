"""Cog for YT Shorts related commands"""

import datetime as dt
import logging
import os
import random

import aiohttp
from discord.ext import commands
from dotenv import load_dotenv

from bot import Bot
from tools.check_tools import is_super_user
from tools.dt_tools import get_local_timezone

cog_info = {
    "cog": {"name": "Shorts"},
    "short": {
        "random": {
            "cmd": {
                "name": "short",
                "fallback": "random",
                "brief": "Postet ein zufälliges YT Short von Schnenko",
            },
        },
        "count": {
            "cmd": {
                "name": "count",
                "brief": "Zeigt die aktuelle Anzahl an YT Shorts im Bot",
            },
        },
        "refresh": {
            "cmd": {
                "name": "refresh",
                "brief": "Aktualisiert die YT Shorts im Bot",
            },
        },
    },
}


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    cog = Shorts(bot)
    await cog.clip_handler.fetch_all_shorts()
    await bot.add_cog(cog)
    logging.info("Cog loaded: Shorts.")


class YTClipsHandler:
    def __init__(self, *, channel_handle: str) -> None:
        logging.info("Initializing YT Shorts handler for channel @%s...", channel_handle)

        if not load_dotenv():
            err_msg = "No .env file found!"
            logging.exception(err_msg)
            raise OSError(err_msg)

        self.yt_api_key = str(os.getenv("YT_API_KEY"))

        self.channel_handle = channel_handle
        self.channel_id = ""

        self.shorts = []
        logging.info("Initialized YT Shorts handler for channel @%s.", channel_handle)

    @property
    def short_count(self) -> int:
        """Number of shorts in handler."""

        return len(self.shorts)

    async def fetch_channel_id(self) -> None:
        """Fetches channel_id for set channel_handle from YT API

        Raises:
            OSError: YT API responded with status code 400 or above
            OSError: YT API response missing data"""

        logging.info("Fetching id for channel @%s...", self.channel_handle)

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                "https://youtube.googleapis.com/youtube/v3/channels",
                params={
                    "part": "id",
                    "forHandle": f"@{self.channel_handle}",
                    "key": self.yt_api_key,
                },
            ) as response,
        ):
            logging.debug("YT responded with code %s.", response.status)

            if not response.ok:
                err_msg = f"YT API responded with Code {response.status}!"
                logging.exception(err_msg)
                raise OSError(err_msg)

            data = await response.json()

            if "items" not in data or not data["items"]:
                err_msg = "YT response missing data"
                logging.exception(err_msg)
                raise OSError(err_msg)

            self.channel_id = data["items"][0]["id"][2:]

            logging.info("Fetched id %s for channel @%s...", self.channel_id, self.channel_handle)

    async def fetch_all_shorts(self) -> None:
        """Fetches all shorts for set channel_id from YT API

        Raises:
            OSError: YT API responded with status code 400 or above
            OSError: YT API response missing data"""

        logging.info("Fetching YT shorts ...")

        if not self.channel_id:
            logging.debug("Channel id not set.")
            await self.fetch_channel_id()

        pages = 0
        shorts = []

        async with aiohttp.ClientSession() as session:
            params = {
                "part": "contentDetails",
                "playlistId": "UUSH" + self.channel_id,
                "maxResults": "0",
                "key": self.yt_api_key,
            }

            async with session.get(
                "https://youtube.googleapis.com/youtube/v3/playlistItems",
                params=params,
            ) as response:
                if not response.ok:
                    err_msg = f"YT API responded with Code {response.status}!"
                    logging.exception(err_msg)
                    raise OSError(err_msg)

                data = await response.json()

                if "pageInfo" not in data:
                    err_msg = "YT response missing data"
                    logging.exception(err_msg)
                    raise OSError(err_msg)

                pages = int(data["pageInfo"]["totalResults"]) // 2 + 1

            params["maxResults"] = "50"

            while pages:
                async with session.get(
                    "https://youtube.googleapis.com/youtube/v3/playlistItems",
                    params=params,
                ) as response:
                    if not response.ok:
                        err_msg = f"YT API responded with Code {response.status}!"
                        logging.exception(err_msg)
                        raise OSError(err_msg)

                    data = await response.json()

                    if "items" not in data or not data["items"]:
                        err_msg = "YT response missing data"
                        logging.exception(err_msg)
                        raise OSError(err_msg)

                    shorts.extend(data["items"])

                    if "nextPageToken" not in data:
                        logging.warning("Recieved no pagination from YT. Fetching stopped.")
                        break

                    params["pageToken"] = data["nextPageToken"]

        self.shorts = [short["contentDetails"]["videoId"] for short in shorts]
        logging.info("Fetched %s YT shorts.", self.short_count)

        random.shuffle(self.shorts)
        logging.info("Shuffled %s YT shorts.", self.short_count)

    async def get_random_short_url(self) -> str:
        """Returns url of a random short and removes it from handler"""

        logging.debug("Getting random short from handler.")
        if not self.shorts:
            logging.debug("No short found in handler.")
            await self.fetch_all_shorts()
        return f"https://www.youtube.com/shorts/{self.shorts.pop()}"


class Shorts(commands.Cog, **cog_info["cog"]):
    """This cog includes YT Short related commands"""

    def __init__(self, bot: Bot, *, channel_handle: str = "schnenko6263") -> None:
        logging.info("Initializing YT Shorts cog...")
        self.bot = bot
        self.clip_handler = YTClipsHandler(channel_handle=channel_handle)
        logging.info("Initialized YT Shorts cog.")

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Shorts.")

    @commands.hybrid_group(**cog_info["short"]["random"]["cmd"])
    async def _short(self, ctx: commands.Context) -> None:
        await ctx.send(await self.clip_handler.get_random_short_url())

    @_short.command(**cog_info["short"]["count"]["cmd"])
    async def _count(self, ctx: commands.Context) -> None:
        await ctx.send(f"Es sind aktuell {self.clip_handler.short_count} in der Warteschlange.")

    @is_super_user()
    @_short.command(**cog_info["short"]["refresh"]["cmd"])
    async def _refresh(self, ctx: commands.Context) -> None:
        start_time = dt.datetime.now(tz=get_local_timezone())
        await ctx.defer(ephemeral=True)
        await self.clip_handler.fetch_all_shorts()
        duration = (dt.datetime.now(tz=get_local_timezone()) - start_time).total_seconds()
        await ctx.send(
            f"Clips neu geladen! Es wurden insgesamt {self.clip_handler.short_count} gefunden. Dauer: {duration}"
        )
