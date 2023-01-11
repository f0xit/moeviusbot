#!/usr/bin/env python3

##### Imports #####
import os
import sys
import getopt
import logging
import subprocess
import random
import re
from datetime import datetime
import time
import json
from urllib.request import urlopen
from urllib.parse import quote as urlquote
import math
import asyncio

from dotenv import load_dotenv
import markovify
import requests
from bs4 import BeautifulSoup
from autocorrect import Speller

import discord
from discord.ext import commands, tasks

# Import Custom Stuff
from event import Event
from myfunc import load_file, save_file, strfdelta

# Import Tools
from tools.logger_tools import LoggerTools

# Check Python version
major_version, minor_version, micro_version, _, _ = sys.version_info
if (major_version, minor_version) < (3, 11):
    sys.exit("Wrong Python version. Please use at least 3.11.")

##### First Setup #####
LOG_TOOL = LoggerTools(level="DEBUG")

# Get options from CLI
try:
    options, arguments = getopt.getopt(sys.argv[1:], "l:", ["loglevel="])
except getopt.GetoptError:
    sys.exit("Option error.")
for option, argument in options:
    match option:
        case['-l' | '--loglevel']:
            LOG_TOOL.set_log_level(argument)

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if DISCORD_TOKEN is None:
    sys.exit('Discord token not found! Please check your .env file!')
else:
    logging.info('Discord token loaded successfully.')

# Get the Discord Client Object
intents = discord.Intents.all()
client = commands.Bot(command_prefix=('!', '?'), intents=intents)

# Variables for global use
QUOTE_BY = ''
TIME_NOW = ''
CHANNELS = {}
LATEST_MSG = []
FRAGEN = []
BIBEL = []
SETTINGS = {}
STATE = {}
RESPONSES = {}
CHANNELS = {}
SERVER = None
SQUADS = {}
FAITH = {}
TEXT_MODEL = None

STARTUP_TIME = datetime.now()

# Create events
EVENTS = {
    'stream': Event('stream'),
    'game': Event('game')
}

##### Functions #####

# Set up everything when load or reload


def startup():
    global FRAGEN, BIBEL, SETTINGS, STATE, RESPONSES, CHANNELS, SERVER, SQUADS, FAITH

    SETTINGS = load_file('settings')
    STATE = load_file('state')
    RESPONSES = load_file('responses')
    SQUADS = load_file('squads')
    FAITH = load_file('faith')

    # Get Discord objects after settings are loaded
    # Get guild = server
    logging.info("Server-Suche startet.")
    SERVER = client.get_guild(int(SETTINGS['server_id']))
    logging.info(
        "Server-Suche abgeschlossen: %s [%s]",
        SERVER.name,
        SERVER.id
    )

    # Get channel for stream and games
    logging.info("Channel-Suche startet.")
    for channel in SERVER.text_channels:
        if channel.name == SETTINGS['channels']['stream']:
            CHANNELS['stream'] = channel
            logging.debug(
                "Channel für Stream gefunden: %s [%s]",
                channel.name.replace('-', ' ').title(),
                channel.id
            )
        elif channel.category is not None:
            if channel.category.name == 'Spiele':
                CHANNELS[channel.name] = channel
                logging.debug(
                    "Spiel gefunden: %s [%s]",
                    channel.name.replace('-', ' ').title(),
                    channel.id
                )
                if channel.name not in SQUADS.keys():
                    SQUADS[channel.name] = {}
                    logging.debug("Leeres Squad erstellt!")
                else:
                    logging.debug(
                        "Squad gefunden: %s",
                        ','.join(SQUADS[channel.name].keys())
                    )

    logging.info("Channel-Suche abgeschlossen.")

    # 500 Fragen
    with open('fragen.txt', 'r', encoding="utf-8") as file:
        FRAGEN = file.readlines()
        logging.info('Die Fragen wurden geladen.')

    with open('moevius-bibel.txt', 'r', encoding="utf-8") as file:
        BIBEL = file.readlines()
        logging.info('Die Bibel wurde geladen.')

    build_markov()

    logging.info("Startup complete!")

# Check for user is Super User


def is_super_user():
    async def wrapper(ctx):
        return ctx.author.name in SETTINGS['super-users']
    return commands.check(wrapper)

# Ult charge


async def add_ult_charge(amount):
    if amount > 1:
        if STATE['ultCharge'] < 100:
            STATE['ultCharge'] = min(STATE['ultCharge'] + amount, 100)

            await client.change_presence(
                activity=discord.Game(f"Charge: {int(STATE['ultCharge'])}%")
            )

            with open('state.json', 'w', encoding="utf-8") as file:
                json.dump(STATE, file)

            logging.debug('Ult-Charge hinzugefügt: %s', amount)
        else:
            logging.info('Ult-Charge bereit.')

