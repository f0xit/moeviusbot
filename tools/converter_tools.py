from __future__ import annotations

import datetime as dt
import re
from string import ascii_lowercase

from discord.ext.commands import BadArgument

from tools.dt_tools import get_local_timezone


def convert_choices_to_list(choices_str: str) -> list[tuple[str, str]]:
    """Takes a string, splits it by semicolons, and turns the chunks into
    a list, enumerated by lowercase letters, starting at 'a'.

    Trailing semicolons or whitespace between semicolons are ignored.

    Example:
        'apple; banana ; ;cake;' is converted into
        [('a', 'apple'),('b', 'banana'),('c', 'cake')]

    Args:
        choices_str (str): A string of choices, seperated by semicolons

    Returns:
        list[tuple[str, str]]: A list of choices, enumerated by lowercase
        letters, starting at 'a'"""

    return list(zip(ascii_lowercase, [name for name in map(str.strip, choices_str.split(";")) if name], strict=False))


async def convert_str_to_dt(argument: str) -> dt.datetime:
    """Accepted string formats: HH:MM | DD.MM HH:MM"""

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
