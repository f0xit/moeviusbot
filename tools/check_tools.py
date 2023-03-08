from discord.ext import commands

from tools.json_tools import load_file


def is_super_user():
    async def wrapper(ctx: commands.Context) -> bool:
        settings = load_file('json/settings.json')

        if settings is None:
            return False

        return ctx.author.name in settings['super-users']
    return commands.check(wrapper)
