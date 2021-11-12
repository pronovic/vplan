# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Database operations.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import logging
from typing import List, Optional

from sqlalchemy import Boolean, Column, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, registry, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta

from vplan.engine.config import config
from vplan.engine.interface import Account, PlanSchema, ServerException

ONLY_ACCOUNT = "default"

_REGISTRY = registry()
_ENGINE: Optional[Engine] = None


# Entities are private to this module because they're only used
# to serialize/deserialize back and forth from the database.
# Nothing else relies on them.  Having an explicit _BaseEntity
# makes MyPy happier.  The implementation was taken from the
# SQLAlchemy documentation.


class _BaseEntity(metaclass=DeclarativeMeta):
    __abstract__ = True
    registry = _REGISTRY
    metadata = _REGISTRY.metadata
    __init__ = _REGISTRY.constructor


class _AccountEntity(_BaseEntity):
    """A SmartThings account."""

    __tablename__ = "account"
    account_name = Column(String, primary_key=True)
    pat_token = Column(String)


class _PlanEntity(_BaseEntity):
    """A vacation lighting plan tied to an account."""

    __tablename__ = "plan"
    plan_name = Column(String, primary_key=True)
    enabled = Column(Boolean)
    definition = Column(String)  # serialized YAML


def engine() -> Engine:
    """Return a reference to the database engine."""
    if not _ENGINE:
        raise ServerException("Database engine is not available")
    return _ENGINE


# pylint: disable=global-statement
def setup_database() -> None:
    """Set up the database connection and create any necessary tables."""
    global _ENGINE
    logging.getLogger("sqlalchemy").setLevel(logging.DEBUG)
    _ENGINE = create_engine(config().database_url, future=True)
    _BaseEntity.metadata.create_all(_ENGINE)


def db_session() -> Session:
    """Return a new session for use as a context manager."""
    return sessionmaker(bind=engine()).begin()  # pylint: disable=no-member


def db_retrieve_all_tables() -> List[str]:
    """Return a list of tables in the application database."""
    return sorted(list(_BaseEntity.metadata.tables.keys()))


def db_retrieve_account() -> Account:
    """Retrieve account information stored in the plan engine."""
    with db_session() as session:
        entity = session.query(_AccountEntity).where(_AccountEntity.account_name == ONLY_ACCOUNT).one()
        return Account(pat_token=entity.pat_token)


def db_create_or_replace_account(account: Account) -> None:
    """Create or replace account information stored in the plan engine."""
    with db_session() as session:
        session.query(_AccountEntity).where(_AccountEntity.account_name == ONLY_ACCOUNT).delete()
        entity = _AccountEntity()
        entity.account_name = ONLY_ACCOUNT
        entity.pat_token = account.pat_token
        session.add(entity)


def db_delete_account() -> None:
    """Delete account information stored in the plan engine."""
    with db_session() as session:
        session.query(_AccountEntity).where(_AccountEntity.account_name == ONLY_ACCOUNT).delete()


def db_retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    with db_session() as session:
        return [entity.plan_name for entity in session.query(_PlanEntity).all()]


def db_retrieve_plan(plan_name: str) -> PlanSchema:
    """Return the plan definition stored in the plan engine."""
    with db_session() as session:
        entity = session.query(_PlanEntity).where(_PlanEntity.plan_name == plan_name).one()
        return PlanSchema.parse_raw(entity.definition)


def db_create_plan(schema: PlanSchema) -> None:
    """Create a plan in the plan engine."""
    with db_session() as session:
        entity = _PlanEntity()
        entity.plan_name = schema.plan.name
        entity.enabled = False
        entity.definition = schema.yaml()
        session.add(entity)


def db_update_plan(schema: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""
    with db_session() as session:
        entity = session.query(_PlanEntity).where(_PlanEntity.plan_name == schema.plan.name).one()
        entity.definition = schema.yaml()


def db_delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""
    with db_session() as session:
        entity = session.query(_PlanEntity).where(_PlanEntity.plan_name == plan_name).one()
        session.delete(entity)


def db_retrieve_plan_enabled(plan_name: str) -> bool:
    """Return the enabled/disabled status of a plan in the plan engine."""
    with db_session() as session:
        entity = session.query(_PlanEntity).where(_PlanEntity.plan_name == plan_name).one()
        return entity.enabled  # type: ignore[no-any-return]


def db_update_plan_enabled(plan_name: str, enabled: bool) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""
    with db_session() as session:
        entity = session.query(_PlanEntity).where(_PlanEntity.plan_name == plan_name).one()
        entity.enabled = enabled
