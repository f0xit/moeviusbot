from typing import Any

import discord
from discord.utils import escape_markdown

from tools.dt_tools import get_random_date

MOEVIUS_COLOR = 0xFF06B5


class PollEmbed(discord.Embed):
    def __init__(self, poll_id: str, poll: dict[str, Any]):
        super().__init__(
            colour=MOEVIUS_COLOR,
            title=escape_markdown(str(poll["title"])),
            type="rich",
            description=escape_markdown(str(poll["description"])),
        )

        self.set_footer(text=f"Umfrage-ID: {poll_id}")


class QuoteEmbed(discord.Embed):
    def __init__(self, title: str, quote: str, quote_by: str):
        super().__init__(
            colour=MOEVIUS_COLOR,
            title=escape_markdown(str(title)),
            type="rich",
            description=escape_markdown(str(quote)),
            timestamp=get_random_date(),
        )

        self.set_footer(text=quote_by)
