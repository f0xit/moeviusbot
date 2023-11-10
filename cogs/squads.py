import logging

import discord
from discord.ext import commands

from bot import Bot


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(Squads(bot))
    logging.info("Cog: Squads loaded.")


class Squads(commands.Cog, name="Events"):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command(
        name="squad", aliases=["sq"], brief="Manage dein Squad mit ein paar simplen Kommandos."
    )
    async def _squad(self, ctx: commands.Context, *args) -> None:
        """Du willst dein Squad managen? Okay, so gehts!
        Achtung: Jeder Game-Channel hat ein eigenes Squad. Du musst also im richtigen Channel sein.

        !squad                  zeigt dir an, wer aktuell im Squad ist.
        !squad add User1 ...    fügt User hinzu. Du kannst auch mehrere User gleichzeitig
                                hinzufügen. "add me" fügt dich hinzu.
        !squad rem User1 ...    entfernt den oder die User wieder."""

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if ctx.channel.category is None:
            await ctx.send("Hey, das ist kein Spiele-Channel, Krah Krah!")
            logging.warning(
                "%s denkt, %s sei ein Spiele-Channel.", ctx.author.name, ctx.channel.name
            )
            return

        if ctx.channel.category.name != "Spiele":
            await ctx.send("Hey, das ist kein Spiele-Channel, Krah Krah!")
            logging.warning(
                "%s denkt, %s sei ein Spiele-Channel.", ctx.author.name, ctx.channel.name
            )
            return

        if len(args) == 1:
            return

        if len(args) == 0:
            if len(self.bot.squads[ctx.channel.name]) > 0:
                game = ctx.channel.name.replace("-", " ").title()
                members = ", ".join(self.bot.squads[ctx.channel.name].keys())
                await ctx.send(f"Das sind die Mitglieder im {game}-Squad, Krah Krah!\n{members}")
                logging.info(
                    "%s hat das Squad in %s angezeigt: %s.",
                    ctx.author.name,
                    ctx.channel.name,
                    members,
                )
            else:
                await ctx.send("Es gibt hier noch kein Squad, Krah Krah!")
                logging.warning(
                    "%s hat das Squad in %s gerufen aber es gibt keins.",
                    ctx.author.name,
                    ctx.channel.name,
                )

            return

        match args[0]:
            case "add" | "a" | "+":
                for arg in args[1:]:
                    member = ctx.author if arg == "me" else self.bot.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name,
                        )
                        continue

                    if member.name in self.bot.squads[ctx.channel.name]:
                        await ctx.send(f"{member.name} scheint schon im Squad zu sein, Krah Krah!")
                        logging.warning(
                            "%s wollte %s mehrfach zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            member.name,
                            ctx.channel.name,
                        )
                        continue

                    self.bot.squads[ctx.channel.name][member.name] = member.id
                    await ctx.send(f"{member.name} wurde zum Squad hinzugefügt, Krah Krah!")
                    logging.info(
                        "%s hat %s zum %s-Squad hinzugefügt.",
                        ctx.author.name,
                        member.name,
                        ctx.channel.name,
                    )

            case "rem" | "r" | "-":
                for arg in args[1:]:
                    member = ctx.author if arg == "me" else self.bot.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name,
                        )
                        continue

                    if member.name not in self.bot.squads[ctx.channel.name]:
                        await ctx.send(
                            "Das macht gar keinen Sinn. "
                            f"{member.name} ist gar nicht im Squad, Krah Krah!"
                        )
                        logging.warning(
                            "%s wollte %s aus dem %s-Squad entfernen, "
                            "aber er war nicht Mitglied.",
                            ctx.author.name,
                            member.name,
                            ctx.channel.name,
                        )
                        continue

                    self.bot.squads[ctx.channel.name].pop(member.name)
                    await ctx.send(f"{member.name} wurde aus dem Squad entfernt, Krah Krah!")
                    logging.info(
                        "%s hat %s aus dem %s-Squad entfernt.",
                        ctx.author.name,
                        member.name,
                        ctx.channel.name,
                    )
