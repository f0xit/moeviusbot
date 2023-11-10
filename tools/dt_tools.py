"""This module contains some helper functions for datetime"""

import datetime as dt

from zoneinfo import ZoneInfo


def get_local_timezone() -> dt.tzinfo | None:
    """Helper function to get the local timezone.

    Returns:
        dt._TzInfo: Timezone object with the local timezone"""

    return ZoneInfo("Europe/Berlin")


def get_week_boundaries() -> tuple[dt.datetime, dt.datetime]:
    """_summary_

    Returns:
        tuple[dt.datetime, dt.datetime]: _description_"""

    today = dt.datetime.combine(dt.date.today(), dt.time(0))

    start = today - dt.timedelta(days=today.weekday())
    end = start + dt.timedelta(days=7) - dt.timedelta(seconds=1)

    return start, end


def strfdelta(
    tdelta: dt.timedelta, fmt: str = "{days} Tage {hours:02d}:{minutes:02d}:{seconds:02d}"
) -> str:
    """Helper function to format time deltas

    Args:
        tdelta (dt.timedelta): time delta to be formatted
        fmt (_type_, optional): _Defaults to '{days} Tage {hours:02d}:{minutes:02d}:{seconds:02d}'.

    Returns:
        str: Formatted time delta."""

    days = tdelta.days
    hours, remainder = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return fmt.format(days=days, hours=hours, minutes=minutes, seconds=seconds)