# Faith


async def add_faith(member, amount):
    global FAITH

    if str(member) in FAITH.keys():
        FAITH[str(member)] += amount
    else:
        FAITH[str(member)] = amount

    with open('faith.json', 'w', encoding="utf-8") as file:
        json.dump(FAITH, file)

    logging.debug('Faith wurde hinzugefügt: %s, %s', member, amount)

# Markov


def build_markov(size: int = 3):
    logging.info("Markov Update gestartet, Size: %s", size)
    start_time = time.time()

    # Build Markov Chain
    with open("channel_messages.txt", 'r', encoding="utf-8") as file:
        global QUOTE_BY
        QUOTE_BY = file.readline()[:-1]
        text = file.read()

    # Build the model.
    global TEXT_MODEL
    TEXT_MODEL = markovify.NewlineText(text, state_size=size)

    logging.info(
        "Markov Update abgeschlossen. Size: %s, Dauer: %s",
        size,
        time.time() - start_time
    )

##### Cogs #####


class Reminder(commands.Cog, name='Events'):
    '''Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten,
    beizutreten oder deren Status abzufragen.

    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP,
    wenn du mehr darüber wissen willst.'''

    def __init__(self, bot):
        self.bot = bot

    # Process an Event-Command (Stream, Game, ...)
    async def process_event_command(self, event_type: str, ctx, args, ult=False):
        global CHANNELS, EVENTS, SQUADS

        # Check for super-user
        if event_type == 'stream' and ctx.author.name not in SETTINGS['super-users'] and not ult:
            await ctx.send('Nanana, das darfst du nicht, Krah Krah!')
            logging.warning(
                '%s wollte den Stream-Reminder einstellen.',
                ctx.author.name
            )

            # Charge!
            await add_ult_charge(1)
            return

        # Charge!
        await add_ult_charge(5)
        await add_faith(ctx.author.id, 10)

        # No argument => Reset stream
        if len(args) == 0:
            EVENTS[event_type].reset()

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
            game_string = ''

            # Check for second argument
            if len(args) == 1:
                # In case of a game, check for the channel
                if event_type == 'game':
                    # Is the channel a game channel?
                    if ctx.channel.name in CHANNELS:
                        # Save the channel for later posts
                        CHANNELS['game'] = ctx.channel
                        game = ctx.channel.name.replace('-', ' ').title()
                        game_string = f". Gespielt wird: {game}"
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
                game_string = f". Gespielt wird: {game}"
                if event_type == 'game':
                    CHANNELS['game'] = SERVER.get_channel(379345471719604236)

            # Update event
            logging.info(
                "%s hat das Event %s geupdatet.", ctx.author.name, event_type
            )
            EVENTS[event_type].update_event(
                '25:00' if ult else event_time, game
            )

            # Add creator to the watchlist
            logging.debug(
                "%s wurde zum Event %s hinzugefügt.", ctx.author.name, event_type
            )
            EVENTS[event_type].add_member(ctx.author)

            # Direct feedback for the creator
            # Stream
            if event_type == 'stream':
                if ctx.channel != CHANNELS['stream']:
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
                    game_string = f". Heute werden {adj} {obj} {vrb}, mit dabei als " \
                        f"Special-Guest: {guest}"

                # Announce the event in the right channel
                if game == 'bot':
                    await client.get_channel(580143021790855178).send(
                        "Macht euch bereit für einen Stream, "
                        + f"um {event_time} Uhr wird am Bot gebastelt, Krah Krah!"
                    )
                else:
                    await CHANNELS['stream'].send(
                        'Kochstudio! ' if ult else ''
                        + "Macht euch bereit für einen Stream, "
                        + f"um {event_time} Uhr{game_string}, Krah Krah!"
                    )
            # Game
            else:
                await ctx.send(
                    f"Macht euch bereit für ein Ründchen Coop um {event_time} "
                    f"Uhr{game_string}, Krah Krah!"
                )
                if ctx.channel.name in SQUADS.keys():
                    members = ''
                    for member in SQUADS[ctx.channel.name].values():
                        if member != ctx.author.id:
                            members += f'<@{member}> '
                    await ctx.send(f"Das gilt insbesondere für das Squad, Krah Krah!\n{members}")

            logging.info(
                "Event-Info wurde mitgeteilt, das Squad wurde benachrichtigt."
            )

    # Process the Request for Event-Info
    async def process_event_info(self, event_type: str, ctx):
        global EVENTS

        # Charge!
        await add_ult_charge(5)
        await add_faith(ctx.author.id, 5)

        # There is no event
        if EVENTS[event_type].event_time == '':
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
            if EVENTS[event_type].event_game == '':
                game_str = ""
            else:
                game_str = f"Gespielt wird: {EVENTS[event_type].event_game}. "

            # Get the members
            members = ", ".join(EVENTS[event_type].event_members.values())

            # Post the info
            await ctx.send(
                f"{begin_string} beginnt um {EVENTS[event_type].event_time} Uhr. "
                + f"{game_str}Mit dabei sind bisher: {members}, Krah Krah!"
            )
            logging.info(
                "%s hat nach einem Event %s gefragt. Die Infos dazu wurden rausgehauen.",
                ctx.author.name,
                event_type
            )

    # Join an event
    async def join_event(self, event_type: str, ctx):
        global EVENTS

        if EVENTS[event_type].event_time == '':
            await ctx.send("Nanu, anscheinend gibt es nichts zum Beitreten, Krah Krah!")
            logging.warning(
                "%s wollte einem Event %s beitreten, dass es nicht gibt.",
                ctx.author.name,
                event_type
            )
        else:
            # Charge!
            await add_ult_charge(5)
            await add_faith(ctx.author.id, 5)

            if ctx.author.display_name in EVENTS[event_type].event_members.values():
                await ctx.send(
                    "Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!"
                )
                logging.warning(
                    "%s steht bereits auf der Teilnehmerliste von Event %s.",
                    ctx.author.name,
                    event_type
                )
            else:
                EVENTS[event_type].add_member(ctx.author)
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
    async def _stream(self, ctx, *args):
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
    async def _game(self, ctx, *args):
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
    async def _join(self, ctx):
        '''Wenn ein Reminder eingerichtet wurde, kannst du ihm mit diesem Kommando beitreten.

        Stehst du auf der Teilnehmerliste, wird der Bot dich per Erwähnung benachrichtigen,
        wenn das Event beginnt oder siche etwas ändern sollte.'''

        global CHANNELS
        if ctx.channel in CHANNELS.values():
            if ctx.channel == CHANNELS['stream']:
                await self.join_event('stream', ctx)
            else:
                await self.join_event('game', ctx)

    @commands.command(
        name='hey',
        aliases=['h'],
        brief='Informiere das Squad über ein bevorstehendes Event.'
    )
    async def _hey(self, ctx):
        global SQUADS, EVENTS

        if ctx.channel.category.name != "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            logging.warning(
                "%s hat das Squad außerhalb eines Spiele-Channels gerufen.",
                ctx.author.name
            )
            return

        if len(SQUADS[ctx.channel.name]) == 0:
            await ctx.send('Hey, hier gibt es kein Squad, Krah Krah!')
            logging.warning(
                "%s hat ein leeres Squad in %s gerufen.",
                ctx.author.name,
                ctx.channel.name
            )
            return

        # Ult & Faith
        await add_ult_charge(5)
        await add_faith(ctx.author.id, 5)

        members = []
        for member in SQUADS[ctx.channel.name].values():
            if member != ctx.author.id and str(member) not in EVENTS['game'].event_members.keys():
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
    async def _squad(self, ctx, *args):
        '''Du willst dein Squad managen? Okay, so gehts!
        Achtung: Jeder Game-Channel hat ein eigenes Squad. Du musst also im richtigen Channel sein.

        !squad                  zeigt dir an, wer aktuell im Squad ist.
        !squad add User1 ...    fügt User hinzu. Du kannst auch mehrere User gleichzeitig
                                hinzufügen. "add me" fügt dich hinzu.
        !squad rem User1 ...    entfernt den oder die User wieder.'''

        global SQUADS

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

        # Ult & Faith
        await add_ult_charge(5)
        await add_faith(ctx.author.id, 5)

        if len(args) == 0:
            if len(SQUADS[ctx.channel.name]) > 0:
                game = ctx.channel.name.replace('-', ' ').title()
                members = ", ".join(SQUADS[ctx.channel.name].keys())
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
            case ["add" | "a" | "+"]:
                for arg in args[1:]:
                    if arg == 'me':
                        member = ctx.author
                    else:
                        member = client.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name
                        )
                        continue

                    if member.name in SQUADS[ctx.channel.name].keys():
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

                    SQUADS[ctx.channel.name][member.name] = member.id
                    await ctx.send(
                        "%s wurde zum Squad hinzugefügt, Krah Krah!",
                        member.name
                    )
                    logging.info(
                        "%s hat %s zum %s-Squad hinzugefügt.",
                        ctx.author.name,
                        member.name,
                        ctx.channel.name
                    )

            case ["rem" | "r" | "-"]:
                for arg in args[1:]:
                    if arg == 'me':
                        member = ctx.author
                    else:
                        member = client.get_user(int(arg[2:-1]))

                    if member is None:
                        await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                        logging.warning(
                            "%s hat versucht, %s zum %s-Squad hinzuzufügen.",
                            ctx.author.name,
                            arg,
                            ctx.channel.name
                        )
                        continue

                    if member.name not in SQUADS[ctx.channel.name].keys():
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

                    SQUADS[ctx.channel.name].pop(member.name)
                    await ctx.send(
                        f"{member.name} wurde aus dem Squad entfernt, Krah Krah!"
                    )
                    logging.info(
                        "%s hat %s aus dem %s-Squad entfernt.",
                        ctx.author.name,
                        member.name,
                        ctx.channel.name
                    )

        save_file('squads', SQUADS)


