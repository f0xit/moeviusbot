"""This module contains some helper functions for Discord converters."""

import datetime as dt
import logging
import re

from discord.ext.commands import BadArgument, Context, Converter

from tools.dt_tools import get_local_timezone


class DtString(Converter):
    """Converter for string to datetime. It alway returns a valid date in the future."""

    async def convert(self, ctx: Context, argument: str) -> dt.datetime:
        """Accepted string formats: HH:MM | DD.MM HH:MM"""

        logging.debug("Converting date for %s", ctx.author)

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
