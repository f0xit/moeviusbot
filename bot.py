#!/usr/bin/env python3
#bot.py

##### Imports #####
import discord
from discord.ext import commands, tasks
import os
import subprocess
from dotenv import load_dotenv
import asyncio
import random
import re
from datetime import datetime
import time
import json
import markovify
from urllib.request import urlopen
from urllib.parse import quote as urlquote
import requests
from bs4 import BeautifulSoup
from autocorrect import Speller
import math

# Import Custom Stuff
from event import Event
from myfunc import log, load_file, save_file, strfdelta

##### First Setup #####
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log('Token wurde geladen.')

# Get the Discord Client Object
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=('!','?'), intents=intents)

# Variables for global use
quoteby = ''
timenow = ''
channels = {}
latestmsg = []

startuptime = datetime.now()

# Create events
events = {
    'stream': Event('stream'),
    'game': Event('game')
}

##### Functions #####

# Set up everything when load or reload
def startup():
    global fragen, bibel, settings, STATE, responses, channels, server, squads, faith

    settings = load_file('settings')
    STATE = load_file('state')
    responses = load_file('responses')
    squads = load_file('squads')
    faith = load_file('faith')

    # Get Discord objects after settings are loaded
    # Get guild = server
    log(f"Server-Suche startet.")
    server = client.get_guild(int(settings['server_id']))
    log(f"Server-Suche abgeschlossen: {server.name} [{server.id}]")

    # Get channel for stream and games
    log(f"Channel-Suche startet.")
    for c in server.text_channels:
        if c.name == settings['channels']['stream']:
            channels['stream'] = c
            log(f"Channel für Stream gefunden: {c.name.replace('-',' ').title()} [{c.id}]")
        elif c.category != None:
            if c.category.name == 'Spiele':
                channels[c.name] = c
                log(f"Spiel gefunden: {c.name.replace('-',' ').title()} [{c.id}]")
                if c.name not in squads.keys():
                    squads[c.name] = {}
                    log(f"Leeres Squad erstellt!")
                else:
                    log(f"Squad gefunden: {','.join(squads[c.name].keys())}")
    
    log(f"Channel-Suche abgeschlossen.")
    
    # 500 Fragen
    with open('fragen.txt', 'r') as f:
        fragen = f.readlines()
        log('Die Fragen wurden geladen.')

    with open('moevius-bibel.txt', 'r') as f:
        bibel = f.readlines()
        log('Die Bibel wurde geladen.')
    
    buildMarkov()

    log("Startup complete!")

# Check for user is Super User
def isSuperUser():
    async def wrapper(ctx):
        return ctx.author.name in settings['super-users']
    return commands.check(wrapper)

# Ult charge
async def addUltCharge(amount):
    global STATE

    if amount > 1:
        if STATE['ultCharge'] < 100:
            STATE['ultCharge'] = min(STATE['ultCharge'] + amount, 100)

            await client.change_presence(activity=discord.Game(f"Charge: {int(STATE['ultCharge'])}%"))

            with open('state.json', 'w') as f:
                json.dump(STATE, f)

            log(f'Ult-Charge hinzugefügt: {amount}')
        else:
            log(f'Ult-Charge bereit.')

# Faith
async def addFaith(id, amount):
    global faith

    try:
        faith[str(id)] += amount
    except:
        faith[str(id)] = amount

    with open('faith.json', 'w') as f:
        json.dump(faith, f)

    log(f'Faith wurde hinzugefügt: {id}, {amount}')

# Markov
def buildMarkov(size: int = 3):
    global text_model, quoteby

    log(f"Markov Update gestartet, Size: {size}")
    start_time = time.time()

    try:
        # Build Markov Chain
        with open("channel_messages.txt") as f:
            quoteby = f.readline()[:-1]
            text = f.read()

        # Build the model.
        text_model = markovify.NewlineText(text, state_size=size)

        log(f"Markov Update abgeschlossen. Size: {size}, Dauer: {(time.time() - start_time)}")
    except:
        log(f"ERROR: Markov fehlgeschlagen. Size: {size}, Dauer: {(time.time() - start_time)}")

