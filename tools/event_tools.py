"""This module contains the classes and functions for handling events in the reminder part
of the discord bot"""

from __future__ import annotations

import datetime as dt
from enum import Enum, auto
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

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
    def fmt_dt(self) -> str:
        return self.time.strftime(DEFAULT_TIME_FMT)
