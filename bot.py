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

#This is how you Get your Complete TimeStamp
def gcts():
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")

#This is how you log it
def log(inputstr):
    print('[' + gcts() + '] ' + inputstr)
    with open('logs/' + datetime.now().strftime('%Y-%m-%d') + '_moevius.log', 'a') as f:
        f.write('[' + gcts() + '] ' + inputstr + '\n')

#Loading .env, important for the token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log('Token wurde geladen.')

#Get the Discord Client Object
client = discord.Client()

#Define global vars
timenow = ''
channels = {}

#Default Settings

def load_file(name):
    try:
        with open(f'{name}.json', 'r') as f:
            return json.load(f)
    except:
        pass

def import_files():
    global settings, responses, server

    settings = load_file('settings')
    responses = load_file('responses')

    #Setup Discord objects after settings are loaded
    #Get guild
    server = client.get_guild(int(settings['server_id']))
    log(f"Server {server.name} gefunden, ID: {settings['server_id']}.")

    #Get channel for streams
    for c in server.text_channels:
        if c.name == settings['channels']['stream']:
            channels['stream'] = c
            log(f"Für den Stream wurde der Channel mit dem Namen {settings['channels']['stream']} gefunden, ID: {c.id}")
    
    #Settings loaded
    log("Die Einstellungen wurden komplett geladen.")

#Importing setting files
def startup():
    global settings, responses, server, stream, fragen

    import_files()

    #Create events and load data
    stream = Event('stream')
    stream.load()
    log(f'Stream-Zeit wurden geladen: {stream.time}')
    
    #Lade die 500 Fragen
    with open('fragen.txt', 'r') as f:
        fragen = f.readlines()
        log('Die Fragen wurden geladen.')

async def loop():
    #I like global variables a lot
    global timenow, stream
    
    #Wait until ready
    await client.wait_until_ready()
    log('Der Loop wurde gestartet.')
    
    #Endless loop for checking timenow
    while True:
        #Update timenow only if it needs to be updated
        if timenow != datetime.now().strftime('%H:%M'):
            timenow = datetime.now().strftime('%H:%M')
            #Check for stream now?
            if stream.time == timenow:
                log('Der Stream geht los.')
                await channels['stream'].send('Oh, ist es denn schon ' + stream.time + ' Uhr? Dann ab auf https://www.twitch.tv/schnenko/ ... der Stream fängt an, Krah Krah!')
                stream.reset()
                stream.save()
                log('Post wurde abgesetzt, Timer wurde resettet.')
        await asyncio.sleep(10)

@client.event
async def on_ready():
    #load settings
    startup()
    log("Ready to Rumble!")

@client.event
async def on_message(message):
    #Somehow has to be there
    if message.author == client.user:
        return
    
    #Commands
    if message.content.startswith('!'):
        #Commands for super-users
        if message.author.name in settings['super-users']:
            #Stream-Command
            if message.content.startswith('stream', 1):
                time = re.findall(r'\d{2}:\d{2}$|$', message.content)[0]
                if time == '':
                    await message.channel.send(f"Danke, {message.author.display_name}, ich werde den Reminder zurücksetzen, Krah Krah!")
                    log(f"{message.author.name} hat den Stream-Zeitpunkt resettet!")
                else:
                    await message.channel.send(f"Danke, {message.author.display_name}, ich werde einen Reminder für {time} Uhr einrichten, Krah Krah!")
                    log(f"{message.author.name} hat den Stream-Zeitpunkt auf {time} festgelegt und das Savefile wurde geupdatet.!")
                stream.update(time)
                stream.save()
            
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
    
    #Requests
    elif message.content.startswith('?'):
        if message.content.startswith('wann', 1):
            if stream.time == '':
                await message.channel.send("Uff, der faule Schnenko hat anscheinend keinen Stream angekündigt, Krah Krah!")
                log(f"{message.author.name} hat nach dem Stream gefragt, aber es gibt keinen.")
            else:
                await message.channel.send(f"Gut, dass du fragst! Der nächste Stream beginnt um {stream.time} Uhr, Krah Krah!")
                log(f"{message.author.name} hat nach dem Stream gefragt.")
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

#Start the Loop
client.loop.create_task(loop())
#Connect to Discord
client.run(TOKEN)