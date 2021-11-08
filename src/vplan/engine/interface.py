# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The public API model.
"""
from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import re
from typing import List, Type

from pydantic import ConstrainedList, ConstrainedStr, Field  # pylint: disable=no-name-in-module
from pydantic_yaml import YamlModel


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
        r"all|every|weekday(s)?|weekend(s)?|(sun(day)?)|mon(day)?|tue(sday)?|wed(nesday)?|thu(rsday)?|fri(day)?|sat(urday)?"
    )


class TriggerDayList(ConstrainedList):
    """A list of trigger days."""

    min_items = 1
    item_type = Type[TriggerDay]


class TriggerTime(ConstrainedStr):
    """A trigger time, either a logical time or HH24:MM."""

    to_lower = True
    strip_whitespace = True
    regex = re.compile(r"sunrise|sunset|midnight|noon|\d{2}:\d{2}")


class TriggerVariation(ConstrainedStr):
    """A trigger variation, either disabled or a description of the varation."""

    to_lower = True
    strip_whitespace = True
    regex = re.compile(r"disabled|none|([+]/-|[+]|-) (\d+) (hours|minutes|seconds)")


class SmartThingsId(ConstrainedStr):
    """A SmartThings identifier (either a name or id), opaque to us."""

    min_length = 1


class ServerException(Exception):
    """A server exception."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Health(YamlModel):
    """API health data"""

    status: str = Field("OK", description="Health status")


class Version(YamlModel):
    """API version data"""

    package: str = Field(..., description="Python package version")
    api: str = Field(..., description="API interface version")


class Trigger(YamlModel):
    """A trigger, tied to a device group"""

    days: List[TriggerDay] = Field(..., description="Days of the week that the trigger executes")
    on_time: TriggerTime = Field(..., description="Time that devices turn on, in the location's time zone")
    off_time: TriggerTime = Field(..., description="Time that devices turn off, in the location's time zone")
    variation: TriggerVariation = Field(..., description="Variation rules applied to the trigger on/off times")


class Device(YamlModel):
    """A device, tied to a device group."""

    name: SmartThingsId = Field(..., description="SmartThings device name")
    room: SmartThingsId = Field(..., description="SmartThings room name, where the device lives")


class DeviceGroup(YamlModel):
    """A device group, tied to a vacation lighting plan."""

    name: VplanName = Field(..., description="Device group name")
    devices: List[Device] = Field(..., description="List of devices in the group")
    triggers: List[Device] = Field(..., description="List of triggers for the group")


class Plan(YamlModel):
    """
    A vacation lighting plan.

    A vacation lighting plan describes how to turn on and off various lighting
    devices in a specific pattern when you are away from home.  The plan can be
    varied by day of week (weekday, weekend, or particular day) and it also
    allows for random variation in the timing, so your lights do not turn on or
    off at exactly the same time every day.  It works for any device with the
    `switch` capability.
    """

    name: VplanName = Field(..., description="Vacation plan name")
    location: SmartThingsId = Field(..., description="SmartThings location name, where the plan will execute")
    groups: List[DeviceGroup] = Field(description="List of device groups managed by the plan", default_factory=lambda: [])


class Account(YamlModel):
    """A SmartThings account."""

    name: VplanName = Field(..., description="Vacation plan name")
    pat_token: SmartThingsId = Field(..., description="SmartThings Personal Access Token (PAT)")
