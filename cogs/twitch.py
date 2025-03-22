"""Cog for Twitch related commands"""

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
    "cog": {"name": "Twitch"},
    "clip": {
        "random": {
            "cmd": {
                "name": "clip",
                "fallback": "random",
                "brief": "Postet einen zufälligen Twitch Clip von Schnenko",
            },
        },
        "count": {
            "cmd": {
                "name": "count",
                "brief": "Zeigt die aktuelle Anzahl an Twitch Clips im Bot",
            },
        },
        "refresh": {
            "cmd": {
                "name": "refresh",
                "brief": "Aktualisiert die Twitch Clips im Bot",
            },
        },
    },
}


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    cog = Twitch(bot)
    await cog.clip_handler.fetch_all_clips()
    await bot.add_cog(cog)
    logging.info("Cog loaded: Twitch.")


class TwitchTokenHandler:
    def __init__(self) -> None:
        logging.info("Initializing Twitch token handler...")

        if not load_dotenv():
            err_msg = "No .env file found!"
            logging.exception(err_msg)
            raise OSError(err_msg)

        self.client_id = str(os.getenv("TWITCH_CLIENT_ID"))
        self.client_secret = str(os.getenv("TWITCH_CLIENT_SECRET"))

        self.token = ""
        self.expire_dt = dt.datetime.now(tz=get_local_timezone())

        logging.info("Initialized Twitch token handler.")

    @property
    def is_expired(self) -> bool:
        """Returns true if token is expired."""

        token_expired = self.expire_dt < dt.datetime.now(tz=get_local_timezone())
        logging.debug("Twitch token is%s expired", "" if token_expired else " not")
        return token_expired

    async def fetch_twitch_token(self) -> None:
        """Fetches twitch token for API requests.

        Raises:
            OSError: No .env file found!
            OSError: Twitch API responded with status code 400 or above
            OSError: Faulty Response from Twitch: Missing access token!"""

        logging.info("Fetching Twitch token ...")

        if not load_dotenv():
            err_msg = "No .env file found!"
            logging.exception(err_msg)
            raise OSError(err_msg)

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
            ) as response,
        ):
            logging.debug("Twitch responded with code %s.", response.status)

            if not response.ok:
                message = (await response.json())["message"]
                err_msg = f"Twitch API responded with Code {response.status}: {message}!"
                logging.exception(err_msg)
                raise OSError(err_msg)

            if "access_token" not in (response_json := await response.json(encoding="utf-8")):
                err_msg = "Faulty Response from Twitch: Missing access token!"
                logging.exception(err_msg)
                raise OSError(err_msg)

            self.token = response_json["access_token"]

            expires_in = dt.timedelta(seconds=response_json["expires_in"])
            self.expire_dt = dt.datetime.now(tz=get_local_timezone()) + expires_in

            logging.debug("Twitch token recieved, expires in %s.", expires_in)
            logging.info("Fetched Twitch token, expires at: %s", self.expire_dt)


