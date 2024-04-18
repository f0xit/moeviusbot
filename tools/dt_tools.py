"""This module contains some helper functions for datetime"""

import datetime as dt
import random

from zoneinfo import ZoneInfo


def get_local_timezone() -> dt.tzinfo:
    """Helper function to get the local timezone.

    Returns:
        dt.tzinfo: Timezone object with the local timezone"""

    return ZoneInfo("Europe/Berlin")


def strfdelta(
    tdelta: dt.timedelta,
    fmt: str = "{days} Tage {hours:02d}:{minutes:02d}:{seconds:02d}",
) -> str:
    """Helper function to format time deltas

    Args:
        tdelta (dt.timedelta): time delta to be formatted
        fmt (str, optional): _Defaults to '{days} Tage {hours:02d}:{minutes:02d}:{seconds:02d}'.

    Returns:
        str: Formatted time delta."""

    days = tdelta.days
    hours, remainder = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return fmt.format(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )


def get_random_date() -> dt.datetime:
    return dt.datetime.fromtimestamp(
        random.SystemRandom().randint(0, int(dt.datetime.now(dt.UTC).timestamp())),
        dt.UTC,
    )
