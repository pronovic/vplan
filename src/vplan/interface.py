# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The interface shared between the client and the engine.
"""
from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import re
from enum import Enum
from typing import Annotated, List, Optional

import pytz
import semver
from pydantic import AfterValidator, BaseModel, Field, StringConstraints, field_validator
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


def _validate_time_zone(value: str) -> str:
    """Validate a pytz timezone name."""
    try:
        pytz.timezone(value.strip())
    except UnknownTimeZoneError as e:
        raise ValueError("Invalid time zone") from e
    return value


def _validate_semver(value: str) -> str:
    """Validate a semantic version."""
    semver.Version.parse(value)  # throws ValueError if version is invalid
    return value


class SwitchState(str, Enum):
    """States that a switch can be in."""

    ON = "on"
    OFF = "off"


VplanName = Annotated[
    str,
    AfterValidator(lambda s: s.strip()),
    StringConstraints(min_length=1, max_length=50, pattern=VPLAN_NAME_REGEX),
    "A name used as an identifier in the vplan infrastructure.",
]

TriggerDay = Annotated[
    str,
    AfterValidator(lambda s: s.lower().strip()),
    StringConstraints(pattern=TRIGGER_DAY_REGEX),
    "Legal values for the trigger day list.",
]

TriggerTime = Annotated[
    str,
    AfterValidator(lambda s: s.lower().strip()),
    StringConstraints(pattern=TRIGGER_TIME_REGEX),
    "A trigger time, either a logical time or HH24:MM.",
]

TriggerVariation = Annotated[
    str,
    AfterValidator(lambda s: s.lower().strip()),
    StringConstraints(pattern=TRIGGER_VARIATION_REGEX),
    "A trigger variation, either disabled or a description of the variation.",
]

SimpleTime = Annotated[
    str,
    AfterValidator(lambda s: s.lower().strip()),
    StringConstraints(pattern=SIMPLE_TIME_REGEX),
    "A simple time in format HH24:MM.",
]

TimeZone = Annotated[
    str,
    AfterValidator(_validate_time_zone),
    "A time zone that is valid for pytz (and hence for apscheduler).",
]


SmartThingsId = Annotated[
    str,
    StringConstraints(min_length=1),
    "A SmartThings identifier (either a name or id), opaque to us.",
]

SemVer = Annotated[
    str,
    AfterValidator(_validate_semver),
    "Semantic version string.",
]


class Health(BaseModel):
    """API health data"""

    status: str = Field(default="OK", description="Health status")


class Version(BaseModel):
    """API version data"""

    package: str = Field(..., description="Python package version")
    api: str = Field(..., description="API interface version")


class Status(BaseModel):
    """The status of a plan or an account."""

    enabled: bool = Field(..., description="Whether the plan or account is enabled.")


class Trigger(BaseModel):
    """A trigger, tied to a device group"""

    days: List[TriggerDay] = Field(..., description="Days of the week that the trigger executes")
    on_time: TriggerTime = Field(..., description="Time that devices turn on, in the location's time zone")
    off_time: TriggerTime = Field(..., description="Time that devices turn off, in the location's time zone")
    variation: TriggerVariation = Field(..., description="Variation rules applied to the trigger on/off times")


class Device(BaseModel):
    """A device, tied to a device group."""

    room: SmartThingsId = Field(..., description="SmartThings room name where the device lives")
    device: SmartThingsId = Field(..., description="SmartThings device name")
    component: SmartThingsId = Field(default="main", description="The component to trigger the command for (default=main)")


class DeviceGroup(BaseModel):
    """A device group, tied to a vacation lighting plan."""

    name: VplanName = Field(..., description="Device group name")
    devices: List[Device] = Field(..., description="List of devices in the group")
    triggers: List[Trigger] = Field(..., description="List of triggers for the group")


class Plan(BaseModel):
    """Vacation lighting plan."""

    name: VplanName = Field(..., description="Vacation plan name")
    location: SmartThingsId = Field(..., description="SmartThings location name where the plan will execute")
    refresh_time: SimpleTime = Field(..., description="The time of day that the daily refresh job runs")
    refresh_zone: TimeZone = Field("UTC", description="The time zone that the daily refresh job runs in (default=UTC)")
    groups: List[DeviceGroup] = Field(description="List of device groups managed by the plan", default_factory=lambda: [])


# noinspection PyNestedDecorators
class PlanSchema(BaseModel):
    """
    Versioned schema for a vacation lighting plan.

    A vacation lighting plan describes how to turn on and off various lighting
    devices in a specific pattern when you are away from home.  The plan can be
    varied by day of week (weekday, weekend, or particular day) and it also
    allows for random variation in the timing, so your lights do not turn on or
    off at exactly the same time every day.  It works for any device with the
    `switch` capability.
    """

    version: SemVer = Field(..., description="Plan schema version")
    plan: Plan = Field(..., description="Vacation plan")

    @field_validator("version")
    @classmethod
    def _validate_version(cls, version: SemVer) -> str:
        min_version = "1.0.0"
        max_version = "1.1.0"
        if semver.compare(version, min_version) < 0 or semver.compare(version, max_version) > 0:
            raise ValueError("Invalid plan schema version")
        return version

    def devices(self, group_name: Optional[str] = None) -> List[Device]:
        """Return a list of devices in a plan, optionally filtered by group name."""
        result = []
        for group in self.plan.groups:
            if group_name is None or group.name == group_name:
                for device in group.devices:
                    result.append(device)
        return result


class Account(BaseModel):
    """A SmartThings account containing a PAT token.."""

    pat_token: SmartThingsId = Field(..., description="SmartThings PAT token")
