import logging

import discord
from discord.ext import commands

from bot import Bot
from tools.json_tools import DictFile


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(Squads(bot))
    logging.info("Cog: Squads loaded.")


class Squads(commands.Cog, name="Events"):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.squads = DictFile("squads")

    async def cog_load(self):
        await self.scan_for_squad_channels()

    async def scan_for_squad_channels(self) -> None:
        """TODO"""

        logging.info("Looking for squad channels ...")

        cat_games = [
            chan
            for chan in next(
                chans
                for cat, chans in self.bot.main_guild.by_category()
                if cat is None or cat.name != "Spiele"
            )
            if isinstance(chan, discord.TextChannel)
        ]

        if not cat_games:
            raise RuntimeError("Category Spiele not found.")

        self.squad_channels = cat_games
        logging.info("%s squad channels found.", len(self.squad_channels))
        logging.debug("Squad channels: %s", self.squad_channels)

    @commands.hybrid_group(
        name="squad", fallback="show", brief="Manage dein Squad mit ein paar simplen Kommandos."
    )
    async def _squad(self, ctx: commands.Context) -> None:
        """TODO"""

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        await ctx.defer()

        if ctx.channel not in self.squad_channels:
            await ctx.send("Hey, das ist kein Spiele-Channel, Krah Krah!")
            return

        if not ctx.channel.id not in self.squads:
            await ctx.send("Es gibt hier noch kein Squad, Krah Krah!")
            return

        game = ctx.channel.name.replace("-", " ").title()

        members = []
        for user_id in self.squads[str(ctx.channel.id)]:
            if (member := self.bot.main_guild.get_member(user_id)) is not None:
                members.append(member.display_name)
                continue

            members.append((await self.bot.main_guild.fetch_member(user_id)).display_name)

        await ctx.send(f"Das sind die Mitglieder im {game}-Squad, Krah Krah!\n{', '.join(members)}")

    @_squad.command(name="add", brief="Fügt User zum Squad hinzu.")
    async def _add_to_squad(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ) -> None:
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        await ctx.defer()

        if ctx.channel not in self.squad_channels:
            await ctx.send("Hey, das ist kein Spiele-Channel, Krah Krah!")
            return

        if not self.squads[str(ctx.channel.id)]:
            self.squads[str(ctx.channel.id)] = [member.id]
            await ctx.send(f"{member.display_name} wurde zum neuen Squad hinzugefügt, Krah Krah!")
            return

        if member.id in self.squads[str(ctx.channel.id)]:
            await ctx.send(f"{member.display_name} scheint schon im Squad zu sein, Krah Krah!")
            return

        self.squads[str(ctx.channel.id)].append(member.id)
        await ctx.send(f"{member.display_name} wurde zum Squad hinzugefügt, Krah Krah!")

    @_squad.command(name="rem", brief="Entfernt User aus dem Squad.")
    async def _rem_from_squad(
        self,
        ctx: commands.Context,
        member: discord.Member,
    ) -> None:
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        await ctx.defer()

        if ctx.channel not in self.squad_channels:
            await ctx.send("Hey, das ist kein Spiele-Channel, Krah Krah!")
            return

        if not self.squads[str(ctx.channel.id)]:
            self.squads[str(ctx.channel.id)] = []
            await ctx.send("Hier gab es gar kein Squad aber ich hab mal eins erstellt, Krah Krah!")
            return

        if member.id not in self.squads[str(ctx.channel.id)]:
            await ctx.send(f"{member.display_name} scheint gar nicht im Squad zu sein, Krah Krah!")
            return

        self.squads[str(ctx.channel.id)].remove(member.id)
        await ctx.send(f"{member.display_name} wurde aus dem Squad entfernt, Krah Krah!")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Re-analizes the guild if a channel is added."""

        logging.info("New channel created: [ID:%s] %s", channel.id, channel.name)
        await self.scan_for_squad_channels()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Re-analizes the guild if a channel is deleted."""

        logging.info("Channel deleted: [ID:%s] %s", channel.id, channel.name)
        await self.scan_for_squad_channels()

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, bef: discord.abc.GuildChannel, aft: discord.abc.GuildChannel
    ) -> None:
        """Re-analizes the guild if a channel is updated."""

        logging.info("Channel updated: [ID:%s] %s > %s", aft.id, bef.name, aft.name)
        await self.scan_for_squad_channels()
