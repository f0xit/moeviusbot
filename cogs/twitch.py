"""Cog for Twitch related commands"""

import asyncio
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

HTTP_STATUS_OK = 200


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    await bot.add_cog(Twitch(bot))
    logging.info("Cog loaded: Twitch.")


class TwitchTokenHandler:
    def __init__(self) -> None:
        load_dotenv()

        self.client_id = str(os.getenv("TWITCH_CLIENT_ID"))
        self.client_secret = str(os.getenv("TWITCH_CLIENT_SECRET"))

        self.token = ""
        self.expire_dt = dt.datetime.now(tz=get_local_timezone())

        asyncio.run(self.fetch_twitch_token())

    @property
    def is_expired(self) -> bool:
        return self.expire_dt > dt.datetime.now(tz=get_local_timezone())

    async def fetch_twitch_token(self) -> None:
        load_dotenv()

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


class TwitchClipsHandler:
    def __init__(self, *, broadcaster_name: str) -> None:
        self.token_handler = TwitchTokenHandler()
        self.clips = []

        broadcaster_info = asyncio.run(self.fetch_creator_info(name=broadcaster_name))
        self.broadcaster_id = broadcaster_info["id"]

        asyncio.run(self.fetch_all_clips())

    @property
    async def headers(self) -> dict[str, str]:
        if self.token_handler.is_expired:
            await self.token_handler.fetch_twitch_token()

        return {
            "Authorization": f"Bearer {self.token_handler.token}",
            "Client-Id": self.token_handler.client_id,
        }

    @property
    def clip_count(self) -> int:
        return len(self.clips)

    async def fetch_creator_info(self, *, name: str) -> dict:
        async with (
            aiohttp.ClientSession(headers=await self.headers) as session,
            session.get("https://api.twitch.tv/helix/users", params={"login": name}) as response,
        ):
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

            return data["data"][0]

    async def fetch_all_clips(self) -> None:
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
                    if response.status != HTTP_STATUS_OK:
                        break

                    data = await response.json()

                    if not data:
                        break

                    clips.extend(data["data"])

                    if "pagination" not in data or "cursor" not in data["pagination"]:
                        break

                    params["after"] = data["pagination"]["cursor"]

        self.clips = clips
        random.shuffle(self.clips)

    async def get_random_clip_url(self) -> str:
        if not self.clips:
            await self.fetch_all_clips()
        return (self.clips.pop())["url"]


class Twitch(commands.Cog, name="Twitch"):
    """This cog includes Twitch related commands"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.clip_handler = TwitchClipsHandler(broadcaster_name="schnenko")

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Twitch.")

    @is_super_user()
    @commands.command(
        name="clip",
        brief="Postet einen zufälligen Twitch Clip von Schnenko",
    )
    async def _clip(self, ctx: commands.Context) -> None:
        await ctx.send(await self.clip_handler.get_random_clip_url())
