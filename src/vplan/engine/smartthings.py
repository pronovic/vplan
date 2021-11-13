# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartThings API client.

Note that all of the public functions in this class are expected to be invoked from
within a SmartThings context, like:

    with SmartThings(pat_token="token", location="My House"):
        set_switch(room="Office", device="Desk Lamp")

The caller is responsible for setting up the context.  If you get a LookupError
from any function, then you've forgotten to set the context.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import json
import logging
from contextvars import ContextVar
from datetime import datetime
from random import randint
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from requests import Response
from requests.models import HTTPError

from vplan.engine.config import config
from vplan.engine.interface import (
    SIMPLE_TIME_REGEX,
    TRIGGER_DAY_REGEX,
    TRIGGER_TIME_REGEX,
    TRIGGER_VARIATION_REGEX,
    Device,
    DeviceGroup,
    PlanSchema,
    SimpleTime,
    SmartThingsClientError,
    SwitchState,
    Trigger,
    TriggerDay,
    TriggerTime,
    TriggerVariation,
)


class LocationContext:

    """
    Context that we maintain for a location to make other requests easier.

    We want the vacation plan to be defined in terms of human-readable names.
    However, the API is structured mostly in terms of ids (location id, room
    id, device id, etc.) and doesn't typically offer a way to look up or filter
    by name.  This means that we need to retrieve the entire list of locations,
    rooms, and devices and create our mappings before we do API calls that need
    to do lookups.  Rather than putting this burden on individual API calls,
    it's simpler to do all of the work up front and make everything available
    via a Python context manager.  At least it's only 3 API calls.

    Most of these APIs allow for pagination. Instead of dealing with that,
    I'm just using really big pages, so I can make a single request.  Most
    users don't have hundreds of locations, rooms, or devices, so I don't think
    this should be too big of a deal.
    """

    LOCATION_LIMIT = "100"
    ROOM_LIMIT = "250"
    DEVICE_LIMIT = "1000"
    RULES_LIMIT = "100"  # you can't create more than 100 as of this writing, anyway

    def __init__(self, pat_token: str, location: str):
        self.pat_token = pat_token
        self.location = location
        self.headers = self._derive_headers()
        self.location_id = self._derive_location_id(location)
        self.room_by_id, self.room_by_name = self._derive_rooms()
        self.device_by_id, self.device_by_name = self._derive_devices()
        self.rule_by_id = self._derive_rule_by_id()

    def _derive_headers(self) -> Dict[str, str]:
        """Fill standard headers for API requests."""
        return {
            "Accept": "application/vnd.smartthings+json;v=1",
            "Accept-Language": "en_US",
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % self.pat_token,
        }

    def _derive_location_id(self, location: str) -> str:
        """Derive the location id for a location name."""
        locations = {}
        url = _url("/locations")
        params = {"limit": LocationContext.LOCATION_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        for item in response.json()["items"]:
            locations[item["name"]] = item["locationId"]
        if not location in locations:
            raise SmartThingsClientError("Configured location not found: %s" % location)
        location_id: str = locations[location]
        logging.info("Location id: %s", location_id)
        return location_id

    def _derive_rooms(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Derive the mapping from room id->name and name->id for the location."""
        room_by_id = {}
        room_by_name = {}
        url = _url("/locations/%s/rooms" % self.location_id)
        params = {"limit": LocationContext.ROOM_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        for item in response.json()["items"]:
            room_by_id[item["roomId"]] = item["name"]
            room_by_name[item["name"]] = item["roomId"]
        logging.info("Location [%s] has %d rooms", self.location, len(room_by_id))
        logging.debug("Rooms by id: %s", json.dumps(room_by_id, indent=2))
        return room_by_id, room_by_name

    def _derive_devices(self) -> Tuple[Dict[str, Device], Dict[str, str]]:
        """Derive the mapping from device id->Device and name->id for the location."""
        device_by_id = {}
        device_by_name = {}
        url = _url("/devices")
        params = {"locationId": self.location_id, "capability": "switch", "limit": LocationContext.DEVICE_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        for item in response.json()["items"]:
            device_id = item["deviceId"]
            device_name = item["label"] if item["label"] else item["name"]  # users see the label, if there is one
            room_name = self.room_by_id[item["roomId"]]
            device = Device(room=room_name, device=device_name)
            device_by_id[device_id] = device
            device_by_name["%s/%s" % (room_name, device.device)] = device_id
        logging.info("Location [%s] has %d devices", self.location, len(device_by_id))
        logging.debug("Devices by name:\n%s", json.dumps(device_by_name, indent=2))
        return device_by_id, device_by_name

    def _derive_rule_by_id(self) -> Dict[str, Dict[str, Any]]:
        rule_by_id = {}
        url = _url("/rules")
        params = {"locationId": self.location_id, "limit": LocationContext.RULES_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        for item in response.json()["items"]:
            rule_id = item["id"]
            rule_by_id[rule_id] = item
        logging.info("Location [%s] has %d rules", self.location, len(rule_by_id))
        logging.debug("Rules by id:\n%s", json.dumps(rule_by_id, indent=2))
        return rule_by_id


# Context managed by the SmartThings context manager
CONTEXT: ContextVar[LocationContext] = ContextVar("CONTEXT")


class SmartThings:
    """Context manager for SmartThings API."""

    def __init__(self, pat_token: str, location: str):
        self.context = CONTEXT.set(LocationContext(pat_token=pat_token, location=location))

    def __enter__(self) -> None:
        return None

    def __exit__(self, _type, value, traceback) -> None:  # type: ignore[no-untyped-def]
        CONTEXT.reset(self.context)


def _base_api_url() -> str:
    """Return the correct API URL based on configuration."""
    return config().smartthings.base_api_url


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (_base_api_url(), endpoint)


def _device_id(device: Device) -> str:
    """Get the device id for a device."""
    return CONTEXT.get().device_by_name["%s/%s" % (device.room, device.device)]


def _headers() -> Dict[str, str]:
    """Get the headers to use for requests."""
    return CONTEXT.get().headers


def _raise_for_status(response: Response) -> None:
    """Check response status, raising ClickException for errors"""
    try:
        response.raise_for_status()
    except HTTPError as e:
        raise SmartThingsClientError("%s" % e) from e


def _build_specific(days: List[TriggerDay], trigger_time: TriggerTime, variation: TriggerVariation) -> Dict[str, Any]:
    """Build a specific time for a rule to execute."""
    variation_minutes = parse_variation(variation)
    reference, offset = parse_trigger_time(trigger_time, variation_minutes)
    days_of_week = parse_days(days)
    specific: Dict[str, Any] = {"reference": reference, "daysOfWeek": days_of_week}
    if offset:
        specific["offset"] = {"value": {"integer": offset}, "unit": "Minute"}
    return {"specific": specific}


def _build_actions(device_ids: List[str], state: SwitchState) -> List[Dict[str, Any]]:
    """Build a list of actions (commands) to execute with in a rule."""
    command = {"component": "main", "capability": "switch", "command": "on" if state == SwitchState.ON else "off"}
    return [{"command": {"devices": device_ids, "commands": [command]}}]


def _build_rule(
    name: str,
    device_ids: List[str],
    days: List[TriggerDay],
    trigger_time: TriggerTime,
    variation: TriggerVariation,
    state: SwitchState,
) -> Dict[str, Any]:
    """Build a rule for a trigger state change, either on or off."""
    specific = _build_specific(days, trigger_time, variation)
    actions = _build_actions(device_ids, state)
    return {"name": name, "actions": [{"every": {"specific": specific, "actions": actions}}]}


def _build_trigger(name: str, device_ids: List[str], trigger: Trigger) -> List[Dict[str, Any]]:
    """Build all rules for a trigger."""
    on = _build_rule("%s/on" % name, device_ids, trigger.days, trigger.on_time, trigger.variation, SwitchState.ON)
    off = _build_rule("%s/off" % name, device_ids, trigger.days, trigger.off_time, trigger.variation, SwitchState.OFF)
    return [on, off]


def _build_group(name: str, group: DeviceGroup) -> List[Dict[str, Any]]:
    """Build all rules for a device group."""
    rules = []
    device_ids = [_device_id(device) for device in group.devices]
    for index, trigger in enumerate(group.triggers):
        rules += _build_trigger("%s/%s/trigger[%d]" % (name, group.name, index), device_ids, trigger)
    return rules


def build_plan_rules(schema: PlanSchema) -> List[Dict[str, Any]]:
    """Build all rules for a plan."""
    rules = []
    for group in schema.plan.groups:
        rules += _build_group("vplan/%s" % schema.plan.name, group)
    return rules


def set_switch(device: Device, state: SwitchState) -> None:
    """Switch a device on or off."""
    command = "on" if state == SwitchState.ON else "off"
    request = {"commands": [{"component": "main", "capability": "switch", "command": command}]}
    url = _url("/devices/%s/commands" % _device_id(device))
    response = requests.post(url=url, headers=_headers(), json=request)
    _raise_for_status(response)


def check_switch(device: Device) -> SwitchState:
    """Check the state of a switch."""
    url = _url("/devices/%s/components/main/capabilities/switch/status" % _device_id(device))
    response = requests.get(url=url, headers=_headers())
    _raise_for_status(response)
    return SwitchState.ON if response.json()["switch"]["value"] == "on" else SwitchState.OFF


def parse_variation(variation: str) -> Optional[int]:
    """Parse a variation, returning random minutes (or None) to modify a trigger time."""
    match = TRIGGER_VARIATION_REGEX.match(variation) if variation else None
    if not match:
        raise ValueError("Invalid variation")
    if match.group(1) in ["disabled", "none"]:
        return None
    direction = match.group(2)
    duration = int(match.group(3))
    unit = match.group(4)
    if unit.startswith("hour"):
        duration *= 60  # convert all durations to minutes
    if direction == "+":
        return randint(0, duration)
    elif direction == "-":
        return randint(-duration, 0)
    else:
        return randint(-duration, duration)


def parse_time(time: Union[str, SimpleTime]) -> Tuple[int, int]:
    """Parse a time string in SimpleTime format and return (hour, minute)."""
    match = SIMPLE_TIME_REGEX.match(time) if time else None
    if not match:
        raise ValueError("Invalid time")
    hour, minute = int(match.group(2)), int(match.group(3))
    if (hour < 0 or hour > 23) or (minute < 0 or minute > 59):
        raise ValueError("Invalid SimpleTime: %s" % time)
    return hour, minute


def parse_trigger_time(trigger: Union[str, TriggerTime], variation: Optional[int]) -> Tuple[str, Optional[int]]:
    """Parse a trigger time and return (reference, offset)."""
    match = TRIGGER_TIME_REGEX.match(trigger) if trigger else None
    if not match:
        raise ValueError("Invalid trigger_time")
    if match.group(1) == "sunrise":
        return "Sunrise", variation if variation and variation != 0 else None
    elif match.group(1) == "sunset":
        return "Sunset", variation if variation and variation != 0 else None
    elif match.group(1) == "midnight":
        return "Midnight", variation if variation and variation > 0 else None  # can't use negative numbers
    elif match.group(1) == "noon":
        return "Noon", variation if variation and variation != 0 else None
    else:
        seconds = (datetime.strptime(match.group(1), "%H:%M") - datetime.strptime("00:00", "%H:%M")).total_seconds()
        minutes = round(seconds / 60) if seconds >= 0 else 0
        offset = minutes + (variation if variation else 0)
        return "Midnight", offset if offset and offset > 0 else None  # can't use negative numbers


def parse_day(day: Union[str, TriggerDay]) -> List[str]:
    """Parse a trigger day and return a normalized list of SmartThings days."""
    match = TRIGGER_DAY_REGEX.match(day) if day else None
    if not match:
        raise ValueError("Invalid day")
    if day.startswith("all") or day.startswith("every"):
        return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    elif day.startswith("weekday"):
        return ["Mon", "Tue", "Wed", "Thu", "Fri"]
    elif day.startswith("weekend"):
        return ["Sun", "Sat"]
    else:
        return [day[0:3].capitalize()]


def parse_days(days: Union[List[str], List[TriggerDay]]) -> List[str]:
    """Parse a list of trigger days and return a normalized list of SmartThings days."""
    sort = {"Sun": 0, "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6}
    result = set()
    if days is None:
        raise ValueError("Days is None")
    for day in days:
        for normalized in parse_day(day):
            result.add(normalized)
    return sorted(list(result), key=lambda day: sort[day])
