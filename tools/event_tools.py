'''This module contains the classes and functions for handling events in the reminder part
of the discord bot'''

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    '''Enum of the supported event types'''
    GAME = "Game"
    STREAM = "Stream"


@dataclass
class Event:
    '''Datalass to represent events like streams and games'''

    event_title: str
    event_type: EventType
    event_dt: dt.datetime
    event_id: int = field(default=0, init=False)
    event_game: str = field(default='')
    event_members: list[int] = field(default_factory=list[int], init=False)

    def __repr__(self) -> str:
        return str(self.__dict__)

    @property
    def is_past(self) -> bool:
        '''Is True if the event is in the past'''
        return self.event_dt < dt.datetime.now()


class EventList(list[Event]):
    '''Class to orgaize events in lists'''

    @property
    def max_event_id(self) -> int:
        '''Returns the highest event id in the event list'''
        if not self:
            return 0

        return max(event.event_id for event in self)


@dataclass
class EventManager:
    '''Class to manage event lists'''
    upcoming_events: EventList = field(default_factory=EventList)
    past_events: EventList = field(default_factory=EventList)

    @property
    def max_event_id(self) -> int:
        '''Returns the highest event id in the event lists of past and upcoming events'''

        return max(self.upcoming_events.max_event_id, self.past_events.max_event_id)

    def add_event(self, event: Event) -> None:
        '''Adds an event to the corresponding list'''

        event.event_id = self.max_event_id + 1

        if event.is_past:
            self.past_events.append(event)
        else:
            self.upcoming_events.append(event)


event_manager = EventManager()

event_manager.add_event(
    Event(
        'Spaß mit Schnenk',
        EventType.STREAM,
        dt.datetime.fromordinal(1),
    )
)

event_manager.add_event(
    Event(
        'Spaß mit Hans',
        EventType.STREAM,
        dt.datetime.fromordinal(1),
    )
)

event_manager.add_event(
    Event(
        'Spaß mit OW',
        EventType.GAME,
        dt.datetime.fromisocalendar(2023, 20, 3)
    )
)