##### Cogs #####
class Reminder(commands.Cog, name='Events'):
    '''Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten, beizutreten oder deren Status abzufragen.
    
    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP, wenn du mehr darüber wissen willst.'''
    
    def __init__(self, bot):
        self.bot = bot
    
    # Process an Event-Command (Stream, Game, ...)
    async def processEventCommand(self, eventType: str, ctx, args, ult=False):
        global channels, events, squads

        # Check for super-user
        if eventType == 'stream' and ctx.author.name not in settings['super-users'] and not ult:
            await ctx.send('Nanana, das darfst du nicht, Krah Krah!')
            log(f'ERROR: {ctx.author.name} wollte den Stream-Reminder einstellen.')

            # Charge!
            await addUltCharge(1)
            return
        
        # Charge!
        await addUltCharge(5)
        await addFaith(ctx.author.id, 10)

        # No argument => Reset stream
        if len(args) == 0:
            events[eventType].reset()

            # Feedback
            # TODO: Wenn wir schon einen Reminder hatten und er wird resettet, lass es alle im richtigen Channel wissen
            await ctx.send(f"Danke, {ctx.author.display_name}, ich habe den Reminder zurückgesetzt, Krah Krah!")

            log(f"Event resettet: {ctx.author.name} - {eventType}")

        # One or more arguments => Set or update stream
        else:
            # TODO: Wenn es ein Update gibt, informiere die Teilnehmer
            # First argument: Time
            time = args[0]

            # Second argument: Game
            game = ''
            gameStr = ''

            # Check for second argument
            if len(args) == 1:
                # In case of a game, check for the channel
                if eventType == 'game':
                    # Is the channel a game channel?
                    if ctx.channel.name in channels.keys():
                        # Save the channel for later posts
                        channels['game'] = ctx.channel
                        game = ctx.channel.name.replace('-',' ').title()
                        gameStr = f". Gespielt wird: {game}"
                    else:
                        await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
                        log(f"ERROR: {ctx.author.name} wollte einen Game-Reminder im Channel {ctx.channel.name} erstellen.")
                        return
            # More than one argument
            else:
                game = ' '.join(args[1:])
                gameStr = f". Gespielt wird: {game}"
                if eventType == 'game':
                    channels['game'] = server.get_channel(379345471719604236)

            # Update event
            log(f"{ctx.author.name} hat das Event {eventType} geupdatet.")
            events[eventType].updateEvent('25:00' if ult else time, game)

            # Add creator to the watchlist
            log(f"{ctx.author.name} wurde zum Event {eventType} hinzugefügt.")
            events[eventType].addMember(ctx.author)
            
            # Direct feedback for the creator
            # Stream
            if eventType == 'stream':
                if ctx.channel != channels['stream']:
                    await ctx.send(f"Ich habe einen Stream-Reminder für {time} Uhr eingerichtet, Krah Krah!")
                
                if ult:
                    a = random.choice(['geile', 'saftige', 'knackige', 'wohlgeformte', 'kleine aber feine', 'prall gefüllte'])
                    o = random.choice(['Möhren', 'Pflaumen', 'Melonen', 'Oliven', 'Nüsse', 'Schinken'])
                    v = random.choice(['mit Öl bepinselt und massiert', 'vernascht', 'gebürstet', 'gefüllt', 'gebuttert', 'geknetet'])
                    guest = f'<@{ctx.author.id}>'
                    gameStr = f". Heute werden {a} {o} {v}, mit dabei als Special-Guest: {guest}"
                # Announce the event in the right channel
                if game == 'bot':
                    await client.get_channel(580143021790855178).send(f"Macht euch bereit für einen Stream, um {time} Uhr wird am Bot gebastelt, Krah Krah!")
                else:
                    await channels['stream'].send(f"{'Kochstudio! ' if ult else ''}Macht euch bereit für einen Stream, um {time} Uhr{gameStr}, Krah Krah!")
            # Game
            else:
                await ctx.send(f"Macht euch bereit für ein Ründchen Coop um {time} Uhr{gameStr}, Krah Krah!")
                if ctx.channel.name in squads.keys():
                    members = ''
                    for m in squads[ctx.channel.name].values():
                        if m != ctx.author.id:
                            members += f'<@{m}> '
                    await ctx.send(f"Das gilt insbesondere für das Squad, Krah Krah!\n{members}")
            log(f"Event-Info wurde mitgeteilt, das Squad wurde benachrichtigt.")
    
    # Process the Request for Event-Info
    async def processEventInfo(self, eventType: str, ctx):
        global events

        # Charge!
        await addUltCharge(5)
        await addFaith(ctx.author.id, 5)

        # There is no event
        if events[eventType].eventTime == '':
            if eventType == 'stream':
                await ctx.send(f"Es wurde noch kein Stream angekündigt, Krah Krah!")
            else:
                await ctx.send(f"Es wurde noch keine Coop-Runde angekündigt, Krah Krah!")
            log(f"ERROR: {ctx.author.name} hat nach einem Event {eventType} gefragt, dass es nicht gibt.")
        
        # There is an event
        else:
            # Get the right words
            if eventType == 'stream':
                beginStr = "Der nächste Stream"
            else:
                beginStr = "Die nächste Coop-Runde"
            
            # Check for game
            if events[eventType].eventGame == '':
                gameStr = ""
            else:
                gameStr = f"Gespielt wird: {events[eventType].eventGame}. "
            
            # Get the members
            members = ", ".join(events[eventType].eventMembers.values())

            # Post the info
            await ctx.send(f"{beginStr} beginnt um {events[eventType].eventTime} Uhr. {gameStr}Mit dabei sind bisher: {members}, Krah Krah!")
            log(f"{ctx.author.name} hat nach einem Event {eventType} gefragt. Die Infos dazu wurden rausgehauen.")

    # Join an event
    async def joinEvent(self, eventType: str, ctx):
        global events

        if events[eventType].eventTime == '':
            await ctx.send(f"Nanu, anscheinend gibt es nichts zum Beitreten, Krah Krah!")
            log(f"ERROR: {ctx.author.name} wollte einem Event {eventType} beitreten, dass es nicht gibt.")
        else:
            # Charge!
            await addUltCharge(5)
            await addFaith(ctx.author.id, 5)

            if ctx.author.display_name in events[eventType].eventMembers.values():
                await ctx.send(f"Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!")
                log(f"ERROR: {ctx.author.name} steht bereits auf der Teilnehmerliste von Event {eventType}.")
            else:
                events[eventType].addMember(ctx.author)
                await ctx.send(f"Alles klar, ich packe dich auf die Teilnehmerliste, Krah Krah!")
                log(f"{ctx.author.name} wurde auf die Teilnehmerliste von Event {eventType} hinzugefügt.")
    
    # Commands
    @commands.command(
        name='stream',
        aliases=['s'],
        brief='Infos und Einstellungen zum aktuellen Stream-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _stream(self, ctx, *args):
        '''Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine Einstellungen anpassen
        
        ?stream             Sagt dir, ob ein Stream angekündigt wurde. Falls ja, erfährst du, wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer sich bisher zum Stream angemeldet hat. Mehr dazu findest du in der Hilfe zum join-Kommando.

        !stream             resettet den aktuellen Reminder.
        !stream hh:mm       stellt einen Reminder für die gewählte Uhrzeit ein.
        !stream hh:mm       game stellt außerdem ein, welches Spiel gespielt wird.'''

        # Stream command
        if ctx.prefix == '!':
            await self.processEventCommand('stream', ctx, args)
        
        # Stream info
        elif ctx.prefix == '?':
            await self.processEventInfo('stream', ctx)
    
    @commands.command(
        name='game',
        aliases=['g'],
        brief='Infos und Einstellungen zum aktuellen Coop-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _game(self, ctx, *args):
        '''Hier kannst du alles über einen aktuellen Coop-Reminder herausfinden oder seine Einstellungen anpassen
        
        ?game               Sagt dir, ob eine Coop-Runde angekündigt wurde. Falls ja, erfährst du, wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer sich bisher zum Coop angemeldet hat. Mehr dazu findest du in der Hilfe zum join-Kommando.

        !game               resettet den aktuellen Reminder.
        !game               hh:mm stellt einen Reminder für die gewählte Uhrzeit im Channel ein.
        !game hh:mm game    stellt wahlweise ein Spiel ein, welches keinen eigenen Channel hat.'''

        # Game command
        if ctx.prefix == '!':
            await self.processEventCommand('game', ctx, args)
        
        # Game info
        elif ctx.prefix == '?':
            await self.processEventInfo('game', ctx)
    
    @commands.command(
        name='join',
        aliases=['j'],
        brief='Tritt einem Event bei.'
    )
    async def _join(self, ctx):
        global channels

        '''Wenn ein Reminder eingerichtet wurde, kannst du ihm mit diesem Kommando beitreten.

        Stehst du auf der Teilnehmerliste, wird der Bot dich per Erwähnung benachrichtigen, wenn das Event beginnt oder siche etwas ändern sollte.'''
        
        if ctx.channel in channels.values():
            if ctx.channel == channels['stream']:
                await self.joinEvent('stream', ctx)
            else:
                await self.joinEvent('game', ctx)
    
    @commands.command(
        name='hey',
        aliases=['h'],
        brief='Informiere das Squad über ein bevorstehendes Event.'
    )
    async def _hey(self, ctx):
        global squads, events

        if ctx.channel.category == "Spiele":
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            log(f"ERROR: {ctx.author.name} hat das Squad außerhalb eines Spiele-Channels gerufen.")
        else:
            # Ult & Faith
            await addUltCharge(5)
            await addFaith(ctx.author.id, 5)

            members = ''
            for m in squads[ctx.channel.name].values():
                if m != ctx.author.id and str(m) not in events['game'].eventMembers.keys():
                    members += f'<@{m}> '
            if members != '':
                await ctx.send(f"Hey Squad! Ja, genau ihr seid gemeint, Krah Krah!\n{members}")
                log(f"{ctx.author.name} hat das Squad in {ctx.channel.name} gerufen.")
            else:
                await ctx.send(f"Entweder gibt es hier kein Squad oder alle wissen schon bescheid, Krah Krah!")
                log(f"ERROR: {ctx.author.name} hat das Squad in {ctx.channel.name} gerufen aber es gibt keins.")
    
    @commands.command(
        name='squad',
        aliases=['sq'],
        brief='Manage dein Squad mit ein paar simplen Kommandos.'
    )
    async def _squad(self, ctx, *args):
        '''Du willst dein Squad managen? Okay, so gehts!
        Achtung: Jeder Game-Channel hat ein eigenes Squad. Du musst also im richtigen Channel sein.
        
        !squad                  zeigt dir an, wer aktuell im Squad ist.
        !squad add User1 ...    fügt User hinzu. Du kannst auch mehrere User gleichzeitig hinzufügen. "add me" fügt dich hinzu.
        !squad rem User1 ...    entfernt den oder die User wieder.'''
        
        global squads

        if ctx.channel.category != None and ctx.channel.category.name == "Spiele":
            # Ult & Faith
            await addUltCharge(5)
            await addFaith(ctx.author.id, 5)

            if len(args) == 0:
                if len(squads[ctx.channel.name]) > 0:
                    game = ctx.channel.name.replace('-',' ').title()
                    members = ", ".join(squads[ctx.channel.name].keys())
                    await ctx.send(f"Das sind die Mitglieder im {game}-Squad, Krah Krah!\n{members}")
                    log(f"{ctx.author.name} hat das Squad in {ctx.channel.name} angezeigt: {members}.")
                else:
                    await ctx.send(f"Es gibt hier noch kein Squad, Krah Krah!")
                    log(f"ERROR: {ctx.author.name} hat das Squad in {ctx.channel.name} gerufen aber es gibt keins.")
            else:
                if args[0] in ["add", "a", "+"] and len(args) > 1:
                    for arg in args[1:]:
                        if arg == 'me':
                            member = ctx.author
                        else:
                            try:
                                member = client.get_user(int(arg[3:-1]))
                            except:
                                member = None
                        
                        try:
                            if member.name in squads[ctx.channel.name].keys():
                                await ctx.send(f"{member.name} scheint schon im Squad zu sein, Krah Krah!")
                                log(f"ERROR: {ctx.author.name} wollte {member.name} mehrfach zum {ctx.channel.name}-Squad hinzuzufügen.")
                            else:
                                squads[ctx.channel.name][member.name] = member.id
                                await ctx.send(f"{member.name} wurde zum Squad hinzugefügt, Krah Krah!")
                                log(f"{ctx.author.name} hat {member.name} zum {ctx.channel.name}-Squad hinzugefügt.")
                        except:
                            await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                            log(f"ERROR: {ctx.author.name} hat versucht, {arg} zum {ctx.channel.name}-Squad hinzuzufügen.")
                            

                if args[0] in ["rem", "r", "-"] and len(args) > 1:
                    for arg in args[1:]:
                        if arg == 'me':
                            member = ctx.author
                        else:
                            try:
                                member = client.get_user(int(arg[3:-1]))
                            except:
                                member = None

                        try:
                            if member.name in squads[ctx.channel.name].keys():
                                squads[ctx.channel.name].pop(member.name)
                                await ctx.send(f"{member.name} wurde aus dem Squad entfernt, Krah Krah!")
                                log(f"{ctx.author.name} hat {member.name} aus dem {ctx.channel.name}-Squad entfernt.")
                            else:
                                await ctx.send(f"Das macht gar keinen Sinn. {member.name} ist gar nicht im Squad, Krah Krah!")
                                log(f"ERROR: {ctx.author.name} wollte {member.name} aus dem {ctx.channel.name}-Squad entfernen, aber er war nicht Mitglied.")
                        except:
                            await ctx.send(f"Ich kenne {arg} nicht, verlinke ihn bitte mit @.")
                            log(f"ERROR: {ctx.author.name} hat versucht, {arg} aus dem {ctx.channel.name}-Squad zu entfernen.")
                        
                save_file('squads', squads)
        else:
            await ctx.send('Hey, das ist kein Spiele-Channel, Krah Krah!')
            log(f"ERROR: {ctx.author.name} denkt, {ctx.channel.name} sei ein Spiele-Channel.")

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
        PS5_PRICE = 499

        history = await ctx.channel.history(limit=2).flatten()
        message = history[1].content
        
        number = float(re.search(r"\d+(,\d+)?", message).group(0).replace(',','.'))

        quotPS5 = number / PS5_PRICE

        if quotPS5 < 1:
            output = f"Wow, das reicht ja gerade mal für {round(quotPS5*100)}% einer PS5."
        else:
            output = f"Wow, das reicht ja gerade mal für {math.floor(quotPS5)} {'PS5' if math.floor(quotPS5) == 1 else 'PS5en'}."

        await ctx.send(output)

    @commands.command(
        name='urbandict',
        aliases=['ud'],
        brief='Durchforstet das Urban Dictionary'
    )
    async def _urbandict(self, ctx, *args):
        # Charge!
        await addUltCharge(5)
        await addFaith(ctx.author.id, 1)

        term = " ".join(args)

        with urlopen(f'http://api.urbandictionary.com/v0/define?term={urlquote(term.replace(" ", "+"))}') as f:
            data = json.loads(f.read().decode('utf-8'))
            try:
                # Case: Definition found
                definition = data['list'][0]['definition'].translate({ord(c): None for c in '[]'})
                example = data['list'][0]['example'].translate({ord(c): None for c in '[]'})

                embed = discord.Embed(title=f"{term.title()}", colour=discord.Colour(0xff00ff), url=f'https://www.urbandictionary.com/define.php?term={term.replace(" ", "+")}', description=f"{definition}\n\n*{example}*")
                await ctx.send(embed=embed)
                log(f"{ctx.author.name} hat {term} im Urban Dictionary recherchiert.")
            except IndexError:
                # Case: No Definition => Try These
                page = requests.get(f'https://www.urbandictionary.com/define.php?term={urlquote(term.replace(" ", "+"))}')
                soup = BeautifulSoup(page.content, 'html.parser')

                try:
                    items = soup.find('div', class_='try-these').find_all('li')[:10]

                    listitems = [*map(lambda i: i.text, items)]

                    output = "\n".join(listitems)
                    
                    embed = discord.Embed(title=f"Suchvorschläge für {term.title()}", colour=discord.Colour(0xff00ff), description=output)
                    await ctx.send(content="Hey, ich habe habe dazu nichts gefunden, aber versuch's doch mal hiermit:", embed=embed)
                except Exception as e:
                    # Nothing found, not even try these
                    await ctx.send(f"Dazu kann ich nun wirklich gar nichts sagen, Krah Krah!")
                    log(f"{ctx.author.name} hat {term} im Urban Dictionary recherchiert. ERROR: {e}")

    # Commands
    @commands.command(
        name='frage',
        aliases=['f'],
        brief='Stellt eine zufällige Frage.'
    )
    async def _frage(self, ctx):
        # Charge & Faith
        await addUltCharge(1)
        await addFaith(ctx.author.id, 1)

        # Get random question
        frage = random.choice(fragen)

        # Build embed object
        embed = discord.Embed(title=f"Frage an {ctx.author.display_name}", colour=discord.Colour(0xff00ff), description=frage)

        # Send embed object
        try:
            await ctx.send(embed=embed)
            log(f"{ctx.author.name} hat eine Frage verlangt. Sie lautet: {frage}")
        except Exception as e:
            log(f'ERROR: Keine Frage gefunden. Leere Zeile in fragen.txt?: {e}')

    @commands.command(
        name='bibel',
        aliases=['bi'],
        brief='Präsentiert die Weisheiten des Krächzers.'
    )
    async def _bibel(self, ctx):
        # Charge & Faith
        await addUltCharge(1)
        await addFaith(ctx.author.id, 1)

        # Get random bible quote
        quote = random.choice(bibel)

        # Build embed object
        embed = discord.Embed(title="Das Wort unseres Herrn, Krah Krah!", colour=discord.Colour(0xff00ff), description=quote)

        # Send embed object
        try:
            await ctx.send(embed=embed)
            log(f"{ctx.author.name} hat ein Bibel-Zitat verlangt. Es lautet: {quote}")
        except Exception as e:
            log(f'ERROR: Keine Frage gefunden. Leere Zeile in fragen.txt?: {e}')
    
    @commands.command(
        name='zitat',
        aliases=['z'],
        brief='Zitiert eine weise Persönlichkeit.'
    )
    async def _quote(self, ctx):
        global text_model, quoteby

        log(f"Quote: {ctx.author.name} hat ein Zitat von {quoteby} verlangt.")

        try:
            quote = text_model.make_sentence(tries=100)
            while quote == None:
                log(f"Quote: Kein Zitat gefunden, neuer Versuch ...")
                quote = text_model.make_sentence(tries=100)

            # No Discord Quotes allowed in Quotes
            quote.replace('>', '')

            embed = discord.Embed(title="Zitat", colour=discord.Colour(0xff00ff), description=str(quote), timestamp=datetime.utcfromtimestamp(random.randint(0, int(datetime.now().timestamp()))))
            embed.set_footer(text=quoteby)
            await ctx.send(embed=embed)
            
            log(f"Quote erfolgreich: {quote} - {quoteby}")
        except Exception as e:
            log(f"ERROR: {e}")
        
        # Ult & Faith
        await addUltCharge(5)
        await addFaith(ctx.author.id, 1)
    
    @commands.command(
        name='ult',
        aliases=['Q','q'],
        brief='Die ultimative Fähigkeit von Mövius dem Krächzer.'
    )
    async def _ult(self, ctx, *args):
        '''Dieses Kommando feuert die ultimative Fähigkeit von Mövius ab oder liefert dir Informationen über die Ult-Charge.
        Alle Kommandos funktionieren mit dem Wort Ult, können aber auch mit Q oder q getriggert werden.
        
        ?ult    Finde heraus, wie viel Charge Mövius gerade hat.
        !ult    Setze die ultimative Fähigkeit von Mövius ein und warte ab, was dieses Mal geschieht.

        Admin Kommandos:
        !ult [add, -a, +] <n: int>  Fügt der Charge n Prozent hinzu.
        !ult [set, -s, =] <n: int>  Setzt die Charge auf n Prozent.'''

        global STATE, channels

        if ctx.prefix == '?':
            # Output charge
            if STATE['ultCharge'] < 90:
                await ctx.send(f"Meine ultimative Fähigkeit lädt sich auf, Krah Krah! [{int(STATE['ultCharge'])}%]")
            elif STATE['ultCharge'] < 100:
                await ctx.send(f"Meine ultimative Fähigkeit ist fast bereit, Krah Krah! [{int(STATE['ultCharge'])}%]")
            else:
                await ctx.send(f"Meine ultimative Fähigkeit ist bereit, Krah Krah! [{int(STATE['ultCharge'])}%]")
            
            await addFaith(ctx.author.id, 1)
            log(f"{ctx.author.name} hat nach meiner Ult-Charge gefragt: {STATE['ultCharge']}%")
        elif ctx.prefix == '!':
            # Do something
            if len(args) == 0:
                # Ultimate is triggered

                if STATE['ultCharge'] < 100:
                    # Not enough charge
                    await ctx.send(f"Meine ultimative Fähigkeit ist noch nicht bereit, Krah Krah! [{int(STATE['ultCharge'])}%]")
                    log(f"{ctx.author.name} wollte meine Ult aktivieren. Charge: {STATE['ultCharge']}%")
                else:
                    # Ult is ready

                    # Faith
                    await addFaith(ctx.author.id, 10)
                    actionID = random.randint(0, 4)
                    
                    if actionID < 2:
                        # Random stream or game
                        gameType = random.choice(['stream', 'game'])
                        time = f'{str(random.randint(0, 23)).zfill(2)}:{str(random.randint(0, 59)).zfill(2)}'
                        games = list(channels.keys())[1:]
                        game = random.choice(games).replace('-',' ').title()

                        await Reminder.processEventCommand(self, gameType, ctx, (time, game), ult=True)
                    elif actionID == 2:
                        # Random questions
                        await Fun._frage(self, ctx)
                    elif actionID == 3:
                        # Random bible quote
                        await Fun._bibel(self, ctx)
                    elif actionID == 4:
                        # Echo-Ult
                        await Administration._avc(Administration, None)

                    # Reset charge
                    STATE['ultCharge'] = 0

                    with open('state.json', 'w') as f:
                        json.dump(STATE, f)

                    await client.change_presence(activity=discord.Game(f"Charge: {int(STATE['ultCharge'])}%"))
            else:
                # Charge is manipulated by a user
                if ctx.author.name in settings['super-users']:
                    # Only allowed if super user
                    if args[0] in ['add', '-a', '+']:
                        # Add charge
                        try:
                            await addUltCharge(int(args[1]))
                        except:
                            await ctx.send('Nanana, so geht das nicht, Krah Krah!')
                    elif args[0] in ['set', '-s', '=']:
                        # Set charge
                        try:
                            STATE['ultCharge'] = max(min(int(args[1]), 100), 0)
                            
                            with open('state.json', 'w') as f:
                                json.dump(STATE, f)

                            await client.change_presence(activity=discord.Game(f"Charge: {int(STATE['ultCharge'])}%"))
                        except:
                            await ctx.send('Nanana, so geht das nicht, Krah Krah!')
                else:
                    await ctx.send('Nanana, das darfst du nicht, Krah Krah!')

    @commands.command(
        name='faith',
        brief='Wie treu sind wohl die Jünger des Mövius'
    )
    async def _faith(self, ctx, *args):
        '''Dieses Kommando zeigt dir, wie viel 🕊-Glaubenspunkte die Jünger von Mövius gerade haben.
        
        ?faith  Alle Jünger des Mövius und ihre 🕊 werden angezeigt.

        Admin Kommandos:
        !faith [add, -a, +] <id: int> <n: int>  Erhöht den Glauben von einem User mit der id um n🕊.
        !faith [rem, -r, -] <id: int> <n: int>  Reudziert den Glauben von einem User mit der id um n🕊.
        !faith [set, -s, =] <id: int> <n: int>  Setzt den Glauben von einem User mit der id auf n🕊.'''
        global faith

        if ctx.prefix == '?':
            # Sort faith descending by value
            sortedFaith = {k: v for k, v in sorted(faith.items(), key=lambda item: item[1], reverse=True)}

            # Output faith per user
            output = ""
            for user, amount in sortedFaith.items():
                try:
                    output += f"{client.get_user(int(user)).display_name}: {format(amount,',d').replace(',','.')}🕊\n"
                except:
                    log(f"ERROR: Ich konnte den User mit der ID {user} nicht finden.")
            
            if output != "":
                embed = discord.Embed(title="Die treuen Jünger des Mövius und ihre Punkte", colour=discord.Colour(0xff00ff), description=output)

                await ctx.send(embed=embed)
            
            log('Faith wurde angezeigt')
        elif ctx.prefix == '!' and ctx.author.name in settings['super-users']:
            if len(args) == 3:
                try:
                    id = int(args[1])
                    user = client.get_user(id)
                    if user == None:
                        raise Exception
                    amount = int(args[2])
                except Exception as e:
                    await ctx.send('Nanana, so geht das nicht, Krah Krah!')
                    log(f"ERROR: Glaube konnte nicht zugewiesen werden: {e}")
                    
                    return
                
                if args[0] in ['add', '-a', '+']:
                    # Add faith
                    await addFaith(id, amount)
                    await ctx.send(f"Alles klar, {user.display_name} hat {amount}🕊 erhalten, Krah Krah!")
                elif args[0] in ['rem', '-r', '-']:
                    # Remove faith
                    await addFaith(id, amount*(-1))
                    await ctx.send(f"Alles klar, {user.display_name} wurden {amount}🕊 abgezogen, Krah Krah!")
                elif args[0] in ['set', '-s', '=']:
                    # Set faith
                    faith[str(id)] = amount
                    await ctx.send(f"Alles klar, {user.display_name} hat nun {amount}🕊, Krah Krah!")
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

        log(f'Wurstfinger: "{message}" → "{correction}", Dauer: {(time.time() - start_time)}')

        await ctx.send(f"Meintest du vielleicht: {correction}")

        # Ult & Faith
        await addUltCharge(5)
        await addFaith(ctx.author.id, 1)

class Administration(commands.Cog, name='Administration'):
    '''Diese Kategorie erfordert bestimmte Berechtigungen'''

    def __init__(self, bot):
        self.bot = bot

    # Commands
    @isSuperUser()
    @commands.command(
        name='av'
    )
    async def _av(self, ctx):
        await server.me.edit(nick=None)

        with open('Inhaling-Seagull.jpg', 'rb') as f:
            ava = f.read()
            try:
                await client.user.edit(avatar=ava)
            except:
                pass

    @isSuperUser()
    @commands.command(
        name='avc'
    )
    async def _avc(self, ctx):
        global server
        clone = random.choice(server.members)

        await server.me.edit(nick=clone.display_name)

        await clone.avatar_url_as(format='jpg').save('clone.jpg')

        with open('clone.jpg', 'rb') as f:
            ava = f.read()
            try:
                await client.user.edit(avatar=ava)
            except:
                pass

    @isSuperUser()
    @commands.command(
        name='downloadHistory',
        aliases=['dh'],
        brief='Besorgt sich die nötigen Daten für den Zitategenerator. ACHTUNG: Kann einige Sekunden bis Minuten dauern.'
    )
    async def _downloadHistory(self, ctx, id: int, lim: int):
        global server, quoteby

        user = await client.fetch_user(id)
        quoteby = user.display_name

        await ctx.send(f"History Download: Lade pro Channel maximal {lim} Nachrichten von {quoteby} herunter, Krah Krah! Das kann einen Moment dauern, Krah Krah!")
        log(f"{ctx.author.name} lädt die Nachrichten von {quoteby} herunter, Limit: {lim}.")
        
        # Download history
        start_time = time.time()
        numberOfChannels = 0
        numberOfSentences = 0
        lines = [quoteby]

        rammgut = client.get_guild(323922215584268290) # Hard coded Rammgut
        for channel in rammgut.text_channels:
            numberOfChannels += 1
            messages = await channel.history(limit=lim).flatten()
            for m in messages:
                if m.author.id == id:
                    sentences = m.content.split('. ')
                    for s in sentences:
                        if s != '':
                            numberOfSentences += 1
                            lines.append(s)

        with open("channel_messages.txt", "w", encoding="utf-8") as f:
            print(*lines, sep='\n', file=f)

        await ctx.send(f"History Download abgeschlossen! {numberOfSentences} Sätze in {numberOfChannels} Channels von {quoteby} heruntergeladen. Dauer: {(time.time() - start_time)}")
        log(f"History Download abgeschlossen! {numberOfSentences} Sätze in {numberOfChannels} Channels von {quoteby} heruntergeladen. Dauer: {(time.time() - start_time)}")
    
    @isSuperUser()
    @commands.command(
        name='buildMarkov',
        aliases=['bm'],
        brief='Generiert das Modell für zufällige Zitate.'
    )
    async def _makequotes(self, ctx, size: int = 3):
        await ctx.send(f"Markov Update wird gestartet.")

        try:
            buildMarkov(size)
            await ctx.send(f"Markov Update abgeschlossen.")
        except Exception as e:
             await ctx.send(f"ERROR: {e}")

    @isSuperUser()
    @commands.command(
        name='bot',
        aliases=['b'],
        brief='Kann den Bot steuern.'
    )
    async def _bot(self, ctx, cmd, *args):
        if cmd in ['version', '-v']:
            try:
                version = subprocess.check_output('git describe --tags', shell=True).strip().decode('ascii')

                await ctx.send(f"Bot läuft auf Version {version}")
                log(f'Version {version}')
            except Exception as e:
                log(f'ERROR: Version konnte nicht erkannt werden: {e}')
        elif cmd in ['reload', '-r']:
            log(f"{ctx.author.name} hat einen Reload gestartet.")
            startup()
        elif cmd in ['uptime', '-u']:
            uptime = (datetime.now() - startuptime)
            uptimestr = strfdelta(uptime, "{days} Tage {hours}:{minutes}:{seconds}")

            await ctx.send(f"Uptime: {uptimestr} seit {startuptime.strftime('%Y.%m.%d %H:%M:%S')}")
            log(f"Uptime: {uptimestr} seit {startuptime.strftime('%Y.%m.%d %H:%M:%S')}")

##### Add the cogs #####
client.add_cog(Reminder(client))
client.add_cog(Fun(client))
client.add_cog(Administration(client))

@client.event
async def on_ready():
    # Load Settings for the first time
    startup()

    # First Ult Charge Update
    await client.change_presence(activity=discord.Game(f"Charge: {int(STATE['ultCharge'])}%"))

    # Start Loop
    await timeCheck.start()

##### Tasks #####
@tasks.loop(seconds=5)
async def timeCheck():
    global timenow, events

    if timenow != datetime.now().strftime('%H:%M'):
        timenow = datetime.now().strftime('%H:%M')

        # Check for daily Stuff at 9am
        if timenow == '09:00':
            global text_model, quoteby

            log(f'Es ist 9 Uhr, Daily wird abgefeuert')

            try:
                quote = text_model.make_sentence(tries=100)
                while quote == None:
                    log(f"Quote: Kein Zitat gefunden, neuer Versuch ...")
                    quote = text_model.make_sentence(tries=100)

                # No Discord Quotes allowed in Quotes
                quote.replace('>', '')

                embed = discord.Embed(title="Zitat des Tages", colour=discord.Colour(0xff00ff), description=str(quote), timestamp=datetime.utcfromtimestamp(random.randint(0, int(datetime.now().timestamp()))))
                embed.set_footer(text=quoteby)
                await server.get_channel(580143021790855178).send(content="Guten Morgen, Krah Krah!", embed=embed)
                log(f'Zitat des Tages: {quote} - {quoteby}')
            except Exception as e:
                log(f'ERROR: Kein Zitat des Tages: {e}')

            await Administration._av(Administration, None)
        
        # Check for events now
        for e in events.values():
            if e.eventTime == timenow:
                log(f"Ein Event beginnt: {e.eventType}!")
                
                members = ""
                for m in e.eventMembers.keys():
                    members += f"<@{m}> "

                if e.eventType == 'stream':
                    if e.eventGame == 'bot':
                        await client.get_channel(580143021790855178).send(f"Oh, ist es denn schon {e.eventTime} Uhr? Dann ab auf https://www.twitch.tv/hanseichlp ... es wird endlich wieder am Bot gebastelt, Krah Krah! Heute mit von der Partie: {members}", tts=False)
                    else:
                        await channels['stream'].send(f"Oh, ist es denn schon {e.eventTime} Uhr? Dann ab auf https://www.twitch.tv/schnenko/ ... der Stream fängt an, Krah Krah! Heute mit von der Partie: {members}", tts=False)
                else:
                    await channels['game'].send(f"Oh, ist es denn schon {e.eventTime} Uhr? Dann ab in den Voice-Chat, {e.eventGame} fängt an, Krah Krah! Heute mit von der Partie: {members}", tts=False)
                
                e.reset()
                log('Event-Post abgesetzt, Timer resettet.')

@client.event
async def on_message(message):
    # Somehow has to be there
    if message.author == client.user:
        return

    # Add a little charge
    await addUltCharge(0.1)
    
    # Requests from file
    if message.content[1:] in responses['req'].keys():
        response = responses['req'][message.content[1:]]
        for r in response['res']:
            await message.channel.send(r.format(**locals(), **globals()))
        log(response['log'].format(**locals(), **globals()))
    
    # Responses from file
    else:
        for key in responses['res'].keys():
            if re.search(key, message.content):
                response = responses['res'][key]
                for r in response['res']:
                    await message.channel.send(content=r.format(**locals(), **globals()), tts=False)
                log(response['log'].format(**locals(), **globals()))

    #Important for processing commands
    await client.process_commands(message)

async def faithOnReact(payload, operation='add'):
    reactionFaith = 10

    if payload.emoji.name == 'Moevius':
        textChannel = client.get_channel(payload.channel_id)
        # Who received the faith
        author = (await textChannel.fetch_message(payload.message_id)).author
        # Who gave the faith
        giver = client.get_user(payload.user_id)

        # Add/Remove Faith, giver always gets 1
        await addFaith(author.id, reactionFaith*(-1 if operation == 'remove' else 1))
        await addFaith(giver.id, 1)

        # Log
        log(f"FaithAdd-Reaction: {giver.display_name} {'nimmt' if operation == 'remove' else 'gibt'} {author.display_name} {reactionFaith}🕊")

@client.event
async def on_raw_reaction_add(payload):
    await faithOnReact(payload)

@client.event
async def on_raw_reaction_remove(payload):
    await faithOnReact(payload, operation='remove')

@client.event
async def on_command_error(ctx, error):
    log(f"ERROR: {ctx.author.name} - {ctx.message.content} - {error}")

#Connect to Discord
client.run(TOKEN)