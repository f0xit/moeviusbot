from __future__ import annotations

from enum import Enum

import discord
from discord.ext import commands

from tools.json_tools import load_file


class SpecialUser(Enum):
    """Enum of special users."""

    HANS = 247117682875432960
    SCHNENK = 257249704872509441
    ZUGGI = 232561052573892608


def is_special_user(user_list: list[SpecialUser]):  # noqa: ANN201
    async def wrapper(ctx: commands.Context) -> bool:
        return ctx.author.id in [user.value for user in user_list]

    return commands.check(wrapper)


def is_super_user():  # noqa: ANN201
    async def wrapper(ctx: commands.Context) -> bool:
        settings = load_file("json/settings.json")

        if not isinstance(settings, dict):
            return False

        return ctx.author.name in settings["super-users"]

    return commands.check(wrapper)


def is_gaming_channel():  # noqa: ANN201
    async def wrapper(ctx: commands.Context) -> bool:
        return (
            not isinstance(ctx.channel, discord.TextChannel)
            or ctx.channel.category is None
            or ctx.channel.category.name != "Spiele"
        )

    return commands.check(wrapper)
