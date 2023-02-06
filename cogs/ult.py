import logging
import random
import discord
from discord.ext import commands
from bot import Bot
from tools.json_tools import DictFile


async def setup(bot: Bot) -> None:
    '''Setup function for the cog.'''
    # await bot.add_cog(Ult(bot))
    # logging.info("Cog: Ult geladen.")
    pass


class Ult(commands.Cog, name='Ult'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.state = DictFile('state')

    async def add_ult_charge(self, amount: int) -> None:
        if amount <= 0:
            logging.warning('Invalid amount of Ult charge.')
            return

        if self.bot.state['ult_charge'] >= 100:
            logging.info('Ult ready!')
            return

        self.bot.state['ult_charge'] = min(
            self.bot.state['ult_charge'] + amount, 100)

        await self.bot.change_presence(
            activity=discord.Game(
                f'Charge: {int(self.bot.state["ult_charge"])}%')
        )

        logging.debug('Ult charge added: %s', amount)

    @commands.command(
        name='ult',
        aliases=['Q', 'q'],
        brief='Die ultimative Fähigkeit von Mövius dem Krächzer.'
    )
    async def _ult(self, ctx: commands.Context, *args) -> None:
        '''Dieses Kommando feuert die ultimative Fähigkeit von Mövius ab oder liefert dir
        Informationen über die Ult-Charge. Alle Kommandos funktionieren mit dem Wort Ult, können
        aber auch mit Q oder q getriggert werden.

        ?ult    Finde heraus, wie viel Charge Mövius gerade hat.
        !ult    Setze die ultimative Fähigkeit von Mövius ein und warte ab, was
                dieses Mal geschieht.

        Admin Kommandos:
        !ult [add, -a, +] <n: int>  Fügt der Charge n Prozent hinzu.
        !ult [set, -s, =] <n: int>  Setzt die Charge auf n Prozent.'''

        if ctx.prefix == '?':
            # Output charge
            if self.bot.state['ult_charge'] < 90:
                await ctx.send(
                    "Meine ultimative Fähigkeit lädt sich auf, Krah Krah! "
                    f"[{int(self.bot.state['ult_charge'])}%]"
                )
            elif self.bot.state['ult_charge'] < 100:
                await ctx.send(
                    "Meine ultimative Fähigkeit ist fast bereit, Krah Krah! "
                    f"[{int(self.bot.state['ult_charge'])}%]"
                )
            else:
                await ctx.send(
                    "Meine ultimative Fähigkeit ist bereit, Krah Krah! "
                    f"[{int(self.bot.state['ult_charge'])}%]"
                )

            logging.info(
                "%s hat nach meiner Ult-Charge gefragt: %s%%",
                ctx.author.name,
                self.bot.state['ult_charge']
            )
        elif ctx.prefix == '!':
            # Do something
            if len(args) == 0:
                # Ultimate is triggered

                if self.bot.state['ult_charge'] < 100:
                    # Not enough charge
                    await ctx.send(
                        "Meine ultimative Fähigkeit ist noch nicht bereit, Krah Krah! "
                        f"[{int(self.bot.state['ult_charge'])}%]"
                    )
                    logging.warning(
                        "%s wollte meine Ult aktivieren. Charge: %s%%",
                        ctx.author.name,
                        self.bot.state['ult_charge']
                    )
                else:
                    # Ult is ready
                    action_id = random.randint(0, 3)

                    if action_id < 2:
                        # Random stream or game
                        game_type = random.choice(['stream', 'game'])
                        event_time = str(random.randint(0, 23)).zfill(2) + ":"
                        event_time += str(random.randint(0, 59)).zfill(2)
                        games = list(self.bot.channels.keys())[1:]
                        game = random.choice(games).replace('-', ' ').title()

                        await Reminder.process_event_command(
                            self, game_type, ctx, (event_time, game), ult=True
                        )
                    elif action_id == 2:
                        # Random questions
                        await Fun._frage(self, ctx)
                    elif action_id == 3:
                        # Random bible quote
                        await Fun._bibel(self, ctx)

                    # Reset charge
                    self.bot.state['ult_charge'] = 0

                    await moevius.change_presence(activity=discord.Game(
                        f"Charge: {int(self.bot.state['ult_charge'])}%")
                    )
            else:
                # Charge is manipulated by a user
                if ctx.author.name in self.bot.settings['super-users']:
                    # Only allowed if super user
                    if args[0] in ['add', '-a', '+']:
                        await add_ult_charge(int(args[1]))
                    elif args[0] in ['set', '-s', '=']:
                        self.bot.state['ult_charge'] = max(
                            min(int(args[1]), 100), 0)

                        await moevius.change_presence(activity=discord.Game(
                            f"Charge: {int(self.bot.state['ult_charge'])}%")
                        )
                else:
                    await ctx.send('Nanana, das darfst du nicht, Krah Krah!')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.change_presence(
            activity=discord.Game(
                f"Charge: {int(self.bot.state['ult_charge'])}%")
        )
