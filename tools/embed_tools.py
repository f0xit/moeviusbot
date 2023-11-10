from typing import Any

import discord

from tools.event_tools import Event

THUMB_URL = "https://static-cdn.jtvnw.net/jtv_user_pictures/2ed0d78d-f66a-409d-829a-b98c512d8534-profile_image-70x70.png"


class StreamEmbed(discord.Embed):
    def __init__(self, *, description: Any | None = None):
        super().__init__(
            colour=0xFF00FF,
            title="**Stream-Ankündigung**",
            type="rich",
            url="https://www.twitch.tv/schnenko",
            description=description,
        )

        self.set_thumbnail(url=THUMB_URL)


class EmbedBuilder:
    @staticmethod
    def single_stream_announcement(event: Event) -> discord.Embed:
        return (
            StreamEmbed(
                description=f"{event.description}\nGebt mir ein Join, Krah Krah!",
            )
            .add_field(name="Wann?", value=event.fmt_dt)
            .add_field(name="Was?", value=event.title)
            .set_footer(text=f"Event ID: {event.id}")
        )
