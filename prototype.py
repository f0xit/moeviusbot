import asyncio
import json
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

HTTP_STATUS_OK = 200


class YTClipsHandler:
    def __init__(self, *, channel_handle: str = "schnenko6263") -> None:
        load_dotenv()
        self.yt_api_key = str(os.getenv("YT_API_KEY"))

        self.clips = []

        if (channel_info := asyncio.run(self.fetch_channel_id(handle=channel_handle))) is None:
            return

        self.channel_id = channel_info

        asyncio.run(self.fetch_all_clips())

    async def fetch_channel_id(self, *, handle: str) -> str:
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                "https://youtube.googleapis.com/youtube/v3/channels",
                params={
                    "part": "id",
                    "forHandle": f"@{handle}",
                    "key": self.yt_api_key,
                },
            ) as response,
        ):
            if response.status != HTTP_STATUS_OK:
                return ""

            data = await response.json()

            return data["items"][0]["id"][2:]

    async def fetch_all_clips(self) -> None:
        async with aiohttp.ClientSession() as session:
            pages = 0
            clips = []

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
                if response.status != HTTP_STATUS_OK:
                    return

                data = await response.json()

                if not data:
                    return

                pages = int(data["pageInfo"]["totalResults"]) // 2 + 1

            params["maxResults"] = "50"

            while pages:
                async with session.get(
                    "https://youtube.googleapis.com/youtube/v3/playlistItems",
                    params=params,
                ) as response:
                    if response.status != HTTP_STATUS_OK:
                        break

                    data = await response.json()

                    if not data:
                        break

                    clips.extend(data["items"])

                    if "nextPageToken" not in data:
                        print("Ende!")
                        break

                    params["pageToken"] = data["nextPageToken"]

        self.clips = clips


handler = YTClipsHandler()

with Path("schnenk_shorts.json").open("w") as fp:
    json.dump(handler.clips, fp)
