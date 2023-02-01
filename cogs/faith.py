import logging
import discord
from discord.ext import commands
from bot import Bot


async def setup(bot: Bot) -> None:
    await bot.add_cog(Faith(bot))
    logging.info('Cog: Faith loaded')


class Faith(commands.Cog, name='Faith'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def faith_on_react(
        self,
        payload: discord.RawReactionActionEvent,
        operation: str = 'add'
    ) -> None:
        if payload.emoji.name != 'Moevius':
            return

        text_channel = self.bot.get_channel(payload.channel_id)

        receiver = (await text_channel.fetch_message(payload.message_id)).author
        giver = self.bot.get_user(payload.user_id)

        await self.add_faith(
            receiver,
            self.bot.settings["faith_on_react"] *
            (-1 if operation == 'remove' else 1)
        )
        await self.add_faith(giver, 1)

        logging.info(
            'Faith on reaction: %s %s %s %s🕊',
            giver.display_name,
            'takes' if operation == 'remove' else 'gives',
            receiver.display_name,
            self.bot.settings['faith_on_react']
        )

    async def add_faith(self, member: discord.User | discord.Member, amount: int) -> None:
        '''Adds the specified amount of faith points to the member's wallet.'''
        member_id: str = str(member.id)

        self.bot.faith[member_id] = self.bot.faith.get(member_id, 0) + amount

        logging.info('Faith was added: %s, %s', member.name, amount)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        if ctx.command.qualified_name not in self.bot.settings['faith_by_command']:
            return

        logging.info(
            'Faith will be added for command: %s',
            ctx.command.qualified_name
        )

        await self.add_faith(
            ctx.author,
            self.bot.settings['faith_by_command'][ctx.command.qualified_name]
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.faith_on_react(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.faith_on_react(payload, operation='remove')

    @commands.group(
        name='faith',
        brief='Wie treu sind wohl die Jünger des Mövius'
    )
    async def _faith(self, ctx: commands.Context) -> None:
        '''Dieses Kommando zeigt dir, wie viel 🕊-Glaubenspunkte die Jünger von Mövius gerade haben.

        ?faith  Alle Jünger des Mövius und ihre 🕊 werden angezeigt.

        Admin Kommandos:
        !faith [add, -a, +] <id> <n>  Erhöht den Glauben von einem User mit der id um n🕊.
        !faith [rem, -r, -] <id> <n>  Reudziert den Glauben von einem User mit der id um n🕊.
        !faith [set, -s, =] <id> <n>  Setzt den Glauben von einem User mit der id auf n🕊.'''

        if ctx.prefix == '?':
            members = {
                member.display_name: amount
                for user, amount in sorted(
                    self.bot.faith.items(),
                    key=lambda item: item[1],
                    reverse=True
                )
                if (member := self.bot.get_user(int(user))) is not None
            }

            output = '```'+'\n'.join([
                f"{user:30}{amount:>6,d}🕊".replace(',', '.')
                for user, amount in members.items()
            ]) + '```'

            if not output:
                await ctx.send('Nanana, da stimmt etwas, Krah Krah!')
                logging.error('Faith could not be displayed.')

                return

            embed = discord.Embed(
                title="Die treuen Jünger des Mövius und ihre Punkte",
                colour=discord.Colour(0xff00ff), description=output
            )

            await ctx.send(embed=embed)
            logging.info('Faith displayed.')

            return

        if ctx.prefix == '!':
            if ctx.author.name not in self.bot.settings['super-users']:
                await ctx.send('Nanana, das darfst du nicht, Krah Krah!')
                logging.warning('Unauthorized user tried to change faith.')

                return

            if ctx.invoked_subcommand is None:
                await ctx.send(
                    "Was möchtest du mit dem Bot anfangen? "
                    "Mit !help faith siehst du, welche Optionen verfügbar sind."
                )

                return

    @_faith.command(
        name='add',
        aliases=['-a', '+']
    )
    async def _add_faith(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: int
    ) -> None:
        await self.add_faith(member, amount)
        logging.info(
            '%s added %s faith to %s.',
            ctx.author.name, amount, member.name
        )
        await ctx.send(
            f"Alles klar, {member.display_name} hat {amount}🕊 erhalten, Krah Krah!"
        )

    @_faith.command(
        name='remove',
        aliases=['-r', '-']
    )
    async def _remove_faith(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: int
    ) -> None:
        await self.add_faith(member, amount*(-1))
        logging.info(
            '%s removed %s faith from %s.',
            ctx.author.name, amount, member.name
        )
        await ctx.send(
            f"Alles klar, {member.display_name} wurden {amount}🕊 abgezogen, Krah Krah!"
        )

    @_faith.command(
        name='set',
        aliases=['-s', '=']
    )
    async def _set_faith(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: int
    ) -> None:
        self.bot.faith.update({str(member.id): amount})
        logging.info(
            '%s set faith to %s for %s.',
            ctx.author.name, amount, member.name
        )
        await ctx.send(
            f"Alles klar, {member.display_name} hat nun {amount}🕊, Krah Krah!"
        )
