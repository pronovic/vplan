# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The public API model.
"""
from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import re
from typing import List, Pattern

from pydantic import ConstrainedStr, Field, validator  # pylint: disable=no-name-in-module
from pydantic_yaml import YamlModel

DAY_PATTERN = re.compile(
    r"all|every|weekday(s)?|weekend(s)?|(sun(day)?)|mon(day)?|tue(sday)?|wed(nesday)?|thu(rsday)?|fri(day)?|sat(urday)?"
)
TIME_PATTERN = re.compile(r"sunrise|sunset|midnight|noon|\d{1,2}:\d{2}")
VARIATION_PATTERN = re.compile(r"([+]/-|[+]|-) (\d+) (hours|minutes|seconds)")


class NameString(ConstrainedStr):
    min_length = 1
    max_length = 50
    strip_whitespace = True


class NonEmptyString(ConstrainedStr):
    min_length = 1
    strip_whitespace = True


def _validate_pattern(field: str, pattern: Pattern[str], value: str) -> str:
    """Validate that a value matches a pattern."""
    value = value.strip().lower() if value else ""
    if not value or not pattern.fullmatch(value):
        raise ValueError("Invalid %s: %s" % (field, value))
    return value


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

    days: List[str] = Field(..., description="Days of the week that the trigger executes")
    on_time: str = Field(..., description="Time that devices turn on, in the location's time zone")
    off_time: str = Field(..., description="Time that devices turn off, in the location's time zone")
    variation: str = Field(..., description="Variation rules applied to the trigger on/off times")

    @classmethod
    @validator("days")
    def _validate_days(cls, days: List[str]) -> List[str]:
        return [_validate_pattern("day", DAY_PATTERN, day) for day in days]

    @classmethod
    @validator("on_time")
    def _validate_on_time(cls, on_time: str) -> str:
        return _validate_pattern("on_time", TIME_PATTERN, on_time)

    @classmethod
    @validator("off_time")
    def _validate_off_time(cls, off_time: str) -> str:
        return _validate_pattern("off_time", TIME_PATTERN, off_time)

    @classmethod
    @validator("variation")
    def _validate_variation(cls, variation: str) -> str:
        return _validate_pattern("variation", VARIATION_PATTERN, variation)


class Device(YamlModel):
    """A device, tied to a device group."""

    name: NonEmptyString = Field(..., description="SmartThings device name")
    room: NonEmptyString = Field(..., description="SmartThings room name, where the device lives")


class DeviceGroup(YamlModel):
    """A device group, tied to a vacation lighting plan."""

    name: NameString = Field(..., description="Device group name")
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

    name: NameString = Field(..., description="Vacation plan name")
    location: NonEmptyString = Field(..., description="SmartThings location name, where the plan will execute")
    groups: List[DeviceGroup] = Field(description="List of device groups managed by the plan", default_factory=lambda: [])


class Account(YamlModel):
    """A SmartThings account."""

    name: NameString = Field(..., description="Vacation plan name")
    pat_token: NonEmptyString = Field(..., description="SmartThings Personal Access Token (PAT)")
