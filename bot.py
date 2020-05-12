#!/usr/bin/env python3
#bot.py

##### Imports #####
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import random
import re
from datetime import datetime
import json

# Import Custom Stuff
from event import Event
from myfunc import log, load_file

##### First Setup #####
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log('Token wurde geladen.')

# Get the Discord Client Object
client = commands.Bot(command_prefix=('!','?'))

# Variables for global use
timenow = ''
channels = {}
ultCharge = 0

# Create events
events = {
    'stream': Event('stream'),
    'game': Event('game')
}

##### Functions #####

# Set up everything when load or reload
def startup():
    global fragen, settings, responses, channels, server

    settings = load_file('settings')
    responses = load_file('responses')

    # Get Discord objects after settings are loaded
    # Get guild = server
    log(f"Server-Suche startet.")
    server = client.get_guild(int(settings['server_id']))
    log(f"Server-Suche abgeschlossen: {server.name} - {server.id}.")

    # Get channel for stream and games
    log(f"Channel-Suche startet.")
    for c in server.text_channels:
        if c.name == settings['channels']['stream']:
            channels['stream'] = c
            log(f"Channel für Stream gefunden: {c.name} - {c.id}")
        elif c.category != None:
            if c.category.name == 'Spiele':
                channels[c.name] = c
                log(f"Channel für Spiel gefunden: {c.name} - {c.id}")
    log(f"Channel-Suche abgeschlossen.")
    
    # 500 Fragen
    with open('fragen.txt', 'r') as f:
        fragen = f.readlines()
        log('Die Fragen wurden geladen.')

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
    
    await client.change_presence(activity=discord.Game(f"Charge: {ultCharge}%"))

async def loop():
    # TODO: Make it a loop-event for the bot
    global timenow, events
    
    #Wait until ready
    await client.wait_until_ready()
    log("Der Loop wurde gestartet.")
    
    #Endless loop for checking timenow
    while True:
        #Update timenow only if it needs to be updated
        if timenow != datetime.now().strftime('%H:%M'):
            timenow = datetime.now().strftime('%H:%M')

            #Check for events now
            for e in events.values():
                if e.eventTime == timenow:
                    log(f"Ein Event beginnt: {e.eventType}!")
                    
                    members = ""
                    for m in e.eventMembers.keys():
                        members += f"<@{m}> "

                    if e.eventType == 'stream':
                        await channels['stream'].send(f"Oh, ist es denn schon {e.eventTime} Uhr? Dann ab auf https://www.twitch.tv/schnenko/ ... der Stream fängt an, Krah Krah! Heute mit von der Partie: {members}")
                    else:
                        await channels['game'].send(f"Oh, ist es denn schon {e.eventTime} Uhr? Dann ab in den Voice-Chat, {e.eventGame} fängt an, Krah Krah! Heute mit von der Partie: {members}")
                    
                    e.reset()
                    log('Event-Post abgesetzt, Timer resettet.')
        await asyncio.sleep(10)

