'''Cog for overwatch related commands'''
import random
import logging
from enum import Enum
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from bot import Bot

PROMT = 'Random Heroes? Kein Problem, Krah Krah!\n'


class Role(Enum):
    '''Enum of current Overwatch classes'''
    TANK = 'Tank'
    DAMAGE = 'Damage'
    SUPPORT = 'Support'


async def setup(bot: Bot) -> None:
    '''Setup function for the cog.'''

    await bot.add_cog(Overwatch(bot))
    logging.info('Cog: Overwatch geladen.')


def append_to_output(input_string: str) -> list[str]:
    '''This function will be replaced soon.'''
    return ["- " + i for i in input_string.split('\n') if i != '']


def load_overwatch_heroes() -> dict[str, str]:
    '''Parses the hero list from the overwatch website and stores it in a dict.

    Returns:
        dict[str, str]: Dictionary of all overwatch heroes. Key is name, value is role.
    '''

    hero_url = 'https://playoverwatch.com/de-de/heroes/'
    response = requests.get(hero_url, timeout=10)

    if response.status_code != 200:
        return {}

    overwatch_soup = BeautifulSoup(response.content, 'html.parser')

    cells = overwatch_soup.find_all(
        'blz-hero-card', class_='heroCard'
    )

    logging.info('Overwatch-Heroes loaded.')

    return {cell.attrs["data-hero-id"].title(): cell.attrs["data-role"].title() for cell in cells}


class Overwatch(commands.Cog, name='Overwatch'):
    '''This cog includes some overwatch related commands'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.heroes = load_overwatch_heroes()

    async def random_hero_for_user(
        self,
        requested_role: Role | None = None
    ) -> str:
        '''This function returns the name of a random overwatch hero. The randomizer
        can be filtered by the role.

        Args:
            requested_role (Role, optional): The hero's role, being either Tank, Damage
            or Support. When Role is None, every hero can be chosen randomly. Defaults to None.

        Returns:
            str: The name of a random hero.
        '''

        if requested_role is None:
            return random.choice(
                list(self.heroes.keys())
            )

        return random.choice([
            hero for hero, role in self.heroes.items()
            if Role(role) is requested_role
        ])

    async def random_hero_for_group(
        self,
        author: discord.Member
    ) -> list[str] | None:
        '''This function returns random heroes for a group of player that are in the
        same voice channel with the author.

        Args:
            author (discord.User | discord.Member): The message author.

        Returns:
            list[str] | None: A list of string, formated like display_name: hero_name
            for every user in the voice channel.
        '''

        if author.voice is None:
            return

        if author.voice.channel is None:
            return

        members = author.voice.channel.members

        heroes = list(self.heroes.keys())
        random.shuffle(heroes)

        return [f"{member.display_name}: {heroes.pop()}" for member in members]

    @commands.command(
        name='owpatchnotes',
        aliases=['owpn'],
        brief='Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes.'
    )
    async def _owpn(self, ctx: commands.Context) -> None:
        '''Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes.'''

        patch_notes_page = requests.get(
            'https://playoverwatch.com/de-de/news/patch-notes/live',
            timeout=10
        )
        patch_notes_soup = BeautifulSoup(
            patch_notes_page.content, 'html.parser'
        )
        latest_patch = patch_notes_soup.find_all(
            'div', class_='PatchNotes-patch'
        )[0].contents

        output_array = []

        for heroes in latest_patch:
            if ('PatchNotes-labels' in heroes.attrs['class']
                    and 'PatchNotes-date' in heroes.contents[0].attrs['class']):
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
            return

        await ctx.send(
            embed=discord.Embed(
                title=f"Heldenupdates vom {output_array[0]}, Krah Krah!",
                colour=discord.Colour(0xff00ff),
                description='\n'.join(output_array[1:-1])
            )
        )

    @ commands.command(
        name='ow',
        brief='Gibt dir oder dem kompletten Voice-Channel zufällige Overwatch-Heroes.'
    )
    async def _ow(self, ctx: commands.Context, who: str = '') -> None:
        '''Dieses Kommando wählt für dich einen zufälligen Overwatch-Hero aus.

        Solltest du dich währenddessen mit anderen Spielern im Voice befinden,
        bekommt jeder im Channel einen zufälligen Hero zugeteilt.
        Wenn du das vermeiden willst und explizit nur einen Hero für dich selber brauchst,
        verwende bitte !ow me.

        Für eine spezifische Rolle, verwende bitte !owd, !ows oder !owt.'''

        if not isinstance(ctx.author, discord.Member):
            return

        if who == 'me' or ctx.author.voice is None:
            logging.info(
                '%s requested a random hero for themselves.',
                ctx.author.name
            )
            await ctx.channel.send(
                PROMT + await self.random_hero_for_user()
            )
        else:
            logging.info(
                '%s requested a random hero for everyone.',
                ctx.author.name
            )
            if (group_output := await self.random_hero_for_group(ctx.author)) is None:
                return
            await ctx.channel.send(
                PROMT + ', '.join(group_output)
            )

    @ commands.command(
        brief='Gibt dir einen zufälligen Overwatch-DPS.'
    )
    async def owd(self, ctx: commands.Context) -> None:
        '''Gibt dir einen zufälligen Overwatch-DPS.
        Dieses Kommando ist ein Alias für !ow me Damage.'''

        logging.info(
            '%s requested a random hero for themselves. Role: Damage.',
            ctx.author.name
        )
        await ctx.channel.send(
            PROMT + await self.random_hero_for_user(Role.DAMAGE)
        )

    @ commands.command(
        brief='Gibt dir einen zufälligen Overwatch-Support.'
    )
    async def ows(self, ctx: commands.Context) -> None:
        '''Gibt dir einen zufälligen Overwatch-Support.
        Dieses Kommando ist ein Alias für !ow me Support.'''

        logging.info(
            '%s requested a random hero for themselves. Role: Support.',
            ctx.author.name
        )
        await ctx.channel.send(
            PROMT + await self.random_hero_for_user(Role.SUPPORT)
        )

    @ commands.command(
        brief='Gibt dir einen zufälligen Overwatch-Tank.'
    )
    async def owt(self, ctx: commands.Context) -> None:
        '''Gibt dir einen zufälligen Overwatch-Tank.
        Dieses Kommando ist ein Alias für !ow me Tank.'''

        logging.info(
            '%s requested a random hero for themselves. Role: Tank.',
            ctx.author.name
        )
        await ctx.channel.send(
            PROMT + await self.random_hero_for_user(Role.TANK)
        )
