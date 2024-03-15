from typing import Any

import discord

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
