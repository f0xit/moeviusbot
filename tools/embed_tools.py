from typing import Any, Optional, Sequence

import discord

from tools.event_tools import Event

THUMB_URL = "https://static-cdn.jtvnw.net/jtv_user_pictures/2ed0d78d-f66a-409d-829a-b98c512d8534-profile_image-70x70.png"
MOEVIUS_COLOR = 0xFF06B5


class PollEmbed(discord.Embed):
    def __init__(self, poll_id: str, poll: dict[str, Any]):
        super().__init__(
            colour=MOEVIUS_COLOR,
            title=poll["title"],
            type="rich",
            description=poll["description"],
        )

        self.set_footer(text=f"Umfrage-ID: {poll_id}")


class StreamEmbed(discord.Embed):
    def __init__(self, *, title: Optional[Any] = None, description: Optional[Any] = None):
        super().__init__(
            colour=0xFF00FF,
            title=title,
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
                title="**Stream-Ankündigung**",
                description=f"{event.description}\nGebt mir ein Join, Krah Krah!",
            )
            .add_field(name="Wann?", value=event.fmt_dt)
            .add_field(name="Was?", value=event.title)
            .set_footer(text=f"Event ID: {event.id}")
        )

    @staticmethod
    def week_streams_announcement(events: Sequence[Event], description: str = "") -> discord.Embed:
        if events is None or not events:
            raise ValueError

        embed = StreamEmbed(title="**Stream-Plan für diese Woche**", description=description)

        for event in events:
            embed.add_field(**event.fmt_field)

        return embed

    @staticmethod
    def events_to_be_announced(events: Sequence[Event]) -> discord.Embed:
        if events is None or not events:
            raise ValueError

        embed = StreamEmbed(title="**Unangekündigte Events**")

        for event in events:
            embed.add_field(**event.fmt_field)

        return embed

    @staticmethod
    def upcoming_events(events: Sequence[Event]) -> discord.Embed:
        if events is None or not events:
            raise ValueError

        embed = StreamEmbed(
            title="**Angekündigte Events**", description="Diese Events sind aktuell angekündigt."
        )

        for event in events:
            embed.add_field(**event.fmt_field)

        return embed

    @staticmethod
    def stream_running(event: Event) -> discord.Embed:
        return StreamEmbed(
            title="**Schnenko nervt!**",
            description=f"**{event.title}**",
        ).add_field(name="Beschreibung:", value=event.description)
