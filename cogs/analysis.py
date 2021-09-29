import discord
from discord.ext import commands

def setup(bot):
    bot.add_cog(Analysis(bot))


class Analysis(commands.Cog, name='Analysis'):
    def __init__(self, bot):
        self.bot = bot

