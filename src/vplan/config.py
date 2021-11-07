# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Configuration for the vacation plan manager, shared across all components.
"""

import datetime
import os
from pathlib import Path
from typing import List, Union

from pydantic import Field, NonNegativeInt, SecretStr  # pylint: disable=no-name-in-module
from pydantic_yaml import SemVer, VersionedYamlModel, YamlEnum, YamlModel

CONFIG_DIR = os.path.join(str(Path.home()), ".config")
VPLAN_DIR = os.path.join(CONFIG_DIR, "vplan")
STATE_DIR = os.path.join(VPLAN_DIR, "state")
RUN_DIR = os.path.join(VPLAN_DIR, "run")
SYSTEMD_DIR = os.path.join(CONFIG_DIR, "systemd", "user")


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
    triggers: List[Trigger] = Field(title="List of lighting action triggers", default_factory=lambda: [])


class VacationConfig(VersionedYamlModel):
    """Vacation configuration."""

    class Config:
        min_version = "1.0.0"
        max_version = "1.0.0"

    version: SemVer = Field(..., title="Vacation configuration version")
    credential_id: SecretStr = Field(..., title="Identifier of the credential to use")
    plan: VacationPlan = Field(..., title="Vacation plan")


class SmartThingsCredential(YamlModel):
    """A SmartThings PAT token credential."""

    id: str = Field("Credential identifier")
    token: SecretStr = Field("SmartThings PAT token")


class CredentialsConfig(VersionedYamlModel):
    """Credentials configuration."""

    class Config:
        min_version = "1.0.0"
        max_version = "1.0.0"

    version: SemVer = Field(..., title="Credential configuration version")
    credentials: List[SmartThingsCredential] = Field(..., title="Available credentials")

    def pat_token(self, credential_id: str) -> str:
        """Return the PAT token associated with a credential id"""
        for credential in self.credentials:
            if credential.id == credential_id:
                return credential.token.get_secret_value()
        raise ValueError("Unknown credential id")


class PlanState(VersionedYamlModel):
    """State maintained for a plan."""

    class Config:
        min_version = "1.0.0"
        max_version = "1.0.0"

    version: SemVer = Field(..., title="Credential configuration version")
    enabled: bool = Field(..., title="Whether the plan is enabled")
    last_state_change: datetime.datetime = Field(..., title="The date the enabled/disabled state was last modified")
    last_plan_change: datetime.datetime = Field(..., title="The date the plan contents were last modified")
