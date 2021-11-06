# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Classes that are part of the API public interface.
"""

from __future__ import annotations  # so we can return a type from one of its own methods

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class Health(BaseModel):
    """
    API health data.
    """

    class Config:
        allow_mutation = False

    status: str = Field("OK")


class Version(BaseModel):
    """
    API version data.

    We include both the package version and the API version, because
    they will vary independently.  We might release multiple versions
    of the Python package without changing the public interface of the
    API.
    """

    class Config:
        allow_mutation = False

    package: str = Field(...)
    api: str = Field(...)


class PlanLocation(BaseModel):

    """
    Identifies a location associated with plan implementation.
    """

    class Config:
        allow_mutation = False

    id: str = Field(..., title="Opaque SmartThings identifier for the location")
    name: str = Field(..., title="Human-readable name of the location")
    time_zone: str = Field(..., title="Time zone id, like 'America/Chicago'")


class PlanRule(BaseModel):
    """
    Identifies a rule that is a part of a plan implementation.
    """

    class Config:
        allow_mutation = False

    id: str = Field(..., title="Opaque SmartThings identifier for the rule")
    name: str = Field(..., title="Human-readable name of the rule")


class PlanImplementation(BaseModel):
    """
    Describes a plan implementation in terms of a set of rules.
    """

    class Config:
        allow_mutation = False

    id: str = Field(..., title="Plan identifier")
    finalized_date: datetime = Field(..., title="Date the plan was finalized at SmartThings")
    location: PlanLocation = Field(..., title="Information about the location associated with the plan")
    rules: List[PlanRule] = Field(..., title="List of rules implementing the plan at SmartThings")


class VacationPlan(BaseModel):
    """
    A vacation lighting plan.

    A vacation lighting plan describes how to turn on and off various lighting
    devices in a specific pattern when you are away from home.  The plan can be
    varied by day of week (weekday, weekend, or particular day) and it also
    allows for random variation in the timing, so your lights do not turn on or
    off at exactly the same time every day.  It works for any device with the
    `switch` capability.
    """

    class Config:
        allow_mutation = False

    id: str = Field(..., title="Plan identifier")
    location_name: str = Field(..., title="Human-readable name of the location")
    last_modified: datetime = Field(..., title="Time the plan was last modified")


class RefreshRequest(BaseModel):
    """Vacation plan refresh request."""

    class Config:
        allow_mutation = False

    current: Optional[VacationPlan] = Field(default=None, title="Current vacation plan, possibly unset")
    new: VacationPlan = Field(..., title="New vacation plan")  # required
