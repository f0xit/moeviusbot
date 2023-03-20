'''This module contains some helper functions for datetime'''

import datetime as dt


def get_local_timezone() -> dt.tzinfo | None:
    '''Helper function to get the local timezone.

    Returns:
        dt._TzInfo: Timezone object with the local timezone'''

    return dt.datetime.now().astimezone().tzinfo


def strfdelta(
    tdelta: dt.timedelta,
    fmt: str = '{days} Tage {hours:02d}:{minutes:02d}:{seconds:02d}'
) -> str:
    '''Helper function to format time deltas

    Args:
        tdelta (dt.timedelta): time delta to be formatted
        fmt (_type_, optional): _Defaults to '{days} Tage {hours:02d}:{minutes:02d}:{seconds:02d}'.

    Returns:
        str: Formatted time delta.'''

    days = tdelta.days
    hours, remainder = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return fmt.format(days=days, hours=hours, minutes=minutes, seconds=seconds)
