from __future__ import annotations

import discord

from tools.dt_tools import get_random_date

MOEVIUS_COLOR = 0xFF06B5


class QuoteEmbed(discord.Embed):
    def __init__(self, title: str, quote: str, quote_by: str) -> None:
        super().__init__(
            colour=MOEVIUS_COLOR,
            title=title,
            type="rich",
            description=quote,
            timestamp=get_random_date(),
        )

        self.set_footer(text=quote_by)
