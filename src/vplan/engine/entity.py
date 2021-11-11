# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The database entity model.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import registry
from sqlalchemy.orm.decl_api import DeclarativeMeta

_REGISTRY = registry()

ONLY_ACCOUNT = "default"

# This makes MyPy happier; taken from the SQLAlchemy documentation
class BaseEntity(metaclass=DeclarativeMeta):
    __abstract__ = True
    registry = _REGISTRY
    metadata = _REGISTRY.metadata
    __init__ = _REGISTRY.constructor


class AccountEntity(BaseEntity):
    """A SmartThings account."""

    __tablename__ = "account"
    account_name = Column(String, primary_key=True)
    pat_token = Column(String)


class PlanEntity(BaseEntity):
    """A vacation lighting plan tied to an account."""

    __tablename__ = "plan"
    plan_name = Column(String, primary_key=True)
    enabled = Column(Boolean)
    definition = Column(String)  # serialized YAML
