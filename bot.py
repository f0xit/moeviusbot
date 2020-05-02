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

#Event-Class
class Event:
    name = ''
    time = ''
    
    def __init__ (self, name):
        self.name = name
    
    def update(self, time):
        self.time = time
    
    def reset(self):
        self.time = ''
        
    def save(self):
        with open(self.name + '.json', 'w') as f:
            json.dump(self.__dict__, f)
    
    def load(self):
        with open(self.name + '.json', 'r') as f:
            self.time = json.load(f)['time']

#This is how you get your complete timestamp
def gcts():
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")

#This is how you log it
def log(inputstr):
    print('[' + gcts() + '] ' + inputstr)

#Loading .env, important for the token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#Get the Discord Client Object
client = discord.Client()

#Create events and load data
stream = Event('stream')
stream.load()
log('Stream-Zeiten wurden geladen.')

#Define timenow for loop
timenow = ''
log('Timenow wurde resettet.')

async def loop():
    #I like global variables a lot
    global timenow
    
    #Wait until ready
    await client.wait_until_ready()
    log('Der Loop wurde gestartet.')
    
    #This defines the channel, where the reminder is posted
    #todo: Selector einbauen für die Games und den Stream, muss dann in die Schleife
    #todo: Channel IDs in ein Settings-File, damit die Konfi leichter wird
    #channel = client.get_channel(323922356491780097) #schnenkonervt
    #log('Aktueller Channel für Streams ist: ##schnenkonervt')
    channel = client.get_channel(666764020073889792) #cayton
    log('Aktueller Channel für Streams ist: #cayton')
    
    #Endless loop for checking timenow
    while True:
        #Update timenow only if it needs to be updated
        if timenow != datetime.now().strftime('%H:%M'):
            timenow = datetime.now().strftime('%H:%M')
            #Check for stream now?
            if stream.time == timenow:
                log('Der Stream geht los.')
                await channel.send('Oh, ist es denn schon ' + stream.time + ' Uhr? Dann ab auf https://www.twitch.tv/schnenko/ ... der Stream fängt an, Krah Krah!')
                stream.reset()
                log('Post wurde abgesetzt, Timer wurde resettet.')
        await asyncio.sleep(10)
    
@client.event
async def on_message(message):
    #Somehow has to be there
    if message.author == client.user:
        return
    
    #Krah krah!
    if re.search('Mövius', message.content):
        await message.channel.send("Krah Krah!")
        log(message.author.name + ' hat mich erwähnt!!!')
    
    #Give me a randiom question
    if message.content == '!frage':
        frage = random.choice(q)
        await message.channel.send("Frage an " + message.author.display_name + ": " + frage)
        log(message.author.name + ' hat eine Frage verlangt. Sie lautet: ' + frage)
    
    #Radeberger? Who the hell needs Radeberger?
    if message.content == '?radeberger':
        await message.channel.send('Nein, Krah Krah!')
        await message.channel.send('Einfach nein, ' + message.author.display_name + ', Krah Krah!')
        log(message.author.name + ' hat einfach gar keinen Geschmack.')
    
    #EVENTS
    #Is there a timer? And if yes: When?
    if message.content == '?wann':
        if stream.time == '':
            await message.channel.send('Uff, der faule Schnenko hat anscheinend keinen Stream angekündigt, Krah Krah!')
            log(message.author.name + ' hat nach dem Stream gefragt, aber es gibt keinen.')
        else:
            await message.channel.send('Gut, dass du fragst! Der nächste Stream beginnt um ' + stream.time + ' Uhr, Krah Krah!')
            log(message.author.name + ' hat nach dem Stream gefragt.')
    
    #Set the timer
    if message.author.name == 'Schnenko' or message.author.name == 'HansEichLP':
        if re.search('^!stream \d{1,2}:\d{2}$', message.content):
            for time in re.findall('\d{1,2}:\d{2}$', message.content):
                log(message.author.name + ' hat einen Stream-Zeipunkt festgelegt: ' + time)
                stream.update(time)
                stream.save()
                await message.channel.send('Danke, ' + message.author.display_name + ', ich werde einen Reminder für ' + stream.time + ' Uhr einrichten, Krah Krah!')
                log('Der Timer wurde gesetzt auf ' + stream.time + ' und das Savefile wurde geupdatet.')

@client.event
async def on_ready():
    log('Ready to go!')


#Lade die 500 Fragen
with open("fragen.txt", "r") as fragen:
    q = fragen.readlines()
    log('Die Fragen wurden geladen.')

#Get Ready To Rumble!!!
#Start the Loop
client.loop.create_task(loop())
#Connect to Discord
client.run(TOKEN)