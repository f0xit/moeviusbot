"""Cog for overwatch related commands"""

from __future__ import annotations

import io
import logging
import random
from enum import Enum, auto
from typing import TYPE_CHECKING

import discord
from bs4 import BeautifulSoup, ResultSet, Tag
from discord.ext import commands

from tools.request_tools import async_request_html

if TYPE_CHECKING:
    from bot import Bot

PROMPT = "Random Heroes? Kein Problem, Krah Krah!\n"
HERO_URL = "https://overwatch.blizzard.com/de-de/heroes/"
PATCH_NOTES_URL = "https://overwatch.blizzard.com/de-de/news/patch-notes/live/"


class OwHeroError(Exception):
    pass


class Role(Enum):
    """Enum of current Overwatch classes"""

    NONE = 0
    TANK = auto()
    DAMAGE = auto()
    SUPPORT = auto()


async def setup(bot: Bot) -> None:
    """Setup function for the cog."""

    overwatch_cog = Overwatch(bot)

    await overwatch_cog.load_overwatch_heroes()

    await bot.add_cog(overwatch_cog)
    logging.info("Cog: Overwatch geladen.")


async def parse_hero_patch(hero: Tag) -> dict | None:
    """Parses a given hero-soup from the overwatch website and stores it in a dict."""

    output_dict = {}
    hero_name_tag = hero.find("h5")
    if not isinstance(hero_name_tag, Tag):
        return None

    hero_name = hero_name_tag.contents[0]

    output_dict[hero_name] = {}

    output_dict[hero_name]["gen"] = [
        list_item.contents[0]
        for general_update in hero.find_all("div", class_="PatchNotesHeroUpdate-generalUpdates")
        for list_item in general_update.find_all(["li", "p"])
    ]

    output_dict[hero_name]["abs"] = {
        (
            ability_name[0]
            if (ability_name := ability.find("div", class_="PatchNotesAbilityUpdate-name").contents)
            else "<Ability name not found>"
        ): [list_item.contents[0] for list_item in ability.find_all("li")]
        for ability in hero.find_all("div", class_="PatchNotesAbilityUpdate-text")
        if ability
    }

    return output_dict


async def parse_patchnotes() -> dict | None:
    """Parses the patchnotes from the overwatch website an creates a dict."""

    output_dict = {}

    patch_notes_soup = BeautifulSoup(await async_request_html(PATCH_NOTES_URL), "html.parser")
    patches: ResultSet[Tag] = patch_notes_soup.find_all("div", class_="PatchNotes-patch")

    for patch in patches:
        entry_point = patch.find("h4", class_="PatchNotes-sectionTitle", string="HELDENUPDATES")
        title_tag = patch.find("h3", class_="PatchNotes-patchTitle")

        if not isinstance(title_tag, Tag) or not isinstance(entry_point, Tag):
            continue

        output_dict = {
            "title": title_tag.contents[0],
            "changes": {},
        }

        entry_section = entry_point.find_parent()
        if entry_section is None:
            continue

        for section in entry_section.next_siblings:
            if not isinstance(section, Tag) or "PatchNotes-section-hero_update" not in section.attrs["class"]:
                break

            section_header = section.find("h4")
            if not isinstance(section_header, Tag):
                continue

            if (hero_class := section_header.contents[0]) not in output_dict:
                output_dict["changes"][hero_class] = {}

            for hero in section_header.next_siblings:
                if not isinstance(hero, Tag) or "PatchNotesHeroUpdate" not in hero.attrs["class"]:
                    continue

                output_dict["changes"][hero_class].update(await parse_hero_patch(hero))

        break

    return output_dict


