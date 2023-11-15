import logging

import sqlalchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """This is the base class for classes that are represented as tables in the DB."""


async def create_all(engine: sqlalchemy.Engine) -> None:
    """This function creates all required tables in the DB."""

    Base.metadata.create_all(engine)
    logging.debug("All tables in DB created.")


def create_engine(db_url: str = "sqlite:///storage.db", echo: bool = False) -> sqlalchemy.Engine:
    """This function creates and returns a DB engine."""

    engine = sqlalchemy.create_engine(db_url, echo=echo)
    logging.debug("DB engine created.")
    return engine
