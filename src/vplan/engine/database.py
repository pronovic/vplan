# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Database operations.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from vplan.engine.config import config
from vplan.engine.interface import ServerException
from vplan.engine.model import Base

_ENGINE: Optional[Engine] = None


def engine() -> Engine:
    """Return a reference to the database engine."""
    if not _ENGINE:
        raise ServerException("Database engine is not available")
    return _ENGINE


def setup_database() -> None:
    """Set up the database connection and create any necessary tables."""
    global _ENGINE  # pylint: disable=global-statement
    logging.getLogger("sqlalchemy").setLevel(logging.DEBUG)
    _ENGINE = create_engine(config().database_url, future=True)
    Base.metadata.create_all(_ENGINE)
