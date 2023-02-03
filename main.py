import os
import sys
import getopt
import logging
import subprocess
import random
import re
import datetime as dt
import math
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from event import Event
from myfunc import strfdelta
from bot import Bot
from tools.logger_tools import LoggerTools

# Check Python version
major_version, minor_version, micro_version, _, _ = sys.version_info
if (major_version, minor_version) < (3, 11):
    sys.exit("Wrong Python version. Please use at least 3.11.")

##### Save startup time #####
STARTUP_TIME = dt.datetime.now()

##### First Setup #####
LOG_TOOL = LoggerTools(level="DEBUG")

# Get options from CLI
try:
    options, arguments = getopt.getopt(sys.argv[1:], "l:", ["loglevel="])
except getopt.GetoptError:
    sys.exit("Option error.")
for option, argument in options:
    match option:
        case '-l' | '--loglevel':
            LOG_TOOL.set_log_level(argument)

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

if discord_token is None:
    sys.exit('Discord token not found! Please check your .env file!')
else:
    logging.info('Discord token loaded successfully.')

moevius = Bot()


def is_super_user():
    # Check for user is Super User
    async def wrapper(ctx: commands.Context):
        return ctx.author.name in moevius.settings['super-users']
    return commands.check(wrapper)


class Reminder(commands.Cog, name='Events'):
    '''Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten,
    beizutreten oder deren Status abzufragen.

    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP,
    wenn du mehr darüber wissen willst.'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.events = {
            'stream': Event('stream'),
            'game': Event('game')
        }
        self.time_now = ''
        self.reminder_checker.start()
        logging.info('Reminder initialized.')

    async def cog_unload(self) -> None:
        self.reminder_checker.cancel()
        logging.info('Reminder unloaded.')

    # Process an Event-Command (Stream, Game, ...)
    async def process_event_command(
        self,
        event_type: str,
        ctx: commands.Context,
        args,
        ult=False
    ) -> None:
        # Check for super-user
        if (
            event_type == 'stream'
            and ctx.author.name not in self.bot.settings['super-users']
            and not ult
        ):
            await ctx.send('Nanana, das darfst du nicht, Krah Krah!')
            logging.warning(
                '%s wollte den Stream-Reminder einstellen.',
                ctx.author.name
            )
            return

        # No argument => Reset stream
        if len(args) == 0:
            self.events[event_type].reset()

            # Feedback
            # TODO: Wenn ein Reminder resettet wird, lass es alle im richtigen Channel wissen
            await ctx.send(
                "Danke, "
                + ctx.author.display_name
                + ", ich habe den Reminder zurückgesetzt, Krah Krah!"
            )

            logging.info(
                "Event resettet: %s - %s",
                ctx.author.name,
                event_type
            )

        # One or more arguments => Set or update stream
        else:
            # TODO: Wenn es ein Update gibt, informiere die Teilnehmer
            # First argument: Time
            event_time = args[0]

            # Second argument: Game
            game = ''

            # Check for second argument
            if len(args) == 1:
                # In case of a game, check for the channel
                if event_type == 'game':
                    # Is the channel a game channel?
                    if ctx.channel.name in self.bot.channels:
                        # Save the channel for later posts
                        self.bot.channels['game'] = ctx.channel
                        game = ctx.channel.name.replace('-', ' ').title()
                    else:
                        await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
                        logging.warning(
                            '%s wollte einen Game-Reminder im Channel %s erstellen.',
                            ctx.author.name,
                            ctx.channel.name
                        )
                        return
            # More than one argument
            else:
                game = ' '.join(args[1:])
                if event_type == 'game':
                    self.bot.channels['game'] = self.bot.guild.get_channel(
                        379345471719604236)

            # Update event
            logging.info(
                "%s hat das Event %s geupdatet.", ctx.author.name, event_type
            )
            self.events[event_type].update_event(
                '25:00' if ult else event_time, game
            )

            # Add creator to the watchlist
            logging.debug(
                "%s wurde zum Event %s hinzugefügt.", ctx.author.name, event_type
            )
            self.events[event_type].add_member(ctx.author)

            # Direct feedback for the creator
            # Stream
            if event_type == 'stream':
                if ctx.channel != self.bot.channels['stream']:
                    await ctx.send(
                        f"Ich habe einen Stream-Reminder für {event_time} "
                        "Uhr eingerichtet, Krah Krah!"
                    )

                if ult:
                    adj = random.choice([
                        'geile',
                        'saftige',
                        'knackige',
                        'wohlgeformte',
                        'kleine aber feine',
                        'prall gefüllte'
                    ])
                    obj = random.choice([
                        'Möhren',
                        'Pflaumen',
                        'Melonen',
                        'Oliven',
                        'Nüsse',
                        'Schinken'
                    ])
                    vrb = random.choice([
                        'mit Öl bepinselt und massiert',
                        'vernascht',
                        'gebürstet',
                        'gefüllt',
                        'gebuttert',
                        'geknetet'
                    ])
                    guest = f'<@{ctx.author.id}>'
                    game = f". Heute werden {adj} {obj} {vrb}, mit dabei als " \
                        f"Special-Guest: {guest}"

                # Announce the event in the right channel
                if game == 'bot':
                    await moevius.get_channel(580143021790855178).send(
                        "Macht euch bereit für einen Stream, "
                        + f"um {event_time} Uhr wird am Bot gebastelt, Krah Krah!"
                    )
                else:
                    await self.bot.channels['stream'].send(
                        '**Kochstudio!**\n' if ult else ''
                        + '**Macht euch bereit für einen Stream!**\n'
                        + f'Wann? {event_time} Uhr\n'
                        + f'Was? {game}\n'
                        + 'Gebt mir ein !join, Krah Krah!'
                    )
            # Game
            else:
                await ctx.send(
                    '**Macht euch bereit für ein Ründchen Coop!**\n'
                    + f'Wann? {event_time} Uhr\n'
                    + f'Was? {game}\n'
                    + 'Gebt mir ein !join, Krah Krah!'
                )
                if ctx.channel.name in self.bot.squads.keys():
                    members = [
                        f'<@{member}> '
                        for member in self.bot.squads[ctx.channel.name].values()
                        if member != ctx.author.id
                    ]
                    if members:
                        await ctx.send(
                            "Das gilt insbesondere für das Squad, Krah Krah!\n"
                            + " ".join(members)
                        )

            logging.info(
                "Event-Info wurde mitgeteilt, das Squad wurde benachrichtigt."
            )

    # Process the Request for Event-Info
    async def process_event_info(
        self,
        event_type: str,
        ctx: commands.Context
    ) -> None:
        if self.events[event_type].event_time == '':
            if event_type == 'stream':
                await ctx.send("Es wurde noch kein Stream angekündigt, Krah Krah!")
            else:
                await ctx.send("Es wurde noch keine Coop-Runde angekündigt, Krah Krah!")
            logging.warning(
                "%s hat nach einem Event %s gefragt, das es nicht gibt.",
                ctx.author.name,
                event_type
            )

        # There is an event
        else:
            # Get the right words
            if event_type == 'stream':
                begin_string = "Der nächste Stream"
            else:
                begin_string = "Die nächste Coop-Runde"

            # Check for game
            if self.events[event_type].event_game == '':
                game_str = ""
            else:
                game_str = f"Gespielt wird: {self.events[event_type].event_game}. "

            # Get the members
            members = ", ".join(self.events[event_type].event_members.values())

            # Post the info
            await ctx.send(
                f"{begin_string} beginnt um {self.events[event_type].event_time} Uhr. "
                + f"{game_str}Mit dabei sind bisher: {members}, Krah Krah!"
            )
            logging.info(
                "%s hat nach einem Event %s gefragt. Die Infos dazu wurden rausgehauen.",
                ctx.author.name,
                event_type
            )

    # Join an event
    async def join_event(
        self,
        event_type: str,
        ctx: commands.Context
    ) -> None:
        if self.events[event_type].event_time == '':
            await ctx.send("Nanu, anscheinend gibt es nichts zum Beitreten, Krah Krah!")
            logging.warning(
                "%s wollte einem Event %s beitreten, dass es nicht gibt.",
                ctx.author.name,
                event_type
            )
        else:
            if ctx.author.display_name in self.events[event_type].event_members.values():
                await ctx.send(
                    "Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!"
                )
                logging.warning(
                    "%s steht bereits auf der Teilnehmerliste von Event %s.",
                    ctx.author.name,
                    event_type
                )
            else:
                self.events[event_type].add_member(ctx.author)
                await ctx.send(
                    "Alles klar, ich packe dich auf die Teilnehmerliste, Krah Krah!"
                )
                logging.info(
                    "%s wurde auf die Teilnehmerliste von Event %s hinzugefügt.",
                    ctx.author.name,
                    event_type
                )

    # Commands
    @commands.command(
        name='stream',
        aliases=['s'],
        brief='Infos und Einstellungen zum aktuellen Stream-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _stream(self, ctx: commands.Context, *args) -> None:
        '''Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine
        Einstellungen anpassen

        ?stream             Sagt dir, ob ein Stream angekündigt wurde. Falls ja, erfährst du,
                            wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer
                            sich bisher zum Stream angemeldet hat. Mehr dazu findest du in der
                            Hilfe zum join-Kommando.

        !stream             resettet den aktuellen Reminder.
        !stream hh:mm       stellt einen Reminder für die gewählte Uhrzeit ein.
        !stream hh:mm       game stellt außerdem ein, welches Spiel gespielt wird.'''

        # Stream command
        if ctx.prefix == '!':
            await self.process_event_command('stream', ctx, args)

        # Stream info
        elif ctx.prefix == '?':
            await self.process_event_info('stream', ctx)

    @commands.command(
        name='game',
        aliases=['g'],
        brief='Infos und Einstellungen zum aktuellen Coop-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _game(self, ctx: commands.Context, *args) -> None:
        '''Hier kannst du alles über einen aktuellen Coop-Reminder herausfinden oder
        seine Einstellungen anpassen

        ?game               Sagt dir, ob eine Coop-Runde angekündigt wurde. Falls ja, erfährst du,
                            wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer
                            sich bisher zum Coop angemeldet hat. Mehr dazu findest du in der
                            Hilfe zum join-Kommando.

        !game               resettet den aktuellen Reminder.
        !game               hh:mm stellt einen Reminder für die gewählte Uhrzeit im Channel ein.
        !game hh:mm game    stellt wahlweise ein Spiel ein, welches keinen eigenen Channel hat.'''

        # Game command
        if ctx.prefix == '!':
            await self.process_event_command('game', ctx, args)

        # Game info
        elif ctx.prefix == '?':
            await self.process_event_info('game', ctx)

    @commands.command(
        name='join',
        aliases=['j'],
        brief='Tritt einem Event bei.'
    )
    async def _join(self, ctx: commands.Context) -> None:
        '''Wenn ein Reminder eingerichtet wurde, kannst du ihm mit diesem Kommando beitreten.

        Stehst du auf der Teilnehmerliste, wird der Bot dich per Erwähnung benachrichtigen,
        wenn das Event beginnt oder siche etwas ändern sollte.'''

        if ctx.channel in self.bot.channels.values():
            if ctx.channel == self.bot.channels['stream']:
                await self.join_event('stream', ctx)
            else:
                await self.join_event('game', ctx)

    @commands.command(
        name='hey',
        aliases=['h'],
        brief='Informiere das Squad über ein bevorstehendes Event.'
    )
    async def _hey(self, ctx: commands.Context) -> None:
        if ctx.channel.category.name != "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            logging.warning(
                "%s hat das Squad außerhalb eines Spiele-Channels gerufen.",
                ctx.author.name
            )
            return

        if len(self.bot.squads[ctx.channel.name]) == 0:
            await ctx.send('Hey, hier gibt es kein Squad, Krah Krah!')
            logging.warning(
                "%s hat ein leeres Squad in %s gerufen.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        members = []
        for member in self.bot.squads[ctx.channel.name].values():
            if (member != ctx.author.id
                        and str(member) not in self.events['game'].event_members.keys()
                    ):
                members.append(f'<@{member}>')

        if len(members) == 0:
            await ctx.send("Hey, es wissen schon alle bescheid, Krah Krah!")
            logging.warning(
                "%s hat das Squad in %s gerufen aber es sind schon alle gejoint.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        await ctx.send(f"Hey Squad! Ja, genau ihr seid gemeint, Krah Krah!\n{' '.join(members)}")
        logging.info(
            "%s hat das Squad in %s gerufen.",
            ctx.author.name,
            ctx.channel.name
        )

    @commands.command(
        name='squad',
        aliases=['sq'],
        brief='Manage dein Squad mit ein paar simplen Kommandos.'
    )
    async def _squad(self, ctx: commands.Context, *args) -> None:
        '''Du willst dein Squad managen? Okay, so gehts!
        Achtung: Jeder Game-Channel hat ein eigenes Squad. Du musst also im richtigen Channel sein.

        !squad                  zeigt dir an, wer aktuell im Squad ist.
        !squad add User1 ...    fügt User hinzu. Du kannst auch mehrere User gleichzeitig
                                hinzufügen. "add me" fügt dich hinzu.
        !squad rem User1 ...    entfernt den oder die User wieder.'''

        if ctx.channel.category is None:
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            logging.warning(
                "%s denkt, %s sei ein Spiele-Channel.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        if ctx.channel.category.name != "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            logging.warning(
                "%s denkt, %s sei ein Spiele-Channel.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        if len(args) == 1:
            return

        if len(args) == 0:
            if len(self.bot.squads[ctx.channel.name]) > 0:
                game = ctx.channel.name.replace('-', ' ').title()
                members = ", ".join(self.bot.squads[ctx.channel.name].keys())
                await ctx.send(
                    f"Das sind die Mitglieder im {game}-Squad, Krah Krah!\n{members}"
                )
                logging.info(
                    "%s hat das Squad in %s angezeigt: %s.",
                    ctx.author.name,
                    ctx.channel.name,
                    members
                )
            else:
                await ctx.send("Es gibt hier noch kein Squad, Krah Krah!")
                logging.warning(
                    "%s hat das Squad in %s gerufen aber es gibt keins.",
                    ctx.author.name,
                    ctx.channel.name
                )

            return

        match args[0]:
            case "add" | "a" | "+":
                for arg in args[1:]:
                    if arg == 'me':
                        member = ctx.author
                    else:
                        member = moevius.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name
                        )
                        continue

                    if member.name in self.bot.squads[ctx.channel.name].keys():
                        await ctx.send(
                            f"{member.name} scheint schon im Squad zu sein, Krah Krah!"
                        )
                        logging.warning(
                            "%s wollte %s mehrfach zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            member.name,
                            ctx.channel.name
                        )
                        continue

                    self.bot.squads[ctx.channel.name][member.name] = member.id
                    await ctx.send(
                        f"{member.name} wurde zum Squad hinzugefügt, Krah Krah!"
                    )
                    logging.info(
                        "%s hat %s zum %s-Squad hinzugefügt.",
                        ctx.author.name,
                        member.name,
                        ctx.channel.name
                    )

            case "rem" | "r" | "-":
                for arg in args[1:]:
                    if arg == 'me':
                        member = ctx.author
                    else:
                        member = moevius.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name
                        )
                        continue

                    if member.name not in self.bot.squads[ctx.channel.name].keys():
                        await ctx.send(
                            "Das macht gar keinen Sinn. "
                            f"{member.name} ist gar nicht im Squad, Krah Krah!"
                        )
                        logging.warning(
                            "%s wollte %s aus dem %s-Squad entfernen, "
                            "aber er war nicht Mitglied.",
                            ctx.author.name,
                            member.name,
                            ctx.channel.name
                        )
                        continue

                    self.bot.squads[ctx.channel.name].pop(member.name)
                    await ctx.send(
                        f"{member.name} wurde aus dem Squad entfernt, Krah Krah!"
                    )
                    logging.info(
                        "%s hat %s aus dem %s-Squad entfernt.",
                        ctx.author.name,
                        member.name,
                        ctx.channel.name
                    )

    @tasks.loop(seconds=5.0)
    async def reminder_checker(self):
        if self.time_now == dt.datetime.now().strftime('%H:%M'):
            return

        self.time_now = dt.datetime.now().strftime('%H:%M')
        for event in self.events.values():
            if event.event_time == self.time_now:
                logging.info("Ein Event beginnt: %s!", event.event_type)

                members = " ".join(
                    [f"<@{id}>" for id in event.event_members.keys()]
                )

                if event.event_type == 'stream':
                    if event.event_game == 'bot':
                        await moevius.get_channel(580143021790855178).send(
                            f"Oh, ist es denn schon {event.event_time} Uhr? "
                            "Dann ab auf https://www.twitch.tv/hanseichlp ... "
                            "es wird endlich wieder am Bot gebastelt, Krah Krah!"
                            f"Heute mit von der Partie: {members}", tts=False
                        )
                    else:
                        await moevius.channels['stream'].send(
                            f"Oh, ist es denn schon {event.event_time} Uhr? "
                            "Dann ab auf https://www.twitch.tv/schnenko/ ... "
                            "der Stream fängt an, Krah Krah! "
                            f"Heute mit von der Partie: {members}", tts=False
                        )
                else:
                    await moevius.channels['game'].send(
                        f"Oh, ist es denn schon {event.event_time} Uhr? Dann ab in den Voice-Chat, "
                        f"{event.event_game} fängt an, Krah Krah! "
                        f"Heute mit von der Partie: {members}", tts=False
                    )

                event.reset()
                logging.info('Event-Post abgesetzt, Timer resettet.')

    @reminder_checker.before_loop
    async def before_reminder_loop(self):
        logging.debug('Waiting for reminder time checker..')
        await self.bot.wait_until_ready()
        logging.info('Reminder time checkerstarted!')


class Fun(commands.Cog, name='Spaß'):
    '''Ein paar spaßige Kommandos für zwischendurch.'''

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        name='ps5',
        brief='Vergleicht die erste Zahl aus der vorherigen Nachricht mit dem  Preis einer PS5.'
    )
    async def _ps5(self, ctx: commands.Context):
        ps5_price = 499

        history = [msg async for msg in ctx.channel.history(limit=2)]
        message = history[1].content

        number = float(
            re.search(r"\d+(,\d+)?", message).group(0).replace(',', '.')
        )

        quot_ps5 = number / ps5_price

        if quot_ps5 < 1:
            await ctx.send(f"Wow, das reicht ja gerade mal für {round(quot_ps5*100)}% einer PS5.")
        else:
            await ctx.send(
                f"Wow, das reicht ja gerade mal für {math.floor(quot_ps5)} "
                f"{'PS5' if math.floor(quot_ps5) == 1 else 'PS5en'}."
            )

    @commands.command(
        name='frage',
        aliases=['f'],
        brief='Stellt eine zufällige Frage.'
    )
    async def _frage(self, ctx: commands.Context):
        frage = random.choice(self.bot.fragen)

        embed = discord.Embed(
            title=f"Frage an {ctx.author.display_name}",
            colour=discord.Colour(0xff00ff),
            description=frage
        )

        await ctx.send(embed=embed)
        logging.info(
            "%s hat eine Frage verlangt. Sie lautet: %s",
            ctx.author.name,
            frage
        )

    @commands.command(
        name='bibel',
        aliases=['bi'],
        brief='Präsentiert die Weisheiten des Krächzers.'
    )
    async def _bibel(self, ctx: commands.Context):
        quote = random.choice(self.bot.bible)

        embed = discord.Embed(
            title="Das Wort unseres Herrn, Krah Krah!",
            colour=discord.Colour(0xff00ff),
            description=quote
        )

        await ctx.send(embed=embed)
        logging.info(
            "%s hat ein Bibel-Zitat verlangt. Es lautet: %s",
            ctx.author.name,
            quote
        )

    @commands.command(
        name='ult',
        aliases=['Q', 'q'],
        brief='Die ultimative Fähigkeit von Mövius dem Krächzer.'
    )
    async def _ult(self, ctx: commands.Context, *args) -> None:
        '''Platzhalter: Das Ult-Kommando ist aktuell deaktiviert'''

        await ctx.send(
            'Die Ult ist aktuell deaktiviert, bitte bleiben Sie in der Leitung, Krah Krah!'
        )


class Administration(commands.Cog, name='Administration'):
    '''Diese Kategorie erfordert bestimmte Berechtigungen'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @is_super_user()
    @commands.group(
        name='bot',
        aliases=['b'],
        brief='Kann den Bot steuern.'
    )
    async def _bot(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Was möchtest du mit dem Bot anfangen? "
                "Mit !help bot siehst du, welche Optionen verfügbar sind."
            )

    @_bot.command(
        name='version',
        aliases=['-v']
    )
    async def _version(self, ctx: commands.Context) -> None:
        console_output = subprocess.check_output(
            'git describe --tags', shell=True
        ).strip().decode('ascii')

        try:
            res = console_output.split('-')
            version_string = ' '.join(res[:2]).title()
            if len(res) >= 2:
                version_string += f'.\nTag is {res[2]} commits behind.'
                version_string += f' Currently running commit {res[3][1:]}'

            await ctx.send(f"Bot läuft auf Version {version_string}")
            logging.info('Version %s', version_string)
        except IndexError:
            logging.error(
                'Something is wrong with the version string: %s', console_output
            )
            await ctx.send(f"Bot läuft auf Version {console_output}")
            logging.info('Version %s', version_string)

    @_bot.command(
        name='uptime',
        aliases=['-u']
    )
    async def _uptime(self, ctx: commands.Context) -> None:
        uptime = (dt.datetime.now() - STARTUP_TIME)
        uptimestr = strfdelta(
            uptime, "{days} Tage {hours}:{minutes}:{seconds}")

        await ctx.send(f"Uptime: {uptimestr} seit {STARTUP_TIME.strftime('%Y.%m.%d %H:%M:%S')}")
        logging.info(
            "Uptime: %s seit %s",
            uptimestr,
            STARTUP_TIME.strftime('%Y.%m.%d %H:%M:%S')
        )

    @_bot.command(
        name='reload',
        aliases=['-r']
    )
    async def _reload(self, ctx: commands.Context) -> None:
        logging.warning("%s hat einen Reload gestartet.", ctx.author.name)
        await ctx.send("Reload wird gestartet.")

        self.bot.load_files_into_attrs()
        self.bot.analyze_guild()

    @is_super_user()
    @commands.group(
        name='extensions',
        aliases=['ext'],
        brief='Verwaltet die Extensions des Bots.'
    )
    async def _extensions(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Aktuell sind folgende Extensions geladen: "
                f"{', '.join(moevius.extensions.keys())}"
            )
            await ctx.send("Mit !help ext siehst du, welche Optionen verfügbar sind.")

    @_extensions.command(
        name='load',
        aliases=['-l'],
        brief='Lädt eine Extension in den Bot.'
    )
    async def _load(self, ctx: commands.Context, extension: str) -> None:
        if 'cogs.' + extension in self.bot.extensions.keys():
            await ctx.send("Diese Extensions ist bereits geladen.")
        else:
            try:
                self.bot.load_extension(f"cogs.{extension}")
                await ctx.send("Die Extension wurde geladen.")
            except Exception as exc_msg:
                await ctx.send(f"ERROR: {exc_msg}")

    @_extensions.command(
        name='unload',
        aliases=['-u'],
        brief='Entfernt eine Extension aus dem Bot.'
    )
    async def _unload(self, ctx: commands.Context, extension: str) -> None:
        if 'cogs.' + extension in self.bot.extensions.keys():
            try:
                moevius.unload_extension(f"cogs.{extension}")
                await ctx.send("Die Extension wurde entfernt.")
            except Exception as exc_msg:
                await ctx.send(f"ERROR: {exc_msg}")
        else:
            await ctx.send("Diese Extensions ist nicht aktiv.")


