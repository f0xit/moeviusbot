#!/usr/bin/env python3
#bot.py

##### Imports #####
import discord
from discord.ext import commands, tasks
import os
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

# Import Custom Stuff
from event import Event
from myfunc import log, load_file, save_file

##### First Setup #####
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log('Token wurde geladen.')

# Get the Discord Client Object
client = commands.Bot(command_prefix=('!','?'))

# Variables for global use
quoteby = ''
timenow = ''
channels = {}
ultCharge = 100

# Create events
events = {
    'stream': Event('stream'),
    'game': Event('game')
}

##### Functions #####

# Set up everything when load or reload
def startup():
    global fragen, bibel, settings, responses, channels, server, squads

    settings = load_file('settings')
    responses = load_file('responses')
    squads = load_file('squads')

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
    global ultCharge

    if ultCharge < 100:
        ultCharge = min(ultCharge + amount, 100)
        if amount > 1:
            log(f'Ult-Charge hinzugefügt: {amount}')
    else:
        log(f'Ult-Charge bereit.')
    
    await client.change_presence(activity=discord.Game(f"Charge: {int(ultCharge)}%"))

# Markov
def buildMarkov():
    global text_model, quoteby

    try:
        # Build Markov Chain
        start_time = time.time()
        with open("channel_messages.txt") as f:
            quoteby = f.readline()[:-1]
            text = f.read()

        # Build the model.
        text_model = markovify.NewlineText(text)
        log(f"Markov Update. Dauer: {(time.time() - start_time)}")
    except:
        log(f"ERROR: Markov fehlgeschlagen. Dauer: {(time.time() - start_time)}")

