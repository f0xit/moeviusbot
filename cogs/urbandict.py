import logging
import json
from typing import Tuple
from urllib.parse import quote as urlquote
import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from bot import Bot


async def setup(bot: Bot) -> None:
    await bot.add_cog(UrbanDict(bot))
    logging.info("Cog: UrbanDict loaded.")


def format_url(url: str, term: str) -> str:
    """Formats the url combined with a serch term.

    Args:
        url (str): The url, needs to end with ?term=
        term (str): The search term.

    Returns:
        str: The formatted url including the search term
    """
    return url + urlquote(term.replace(' ', '+'))


async def request_ud_definition(term: str) -> Tuple[str, str]:
    """Uses the urban dictionary API and returns the first definition
    and the corresponding example sentence. Returns a Tuple of empty
    strings, if no definition exists.

    Args:
        term (str): The search term for the API.

    Returns:
        Tuple[str, str]: (definition, example)
    """
    api_url = 'http://api.urbandictionary.com/v0/define?term='

    response = requests.get(
        format_url(api_url, term),
        timeout=10
    )

    if response.status_code != 200:
        return '', ''

    data = json.loads(response.text)

    if not data['list']:
        return '', ''

    first_result: dict[str, str] = data['list'][0]

    definition = first_result['definition'].translate(
        {ord(c): None for c in '[]'}
    )
    example = first_result['example'].translate(
        {ord(c): None for c in '[]'}
    )

    return definition, example


async def request_try_these(term: str) -> list[str] | None:
    """Scrapes the urban dictionary website to find existing definitions,
    when the search term doesn't have one.

    Args:
        term (str): The search term.

    Returns:
        list[str] | None: A list of existing terms to try.
            None if nothing was found.
    """
    page_url = 'https://www.urbandictionary.com/define.php?term='

    response = requests.get(
        format_url(page_url, term),
        timeout=10
    )

    if response.status_code != 404:
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    if not (div := soup.find('div', class_='try-these')):
        return

    if not (items := div.find_all('li')[:10]):
        return

    return [item.text for item in items]


class UrbanDict(commands.Cog, name='UrbanDict'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command(
        name='urbandict',
        aliases=['ud'],
        brief='Durchforstet das Urban Dictionary'
    )
    async def _urbandict(self, ctx: commands.Context, *args):
        term = ' '.join(args)

        logging.info(
            '%s looked for %s in the Urban Dictionary.',
            ctx.author.name,
            term
        )

        definition, example = await request_ud_definition(term)

        if definition:
            logging.debug(
                'Definition found.'
            )
            await ctx.send(embed=discord.Embed(
                title=f"{term.title()}",
                colour=discord.Colour(0xff00ff),
                url=format_url(
                    'https://www.urbandictionary.com/define.php?term=', term
                ),
                description=f'{definition}\n\n*{example}*'
            ))
        elif (try_these := await request_try_these(term)):
            logging.debug(
                'No definition found, but a list of try-these.'
            )
            await ctx.send(
                content='Hey, ich habe habe dazu nichts gefunden, '
                'aber versuch\'s doch mal hiermit:',
                embed=discord.Embed(
                    title=f'Suchvorschläge für {term.title()}',
                    colour=discord.Colour(0xff00ff),
                    description='\n'.join(try_these)
                )
            )
        else:
            logging.debug(
                'No definition found.'
            )
            await ctx.send('Dazu kann ich nun wirklich gar nichts sagen, Krah Krah!')