class TwitchClipsHandler:
    def __init__(self, *, broadcaster_name: str) -> None:
        logging.info("Initializing Twitch clip handler for broadcaster %s...", broadcaster_name)
        self.token_handler = TwitchTokenHandler()

        self.broadcaster_name = broadcaster_name
        self.broadcaster_id = ""

        self.clips = []
        logging.info("Initialized Twitch clip handler for broadcaster %s.", broadcaster_name)

    @property
    async def headers(self) -> dict[str, str]:
        """Returns header file for authorizing at Twitch API.

        Returns:
            dict[str, str]: Header dict with Token and Client-Id."""

        logging.debug("Generating request header...")

        if self.token_handler.is_expired:
            await self.token_handler.fetch_twitch_token()

        return {
            "Authorization": f"Bearer {self.token_handler.token}",
            "Client-Id": self.token_handler.client_id,
        }

    @property
    def clip_count(self) -> int:
        """Number of clips in handler."""

        return len(self.clips)

    async def fetch_broadcaster_id(self) -> None:
        """Fetches broadcaster_id for set broadcaster_name from Twitch API.

        Raises:
            OSError: Twitch API responded with status code 400 or above
            OSError: Twitch response missing data"""

        logging.info("Fetching id for broadcaster %s...", self.broadcaster_name)

        async with (
            aiohttp.ClientSession(headers=await self.headers) as session,
            session.get("https://api.twitch.tv/helix/users", params={"login": self.broadcaster_name}) as response,
        ):
            logging.debug("Twitch responded with code %s.", response.status)

            if not response.ok:
                message = (await response.json())["message"]
                err_msg = f"Twitch API responded with Code {response.status}: {message}"
                logging.exception(err_msg)
                raise OSError(err_msg)

            data = await response.json()

            if "data" not in data or not data["data"]:
                err_msg = "Twitch response missing data"
                logging.exception(err_msg)
                raise OSError(err_msg)

            self.broadcaster_id = data["data"][0]["id"]

            logging.info("Fetched id %s for broadcaster %s...", self.broadcaster_id, self.broadcaster_name)

    async def fetch_all_clips(self) -> None:
        """Fetches all clips for set broadcaster_id from Twitch API.

        Raises:
            OSError: Twitch API responded with status code 400 or above"""

        logging.info("Fetching Twitch clips ...")

        if not self.broadcaster_id:
            logging.debug("Broadcaster id not set.")
            await self.fetch_broadcaster_id()

        async with aiohttp.ClientSession(headers=await self.headers) as session:
            clips = []

            params = {
                "broadcaster_id": self.broadcaster_id,
                "first": "100",
            }

            while True:
                async with session.get(
                    "https://api.twitch.tv/helix/clips",
                    params=params,
                ) as response:
                    logging.debug("Twitch responded with code %s.", response.status)

                    if not response.ok:
                        message = (await response.json())["message"]
                        err_msg = f"Twitch API responded with Code {response.status}: {message}"
                        logging.exception(err_msg)
                        raise OSError(err_msg)

                    data = await response.json()

                    if not data:
                        logging.warning("Recieved not data from Twitch. Fetching stopped.")
                        break

                    logging.debug("Fetched %s clips, adding to list ...", len(data["data"]))

                    clips.extend(data["data"])

                    if "pagination" not in data or "cursor" not in data["pagination"]:
                        logging.warning("Recieved not pagination from Twitch. Fetching stopped.")
                        break

                    logging.debug("Next pagination cursor: %s", data["pagination"]["cursor"])

                    params["after"] = data["pagination"]["cursor"]

        self.clips = [clip["id"] for clip in clips]
        logging.info("Fetched %s Twitch clips.", self.clip_count)

        random.shuffle(self.clips)
        logging.info("Shuffled %s Twitch clips.", self.clip_count)

    async def get_random_clip_url(self) -> str:
        """Returns url of a random clip and removes it from handler"""

        logging.debug("Getting random clip from handler.")
        if not self.clips:
            logging.debug("No clips found in handler.")
            await self.fetch_all_clips()
        return f"https://clips.twitch.tv/{self.clips.pop()}"


class Twitch(commands.Cog, **cog_info["cog"]):
    """This cog includes Twitch related commands"""

    def __init__(self, bot: Bot, *, broadcaster_name: str = "schnenko") -> None:
        logging.info("Initializing Twitch cog...")
        self.bot = bot
        self.clip_handler = TwitchClipsHandler(broadcaster_name=broadcaster_name)
        logging.info("Initialized Twitch cog.")

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Twitch.")

    @is_super_user()
    @commands.hybrid_group(**cog_info["clip"]["random"]["cmd"])
    async def _clip(self, ctx: commands.Context) -> None:
        await ctx.send(await self.clip_handler.get_random_clip_url())

    @_clip.command(**cog_info["clip"]["count"]["cmd"])
    async def _count(self, ctx: commands.Context) -> None:
        await ctx.send(f"Es sind aktuell {self.clip_handler.clip_count} in der Warteschlange.")

    @is_super_user()
    @_clip.command(**cog_info["clip"]["refresh"]["cmd"])
    async def _refresh(self, ctx: commands.Context) -> None:
        start_time = dt.datetime.now(tz=get_local_timezone())
        await ctx.defer(ephemeral=True)
        await self.clip_handler.fetch_all_clips()
        duration = (dt.datetime.now(tz=get_local_timezone()) - start_time).total_seconds()
        await ctx.send(
            f"Clips neu geladen! Es wurden insgesamt {self.clip_handler.clip_count} gefunden. Dauer: {duration}"
        )
