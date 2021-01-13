import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import random

from myfunc import log
# TODO: Fix Ult & Faith in general

def setup(bot):
    bot.add_cog(Overwatch(bot))
    log("Cog: Overwatch geladen.")

class Overwatch(commands.Cog, name='Overwatch'):
    def __init__(self, bot):
        self.bot = bot

        self.overwatchPage = requests.get(f'https://playoverwatch.com/de-de/heroes/')
        self.overwatchSoup = BeautifulSoup(self.overwatchPage.content, 'html.parser')
        self.heroes = {}

        cells = self.overwatchSoup.find_all('div', class_='hero-portrait-detailed-container')

        for c in cells:
            self.heroes[c.text] = c.attrs["data-groups"][2:-2].title()

        log("Overwatch-Heroes geladen.")

    # Commands
    @commands.command(
        name='owpatchnotes',
        aliases=['owpn'],
        brief='Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes'
    )
    async def _owpn(self, ctx):
        patchNotesPage = requests.get(f'https://playoverwatch.com/de-de/news/patch-notes/live')
        patchNotesSoup = BeautifulSoup(patchNotesPage.content, 'html.parser')
        patch = patchNotesSoup.find_all('div', class_='PatchNotes-patch')[0].contents

        outputArray = []

        for heroes in patch:
            if 'PatchNotes-labels' in heroes.attrs['class']:
                if 'PatchNotes-date' in heroes.contents[0].attrs['class']:
                    # Patch Date
                    outputArray.append(heroes.text)

                    continue
            
            if 'PatchNotes-section-hero_update' not in heroes.attrs['class']:
                continue

            for h in heroes:
                if h.name != 'div' or h.contents == []:
                    continue

                # Hero name
                outputArray.append(f"**{h.contents[0].text}**")

                # Hero abilities
                for field in h.contents[1].contents:
                    if 'PatchNotesHeroUpdate-generalUpdates' in field.attrs['class']:
                        if len(field.contents) == 2:
                            outputArray.append("Allgemein")
                            outputArray += ["- " + i for i in field.contents[0].text.split('\n') if i != '']
                        else:
                            outputArray.append(field.contents[0].text)
                            outputArray += ["- " + i for i in field.contents[2].text.split('\n') if i != '']

                    elif 'PatchNotesHeroUpdate-abilitiesList' in field.attrs['class']:
                        heroAbilities = field.contents

                        for a in heroAbilities:
                            outputArray.append(a.contents[1].contents[0].text)
                            outputArray += ["- " + i for i in a.contents[1].contents[1].text.split('\n') if i != '']

                outputArray.append('')

            break

        if len(outputArray) <= 1:
            await ctx.send("Im letzten Patch gab es anscheinend keine Heldenupdates, Krah Krah!")

        else:
            embed = discord.Embed(
                title=f"Heldenupdates vom {outputArray[0]}, Krah Krah!",
                colour=discord.Colour(0xff00ff),
                description='\n'.join(outputArray[1:-1])
            )

            await ctx.send(embed=embed)


    @commands.command(
        name='ow',
        brief='Gibt dir oder dem kompletten Voice-Channel zufällige Overwatch-Heroes.'
    )
    async def _ow(self, ctx, who="", role=None):
        '''Dieses Kommando wählt für dich einen zufälligen Overwatch-Hero aus.

        Solltest du dich währenddessen mit anderen Spielern im Voice befinden, bekommt jeder im Channel einen zufälligen Hero zugeteilt.
        Wenn du das vermeiden willst und explizit nur einen Hero für dich selber brauchst, verwende bitte !ow me.
        
        Für eine spezifische Rolle, verwende bitte !owd, !ows oder !owt.'''

        log(f"{ctx.author.name} hat einen zufälligen Overwatch-Hero für {'sich' if who == 'me' else 'alle'} verlangt. Rolle: {role}")

        output = ["Random Heroes? Kein Problem, Krah Krah!"]

        if who == "" and ctx.author.voice != None:
            members = ctx.author.voice.channel.members
        else:
            members = [ctx.author]

        if role in ["Support", "Damage", "Tank"]:
            heroes = {h: r for h, r in self.heroes.items() if r == role}
        else:
            heroes = self.heroes
        
        for m in members:
            hero = random.choice(list(heroes.keys()))

            output.append(f"{m.display_name} spielt: {hero} ({heroes.pop(hero)})")
        
        if output != []:
            await ctx.channel.send("\n".join(output))
            log(f"Heroes für diese Runde: {', '.join(output[1:])}.")
            # await addUltCharge(5)
            # await addFaith(ctx.author.id, 10)
        else:
            log("Keine Heroes gefunden. Es könnte ein Fehler vorliegen.")
        
    @commands.command(
        name='owd',
        brief='Gibt dir einen zufälligen Overwatch-DPS.'
    )
    async def _owd(self, ctx):
        '''Gibt dir einen zufälligen Overwatch-DPS.
        
        Dieses Kommando ist ein Alias für !ow me Damage.'''

        await self._ow(ctx, "me", "Damage")

    @commands.command(
        name='ows',
        brief='Gibt dir einen zufälligen Overwatch-Support.'
    )
    async def _ows(self, ctx):
        '''Gibt dir einen zufälligen Overwatch-Support.
        
        Dieses Kommando ist ein Alias für !ow me Support.'''

        await self._ow(ctx, "me", "Support")

    @commands.command(
        name='owt',
        brief='Gibt dir einen zufälligen Overwatch-Tank.'
    )
    async def _owt(self, ctx):
        '''Gibt dir einen zufälligen Overwatch-Tank.
        
        Dieses Kommando ist ein Alias für !ow me Tank.'''

        await self._ow(ctx, "me", "Tank")