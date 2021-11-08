# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Database operations.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import logging
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from vplan.engine.config import config
from vplan.engine.entity import BaseEntity
from vplan.engine.interface import ServerException

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
    BaseEntity.metadata.create_all(_ENGINE)


def get_tables() -> List[str]:
    """Return a list of tables in the application database."""
    return sorted(list(BaseEntity.metadata.tables.keys()))