class Fun(commands.Cog, name='Spaß'):
    '''Ein paar spaßige Kommandos für zwischendurch.'''

    def __init__(self, bot):
        self.bot = bot
        self.speller = Speller()

    @commands.command(
        name='ps5',
        brief='Vergleicht die erste Zahl aus der vorherigen Nachricht mit dem  Preis einer PS5.'
    )
    async def _ps5(self, ctx):
        ps5_price = 499

        history = await ctx.channel.history(limit=2).flatten()
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
        name='urbandict',
        aliases=['ud'],
        brief='Durchforstet das Urban Dictionary'
    )
    async def _urbandict(self, ctx, *args):
        # Charge!
        await add_ult_charge(5)
        await add_faith(ctx.author.id, 1)

        term = " ".join(args)
        url = 'http://api.urbandictionary.com/v0/define?term=' + \
            urlquote(term.replace(" ", "+"))

        with urlopen(url) as file:
            data = json.loads(file.read().decode('utf-8'))
            try:
                # Case: Definition found
                definition = data['list'][0]['definition'].translate(
                    {ord(c): None for c in '[]'})
                example = data['list'][0]['example'].translate(
                    {ord(c): None for c in '[]'})

                embed = discord.Embed(
                    title=f"{term.title()}",
                    colour=discord.Colour(0xff00ff),
                    url=f'https://www.urbandictionary.com/define.php?term={term.replace(" ", "+")}',
                    description=f"{definition}\n\n*{example}*"
                )
                await ctx.send(embed=embed)
                logging.info(
                    "%s hat %s im Urban Dictionary recherchiert.",
                    ctx.author.name,
                    term
                )
            except IndexError:
                # Case: No Definition => Try These
                page = requests.get(
                    'https://www.urbandictionary.com/define.php?term='
                    f'{urlquote(term.replace(" ", "+"))}'
                )
                soup = BeautifulSoup(page.content, 'html.parser')

                items = soup.find(
                    'div', class_='try-these').find_all('li')[:10]

                if items is None:
                    # Nothing found, not even try these
                    await ctx.send("Dazu kann ich nun wirklich gar nichts sagen, Krah Krah!")
                    logging.error(
                        "%s hat %s im Urban Dictionary recherchiert.",
                        ctx.author.name,
                        term
                    )
                    return

                listitems = [*map(lambda i: i.text, items)]

                output = "\n".join(listitems)

                embed = discord.Embed(
                    title=f"Suchvorschläge für {term.title()}",
                    colour=discord.Colour(0xff00ff),
                    description=output
                )
                await ctx.send(
                    content="Hey, ich habe habe dazu nichts gefunden, "
                    "aber versuch's doch mal hiermit:",
                    embed=embed
                )

    @commands.command(
        name='frage',
        aliases=['f'],
        brief='Stellt eine zufällige Frage.'
    )
    async def _frage(self, ctx):
        # Charge & Faith
        await add_ult_charge(1)
        await add_faith(ctx.author.id, 1)

        # Get random question
        frage = random.choice(FRAGEN)

        # Build embed object
        embed = discord.Embed(
            title=f"Frage an {ctx.author.display_name}",
            colour=discord.Colour(0xff00ff),
            description=frage
        )

        # Send embed object
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
    async def _bibel(self, ctx):
        # Charge & Faith
        await add_ult_charge(1)
        await add_faith(ctx.author.id, 1)

        # Get random bible quote
        quote = random.choice(BIBEL)

        # Build embed object
        embed = discord.Embed(
            title="Das Wort unseres Herrn, Krah Krah!",
            colour=discord.Colour(0xff00ff),
            description=quote
        )

        # Send embed object
        await ctx.send(embed=embed)
        logging.info(
            "%s hat ein Bibel-Zitat verlangt. Es lautet: %s",
            ctx.author.name,
            quote
        )

    @commands.group(
        name='zitat',
        aliases=['z'],
        brief='Zitiert eine weise Persönlichkeit.'
    )
    async def _quote(self, ctx):
        global TEXT_MODEL, QUOTE_BY

        if ctx.invoked_subcommand is None:
            logging.info(
                "%s hat ein Zitat von %s verlangt.",
                ctx.author.name,
                QUOTE_BY
            )

            quote = TEXT_MODEL.make_sentence(tries=500)

            if quote is None:
                logging.warning("Kein Quote gefunden.")
                await ctx.send(
                    "Ich habe wirklich alles versucht, aber ich konnte einfach "
                    "kein Zitat finden, Krah Krah!"
                )
            else:
                # No Discord Quotes allowed in Quotes
                quote.replace('>', '')

                embed = discord.Embed(
                    title="Zitat",
                    colour=discord.Colour(0xff00ff),
                    description=str(quote),
                    timestamp=datetime.utcfromtimestamp(
                        random.randint(0, int(datetime.now().timestamp()))
                    )
                )
                embed.set_footer(text=QUOTE_BY)
                await ctx.send(embed=embed)

                logging.info(
                    "Quote erfolgreich: %s - %s",
                    quote,
                    QUOTE_BY
                )

            # Ult & Faith
            await add_ult_charge(5)
            await add_faith(ctx.author.id, 1)

    @is_super_user()
    @_quote.command(
        name='downloadHistory',
        aliases=['dh'],
        brief='Besorgt sich die nötigen Daten für den Zitategenerator. '
        'ACHTUNG: Kann je nach Limit einige Sekunden bis Minuten dauern.'
    )
    async def _download_history(self, ctx, member_id: int, lim: int = 1000):
        global SERVER, QUOTE_BY

        user = await client.fetch_user(member_id)
        QUOTE_BY = user.display_name

        await ctx.send(
            f"History Download: Lade pro Channel maximal {lim} "
            f"Nachrichten von {QUOTE_BY} herunter, "
            "Krah Krah! Das kann einen Moment dauern, Krah Krah!"
        )
        logging.info(
            "%s lädt die Nachrichten von %s herunter, Limit: %s.",
            ctx.author.name,
            QUOTE_BY,
            lim
        )

        # Download history
        start_time = time.time()
        number_of_channels = 0
        number_of_sentences = 0
        lines = [QUOTE_BY]

        rammgut = client.get_guild(323922215584268290)  # Hard coded Rammgut
        for channel in rammgut.text_channels:
            number_of_channels += 1
            try:
                messages = await channel.history(limit=lim).flatten()
            except discord.Forbidden as exc_msg:
                logging.error(
                    "Fehler beim Lesen der History in channel %s: %s",
                    channel.name,
                    str(exc_msg)
                )
                continue

            for message in messages:
                if message.author.id == member_id:
                    sentences = message.content.split('. ')
                    for sentence in sentences:
                        if sentence != '':
                            number_of_sentences += 1
                            lines.append(sentence)

        with open("channel_messages.txt", "w", encoding="utf-8") as file:
            print(*lines, sep='\n', file=file)

        await ctx.send(
            f"History Download abgeschlossen! {number_of_sentences} Sätze in {number_of_channels} "
            f"Channels von {QUOTE_BY} heruntergeladen. Dauer: {(time.time() - start_time)}"
        )
        logging.info(
            "History Download abgeschlossen! %s Sätze in %s "
            "Channels von %s heruntergeladen. Dauer: %s",
            number_of_sentences,
            number_of_channels,
            QUOTE_BY,
            time.time() - start_time
        )

    @is_super_user()
    @_quote.command(
        name='buildMarkov',
        aliases=['bm'],
        brief='Generiert das Modell für zufällige Zitate.'
    )
    async def _makequotes(self, ctx, size: int = 3):
        await ctx.send("Markov Update wird gestartet.")

        build_markov(size)
        await ctx.send("Markov Update abgeschlossen.")

    @commands.command(
        name='ult',
        aliases=['Q', 'q'],
        brief='Die ultimative Fähigkeit von Mövius dem Krächzer.'
    )
    async def _ult(self, ctx, *args):
        '''Dieses Kommando feuert die ultimative Fähigkeit von Mövius ab oder liefert dir
        Informationen über die Ult-Charge. Alle Kommandos funktionieren mit dem Wort Ult, können
        aber auch mit Q oder q getriggert werden.

        ?ult    Finde heraus, wie viel Charge Mövius gerade hat.
        !ult    Setze die ultimative Fähigkeit von Mövius ein und warte ab, was
                dieses Mal geschieht.

        Admin Kommandos:
        !ult [add, -a, +] <n: int>  Fügt der Charge n Prozent hinzu.
        !ult [set, -s, =] <n: int>  Setzt die Charge auf n Prozent.'''

        global STATE, CHANNELS

        if ctx.prefix == '?':
            # Output charge
            if STATE['ultCharge'] < 90:
                await ctx.send(
                    "Meine ultimative Fähigkeit lädt sich auf, Krah Krah! "
                    f"[{int(STATE['ultCharge'])}%]"
                )
            elif STATE['ultCharge'] < 100:
                await ctx.send(
                    "Meine ultimative Fähigkeit ist fast bereit, Krah Krah! "
                    f"[{int(STATE['ultCharge'])}%]"
                )
            else:
                await ctx.send(
                    "Meine ultimative Fähigkeit ist bereit, Krah Krah! "
                    f"[{int(STATE['ultCharge'])}%]"
                )

            await add_faith(ctx.author.id, 1)
            logging.info(
                "%s hat nach meiner Ult-Charge gefragt: %s%%",
                ctx.author.name,
                STATE['ultCharge']
            )
        elif ctx.prefix == '!':
            # Do something
            if len(args) == 0:
                # Ultimate is triggered

                if STATE['ultCharge'] < 100:
                    # Not enough charge
                    await ctx.send(
                        "Meine ultimative Fähigkeit ist noch nicht bereit, Krah Krah! "
                        f"[{int(STATE['ultCharge'])}%]"
                    )
                    logging.warning(
                        "%s wollte meine Ult aktivieren. Charge: %s%%",
                        ctx.author.name,
                        STATE['ultCharge']
                    )
                else:
                    # Ult is ready

                    # Faith
                    await add_faith(ctx.author.id, 10)
                    action_id = random.randint(0, 3)

                    if action_id < 2:
                        # Random stream or game
                        game_type = random.choice(['stream', 'game'])
                        event_time = str(random.randint(0, 23)).zfill(2) + ":"
                        event_time += str(random.randint(0, 59)).zfill(2)
                        games = list(CHANNELS.keys())[1:]
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
                    STATE['ultCharge'] = 0

                    with open('state.json', 'w', encoding="utf-8") as file:
                        json.dump(STATE, file)

                    await client.change_presence(activity=discord.Game(
                        f"Charge: {int(STATE['ultCharge'])}%")
                    )
            else:
                # Charge is manipulated by a user
                if ctx.author.name in SETTINGS['super-users']:
                    # Only allowed if super user
                    if args[0] in ['add', '-a', '+']:
                        await add_ult_charge(int(args[1]))
                    elif args[0] in ['set', '-s', '=']:
                        STATE['ultCharge'] = max(min(int(args[1]), 100), 0)

                        with open('state.json', 'w', encoding="utf-8") as file:
                            json.dump(STATE, file)

                        await client.change_presence(activity=discord.Game(
                            f"Charge: {int(STATE['ultCharge'])}%")
                        )
                else:
                    await ctx.send('Nanana, das darfst du nicht, Krah Krah!')

    @ commands.command(
        name='faith',
        brief='Wie treu sind wohl die Jünger des Mövius'
    )
    async def _faith(self, ctx, *args):
        '''Dieses Kommando zeigt dir, wie viel 🕊-Glaubenspunkte die Jünger von Mövius gerade haben.

        ?faith  Alle Jünger des Mövius und ihre 🕊 werden angezeigt.

        Admin Kommandos:
        !faith [add, -a, +] <id> <n>  Erhöht den Glauben von einem User mit der id um n🕊.
        !faith [rem, -r, -] <id> <n>  Reudziert den Glauben von einem User mit der id um n🕊.
        !faith [set, -s, =] <id> <n>  Setzt den Glauben von einem User mit der id auf n🕊.'''
        global FAITH

        if ctx.prefix == '?':
            # Sort faith descending by value
            sorted_faith = dict(
                sorted(FAITH.items(), key=lambda item: item[1], reverse=True)
            )

            # Output faith per user
            output = ""
            for user, amount in sorted_faith.items():
                member = client.get_user(int(user))

                if member is None:
                    continue

                output += f"{member.display_name}: "
                output += f"{format(amount,',d').replace(',','.')}🕊\n"

            if output != "":
                embed = discord.Embed(
                    title="Die treuen Jünger des Mövius und ihre Punkte",
                    colour=discord.Colour(0xff00ff), description=output
                )

                await ctx.send(embed=embed)

            logging.info('Faith wurde angezeigt')
        elif ctx.prefix == '!' and ctx.author.name in SETTINGS['super-users']:
            if len(args) == 3:
                member_id = int(args[1])
                user = client.get_user(member_id)

                if user is None:
                    await ctx.send('Nanana, so geht das nicht, Krah Krah!')
                    return

                amount = int(args[2])

                if args[0] in ['add', '-a', '+']:
                    # Add faith
                    await add_faith(member_id, amount)
                    await ctx.send(
                        f"Alles klar, {user.display_name} hat {amount}🕊 erhalten, Krah Krah!"
                    )
                elif args[0] in ['rem', '-r', '-']:
                    # Remove faith
                    await add_faith(member_id, amount*(-1))
                    await ctx.send(
                        f"Alles klar, {user.display_name} wurden {amount}🕊 abgezogen, Krah Krah!"
                    )
                elif args[0] in ['set', '-s', '=']:
                    # Set faith
                    FAITH[str(member_id)] = amount
                    await ctx.send(
                        f"Alles klar, {user.display_name} hat nun {amount}🕊, Krah Krah!"
                    )
            else:
                await ctx.send('Nanana, so geht das nicht, Krah Krah! [add|rem|set] id amount')
        else:
            await ctx.send('Nanana, das darfst du nicht, Krah Krah!')

    @commands.command(
        name='wurstfinger'
    )
    async def _wurstfinger(self, ctx):
        start_time = time.time()

        history = await ctx.channel.history(limit=2).flatten()
        message = history[1].content
        correction = self.speller(message)

        logging.info(
            'Wurstfinger: "%s" → "%s", Dauer: %s',
            message,
            correction,
            time.time() - start_time
        )

        await ctx.send(f"Meintest du vielleicht: {correction}")

        # Ult & Faith
        await add_ult_charge(5)
        await add_faith(ctx.author.id, 1)