##### Cogs #####
class Reminder(commands.Cog, name='Events'):
    '''Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten, beizutreten oder deren Status abzufragen.
    
    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP, wenn du mehr darüber wissen willst.'''
    
    def __init__(self, bot):
        self.bot = bot
    
    # Process an Event-Command (Stream, Game, ...)
    async def processEventCommand(self, eventType: str, ctx, args):
        global channels, events, squads

        # Check for super-user
        if eventType == 'stream' and ctx.author.name not in settings['super-users']:
            await ctx.send('Nanana, das darfst du nicht, Krah Krah!')
            log(f'ERROR: {ctx.author.name} wollte den Stream-Reminder einstellen.')

            # Charge!
            await addUltCharge(1)
            return
        
        # Charge!
        await addUltCharge(5)

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

            # Update event
            log(f"{ctx.author.name} hat das Event {eventType} geupdatet.")
            events[eventType].updateEvent(time, game)

            # Add creator to the watchlist
            log(f"{ctx.author.name} wurde zum Event {eventType} hinzugefügt.")
            events[eventType].addMember(ctx.author)
            
            # Direct feedback for the creator
            # Stream
            if eventType == 'stream':
                if ctx.channel != channels['stream']:
                    await ctx.send(f"Ich habe einen Stream-Reminder für {time} Uhr eingerichtet, Krah Krah!")
                
                # Announce the event in the right channel
                await channels['stream'].send(f"Macht euch bereit für einen Stream, um {time} Uhr{gameStr}, Krah Krah!")
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

    global bibel
    
    def __init__(self, bot):
        self.bot = bot

    # Commands
    @commands.command(
        name='frage',
        aliases=['f'],
        brief='Stellt eine zufällige Frage.'
    )
    async def _frage(self, ctx):
        # Charge!
        await addUltCharge(1)

        frage = random.choice(fragen)

        embed = discord.Embed(colour=discord.Colour(0xff00ff))
        embed.add_field(name=f"Frage an {ctx.author.display_name}", value=frage)

        await ctx.send(embed=embed)
        log(f"{ctx.author.name} hat eine Frage verlangt. Sie lautet: {frage}")
    
    @commands.command(
        name='urbandict',
        aliases=['ud'],
        brief='Durchforstet das Urban Dictionary'
    )
    async def _urbandict(self, ctx, *args):
        # Charge!
        await addUltCharge(1)

        with urlopen(f'http://api.urbandictionary.com/v0/define?term={urlquote(args[0])}') as f:
            data = json.loads(f.read().decode('utf-8'))
            definition = data['list'][0]['definition'].translate({ord(c): None for c in '[]'})
        
        embed = discord.Embed(colour=discord.Colour(0xff00ff))
        embed.set_footer(text="Quelle: Urban Dictionary")
        embed.add_field(name=f"Definition von {args[0]}", value=definition)

        await ctx.send(embed=embed)
        log(f"{ctx.author.name} hat {args[0]} im Urban Dictionary recherchiert.")

    @commands.command(
        name='bibel',
        aliases=['b'],
        brief='Präsentiert die Weisheiten des Krächzers.'
    )
    async def _bibel(self, ctx):
        # Charge!
        await addUltCharge(5)

        quote = random.choice(bibel)

        embed = discord.Embed(colour=discord.Colour(0xff00ff))
        embed.add_field(name=f"Das Wort unseres Herrn, Krah Krah!", value=quote)

        await ctx.send(embed=embed)
        log(f"{ctx.author.name} hat eine Bibel-Zitat verlangt. Es lautet: {quote}")
    
    @commands.command(
        name='Q',
        aliases=['q'],
        brief='Setzt Mövius ultimative Fähigkeit ein.'
    )
    async def _ult(self, ctx):
        global ultCharge, channels

        if ultCharge < 100:
            await ctx.send(f"Meine ultimative Fähigkeit ist noch nicht bereit, Krah Krah! [{int(ultCharge)}%]")
            log(f"{ctx.author.name} wollte meine Ult aktivieren. Charge: {ultCharge}%")
        else:
            # Ult
            actionID = random.randint(0, 4)
            
            if actionID < 2:
                # Random Stream & Game
                gameType = random.choice(['stream', 'game'])
                time = f'{str(random.randint(0, 23)).zfill(2)}:{str(random.randint(0, 59)).zfill(2)}'
                games = list(channels.keys())[1:]
                game = random.choice(games).replace('-',' ').title()

                await Reminder.processEventCommand(self, gameType, ctx, (time, game))
            elif actionID == 2:
                await Fun._frage(self, ctx)
            elif actionID == 3:
                await Fun._bibel(self, ctx)
            elif actionID == 4:
                await Administration._avc(Administration, None)

            # reset Ult
            ultCharge = 0
            await client.change_presence(activity=discord.Game(f"Charge: {int(ultCharge)}%"))

    @commands.command(
        name='charge',
        aliases=['c'],
        brief='Gibt die aktuelle Ult-Charge an.'
    )
    async def _charge(self, ctx):
        global ultCharge

        if ultCharge < 90:
            await ctx.send(f"Meine ultimative Fähigkeit lädt sich auf, Krah Krah! [{int(ultCharge)}%]")
        elif ultCharge < 100:
            await ctx.send(f"Meine ultimative Fähigkeit ist fast bereit, Krah Krah! [{int(ultCharge)}%]")
        else:
            await ctx.send(f"Meine ultimative Fähigkeit ist bereit, Krah Krah! [{int(ultCharge)}%]")
        
        log(f"{ctx.author.name} hat nach meiner Ult-Charge gefragt: {ultCharge}%")
    
    @commands.command(
        name='zitat',
        aliases=['z'],
        brief='Zitiert eine weise Persönlichkeit.'
    )
    async def _quote(self, ctx):
        global text_model

        try:
            embed = discord.Embed(colour=discord.Colour(0xff00ff), timestamp=datetime.utcfromtimestamp(random.randint(0, int(datetime.now().timestamp()))))
            embed.set_footer(text="Schnenko")
            embed.add_field(name=f"Zitat", value=str(text_model.make_sentence(tries=100)))

            await ctx.send(embed=embed)
            
            log(f"{ctx.author.name} hat ein Zitat von {quoteby} verlangt.")
        except:
            pass