@moevius.event
async def on_message(message: discord.Message) -> None:
    if message.author == moevius.user:
        return

    # Requests from file
    if message.content[1:] in moevius.responses['req'].keys():
        response = moevius.responses['req'][message.content[1:]]
        for res in response['res']:
            await message.channel.send(res.format(**locals(), **globals()))
        logging.info(response['log'].format(**locals(), **globals()))

    # Responses from file
    else:
        for key in moevius.responses['res'].keys():
            if re.search(key, message.content):
                response = moevius.responses['res'][key]
                for res in response['res']:
                    await message.channel.send(
                        content=res.format(**locals(), **globals()), tts=False
                    )
                logging.info(response['log'].format(**locals(), **globals()))

    # Important for processing commands
    await moevius.process_commands(message)


@moevius.event
async def on_ready() -> None:
    # Load Settings for the first time
    moevius.analyze_guild()

    for filename in os.listdir('./cogs'):
        if (filename.endswith('.py')
                and not filename.startswith('__')
                and f"cogs.{filename[:-3]}" not in moevius.extensions.keys()):
            await moevius.load_extension(f"cogs.{filename[:-3]}")

    ##### Add the cogs #####
    await moevius.add_cog(Administration(moevius))
    await moevius.add_cog(Reminder(moevius))
    await moevius.add_cog(Fun(moevius))


@moevius.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    logging.error("%s - %s - %s", ctx.author.name, ctx.message.content, error)
    await moevius.get_user(247117682875432960).send(
        f"```*ERROR*\n{ctx.author.name}\n{ctx.message.content}\n{error}```"
    )


@moevius.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel) -> None:
    logging.info('New channel created: [ID:%s] %s', channel.id, channel.name)
    moevius.analyze_guild()


@moevius.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel) -> None:
    logging.info('Channel deleted: [ID:%s] %s', channel.id, channel.name)
    moevius.analyze_guild()


@moevius.event
async def on_guild_channel_update(
    before: discord.abc.GuildChannel,
    after: discord.abc.GuildChannel
) -> None:
    logging.info('Channel updated: [ID:%s] %s', after.id, after.name)
    moevius.analyze_guild()


if __name__ == "__main__":
    moevius.run(discord_token)
