# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Classes that are part of the API public interface.
"""

from __future__ import annotations  # so we can return a type from one of its own methods

import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field, NonNegativeInt  # pylint: disable=no-name-in-module
from pydantic_yaml import YamlEnum, YamlModel


class Health(BaseModel):
    """API health data"""

    status: str = Field("OK")


class Version(BaseModel):
    """API version data"""

    package: str = Field(...)
    api: str = Field(...)


class TriggerDay(str, YamlEnum):
    """The days that a trigger can execute."""

    ALL = "all"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"
    SUNDAY = "sun"
    MONDAY = "mon"
    TUESDAY = "tue"
    WEDNESDAY = "wed"
    THURSDAY = "thu"
    FRIDAY = "fri"
    SATURDAY = "sat"


class TriggerTime(str, YamlEnum):
    """Special times at which a trigger can execute."""

    SUNRISE = "sunrise"
    SUNSET = "sunset"
    MIDNIGHT = "midnight"
    NOON = "noon"


class TriggerAction(str, YamlEnum):
    """Actions that a trigger can execute."""

    SWITCH_ON = "switch_on"
    SWITCH_OFF = "switch_off"


class TriggerDevice(YamlModel):
    """A device operated on by a trigger; must support the 'switch' capability."""

    room: str = Field(..., title="Room that the device exists within", min_length=1)
    device: str = Field(..., title="Name of the device", min_length=1)


class VariationUnit(str, YamlEnum):
    """Units of time for a trigger variation period."""

    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"


class VariationDirection(str, YamlEnum):
    """Direction of the variation, before and/or after the trigger time."""

    BEFORE = "before"
    AFTER = "after"
    BOTH = "both"


class TriggerVariation(YamlModel):
    """A variation for a trigger, a period of time before and/or after the trigger time."""

    period: NonNegativeInt = Field(..., title="The variation period")
    unit: VariationUnit = Field(title="The variation unit", default=VariationUnit.MINUTES)
    direction: VariationDirection = Field(title="The variation direction", default=VariationDirection.BOTH)


class Trigger(YamlModel):
    """A trigger for a plan action"""

    id: str = Field(..., title="Identifier for this trigger", min_length=1)
    days: List[TriggerDay] = Field(..., title="Days of the week that the trigger executes")
    time: Union[TriggerTime, datetime.time] = Field(..., title="Time that a trigger executes, in the location's time zone")
    variation: TriggerVariation = Field(title="Trigger in minutes", default=TriggerVariation(period=0))
    action: TriggerAction = Field(..., title="The action that the trigger executes")
    devices: List[TriggerDevice] = Field(..., title="Devices that the trigger operates on")


class VacationPlan(YamlModel):
    """
    A vacation lighting plan.

    A vacation lighting plan describes how to turn on and off various lighting
    devices in a specific pattern when you are away from home.  The plan can be
    varied by day of week (weekday, weekend, or particular day) and it also
    allows for random variation in the timing, so your lights do not turn on or
    off at exactly the same time every day.  It works for any device with the
    `switch` capability.
    """

    id: str = Field(..., title="Plan identifier", min_length=1)
    location: str = Field(..., title="Name of the location", min_length=1)
    enabled: bool = Field(..., title="Whether the plan is enabled")
    triggers: List[Trigger] = Field(title="List of lighting action triggers", default_factory=lambda: [])


class TriggerRule(BaseModel):
    """Identifies a rule that implements a trigger."""

    trigger_id: str = Field(..., title="Id of the trigger this rule is associated with")
    rule_id: str = Field(..., title="Identifier for the rule at SmartThings")
    rule_name: str = Field(..., title="Name of the rule at SmartThings")


class RefreshRequest(BaseModel):
    """Vacation plan refresh request."""

    current: Optional[VacationPlan] = Field(default=None, title="Current vacation plan, possibly unset")
    new: VacationPlan = Field(..., title="New vacation plan")


class RefreshResult(BaseModel):
    """The result from a plan request refresh request."""

    id: str = Field(..., title="Plan identifier")
    location: str = Field(..., title="Name of the location")
    time_zone: str = Field(..., title="Time zone that the plan will execute in")
    finalized_date: datetime.datetime = Field(..., title="Date the plan was finalized in the SmartThings infrastructure")
    rules: List[TriggerRule] = Field(..., title="List of the SmartThings rules that implement the plan triggers")


class TriggerResult(BaseModel):
    """The result from a trigger test request."""

    id: str = Field(..., title="Plan identifier")
    location: str = Field(..., title="Name of the location")
    time_zone: str = Field(..., title="Time zone that the trigger was executed in")
    rule: TriggerRule = Field(..., title="The trigger rule that was tested")