class Administration(commands.Cog, name='Administration'):
    '''Diese Kategorie erfordert bestimmte Berechtigungen'''

    def __init__(self, bot):
        self.bot = bot

    # Commands
    @isSuperUser()
    @commands.command(
        name='reload',
        aliases=['r'],
        brief='Lädt die Einstellungen neu.'
    )
    async def _reload(self, ctx):
        log(f"{ctx.author.name} hat einen Reload gestartet.")
        startup()

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
        name='getquotes',
        aliases=['gq'],
        brief='Besorgt sich die nötigen Daten für den Zitategenerator. ACHTUNG: Nicht zu oft machen.'
    )
    async def _getquotes(self, ctx, id: int, lim: int):
        global server, quoteby

        user = await client.fetch_user(id)
        quoteby = user.display_name

        log(f"{ctx.author.name} lädt die Nachrichten von {quoteby} herunter.")
        
        # Download history
        start_time = time.time()
        lines = [quoteby]

        rammgut = client.get_guild(323922215584268290)
        for channel in rammgut.text_channels:
            messages = await channel.history(limit=lim).flatten()
            for m in messages:
                if m.author.id == id:
                    sentences = m.content.split('. ')
                    for s in sentences:
                        if s != '':
                            lines.append(s)

        with open("channel_messages.txt", "w", encoding="utf-8") as f:
            print(*lines, sep='\n', file=f)

        await ctx.send(f"History Update: {len(lines)} Sätze von {user.name}. Dauer: {(time.time() - start_time)}")
        log(f"History Update: {len(lines)} Sätze von {user.name}. Dauer: {(time.time() - start_time)}")
    
    @isSuperUser()
    @commands.command(
        name='makequotes',
        aliases=['mk'],
        brief='Generiert das Modell für zufällige Zitate.'
    )
    async def _makequotes(self, ctx):
        buildMarkov()

        await ctx.send(f"Markov Update.")
    
    @isSuperUser()
    @commands.command(
        name='addcharge',
        aliases=['ac'],
        brief='Ändert die Ult-Charge.'
    )
    async def _charge(self, ctx, charge: int):
        global ultCharge
        ultCharge = min(int(charge),100)
        await client.change_presence(activity=discord.Game(f"Charge: {int(ultCharge)}%"))

##### Add the cogs #####
client.add_cog(Reminder(client))
client.add_cog(Fun(client))
client.add_cog(Administration(client))

@client.event
async def on_ready():
    # Load Settings for the first time
    startup()

    await Administration._av(Administration, None)

    # First Ult Charge Update
    await client.change_presence(activity=discord.Game(f"Charge: {int(ultCharge)}%"))

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
            global text_model

            try:
                embed = discord.Embed(colour=discord.Colour(0xff00ff), timestamp=datetime.utcfromtimestamp(random.randint(0, int(datetime.now().timestamp()))))
                embed.set_footer(text="Schnenko")   
                embed.add_field(name="Zitat des Tages", value=str(text_model.make_sentence(tries=100)))

                await server.get_channel(706383037012770898).send(content="Guten Morgen, Krah Krah!", embed=embed)
                log(f'Zitat des Tages.')
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
                    await channels['stream'].send(content=f"Oh, ist es denn schon {e.eventTime} Uhr? Dann ab auf https://www.twitch.tv/schnenko/ ... der Stream fängt an, Krah Krah! Heute mit von der Partie: {members}", tts=True)
                else:
                    await channels['game'].send(content=f"Oh, ist es denn schon {e.eventTime} Uhr? Dann ab in den Voice-Chat, {e.eventGame} fängt an, Krah Krah! Heute mit von der Partie: {members}", tts=True)
                
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
                    await message.channel.send(content=r.format(**locals(), **globals()), tts=True)
                log(response['log'].format(**locals(), **globals()))

    #Important for processing commands
    await client.process_commands(message)

#Connect to Discord
client.run(TOKEN)