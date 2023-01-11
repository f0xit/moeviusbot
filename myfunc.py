# Helper Functions
from datetime import datetime
import json
import logging

# Timestamps for loggin


def gcts() -> str:
    return datetime.now().strftime("%Y.%m.%d %H:%M:%S")

# Format time delta for uptime


def strfdelta(tdelta, fmt: str) -> str:
    delta = {"days": tdelta.days}
    delta["hours"], rem = divmod(tdelta.seconds, 3600)
    delta["minutes"], delta["seconds"] = divmod(rem, 60)
    delta["minutes"] = str(delta["minutes"]).zfill(2)
    delta["seconds"] = str(delta["seconds"]).zfill(2)
    return fmt.format(**delta)

# A quick and dirty load function for .json-files


def load_file(name) -> dict:
    try:
        with open(f'{name}.json', 'r', encoding="utf-8") as file:
            return json.load(file)
    except IOError:
        logging.error('File %s konnte nicht geladen werden!', name)
        return {}


def save_file(name, content) -> None:
    try:
        with open(f'{name}.json', 'w', encoding="utf-8") as file:
            json.dump(content, file)
    except IOError:
        logging.error('File %s konnte nicht gespeichert werden!', name)