##### Cogs #####
class Reminder(commands.Cog, name='Events'):
    '''Diese Kommandos dienen dazu, Reminder für Streams oder Coop-Sessions einzurichten, beizutreten oder deren Status abzufragen.
    
    Bestimmte Kommandos benötigen bestimmte Berechtigungen. Kontaktiere HansEichLP, wenn du mehr darüber wissen willst.'''
    
    def __init__(self, bot):
        self.bot = bot
    
    # Process an Event-Command (Stream, Game, ...)
    async def processEventCommand(self, eventType: str, ctx, args):
        global channels, events

        # Check for super-user
        if ctx.author.name not in settings['super-users']:
            await ctx.send('Nanana, das darfst du nicht, Krah Krah!')

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
                        return
            # More than one argument
            else:
                game = ' '.join(args[1:])
                gameStr = f". Gespielt wird: {game}"

            # Update event
            events[eventType].updateEvent(time, game)

            # Add creator to the watchlist
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

    # Join an event
    async def joinEvent(self, eventType: str, ctx):
        global events

        if events[eventType].eventTime == '':
            await ctx.send(f"Nanu, anscheinend gibt es nichts zum Beitreten, Krah Krah!")
        else:
            # Charge!
            await addUltCharge(5)
            if ctx.author.display_name in events[eventType].eventMembers.values():
                await ctx.send(f"Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!")
            else:
                events[eventType].addMember(ctx.author)
                await ctx.send(f"Alles klar, ich packe dich auf die Teilnehmerliste, Krah Krah!")
    
    # Commands
    @commands.command(
        name='stream',
        brief='Infos und Einstellungen zum aktuellen Stream-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _stream(self, ctx, *args):
        '''Hier kannst du alles über einen aktuellen Stream-Reminder herausfinden oder seine Einstellungen anpassen
        
        ?stream Sagt dir, ob ein Stream angekündigt wurde. Falls ja, erfährst du, wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer sich bisher zum Stream angemeldet hat. Mehr dazu findest du in der Hilfe zum join-Kommando.

        !stream resettet den aktuellen Reminder.
        !stream hh:mm stellt einen Reminder für die gewählte Uhrzeit ein.
        !stream hh:mm game stellt außerdem ein, welches Spiel gespielt wird.'''

        # Stream command
        if ctx.prefix == '!':
            await self.processEventCommand('stream', ctx, args)
        
        # Stream info
        elif ctx.prefix == '?':
            await self.processEventInfo('stream', ctx)
    
    @commands.command(
        name='game',
        brief='Infos und Einstellungen zum aktuellen Coop-Reminder.',
        usage='(hh:mm) (game)'
    )
    async def _game(self, ctx, *args):
        '''Hier kannst du alles über einen aktuellen Coop-Reminder herausfinden oder seine Einstellungen anpassen
        
        ?game Sagt dir, ob eine Coop-Runde angekündigt wurde. Falls ja, erfährst du, wann und welches Spiel gestream wird. Außerdem kannst du sehen, wer sich bisher zum Coop angemeldet hat. Mehr dazu findest du in der Hilfe zum join-Kommando.

        !game resettet den aktuellen Reminder.
        !game hh:mm stellt einen Reminder für die gewählte Uhrzeit im Channel ein.
        !game hh:mm game stellt wahlweise ein Spiel ein, welches keinen eigenen Channel hat.'''

        # Game command
        if ctx.prefix == '!':
            await self.processEventCommand('game', ctx, args)
        
        # Game info
        elif ctx.prefix == '?':
            await self.processEventInfo('game', ctx)
    
    @commands.command(
        name='join',
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

class Fun(commands.Cog, name='Spaß'):
    '''Ein paar spaßige Kommandos für zwischendurch.'''
    
    def __init__(self, bot):
        self.bot = bot

    # Commands
    @commands.command(
        name='frage',
        brief='Stellt eine zufällige Frage.'
    )
    async def _frage(self, ctx):
        # Charge!
        await addUltCharge(1)

        frage = random.choice(fragen)
        await ctx.send(f"Frage an {ctx.author.display_name}: {frage}")
        log(f"{ctx.author.name} hat eine Frage verlangt. Sie lautet: {frage}")
    
    @commands.command(
        name='Q',
        brief='Setzt Mövius ultimative Fähigkeit ein.'
    )
    async def _ult(self, ctx):
        global ultCharge

        if ultCharge < 100:
            await ctx.send(f"Meine ultimative Fähigkeit ist noch nicht bereit, Krah Krah! [{ultCharge}%]")
        else:
            await ctx.send(f"BOOOOOOOOOB, TU DOCH WAS!!!")
            ultCharge = 0

class Administration(commands.Cog, name='Administration'):
    '''Diese Kategorie erfordert bestimmte Berechtigungen'''

    def __init__(self, bot):
        self.bot = bot

    # Commands
    @isSuperUser()
    @commands.command(
        name='reload',
        brief='Lädt die Einstellungen neu.'
    )
    async def _reload(self, ctx):
        log(f"{ctx.author.name} bittet mich, die Einstellungen zurückzusetzen...")
        startup()

##### Add the cogs #####
client.add_cog(Reminder(client))
client.add_cog(Fun(client))
client.add_cog(Administration(client))

@client.event
async def on_ready():
    #Load Settings for the first time
    startup()
    log("Ready to Rumble!")

    # First Ult Charge Update
    await client.change_presence(activity=discord.Game(f"Charge: {ultCharge}%"))

    #Start the Loop
    client.loop.create_task(loop())

@client.event
async def on_message(message):
    #Somehow has to be there
    if message.author == client.user:
        return
    
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
                    await message.channel.send(r.format(**locals(), **globals()))
                log(response['log'].format(**locals(), **globals()))

    #Important for processing commands
    await client.process_commands(message)

#Connect to Discord
client.run(TOKEN)