#!/usr/bin/env python3
#bot.py

import discord
import os
from dotenv import load_dotenv
import asyncio
import random
import re
from datetime import datetime
import json

#Import own classes
from event import Event
from myfunc import log

#Loading .env, important for the token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log('Token wurde geladen.')

#Get the Discord Client Object
client = discord.Client()

#Define global vars
timenow = ''
channels = {}
charge = 0

#Create events
events = {
    'stream': Event('stream'),
    'game': Event('game')
}

def addCharge(amount):
    global charge
    if charge < 100:
        charge = min(charge + amount, 100)

def load_file(name):
    #try:
        with open(f'{name}.json', 'r') as f:
            return json.load(f)
    #except:
        #pass

def import_files():
    global settings, responses, channels, server

    settings = load_file('settings')
    responses = load_file('responses')

    #Setup Discord objects after settings are loaded
    #Get guild
    log(f"Server-Suche startet.")
    server = client.get_guild(int(settings['server_id']))
    log(f"Server-Suche abgeschlossen: {server.name} - {server.id}.")

    #Get channel for stream and games
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

#Importing setting files
def startup():
    global fragen, events

    for e in events.values():
        e.load()

    import_files()
    
    #Lade die 500 Fragen
    with open('fragen.txt', 'r') as f:
        fragen = f.readlines()
        log('Die Fragen wurden geladen.')

async def loop():
    #I like global variables a lot
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
                if e.time == timenow:
                    log(f"Ein Event beginnt: {e.name}!")
                    
                    members = ""
                    for m in e.members.keys():
                        members += f"<@{m}> "

                    if e.name == 'stream':
                        await channels['stream'].send(f"Oh, ist es denn schon {e.time} Uhr? Dann ab auf https://www.twitch.tv/schnenko/ ... der Stream fängt an, Krah Krah! Heute mit von der Partie: {members}")
                    elif e.name == 'game':
                        await channels['game'].send(f"Oh, ist es denn schon {e.time} Uhr? Dann ab in den Voice-Chat, {e.game} fängt an, Krah Krah! Heute mit von der Partie: {members}")
                    e.reset()
                    e.save()
                    log('Event-Post abgesetzt, Timer resettet.')
        await asyncio.sleep(10)

@client.event
async def on_ready():
    #Load Settings for the first time
    startup()
    log("Ready to Rumble!")

    #Start the Loop
    client.loop.create_task(loop())

