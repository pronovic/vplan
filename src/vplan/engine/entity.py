# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The database entity model.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

from sqlalchemy import Boolean, Column, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import RelationshipProperty, registry, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta

_REGISTRY = registry()


# This makes MyPy happier; taken from the SQLAlchemy documentation
class Base(metaclass=DeclarativeMeta):
    __abstract__ = True
    registry = _REGISTRY
    metadata = _REGISTRY.metadata
    __init__ = _REGISTRY.constructor


class Account(Base):
    """A SmartThings account."""

    __tablename__ = "account"
    account_id = Column(Integer, Identity(), primary_key=True)
    name = Column(String)
    pat_token = Column(String)
    enabled = Column(Boolean)
    plans: RelationshipProperty[Plan] = relationship("Plan", backref="account")


class Plan(Base):
    """A vacation lighting plan, tied to an account."""

    __tablename__ = "plan"
    plan_id = Column(Integer, Identity(), primary_key=True)
    account_id = Column(Integer, ForeignKey("account.account_id"))
    name = Column(String)
    location = Column(String)
    version = Column(Integer)
    groups: RelationshipProperty[DeviceGroup] = relationship("DeviceGroup", backref="plan")


class DeviceGroup(Base):
    """A device group, tied to a vacation lighting plan."""

    __tablename__ = "device_group"
    group_id = Column(Integer, Identity(), primary_key=True)
    plan_id = Column(Integer, ForeignKey("plan.plan_id"))
    name = Column(String)
    devices: RelationshipProperty[Device] = relationship("Device", backref="group")
    triggers: RelationshipProperty[Trigger] = relationship("Trigger", backref="group")


class Device(Base):
    """A device, tied to a device group."""

    __tablename__ = "device"
    device_id = Column(Integer, Identity(), primary_key=True)
    group_id = Column(Integer, ForeignKey("device_group.group_id"))
    name = Column(String)
    room = Column(String)


class Trigger(Base):
    """A trigger, tied to a device group"""

    __tablename__ = "switch_trigger"
    trigger_id = Column(Integer, Identity(), primary_key=True)
    group_id = Column(Integer, ForeignKey("device_group.group_id"))
    days = Column(String)
    on_time = Column(String)
    off_time = Column(String)
    variation = Column(String)