class Administration(commands.Cog, name='Administration'):
    '''Diese Kategorie erfordert bestimmte Berechtigungen'''

    def __init__(self, bot):
        self.bot = bot

    @is_super_user()
    @commands.group(
        name='bot',
        aliases=['b'],
        brief='Kann den Bot steuern.'
    )
    async def _bot(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Was möchtest du mit dem Bot anfangen? "
                "Mit !help bot siehst du, welche Optionen verfügbar sind."
            )

    @_bot.command(
        name='version',
        aliases=['-v']
    )
    async def _version(self, ctx):
        version = subprocess.check_output(
            'git describe --tags', shell=True).strip().decode('ascii')

        await ctx.send(f"Bot läuft auf Version {version}")
        logging.info('Version %s', version)

    @_bot.command(
        name='uptime',
        aliases=['-u']
    )
    async def _uptime(self, ctx):
        uptime = (datetime.now() - STARTUP_TIME)
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
    async def _reload(self, ctx):
        logging.warning("%s hat einen Reload gestartet.", ctx.author.name)
        await ctx.send("Reload wird gestartet.")

        startup()

    @is_super_user()
    @commands.group(
        name='extensions',
        aliases=['ext'],
        brief='Verwaltet die Extensions des Bots.'
    )
    async def _extensions(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Aktuell sind folgende Extensions geladen: "
                f"{', '.join(client.extensions.keys())}"
            )
            await ctx.send("Mit !help ext siehst du, welche Optionen verfügbar sind.")

    @_extensions.command(
        name='load',
        aliases=['-l'],
        brief='Lädt eine Extension in den Bot.'
    )
    async def _load(self, ctx, extension):
        if 'cogs.' + extension in client.extensions.keys():
            await ctx.send("Diese Extensions ist bereits geladen.")
        else:
            try:
                client.load_extension(f"cogs.{extension}")
                await ctx.send("Die Extension wurde geladen.")
            except Exception as exc_msg:
                await ctx.send(f"ERROR: {exc_msg}")

    @_extensions.command(
        name='unload',
        aliases=['-u'],
        brief='Entfernt eine Extension aus dem Bot.'
    )
    async def _unload(self, ctx, extension):
        if 'cogs.' + extension in client.extensions.keys():
            try:
                client.unload_extension(f"cogs.{extension}")
                await ctx.send("Die Extension wurde entfernt.")
            except Exception as exc_msg:
                await ctx.send(f"ERROR: {exc_msg}")
        else:
            await ctx.send("Diese Extensions ist nicht aktiv.")