@client.event
async def on_message(message):
    #Somehow has to be there
    if message.author == client.user:
        return
    
    #Commands
    if message.content.startswith('!'):
        command = str(message.content.split(' ')[0][1:])
        #Commands for super-users
        if message.author.name in settings['super-users']:
            #Stream-Command
            if command in events.keys():
                try:
                    time = str(message.content.split(' ')[1])

                    if command == 'stream':
                        events['stream'].updateStream(time)
                        if message.author.id in events['stream'].members.keys():
                            pass
                        else:
                            events['stream'].addMember(message.author)
                        
                        if message.channel != channels['stream']:
                            await message.channel.send(f"Ich habe einen Stream-Reminder für {time} Uhr im Channel {channels['stream']} eingerichtet, Krah Krah!")
                        await channels['stream'].send(f"Macht euch bereit für einen Stream, um {time} Uhr geht es los, Krah Krah!")
                    elif command == 'game':
                        channels['game'] = message.channel
                        game = channels['game'].name.replace('-',' ').title()
                        events['game'].updateGame(time, game)

                        if message.author.id in events['game'].members.keys():
                            pass
                        else:
                            events['game'].addMember(message.author)
                        
                        await message.channel.send(f"Danke, {message.author.display_name}, ich habe einen Coop-Reminder für {game} um {time} Uhr eingerichtet, Krah Krah!")
                except:
                    events[command].reset()
                    await message.channel.send(f"Danke, {message.author.display_name}, ich habe den Reminder zurückgesetzt, Krah Krah!")
                    log(f"Event resettet: {message.author.name} - {command}")         
            
            #Reload-Settings
            elif message.content.startswith('reload', 1):
                log(f"{message.author.name} bittet mich, die Einstellungen zurückzusetzen...")
                import_files()

        #Commands for everyone
        #Frage
        if message.content.startswith('frage', 1):
            frage = random.choice(fragen)
            await message.channel.send(f"Frage an {message.author.display_name}: {frage}")
            log(f"{message.author.name} hat eine Frage verlangt. Sie lautet: {frage}")
            addCharge(20)
        elif message.content.startswith('Q', 1):
            if charge < 100:
                await message.channel.send(f"Meine ultimative Fähigkeit ist noch nicht bereit, Krah Krah! [{charge}%]")
            else:
                await message.channel.send(f"BOOOOOOOOOB, TU DOCH WAS!!!")


        #Join Event
        if message.content.startswith('join', 1):
            if message.channel in channels.values():
                if message.channel == channels['stream']:
                    if events['stream'].time == '':
                        await message.channel.send(f"Nanu, anscheinend gibt es nichts zum Beitreten, Krah Krah!")
                    else:
                        if message.author.display_name in events['stream'].members.values():
                            await message.channel.send(f"Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!")
                        else:
                            events['stream'].addMember(message.author)
                            await message.channel.send(f"Alles klar, {message.author.display_name}, ich packe dich auf die Teilnehmerliste für den Stream, Krah Krah!")
                else:
                    if events['game'].time == '':
                        await message.channel.send(f"Nanu, anscheinend gibt es nichts zum Beitreten, Krah Krah!")
                    else:
                        if message.author.display_name in events['game'].members.values():
                            await message.channel.send(f"Hey du Vogel, du stehst bereits auf der Teilnehmerliste, Krah Krah!")
                        else:
                            events['game'].addMember(message.author)
                            await message.channel.send(f"Alles klar, {message.author.display_name}, ich packe dich auf die Teilnehmerliste für {events['game'].game}, Krah Krah!")
    
    #Requests
    elif message.content.startswith('?'):
        if message.content.startswith('wann', 1):
            if events['stream'].time != '':
                await message.channel.send(f"Der nächste Stream beginnt um {events['stream'].time} Uhr, Krah Krah!")
            if events['game'].time != '':
                await message.channel.send(f"Wir spielen {events['game'].game} heute um {events['game'].time} Uhr, Krah Krah!")
        elif message.content.startswith('wer', 1):
            if events['stream'].time != '':
                members = ", ".join(events['stream'].members.values())
                await message.channel.send(f"Heute beim Stream dabei sind bisher: {members}, Krah Krah!")
            if events['game'].time != '':
                members = ", ".join(events['game'].members.values())
                await message.channel.send(f"Heute bei {events['game'].game} dabei sind bisher: {members}, Krah Krah!")
        elif message.content.startswith('charge', 1):
            if charge < 90:
                await message.channel.send(f"Meine ultimative Fähigkeit lädt sich auf, Krah Krah! [{charge}%]")
            elif charge < 100:
                await message.channel.send(f"Meine ultimative Fähigkeit ist fast bereit, Krah Krah! [{charge}%]")
            else:
                await message.channel.send(f"Meine ultimative Fähigkeit ist bereit, Krah Krah! [{charge}%]")


        #Other requests from responses-file
        elif message.content[1:] in responses['req'].keys():
            response = responses['req'][message.content[1:]]
            for r in response['res']:
                await message.channel.send(r.format(**locals(), **globals()))
            log(response['log'].format(**locals(), **globals()))
    
    #Responses
    else:
        for key in responses['res'].keys():
            if re.search(key, message.content):
                response = responses['res'][key]
                for r in response['res']:
                    await message.channel.send(r.format(**locals(), **globals()))
                log(response['log'].format(**locals(), **globals()))

#Connect to Discord
client.run(TOKEN)