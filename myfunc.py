# Helper Functions
from datetime import datetime


def gcts() -> str:
    # Timestamps
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")


def strfdelta(tdelta, fmt: str) -> str:
    # Format time delta for uptime
    delta = {"days": tdelta.days}
    delta["hours"], rem = divmod(tdelta.seconds, 3600)
    delta["minutes"], delta["seconds"] = divmod(rem, 60)
    delta["minutes"] = str(delta["minutes"]).zfill(2)
    delta["seconds"] = str(delta["seconds"]).zfill(2)
    return fmt.format(**delta)