class Overwatch(commands.Cog, name="Overwatch"):
    """This cog includes some overwatch related commands"""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.heroes: dict[str, str] = {}

    async def load_overwatch_heroes(self) -> None:
        """Parses the hero list from the overwatch website and stores it in a dict."""

        logging.info("Loading Overwatch heroes...")

        cells = BeautifulSoup(
            await async_request_html(HERO_URL),
            "html.parser",
        ).find_all(
            "blz-hero-card",
            class_="heroCard",
        )

        if cells is None:
            msg = "Could not load Overwatch heroes!"
            raise OwHeroError(msg)

        self.heroes = {cell.attrs["data-hero-id"].title(): cell.attrs["data-role"].upper() for cell in cells}
        logging.info("Overwatch heroes loaded: %s heroes.", len(cells))

    async def random_hero_for_user(self, requested_role: Role = Role.NONE) -> str:
        """This function returns the name of a random overwatch hero. The randomizer
        can be filtered by the role."""

        if not self.heroes:
            await self.load_overwatch_heroes()

        if requested_role == Role.NONE:
            return random.SystemRandom().choice(list(self.heroes.keys()))

        return random.SystemRandom().choice([hero for hero, role in self.heroes.items() if role == requested_role.name])

    async def random_hero_for_group(self, author: discord.Member) -> list[str]:
        """This function returns random heroes for a group of player that are in the
        same voice channel with the author."""

        if author.voice is None or author.voice.channel is None:
            msg = "User not in voice channel!"
            raise OwHeroError(msg)

        members = author.voice.channel.members

        if not self.heroes:
            await self.load_overwatch_heroes()

        heroes = list(self.heroes.keys())
        random.shuffle(heroes)

        return [f"{member.display_name}: {heroes.pop()}" for member in members]

    @commands.command(
        name="owpatchnotes",
        aliases=["owpn"],
        brief="Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes.",
    )
    async def _owpn(self, ctx: commands.Context) -> None:
        """Liefert dir, falls vorhanden, die neusten Änderungen bei Helden aus den Patchnotes."""

        if (patchnotes := await parse_patchnotes()) is None:
            await ctx.send("Etwas ist schiefgelaufen, Krah Krah!")
            return

        if not patchnotes:
            await ctx.send("Anscheinend gab es in letzter Zeit keine Heldenupdates, Krah Krah!")
            return

        embed_list = []
        output = io.StringIO()

        for hero_class in patchnotes["changes"].items():
            embed = discord.Embed(title=hero_class[0].capitalize(), colour=discord.Colour(0xFF00FF))
            for hero in hero_class[1].items():
                if hero[1]["gen"]:
                    output.write("__Allgemein__:\n")
                    output.write("\n".join(hero[1]["gen"]))
                    output.write("\n")

                if hero[1]["abs"]:
                    for ability in hero[1]["abs"]:
                        output.write(f"__{ability}__:\n")
                        output.write("\n".join(hero[1]["abs"][ability]))
                        output.write("\n")

                embed.add_field(name=hero[0], value=output.getvalue(), inline=False)

                output.truncate(0)
                output.seek(0)

            embed_list.append(embed)

        await ctx.send(f"**{patchnotes['title']}**", embeds=embed_list)

        output.close()

    @commands.command(name="ow", brief="Gibt dir oder dem kompletten Voice-Channel zufällige Overwatch-Heroes.")
    async def _ow(self, ctx: commands.Context, who: str = "") -> None:
        """Dieses Kommando wählt für dich einen zufälligen Overwatch-Hero aus.

        Solltest du dich währenddessen mit anderen Spielern im Voice befinden,
        bekommt jeder im Channel einen zufälligen Hero zugeteilt.
        Wenn du das vermeiden willst und explizit nur einen Hero für dich selber brauchst,
        verwende bitte !ow me.

        Für eine spezifische Rolle, verwende bitte !owd, !ows oder !owt."""

        if not isinstance(ctx.author, discord.Member):
            return

        if who == "me" or ctx.author.voice is None:
            logging.info("%s requested a random hero for themselves.", ctx.author.name)

            await ctx.channel.send(PROMPT + (await self.random_hero_for_user()))
        else:
            logging.info("%s requested a random hero for everyone.", ctx.author.name)

            await ctx.channel.send(PROMPT + ", ".join(await self.random_hero_for_group(ctx.author)))

    @commands.command(brief="Gibt dir einen zufälligen Overwatch-DPS.")
    async def owd(self, ctx: commands.Context) -> None:
        """Gibt dir einen zufälligen Overwatch-DPS."""

        logging.info("%s requested a random hero for themselves, Role: Damage.", ctx.author.name)

        await ctx.channel.send(PROMPT + (await self.random_hero_for_user(Role.DAMAGE)))

    @commands.command(brief="Gibt dir einen zufälligen Overwatch-Support.")
    async def ows(self, ctx: commands.Context) -> None:
        """Gibt dir einen zufälligen Overwatch-Support."""

        logging.info("%s requested a random hero for themselves, Role: Support.", ctx.author.name)

        await ctx.channel.send(PROMPT + (await self.random_hero_for_user(Role.SUPPORT)))

    @commands.command(brief="Gibt dir einen zufälligen Overwatch-Tank.")
    async def owt(self, ctx: commands.Context) -> None:
        """Gibt dir einen zufälligen Overwatch-Tank."""

        logging.info("%s requested a random hero for themselves, Role: Tank.", ctx.author.name)

        await ctx.channel.send(PROMPT + (await self.random_hero_for_user(Role.TANK)))
