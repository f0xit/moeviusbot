# bot.py
import os
import random
import re
import asyncio
from datetime import datetime
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

#Fragen laden yay
q = []
t = open("fragen.txt", "r")

for l in t:
    if l != "":
        q.append(l)
    
t.close()

timenow = ''
eventtime = ''

async def loop():
    global timenow
    global eventtime
    await client.wait_until_ready()
    channel = client.get_channel(323922356491780097) #schnenkonervt
    #channel = client.get_channel(666764020073889792) #cayton
    
    while True:
        if timenow != datetime.now().strftime('%H:%M'):
            timenow = datetime.now().strftime('%H:%M')
            if eventtime == timenow:
                await channel.send('Oh, ist es denn schon ' + eventtime + ' Uhr? Dann ab auf https://www.twitch.tv/schnenko/ ... der Stream fängt an, Krah Krah!')
                eventtime = ''
        await asyncio.sleep(10)
    
@client.event
async def on_message(message):
    global eventtime
    if message.author == client.user:
        return

    if message.content == '!frage':
        frage = random.choice(q)
        await message.channel.send("Frage an " + message.author.display_name + ": " + frage)
        
    if message.content == '?radeberger':
        await message.channel.send('Nein, Krah Krah!')
        await message.channel.send('Einfach nein, ' + message.author.display_name + ', Krah Krah!')
        
    if message.content == '?wann':
        if eventtime == '':
            await message.channel.send('Uff, der faule Schnenko hat anscheinend keinen Stream angekündigt, Krah Krah!')
        else:
            await message.channel.send('Gut, dass du fragst! Der nächste Stream beginnt um ' + eventtime + ' Uhr, Krah Krah!')
        
    if re.search('Mövius', message.content):
        await message.channel.send("Krah Krah!")
    
    if message.author.name == 'Schnenko' or message.author.name == 'HansEichLP':
        if re.search('^!stream \d{1,2}:\d{2}$', message.content):
            for time in re.findall('\d{1,2}:\d{2}$', message.content):
                eventtime = time
                await message.channel.send('Danke, ' + message.author.display_name + ', ich werde einen Reminder für ' + eventtime + ' Uhr einrichten, Krah Krah!')

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.loop.create_task(loop())
client.run(TOKEN)