@client.event
async def on_ready():
    # Load Settings for the first time
    startup()

    for filename in os.listdir('./cogs'):
        if (filename.endswith('.py')
                and not filename.startswith('__')
                and f"cogs.{filename[:-3]}" not in client.extensions.keys()):
            await client.load_extension(f"cogs.{filename[:-3]}")

    # First Ult Charge Update
    await client.change_presence(activity=discord.Game(f"Charge: {int(STATE['ultCharge'])}%"))

    # Start Loop
    time_check.start()

##### Tasks #####


@tasks.loop(seconds=5)
async def time_check() -> None:
    global TIME_NOW, EVENTS

    if TIME_NOW == datetime.now().strftime('%H:%M'):
        return

    TIME_NOW = datetime.now().strftime('%H:%M')

    # Check for daily Stuff at 9am
    if TIME_NOW == '09:00':
        global TEXT_MODEL, QUOTE_BY

        logging.info('Es ist 9 Uhr, Daily wird abgefeuert')

        try:
            quote = TEXT_MODEL.make_sentence(tries=100)
            while quote is None:
                logging.warning(
                    "Quote: Kein Zitat gefunden, neuer Versuch ..."
                )
                quote = TEXT_MODEL.make_sentence(tries=100)

            # No Discord Quotes allowed in Quotes
            quote.replace('>', '')

            embed = discord.Embed(
                title="Zitat des Tages",
                colour=discord.Colour(0xff00ff),
                description=str(quote),
                timestamp=datetime.utcfromtimestamp(
                    random.randint(0, int(datetime.now().timestamp()))
                )
            )
            embed.set_footer(text=QUOTE_BY)
            await SERVER.get_channel(580143021790855178).send(
                content="Guten Morgen, Krah Krah!",
                embed=embed
            )
            logging.info('Zitat des Tages: %s - %s', quote, QUOTE_BY)
        except Exception as exc_msg:
            logging.error('Kein Zitat des Tages: %s', exc_msg)

    if TIME_NOW == '19:30':
        try:
            for command in client.commands:
                if command.name == 'gartic':
                    await command.__call__(None, channel=client.get_channel(815702384688234538))
        except Exception as exc_msg:
            logging.error(
                'ERROR: Kein Gartic-Image des Tages: %s', exc_msg)

    # Check for events now
    for event in EVENTS.values():
        if event.event_time == TIME_NOW:
            logging.info("Ein Event beginnt: %s!", event.event_type)

            members = " ".join(
                [f"<@{id}>" for id in event.event_members.keys()]
            )

            if event.event_type == 'stream':
                if event.event_game == 'bot':
                    await client.get_channel(580143021790855178).send(
                        f"Oh, ist es denn schon {event.event_time} Uhr? "
                        "Dann ab auf https://www.twitch.tv/hanseichlp ... "
                        "es wird endlich wieder am Bot gebastelt, Krah Krah!"
                        f"Heute mit von der Partie: {members}", tts=False
                    )
                else:
                    await CHANNELS['stream'].send(
                        f"Oh, ist es denn schon {event.event_time} Uhr? "
                        "Dann ab auf https://www.twitch.tv/schnenko/ ... "
                        "der Stream fängt an, Krah Krah! "
                        f"Heute mit von der Partie: {members}", tts=False
                    )
            else:
                await CHANNELS['game'].send(
                    f"Oh, ist es denn schon {event.event_time} Uhr? Dann ab in den Voice-Chat, "
                    f"{event.event_game} fängt an, Krah Krah! "
                    f"Heute mit von der Partie: {members}", tts=False
                )

            event.reset()
            logging.info('Event-Post abgesetzt, Timer resettet.')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Add a little charge
    await add_ult_charge(0.1)

    # Requests from file
    if message.content[1:] in RESPONSES['req'].keys():
        response = RESPONSES['req'][message.content[1:]]
        for res in response['res']:
            await message.channel.send(res.format(**locals(), **globals()))
        logging.info(response['log'].format(**locals(), **globals()))

    # Responses from file
    else:
        for key in RESPONSES['res'].keys():
            if re.search(key, message.content):
                response = RESPONSES['res'][key]
                for res in response['res']:
                    await message.channel.send(
                        content=res.format(**locals(), **globals()), tts=False
                    )
                logging.info(response['log'].format(**locals(), **globals()))

    # Important for processing commands
    await client.process_commands(message)


