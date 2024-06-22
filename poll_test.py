"""Main file of the Moevius Discord Bot"""

import asyncio
import datetime as dt
import logging
import os
import re
import sys

import discord
from discord.ext.commands import BadArgument
from dotenv import load_dotenv

from bot import Bot
from cogs.polls import convert_choices_to_list
from tools.dt_tools import get_local_timezone
from tools.logger_tools import LoggerTools
from tools.py_version_tools import check_python_version
from tools.view_tools import emoji_from_asciilo

check_python_version()

STARTUP_TIME = dt.datetime.now()
LOG_TOOL = LoggerTools(level="DEBUG")
discord.utils.setup_logging(root=False)

MOEVIUS = Bot()

TITEL = "Wann Terraria Hardcore?"
CHOICES = "Freitag 19.7.; Samstag 20.7.; Anderer Vorschlag (in den Chat schreiben)"
BESCHREIBUNG = "Hier die Abstimmung für diejenigen, die teilnehmen wollen. Abstimmung läuft bis Sonntag."
UMFRAGE_ENDET = "23.06. 18:00"


async def convert_str_to_dt(argument: str) -> dt.datetime:
    """Accepted string formats: HH:MM | DD.MM. HH:MM"""

    date_match = re.match(
        r"(?:(?P<day>\d{1,2})\.(?P<month>\d{1,2})\.\s)?(?P<hour>\d{,2}):(?P<minute>\d{1,2})",
        argument,
    )

    if date_match is None:
        raise BadArgument

    today = dt.datetime.now(get_local_timezone())

    match date_match.groups():
        case (None, None, hour, minute):
            event_date = dt.datetime(
                today.year,
                today.month,
                today.day,
                int(hour),
                int(minute),
                tzinfo=get_local_timezone(),
            )

            if event_date < today:
                event_date += dt.timedelta(1)

        case (day, month, hour, minute):
            event_date = dt.datetime(
                today.year,
                int(month),
                int(day),
                int(hour),
                int(minute),
                tzinfo=get_local_timezone(),
            )

            if event_date < today:
                event_date = event_date.replace(year=today.year + 1)

        case _:
            raise BadArgument

    return event_date


@MOEVIUS.event
async def on_ready() -> None:
    poll_channel = MOEVIUS.get_channel(706383037012770898)

    if not isinstance(poll_channel, discord.TextChannel):
        return

    end_date = await convert_str_to_dt(UMFRAGE_ENDET)

    end_from_now = end_date - dt.datetime.now(get_local_timezone())

    poll = discord.Poll(TITEL, duration=end_from_now, multiple=True)

    for ch, text in convert_choices_to_list(CHOICES):
        poll.add_answer(text=text, emoji=emoji_from_asciilo(ch))

    await poll_channel.send(BESCHREIBUNG, poll=poll)


async def main() -> None:
    load_dotenv()

    if (discord_token := os.getenv("DISCORD_TOKEN")) is None:
        sys.exit("Discord token not found! Please check your .env file!")
    else:
        logging.info("Discord token loaded successfully.")

    await MOEVIUS.start(discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopping Moevius ...")
        asyncio.run(MOEVIUS.close())
        logging.info("Moevius stopped. Good night.")
        sys.exit(130)
