# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The public API model.
"""
from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import re
from enum import Enum
from typing import List, Optional, Type, Union

import pytz
from pydantic import ConstrainedList, ConstrainedStr, Field  # pylint: disable=no-name-in-module
from pydantic_yaml import SemVer, VersionedYamlModel, YamlModel
from pytz import UnknownTimeZoneError

VPLAN_NAME_REGEX = re.compile(r"^[a-z0-9-]+$")
TRIGGER_DAY_REGEX = re.compile(
    r"^(all|every|weekday(s)?|weekend(s)?|(sun(day)?)|mon(day)?|tue(sday)?|wed(nesday)?|thu(rsday)?|fri(day)?|sat(urday)?)$"
)
TRIGGER_TIME_REGEX = re.compile(r"^(sunrise|sunset|midnight|noon|\d{2}:\d{2})$")
TRIGGER_VARIATION_REGEX = re.compile(r"^(disabled|none|([+]/-|[+]|-) (\d+) (hour(s)?|minute(s)?))$")
SIMPLE_TIME_REGEX = re.compile(r"^((\d{2}):(\d{2}))$")

ONLY_ACCOUNT = "default"
VPLAN_RULE_PREFIX = "vplan"


class SwitchState(str, Enum):
    """States that a switch can be in."""

    ON = "on"
    OFF = "off"


class VplanName(ConstrainedStr):
    """A name used as an identifier in the vplan infrastructure."""

    min_length = 1
    max_length = 50
    strip_whitespace = True
    regex = VPLAN_NAME_REGEX


class TriggerDay(ConstrainedStr):
    """Legal values for the trigger day list."""

    to_lower = True
    strip_whitespace = True
    regex = TRIGGER_DAY_REGEX


class TriggerDayList(ConstrainedList):
    """A list of trigger days."""

    min_items = 1
    item_type = Type[TriggerDay]


class TriggerTime(ConstrainedStr):
    """A trigger time, either a logical time or HH24:MM."""

    to_lower = True
    strip_whitespace = True
    regex = TRIGGER_TIME_REGEX


class TriggerVariation(ConstrainedStr):
    """A trigger variation, either disabled or a description of the variation."""

    to_lower = True
    strip_whitespace = True
    regex = TRIGGER_VARIATION_REGEX


class SimpleTime(ConstrainedStr):
    """A simple time in format HH24:MM."""

    to_lower = True
    strip_whitespace = True
    regex = SIMPLE_TIME_REGEX


class TimeZone(ConstrainedStr):
    """A time zone that is valid for pytz (and hence for apscheduler)."""

    strip_whitespace = True

    @classmethod
    def validate(cls, value: Union[str]) -> Union[str]:
        try:
            pytz.timezone(value)
        except UnknownTimeZoneError as e:
            raise ValueError("Invalid time zone") from e
        return value


class SmartThingsId(ConstrainedStr):
    """A SmartThings identifier (either a name or id), opaque to us."""

    min_length = 1


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
    location: SmartThingsId = Field(..., description="SmartThings location name where the plan will execute")
    refresh_time: SimpleTime = Field(..., description="The time of day that the daily refresh job runs")
    refresh_zone: TimeZone = Field("UTC", description="The time zone that the daily refresh job runs in (default=UTC)")
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

    def devices(self, group_name: Optional[str] = None) -> List[Device]:
        """Return a list of devices in a plan, optionally filtered by group name."""
        result = []
        for group in self.plan.groups:
            if group_name is None or group.name == group_name:
                for device in group.devices:
                    result.append(device)
        return result


class Account(YamlModel):
    """A SmartThings account containing a PAT token.."""

    pat_token: SmartThingsId = Field(..., description="SmartThings PAT token")
