import asyncio
import datetime as dt
import json
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

from tools.dt_tools import get_local_timezone

HTTP_STATUS_OK = 200


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
            if response.status != HTTP_STATUS_OK:
                return

            response_json = await response.json(encoding="utf-8")

            if "access_token" not in response_json:
                return

            self.token = response_json["access_token"]

            expires_in = dt.timedelta(seconds=response_json["expires_in"])
            self.expire_dt = dt.datetime.now(tz=get_local_timezone()) + expires_in


class TwitchClipsHandler:
    def __init__(self, *, broadcaster_name: str = "schnenko") -> None:
        self.token_handler = TwitchTokenHandler()
        self.clips = []

        if (broadcaster_info := asyncio.run(self.fetch_creator_info(name=broadcaster_name))) is None:
            return

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

    async def fetch_creator_info(self, *, name: str) -> dict | None:
        async with (
            aiohttp.ClientSession(headers=await self.headers) as session,
            session.get("https://api.twitch.tv/helix/users", params={"login": name}) as response,
        ):
            if response.status != HTTP_STATUS_OK:
                return None

            data = await response.json()

            if not data["data"]:
                return None

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


handler = TwitchClipsHandler()

with Path("clips.json").open("w") as fp:
    json.dump(handler.clips, fp)
