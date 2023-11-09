"""Cog for the faith point mechanic"""
import logging

import discord
from discord.ext import commands

from bot import Bot
from tools.check_tools import is_super_user
from tools.json_tools import DictFile

default_fields = {
    "member": commands.parameter(
        description="Server Mitglied. Möglicher Input: ID, Mention, Name."
    ),
    "points": commands.parameter(description="Menge an 🕊️-Punkten als ganze Zahl."),
}


async def setup(bot: Bot) -> None:
    """Setup function for the cog"""
    await bot.add_cog(Faith(bot))
    logging.info("Cog loaded: Faith.")


class Faith(commands.Cog, name="Faith"):
    """This cog includes everything related to the faith mechanic"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.faith = DictFile("faith")

    async def cog_unload(self) -> None:
        logging.info("Cog unloaded: Faith.")

    async def add_faith(self, member: discord.User | discord.Member, amount: int) -> None:
        """Adds a specified amount of faith points to the specified member"""

        member_id = str(member.id)

        self.faith[member_id] = self.faith.get(member_id, 0) + amount

        logging.info("Faith added: %s, %s", member.name, amount)

    async def faith_on_react(self, payload: discord.RawReactionActionEvent) -> None:
        """Processes reaction events to grant faith points"""

        if payload.emoji.name != "Moevius":
            return

        amount = self.bot.settings["faith_on_react"]

        if payload.event_type == "REACTION_REMOVE":
            amount *= -1

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        faith_given_to = (await channel.fetch_message(payload.message_id)).author
        await self.add_faith(faith_given_to, amount)

        if (faith_given_by := self.bot.get_user(payload.user_id)) is None:
            return
        await self.add_faith(faith_given_by, 1)

        logging.info(
            "Faith on reaction: %s %s %s %s🕊",
            faith_given_by.display_name,
            "takes" if amount <= 1 else "gives",
            faith_given_to.display_name,
            self.bot.settings["faith_on_react"],
        )

    @commands.group(name="faith", brief="Wie treu sind die Jünger des Mövius.")
    async def _faith(self, ctx: commands.Context) -> None:
        """Zeigt alle Jünger des Mövius und ihre 🕊 an."""

        if ctx.invoked_subcommand is not None:
            return

        members = {
            member.display_name: amount
            for user, amount in sorted(self.faith.items(), key=lambda item: item[1], reverse=True)
            if (member := self.bot.get_user(int(user))) is not None
        }

        output = (
            "```"
            + "\n".join(
                [f"{user:30}{amount:>6,d}🕊".replace(",", ".") for user, amount in members.items()]
            )
            + "```"
        )

        if not output:
            await ctx.send("Nanana, da stimmt etwas, Krah Krah!")
            logging.error("Faith could not be displayed.")

            return

        await ctx.send(
            embed=discord.Embed(
                title="Die treuen Jünger des Mövius und ihre Punkte",
                colour=discord.Colour(0xFF00FF),
                description=output,
            )
        )
        logging.info("Faith displayed.")

    @is_super_user()
    @_faith.command(name="add", aliases=["-a", "+"], brief="Gibt einem User 🕊️-Punkte.")
    async def _add_faith(
        self,
        ctx: commands.Context,
        member: discord.Member = default_fields["member"],
        amount: int = default_fields["points"],
    ) -> None:
        """Gibt einem User 🕊️-Punkte."""

        logging.info("Manual faith added by %s", ctx.author.name)

        await self.add_faith(member, amount)

        await ctx.send(f"Alles klar, {member.display_name} hat {amount}🕊 erhalten, Krah Krah!")

    @is_super_user()
    @_faith.command(name="remove", aliases=["-r", "-"], brief="Entfernt einem User 🕊️-Punkte.")
    async def _rem_faith(
        self,
        ctx: commands.Context,
        member: discord.Member = default_fields["member"],
        amount: int = default_fields["points"],
    ) -> None:
        """Entfernt einem User 🕊️-Punkte."""

        logging.info("Manual faith removed by %s", ctx.author.name)
        await self.add_faith(member, amount * (-1))

        await ctx.send(f"Alles klar, {member.display_name} wurden {amount}🕊 abgezogen, Krah Krah!")

    @is_super_user()
    @_faith.command(
        name="set",
        aliases=["-s", "="],
        brief="Setzt die 🕊️-Punkte eines Users auf einen bestimmten Wert.",
    )
    async def _set_faith(
        self,
        ctx: commands.Context,
        member: discord.Member = default_fields["member"],
        amount: int = default_fields["points"],
    ) -> None:
        """Setzt die 🕊️-Punkte eines Users auf einen bestimmten Wert."""

        logging.info("Manual faith set by %s", ctx.author.name)
        self.faith.update({str(member.id): amount})

        await ctx.send(f"Alles klar, {member.display_name} hat nun {amount}🕊, Krah Krah!")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Checks wether the completed command is in the faith_by_command-list
        and add the amount of faith points to the user who invoked the command."""

        if ctx.command is None:
            return

        if ctx.command.qualified_name not in self.bot.settings["faith_by_command"]:
            logging.warning("Command %s not in Settings.", ctx.command.qualified_name)
            return

        logging.info("Faith will be added for command: %s", ctx.command.qualified_name)

        amount: int = self.bot.settings["faith_by_command"][ctx.command.qualified_name]

        await self.add_faith(ctx.author, amount)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Adds faith points somone added to a message."""
        await self.faith_on_react(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Removes faith points somone added to a message."""
        await self.faith_on_react(payload)
