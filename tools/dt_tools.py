import datetime as dt


def get_local_timezone() -> dt.tzinfo | None:
    """Quick tool to get the local timezone.

    Returns:
        dt._TzInfo: Timezone object with the local timezone"""

    return dt.datetime.now().astimezone().tzinfo
