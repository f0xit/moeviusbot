from discord.ext import commands
from tools import json_tools


def is_super_user():
    async def wrapper(ctx: commands.Context):
        settings = json_tools.load_file('json/settings.json')
        return ctx.author.name in settings['super-users']
    return commands.check(wrapper)