async def faith_on_react(payload: discord.RawReactionActionEvent, operation: str = 'add') -> None:
    reaction_faith = 10

    if payload.emoji.name != 'Moevius':
        return

    text_channel = client.get_channel(payload.channel_id)
    # Who received the faith
    author = (await text_channel.fetch_message(payload.message_id)).author
    # Who gave the faith
    giver = client.get_user(payload.user_id)

    # Add/Remove Faith, giver always gets 1
    await add_faith(author.id, reaction_faith*(-1 if operation == 'remove' else 1))
    await add_faith(giver.id, 1)

    # Log
    logging.info(
        "FaithAdd-Reaction: %s %s %s %s🕊",
        giver.display_name,
        'nimmt' if operation == 'remove' else 'gibt',
        author.display_name,
        reaction_faith
    )


@client.event
async def on_raw_reaction_add(payload):
    await faith_on_react(payload)


@client.event
async def on_raw_reaction_remove(payload):
    await faith_on_react(payload, operation='remove')


@client.event
async def on_command_error(ctx, error):
    logging.error("%s - %s - %s", ctx.author.name, ctx.message.content, error)


async def add_cogs():
    ##### Add the cogs #####
    await client.add_cog(Administration(client))
    await client.add_cog(Reminder(client))
    await client.add_cog(Fun(client))


# Connect to Discord
if __name__ == "__main__":
    asyncio.run(add_cogs())

    client.run(DISCORD_TOKEN)
