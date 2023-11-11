"""This module contains the classes and functions for handling events in the reminder part
of the discord bot"""

from __future__ import annotations

import datetime as dt
import logging
from enum import Enum, auto
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tools.db_tools import Base

DEFAULT_TIME_FMT = "%d.%m um %H:%M Uhr"


class EventType(Enum):
    """Enum of the supported event types"""

    GAME = auto()
    STREAM = auto()


class Event(Base):
    """This class is used for events like streams or coop sessions"""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[EventType]
    title: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    time: Mapped[dt.datetime]
    creator: Mapped[int]
    announced: Mapped[bool] = mapped_column(default=False)
    started: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return (
            f"Event(id={self.id!r}, type={self.type!r}, title={self.title!r}, "
            f"description={self.description!r}, time={self.time!r}, creator={self.creator!r}, "
            f"announced={self.announced!r}, started={self.started!r})"
        )

    def __str__(self) -> str:
        return f"#{self.id:04}-{self.type}: {self.time} {self.title}"

    @property
    def fmt_field(self) -> dict:
        return {
            "name": f"**ID: {self.id:04}**",
            "value": f"[{self.type}] {self.fmt_dt}\n{self.title}\n{self.description}",
            "inline": False,
        }

    @property
    def fmt_dt(self) -> str:
        return self.time.strftime(DEFAULT_TIME_FMT)

    @staticmethod
    async def get_upcoming_events(session: Session) -> Sequence[Event]:
        events = session.execute(select(Event)).scalars.all()
        logging.info("Updated list of upcoming events. Amount: %s", events.count)
        return events

    @staticmethod
    async def get_events_to_announce(session: Session) -> Sequence[Event]:
        events = session.execute(select(Event)).scalars.all()
        logging.info("Updated list of events to announce. Amount: %s", events.count)
        return events

    @staticmethod
    async def get_week_events_to_announce(session: Session) -> Sequence[Event]:
        events = session.execute(select(Event)).scalars.all()
        logging.info("Updated list of events to announce. Amount: %s", events.count)
        return events
