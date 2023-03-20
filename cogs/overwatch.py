'''Cog for overwatch related commands'''
import logging
import random
from enum import Enum

import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from result import Err, Ok, Result, UnwrapError

from bot import Bot
from tools.request_tools import async_request_html

PROMT = 'Random Heroes? Kein Problem, Krah Krah!\n'


class Role(Enum):
    '''Enum of current Overwatch classes'''

    NONE = 0
    TANK = 1
    DAMAGE = 2
    SUPPORT = 3


async def setup(bot: Bot) -> None:
    '''Setup function for the cog.'''

    overwatch_cog = Overwatch(bot)

    if (await overwatch_cog.load_overwatch_heroes()).is_err():
        logging.error('Loading heroes failed: %s')
        return

    await bot.add_cog(overwatch_cog)
    logging.info('Cog: Overwatch geladen.')


def append_to_output(input_string: str) -> list[str]:
    '''This function will be replaced soon.'''

    return ["- " + i for i in input_string.split('\n') if i != '']


class Overwatch(commands.Cog, name='Overwatch'):
    '''This cog includes some overwatch related commands'''

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.heroes: dict[str, str] = {}

    async def load_overwatch_heroes(self) -> Result[str, str]:
        '''Parses the hero list from the overwatch website and stores it in a dict.'''

        logging.info('Loading Overwatch heroes...')

        hero_url = 'https://playoverwatch.com/de-de/heroes/'

        try:
            hero_result = (await async_request_html(hero_url)).unwrap()
        except UnwrapError as err_msg:
            logging.error('Request failed: %s', err_msg)
            return Err(f'Requesting hero list failed: {err_msg}')

        overwatch_soup = BeautifulSoup(hero_result, 'html.parser')

        cells = overwatch_soup.find_all('blz-hero-card', class_='heroCard')

        if cells is None:
            return Err('Finding heroes on website failed!')

        self.heroes = {
            cell.attrs["data-hero-id"].title(): cell.attrs["data-role"].title()
            for cell in cells
        }

        logging.info('Overwatch heroes loaded: %s heroes.', len(cells))
        return Ok(f'Overwatch heroes loaded: {len(cells)} heroes.')

    async def random_hero_for_user(self, requested_role: Role = Role.NONE) -> Result[str, str]:
        '''This function returns the name of a random overwatch hero. The randomizer
        can be filtered by the role.'''

        if (not self.heroes) and (await self.load_overwatch_heroes()).is_err():
            return Err('Loading heroes failed.')

        if requested_role == Role.NONE:
            return Ok(random.choice(
                list(self.heroes.keys())
            ))

        return Ok(random.choice([
            hero for hero, role in self.heroes.items()
            if Role(role) is requested_role
        ]))

    async def random_hero_for_group(
        self,
        author: discord.Member
    ) -> Result[list[str], str]:
        '''This function returns random heroes for a group of player that are in the
        same voice channel with the author.'''

        if author.voice is None or author.voice.channel is None:
            return Err('User not in voice channel!')

        members = author.voice.channel.members

        if (not self.heroes) and (await self.load_overwatch_heroes()).is_err():
            return Err('Loading heroes failed.')

        heroes = list(self.heroes.keys())
        random.shuffle(heroes)

        return Ok([f"{member.display_name}: {heroes.pop()}" for member in members])

    @commands.command(
        name='owpatchnotes',
        aliases=['owpn'],
        brief='Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes.'
    )
    async def _owpn(self, ctx: commands.Context) -> None:
        '''Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes.'''

        patch_notes_url = 'https://playoverwatch.com/de-de/news/patch-notes/live'

        try:
            patch_notes_result = (await async_request_html(patch_notes_url)).unwrap()
        except UnwrapError as err_msg:
            logging.error('Request failed: %s', err_msg)
            return

        patch_notes_soup = BeautifulSoup(patch_notes_result, 'html.parser')

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

            try:
                await ctx.channel.send(
                    PROMT + (await self.random_hero_for_user()).unwrap()
                )
            except UnwrapError as err_msg:
                logging.error(err_msg)
        else:
            logging.info(
                '%s requested a random hero for everyone.',
                ctx.author.name
            )

            try:
                await ctx.channel.send(
                    PROMT + ', '.join((await self.random_hero_for_group(ctx.author)).unwrap())
                )
            except UnwrapError as err_msg:
                logging.error(err_msg)

    @ commands.command(
        brief='Gibt dir einen zufälligen Overwatch-DPS.'
    )
    async def owd(self, ctx: commands.Context) -> None:
        '''Gibt dir einen zufälligen Overwatch-DPS.'''

        logging.info(
            '%s requested a random hero for themselves, Role: Damage.',
            ctx.author.name
        )

        try:
            await ctx.channel.send(
                PROMT + (await self.random_hero_for_user(Role.DAMAGE)).unwrap()
            )
        except UnwrapError as err_msg:
            logging.error(err_msg)

    @ commands.command(
        brief='Gibt dir einen zufälligen Overwatch-Support.'
    )
    async def ows(self, ctx: commands.Context) -> None:
        '''Gibt dir einen zufälligen Overwatch-Support.'''

        logging.info(
            '%s requested a random hero for themselves, Role: Support.',
            ctx.author.name
        )

        try:
            await ctx.channel.send(
                PROMT + (await self.random_hero_for_user(Role.SUPPORT)).unwrap()
            )
        except UnwrapError as err_msg:
            logging.error(err_msg)

    @ commands.command(
        brief='Gibt dir einen zufälligen Overwatch-Tank.'
    )
    async def owt(self, ctx: commands.Context) -> None:
        '''Gibt dir einen zufälligen Overwatch-Tank.'''

        logging.info(
            '%s requested a random hero for themselves, Role: Tank.',
            ctx.author.name
        )

        try:
            await ctx.channel.send(
                PROMT + (await self.random_hero_for_user(Role.TANK)).unwrap()
            )
        except UnwrapError as err_msg:
            logging.error(err_msg)
