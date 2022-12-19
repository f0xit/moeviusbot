import random
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

from myfunc import log


async def setup(bot):
    await bot.add_cog(Overwatch(bot))
    log("Cog: Overwatch geladen.")


def append_to_output(input_string: str):
    return ["- " + i for i in input_string.split('\n') if i != '']


class Overwatch(commands.Cog, name='Overwatch'):
    def __init__(self, bot):
        self.bot = bot

        self.overwatch_page = requests.get(
            'https://playoverwatch.com/de-de/heroes/')
        self.overwatch_soup = BeautifulSoup(
            self.overwatch_page.content, 'html.parser')
        self.heroes = {}

        cells = self.overwatch_soup.find_all(
            'div', class_='hero-portrait-detailed-container')

        for cell in cells:
            self.heroes[cell.text] = cell.attrs["data-groups"][2:-2].title()

        log("Overwatch-Heroes geladen.")

    # Commands
    @commands.command(
        name='owpatchnotes',
        aliases=['owpn'],
        brief='Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes'
    )
    async def _owpn(self, ctx):
        patch_notes_page = requests.get(
            'https://playoverwatch.com/de-de/news/patch-notes/live')
        patch_notes_soup = BeautifulSoup(
            patch_notes_page.content, 'html.parser')
        patch = patch_notes_soup.find_all(
            'div', class_='PatchNotes-patch')[0].contents

        output_array = []

        for heroes in patch:
            if 'PatchNotes-labels' in heroes.attrs['class']:
                if 'PatchNotes-date' in heroes.contents[0].attrs['class']:
                    # Patch Date
                    output_array.append(heroes.text)

                    continue

            if 'PatchNotes-section-hero_update' not in heroes.attrs['class']:
                continue

            for hero in heroes:
                if hero.name != 'div' or hero.contents == []:
                    continue

                # Hero name
                output_array.append(f"**{hero.contents[0].text}**")

                # Hero abilities
                for field in hero.contents[1].contents:
                    if 'PatchNotesHeroUpdate-generalUpdates' in field.attrs['class']:
                        if len(field.contents) == 2:
                            output_array.append("Allgemein")
                            output_array += append_to_output(
                                field.contents[0].text
                            )
                        else:
                            output_array.append(field.contents[0].text)
                            output_array += append_to_output(
                                field.contents[2].text
                            )
                    elif 'PatchNotesHeroUpdate-abilitiesList' in field.attrs['class']:
                        hero_abilities = field.contents

                        for ability in hero_abilities:
                            output_array.append(
                                ability.contents[1].contents[0].text)
                            output_array += append_to_output(
                                ability.contents[1].contents[1].text
                            )

                output_array.append('')

            break

        if len(output_array) <= 1:
            await ctx.send("Im letzten Patch gab es anscheinend keine Heldenupdates, Krah Krah!")

        else:
            embed = discord.Embed(
                title=f"Heldenupdates vom {output_array[0]}, Krah Krah!",
                colour=discord.Colour(0xff00ff),
                description='\n'.join(output_array[1:-1])
            )

            await ctx.send(embed=embed)

    async def random_hero(self, ctx, who="", role=None):
        log(ctx.author.name
            + "hat einen zufälligen Overwatch-Hero für "
            + ('sich ' if who == 'me' else 'alle ')
            + "verlangt. Rolle: "
            + str(role)
            )

        output = ["Random Heroes? Kein Problem, Krah Krah!"]

        if who == "" and ctx.author.voice is not None:
            members = ctx.author.voice.channel.members
        else:
            members = [ctx.author]

        if role in ["Support", "Damage", "Tank"]:
            heroes = {h: r for h, r in self.heroes.items() if r == role}
        else:
            heroes = self.heroes

        for member in members:
            hero = random.choice(list(heroes.keys()))

            output.append(
                f"{member.display_name} spielt: {hero} ({heroes.pop(hero)})")

        if output != []:
            await ctx.channel.send("\n".join(output))
            log(f"Heroes für diese Runde: {', '.join(output[1:])}.")
            # await addUltCharge(5)
            # await addFaith(ctx.author.id, 10)
        else:
            log("Keine Heroes gefunden. Es könnte ein Fehler vorliegen.")

    @commands.command(
        brief='Gibt dir oder dem kompletten Voice-Channel zufällige Overwatch-Heroes.'
    )
    async def ow(self, ctx, who=""):
        '''Dieses Kommando wählt für dich einen zufälligen Overwatch-Hero aus.

        Solltest du dich währenddessen mit anderen Spielern im Voice befinden,
        bekommt jeder im Channel einen zufälligen Hero zugeteilt.
        Wenn du das vermeiden willst und explizit nur einen Hero für dich selber brauchst,
        verwende bitte !ow me.

        Für eine spezifische Rolle, verwende bitte !owd, !ows oder !owt.'''

        await self.random_hero(ctx, who)

    @commands.command(
        brief='Gibt dir einen zufälligen Overwatch-DPS.'
    )
    async def owd(self, ctx):
        '''Gibt dir einen zufälligen Overwatch-DPS.

        Dieses Kommando ist ein Alias für !ow me Damage.'''

        await self.random_hero(ctx, "me", "Damage")

    @commands.command(
        brief='Gibt dir einen zufälligen Overwatch-Support.'
    )
    async def ows(self, ctx):
        '''Gibt dir einen zufälligen Overwatch-Support.

        Dieses Kommando ist ein Alias für !ow me Support.'''

        await self.random_hero(ctx, "me", "Support")

    @commands.command(
        brief='Gibt dir einen zufälligen Overwatch-Tank.'
    )
    async def owt(self, ctx):
        '''Gibt dir einen zufälligen Overwatch-Tank.

        Dieses Kommando ist ein Alias für !ow me Tank.'''

        await self.random_hero(ctx, "me", "Tank")
