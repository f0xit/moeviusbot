#!/usr/bin/env python3
#bot.py

#Wenn der ganze Quatsch fertig ist, nenne ich es Version 1.0
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

def fstr(inputstr):
    return 

#Loading .env, important for the token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log('Token wurde geladen.')

#Get the Discord Client Object
client = discord.Client()

#Define global vars
timenow = ''
server = {}
channels = {}
responses = {}

#Default Settings
settings = {
    "debug": True,
    "server_id": 337227463564328970,
    "channels": {
        "stream": "test"
    },
    "super-users": [
        "HansEichLP",
        "Schnenko"
    ]
}

#Importing setting files
def load_settings():
    global settings
    global server
    global responses

    #Load main settings
    try:
        with open('settings.json', 'r') as f:
            json_settings = json.load(f)

            if json_settings['debug'] != True:
                for key in settings:
                    try:
                        settings[key] = json_settings[key]
                        log(f'Settings: {key} aus Datei geladen: {settings[key]}')
                    except:
                        log(f'Settings: {key} aus Default geladen: {settings[key]}')
            else:
                log('DEBUG-MODE! Alle Settings wurden aus Default geladen.')
    except FileNotFoundError:
        log('Es konnte keine Datei gefunden werden, die Defaults werden geladen.')
    
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

    #Load respons settings
    try:
        with open('responses.json', 'r') as f:
            responses = json.load(f)
            log("Die Responses wurden geladen.")
    except FileNotFoundError:
        log("Es konnten keine Responses geladen werden.")

#Create events and load data
stream = Event('stream')
stream.load()
log(f'Stream-Zeit wurden geladen: {stream.time}')

#Lade die 500 Fragen
with open('fragen.txt', 'r') as fragen:
    q = fragen.readlines()
    log('Die Fragen wurden geladen.')

async def loop():
    #I like global variables a lot
    global timenow
    
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
    load_settings()
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
                load_settings()

        #Commands for everyone
        else:
            #Frage
                if message.content.startswith('frage', 1):
                    frage = random.choice(q)
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