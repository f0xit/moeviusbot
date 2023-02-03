import logging
import discord
from discord.ext import commands
from bot import Bot
from tools.check_tools import is_super_user
from tools.json_tools import DictFile


async def setup(bot: Bot) -> None:
    await bot.add_cog(Faith(bot))
    logging.info('Cog: Faith loaded')


class Faith(commands.Cog, name='Faith'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.faith = DictFile('faith')

    async def add_faith(self, member: discord.User | discord.Member, amount: int) -> None:
        '''Adds a specified amount of faith points to the specified member'''
        member_id: str = str(member.id)

        self.faith[member_id] = self.faith.get(member_id, 0) + amount

        logging.info('Faith added: %s, %s', member.name, amount)

    async def faith_on_react(self, payload: discord.RawReactionActionEvent) -> None:
        '''Processes reaction events to grant faith points'''
        if payload.emoji.name != 'Moevius':
            return

        amount = self.bot.settings["faith_on_react"]
        if payload.event_type == "REACTION_REMOVE":
            amount *= -1

        channel = self.bot.get_channel(payload.channel_id)
        faith_given_to = (await channel.fetch_message(payload.message_id)).author
        faith_given_by = self.bot.get_user(payload.user_id)

        await self.add_faith(faith_given_to, amount)
        await self.add_faith(faith_given_by, 1)

        logging.info(
            'Faith on reaction: %s %s %s %s🕊',
            faith_given_by.display_name,
            'takes' if amount <= 1 else 'gives',
            faith_given_to.display_name,
            self.bot.settings['faith_on_react']
        )

    @is_super_user()
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

        if ctx.invoked_subcommand is not None:
            return

        if ctx.prefix == '!':
            await ctx.send(
                'Was möchtest du mit dem Bot anfangen? '
                'Mit !help faith siehst du, welche Optionen verfügbar sind.'
            )

            return

        members = {
            member.display_name: amount
            for user, amount in sorted(
                self.faith.items(),
                key=lambda item: item[1],
                reverse=True
            )
            if (member := self.bot.get_user(int(user))) is not None
        }

        output = '```'+'\n'.join([
            f'{user:30}{amount:>6,d}🕊'.replace(',', '.')
            for user, amount in members.items()
        ]) + '```'

        if not output:
            await ctx.send('Nanana, da stimmt etwas, Krah Krah!')
            logging.error('Faith could not be displayed.')

            return

        await ctx.send(
            embed=discord.Embed(
                title="Die treuen Jünger des Mövius und ihre Punkte",
                colour=discord.Colour(0xff00ff), description=output
            )
        )
        logging.info('Faith displayed.')

    @is_super_user()
    @_faith.command(name='add', aliases=['-a', '+'])
    async def _add_faith(self, ctx: commands.Context, member: discord.Member, amount: int) -> None:
        if ctx.prefix == '?':
            return

        logging.info('Manual faith added by %s', ctx.author.name)
        await self.add_faith(member, amount)

        await ctx.send(
            f'Alles klar, {member.display_name} hat {amount}🕊 erhalten, Krah Krah!'
        )

    @is_super_user()
    @_faith.command(name='remove', aliases=['-r', '-'])
    async def _rem_faith(self, ctx: commands.Context, member: discord.Member, amount: int) -> None:
        if ctx.prefix == '?':
            return

        logging.info('Manual faith removed by %s', ctx.author.name)
        await self.add_faith(member, amount*(-1))

        await ctx.send(
            f'Alles klar, {member.display_name} wurden {amount}🕊 abgezogen, Krah Krah!'
        )

    @is_super_user()
    @_faith.command(name='set', aliases=['-s', '='])
    async def _set_faith(self, ctx: commands.Context, member: discord.Member, amount: int) -> None:
        if ctx.prefix == '?':
            return

        logging.info('Manual faith set by %s', ctx.author.name)
        self.faith.update({str(member.id): amount})

        await ctx.send(f'Alles klar, {member.display_name} hat nun {amount}🕊, Krah Krah!')

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        if ctx.command.qualified_name not in self.bot.settings['faith_by_command']:
            logging.warning(
                'Command %s not in Settings.',
                ctx.command.qualified_name
            )
            return

        logging.info(
            'Faith will be added for command: %s',
            ctx.command.qualified_name
        )

        amount = self.bot.settings['faith_by_command'][ctx.command.qualified_name]

        await self.add_faith(ctx.author, amount)

    @ commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.faith_on_react(payload)

    @ commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.faith_on_react(payload)
