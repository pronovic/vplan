# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The database entity model.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import RelationshipProperty, registry, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy_json import NestedMutableJson

_REGISTRY = registry()

DEFAULT_ACCOUNT = "default"

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
    enabled = Column(Boolean)
    plans: RelationshipProperty[PlanEntity] = relationship("PlanEntity", cascade="all,delete", backref="account")


class PlanEntity(BaseEntity):
    """A vacation lighting plan tied to an account."""

    # See the following for a discussion of JSON with SQLAlchemy:
    #
    #    https://amercader.net/blog/beware-of-json-fields-in-sqlalchemy/
    #    https://github.com/edelooff/sqlalchemy-json
    #
    # There are some subtle gotchas that sqlalchemy-json attempts to resolve.

    __tablename__ = "plan"
    plan_name = Column(String, primary_key=True)
    account_name = Column(Integer, ForeignKey("account.account_name"))
    enabled = Column(Boolean)
    definition = Column(NestedMutableJson)
