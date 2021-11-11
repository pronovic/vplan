# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The public API model.
"""
from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import re
from typing import List, Type

from pydantic import ConstrainedList, ConstrainedStr, Field  # pylint: disable=no-name-in-module
from pydantic_yaml import SemVer, VersionedYamlModel, YamlModel


class VplanName(ConstrainedStr):
    """A name used as an identifier in the vplan infrastructure."""

    min_length = 1
    max_length = 50
    strip_whitespace = True
    regex = re.compile(r"^[a-z0-9-]+$")


class TriggerDay(ConstrainedStr):
    """Legal values for the trigger day list."""

    to_lower = True
    strip_whitespace = True
    regex = re.compile(
        r"^(all|every|weekday(s)?|weekend(s)?|(sun(day)?)|mon(day)?|tue(sday)?|wed(nesday)?|thu(rsday)?|fri(day)?|sat(urday)?)$"
    )


class TriggerDayList(ConstrainedList):
    """A list of trigger days."""

    min_items = 1
    item_type = Type[TriggerDay]


class TriggerTime(ConstrainedStr):
    """A trigger time, either a logical time or HH24:MM."""

    to_lower = True
    strip_whitespace = True
    regex = re.compile(r"^(sunrise|sunset|midnight|noon|\d{2}:\d{2})$")


class TriggerVariation(ConstrainedStr):
    """A trigger variation, either disabled or a description of the variation."""

    to_lower = True
    strip_whitespace = True
    regex = re.compile(r"^(disabled|none|([+]/-|[+]|-) (\d+) (hour(s)?|minute(s)?|second(s)?))$")


class SimpleTime(ConstrainedStr):
    """A simple time in format HH24:MM."""

    to_lower = True
    strip_whitespace = True
    regex = re.compile(r"^(\d{2}:\d{2})$")


class SmartThingsId(ConstrainedStr):
    """A SmartThings identifier (either a name or id), opaque to us."""

    min_length = 1


class ServerException(Exception):
    """A server exception."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AlreadyExistsError(ServerException):
    """A resource already exists."""


class Health(YamlModel):
    """API health data"""

    status: str = Field("OK", description="Health status")


class Version(YamlModel):
    """API version data"""

    package: str = Field(..., description="Python package version")
    api: str = Field(..., description="API interface version")


class Status(YamlModel):
    """The status of a plan or an account."""

    enabled: bool = Field(..., description="Whether the plan or account is enabled.")


class Trigger(YamlModel):
    """A trigger, tied to a device group"""

    days: List[TriggerDay] = Field(..., description="Days of the week that the trigger executes")
    on_time: TriggerTime = Field(..., description="Time that devices turn on, in the location's time zone")
    off_time: TriggerTime = Field(..., description="Time that devices turn off, in the location's time zone")
    variation: TriggerVariation = Field(..., description="Variation rules applied to the trigger on/off times")


class Device(YamlModel):
    """A device, tied to a device group."""

    room: SmartThingsId = Field(..., description="SmartThings room name where the device lives")
    device: SmartThingsId = Field(..., description="SmartThings device name")


class DeviceGroup(YamlModel):
    """A device group, tied to a vacation lighting plan."""

    name: VplanName = Field(..., description="Device group name")
    devices: List[Device] = Field(..., description="List of devices in the group")
    triggers: List[Trigger] = Field(..., description="List of triggers for the group")


class Plan(YamlModel):
    """Vacation lighting plan."""

    name: VplanName = Field(..., description="Vacation plan name")
    location: SmartThingsId = Field(..., description="SmartThings location name, where the plan will execute")
    refresh_time: SimpleTime = Field(..., description="The time of day that the daily refresh job runs")
    groups: List[DeviceGroup] = Field(description="List of device groups managed by the plan", default_factory=lambda: [])


class PlanSchema(VersionedYamlModel):

    """
    Versioned schema for a vacation lighting plan.

    A vacation lighting plan describes how to turn on and off various lighting
    devices in a specific pattern when you are away from home.  The plan can be
    varied by day of week (weekday, weekend, or particular day) and it also
    allows for random variation in the timing, so your lights do not turn on or
    off at exactly the same time every day.  It works for any device with the
    `switch` capability.
    """

    class Config:
        min_version = "1.0.0"
        max_version = "1.0.0"

    version: SemVer = Field(..., description="Plan schema version")
    plan: Plan = Field(..., description="Vacation plan")


class Account(YamlModel):
    """A SmartThings account."""

    name: VplanName = Field(..., description="Account name")
    pat_token: SmartThingsId = Field(..., description="SmartThings Personal Access Token (PAT)")
