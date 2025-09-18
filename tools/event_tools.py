"""This module contains the classes and functions for handling events in the reminder part
of the discord bot"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum, auto

from tools.dt_tools import get_local_timezone


class EventType(Enum):
    """Enum of the supported event types"""

    GAME = auto()
    STREAM = auto()

    def __str__(self) -> str:
        return self.name.lower()


@dataclass
class Event:
    """Datalass to represent events like streams and games"""

    event_type: EventType
    event_title: str
    event_dt: dt.datetime
    event_members: list[int]
    event_id: int = 0
    event_game: str = field(default="")

    def __str__(self) -> str:
        return (
            f"Event ({self.event_type}, {self.event_dt}, {self.event_game}, {' '.join(map(str, self.event_members))})"
        )

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return False

        return self.event_id == other.event_id

    @property
    def is_past(self) -> bool:
        """Is True if the event is in the past"""
        return self.event_dt < dt.datetime.now(tz=get_local_timezone())


class EventList(list[Event]):
    """Class to orgaize events in lists"""

    @property
    def max_event_id(self) -> int:
        """Returns the highest event id in the event list"""
        if not self:
            return 0

        return max(event.event_id for event in self)


@dataclass
class EventManager:
    """Class to manage event lists"""

    upcoming_events: EventList = field(default_factory=EventList)
    past_events: EventList = field(default_factory=EventList)

    @property
    def max_event_id(self) -> int:
        """Returns the highest event id in the event lists of past and upcoming events"""

        return max(self.upcoming_events.max_event_id, self.past_events.max_event_id)

    def add_event(self, event: Event) -> Event:
        event.event_id = self.max_event_id + 1

        if event.is_past:
            self.past_events.append(event)
        else:
            self.upcoming_events.append(event)

        return event
