from dataclasses import dataclass, field
from enum import Enum
import datetime as dt


class EventType(Enum):
    GAME = "Game"
    STREAM = "Stream"


class Event:
    '''Class to represent events like streams and games'''

    def __init__(
        self,
        event_title: str,
        event_type: EventType,
        event_dt: dt.datetime,
        /,
        event_game: str = '',

    ) -> None:
        self._event_id = 0
        self._event_title = event_title
        self._event_type = event_type
        self._event_dt = event_dt
        self._event_game = event_game
        self._event_members: list[int] = []

    def __repr__(self) -> str:
        return str(self.__dict__)

    @property
    def event_id(self) -> int:
        return self._event_id

    @property
    def is_past(self) -> bool:
        return self._event_dt < dt.datetime.now()

    @event_id.setter
    def event_id(self, id) -> None:
        self._event_id = id


class EventList(list[Event]):
    '''Class to orgaize events in lists'''

    @property
    def max_event_id(self) -> int:
        if not len(self):
            return 0

        return max(event.event_id for event in self)


@dataclass
class EventManager:
    '''Class to manage event lists'''
    upcoming_events: EventList = field(default_factory=EventList)
    past_events: EventList = field(default_factory=EventList)

    @property
    def highest_id(self) -> int:
        return max(self.upcoming_events.max_event_id, self.past_events.max_event_id)

    def add_event(self, event: Event) -> None:
        event.event_id = self.highest_id + 1

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

print(event_manager)
print(event_manager.highest_id)
