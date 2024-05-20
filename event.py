"""This module contains the event class"""

import datetime as dt
import logging
from enum import Enum, auto

from discord import Member, User

from tools.json_tools import load_file, save_file


class EventType(Enum):
    """Enum of the supported event types"""

    GAME = auto()
    STREAM = auto()

    def __str__(self) -> str:
        return self.name.lower()


class Event:
    """This class is used for events like streams or coop sessions"""

    def __init__(
        self,
        type: EventType,
        time: dt.datetime | None = None,
        game: str = "",
        members: list[int] | None = None,
    ) -> None:
        self.type: EventType = type
        self.time: dt.datetime | None = time
        self.game: str = game
        self.members: list[int] = [] if members is None else members

    def __str__(self) -> str:
        return f"Event ({self.type}, {self.time}, {self.game}, {" ".join(map(str, self.members))})"

    def update_event(self, event_time: dt.datetime, event_game: str) -> None:
        """Updates the event.

        Args:
            event_time (str): Format is HH:MM
            event_game (str): Name of the game played/streamed"""

        self.time = event_time
        self.game = event_game

        self.save()

    def add_member(self, new_member: User | Member) -> None:
        """Adds a member to the event

        Args:
            new_member (User | Member): The added member"""

        if new_member.id in self.members:
            return

        self.members.append(new_member.id)

    def reset(self) -> None:
        """Resets all instance attributes"""

        self.time = None
        self.game = ""
        self.members = []

        self.save()

    def save(self) -> None:
        """Saves the event to a json-file"""

        save_file(str(self.type) + ".json", self.__dict__)

    def load(self) -> None:
        """Loads the event from a json-file if possible"""

        data = load_file(str(self.type) + ".json")

        if not isinstance(data, dict):
            raise OSError

        self.time = dt.datetime.fromisoformat(data["event_time"])
        self.game = data["event_game"]
        self.members = data["event_members"]

        logging.info("Event loaded. %s", self)
