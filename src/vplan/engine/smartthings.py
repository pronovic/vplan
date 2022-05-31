# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
SmartThings API client.

Note that all of the public functions in this class that interact with an
API are expected to be invoked from within a SmartThings context, like:

    with SmartThings(pat_token="token", location="My House"):
        set_switch(room="Office", device="Desk Lamp")

If you get a LookupError from any function, then you've forgotten to
set the context.
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import json
import logging
from contextvars import ContextVar
from datetime import datetime
from random import randint
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from vplan.engine.config import config
from vplan.engine.exception import InvalidPlanError, SmartThingsClientError
from vplan.interface import (
    SIMPLE_TIME_REGEX,
    TRIGGER_DAY_REGEX,
    TRIGGER_TIME_REGEX,
    TRIGGER_VARIATION_REGEX,
    VPLAN_RULE_PREFIX,
    Device,
    DeviceGroup,
    PlanSchema,
    SimpleTime,
    SwitchState,
    Trigger,
    TriggerDay,
    TriggerTime,
    TriggerVariation,
)


# noinspection PyMethodMayBeStatic
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
    via a Python context manager.  At least it's only a few API calls.

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
        result = self._retrieve_locations()
        for item in result:
            locations[item["name"]] = item["locationId"]
        if not location in locations:
            raise SmartThingsClientError("Configured location not found: %s" % location)
        lid: str = locations[location]
        logging.info("Location id: %s", lid)
        return lid

    def _derive_rooms(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Derive the mapping from room id->name and name->id for the location."""
        room_by_id = {}
        room_by_name = {}
        result = self._retrieve_rooms()
        for item in result:
            room_by_id[item["roomId"]] = item["name"]
            room_by_name[item["name"]] = item["roomId"]
        logging.info("Location [%s] has %d rooms", self.location, len(room_by_id))
        if room_by_id:
            logging.debug("Rooms by id: %s", json.dumps(room_by_id, indent=2))
        return room_by_id, room_by_name

    def _derive_devices(self) -> Tuple[Dict[str, Device], Dict[str, str]]:
        """Derive the mapping from device id->Device and name->id for the location."""
        device_by_id = {}
        device_by_name = {}
        result = self._retrieve_devices()
        for item in result:
            did = item["deviceId"]
            device_name = item["label"] if item["label"] else item["name"]  # users see the label, if there is one
            room_name = self.room_by_id[item["roomId"]]
            device = Device(room=room_name, device=device_name)
            device_by_id[did] = device
            device_by_name["%s/%s" % (room_name, device.device)] = did
        logging.info("Location [%s] has %d devices", self.location, len(device_by_id))
        if device_by_name:
            logging.debug("Devices by name:\n%s", json.dumps(device_by_name, indent=2))
        return device_by_id, device_by_name

    def _derive_rule_by_id(self) -> Dict[str, Dict[str, Any]]:
        """Derive the mapping from rule id->name, including only rules managed by us."""
        rule_by_id = {}
        result = self._retrieve_rules()
        for item in result:
            if item["name"].startswith("%s/" % VPLAN_RULE_PREFIX):  # we identify our rules by name
                rule_id = item["id"]
                rule_by_id[rule_id] = item
        logging.info("Location [%s] has %d managed rules", self.location, len(rule_by_id))
        if rule_by_id:
            logging.debug("Managed rules by id:\n%s", json.dumps(rule_by_id, indent=2))
        return rule_by_id

    def _retrieve_locations(self) -> List[Dict[str, Any]]:
        """Retrieve all locations associated with a token."""
        url = _url("/locations")
        params = {"limit": LocationContext.LOCATION_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        result = response.json()
        return result["items"] if "items" in result else []  # type: ignore

    def _retrieve_rooms(self) -> List[Dict[str, Any]]:
        """Retrieve all rooms associated with a token."""
        url = _url("/locations/%s/rooms" % self.location_id)
        params = {"limit": LocationContext.ROOM_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        result = response.json()
        return result["items"] if "items" in result else []  # type: ignore

    def _retrieve_devices(self) -> List[Dict[str, Any]]:
        """Retrieve all devices associated with a token."""
        url = _url("/devices")
        params = {"locationId": self.location_id, "capability": "switch", "limit": LocationContext.DEVICE_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        result = response.json()
        return result["items"] if "items" in result else []  # type: ignore

    def _retrieve_rules(self) -> List[Dict[str, Any]]:
        """Retrieve all rules associated with a token."""
        url = _url("/rules")
        params = {"locationId": self.location_id, "limit": LocationContext.RULES_LIMIT}
        response = requests.get(url=url, headers=self.headers, params=params)
        _raise_for_status(response)
        result = response.json()
        return result["items"] if "items" in result else []  # type: ignore


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


def _headers() -> Dict[str, str]:
    """Get the headers to use for requests."""
    return CONTEXT.get().headers


def _raise_for_status(response: requests.Response) -> None:
    """Check response status, raising SmartThingsClientError for errors"""
    try:
        response.raise_for_status()
    except requests.models.HTTPError as e:
        raise SmartThingsClientError("%s" % e) from e


def _build_specific(
    days: Union[List[str], List[TriggerDay]],
    trigger_time: Union[str, TriggerTime],
    variation: Union[str, TriggerVariation],
) -> Dict[str, Any]:
    """Build a specific time for a rule to execute."""
    variation_minutes = parse_variation(variation)
    reference, offset = parse_trigger_time(trigger_time, variation_minutes)
    days_of_week = parse_days(days)
    specific: Dict[str, Any] = {"reference": reference, "daysOfWeek": days_of_week}
    if offset:
        specific["offset"] = {"value": {"integer": offset}, "unit": "Minute"}
    return specific


def _build_actions(device_ids: List[str], state: SwitchState) -> List[Dict[str, Any]]:
    """Build a list of actions (commands) to execute with in a rule."""
    command = {"component": "main", "capability": "switch", "command": "on" if state == SwitchState.ON else "off"}
    return [{"command": {"devices": device_ids, "commands": [command]}}]


def device_id(device: Device) -> str:
    """Get the device id for a device from the context."""
    key = "%s/%s" % (device.room, device.device)
    if not key in CONTEXT.get().device_by_name:
        raise InvalidPlanError("Invalid device: %s" % key)
    return CONTEXT.get().device_by_name[key]


def location_id() -> str:
    """Get the location id from the context."""
    return CONTEXT.get().location_id


def managed_rule_ids(plan_name: str) -> List[str]:
    """Get a list of the managed rule ids from the context, filtered to those associated with a plan."""
    return [
        rule["id"]
        for rule in CONTEXT.get().rule_by_id.values()
        if rule["name"].startswith("%s/%s" % (VPLAN_RULE_PREFIX, plan_name))
    ]


def replace_managed_rules(plan_name: str, managed_rules: List[Dict[str, Any]]) -> None:
    """Replace the managed rules for this plan in the context."""
    for rule_id in managed_rule_ids(plan_name):
        del CONTEXT.get().rule_by_id[rule_id]
    for rule in managed_rules:
        CONTEXT.get().rule_by_id[rule["id"]] = rule


def build_rule(
    name: str,
    device_ids: List[str],
    days: Union[List[str], List[TriggerDay]],
    trigger_time: Union[str, TriggerTime],
    variation: Union[str, TriggerVariation],
    state: SwitchState,
) -> Dict[str, Any]:
    """Build a rule for a trigger state change, either on or off."""
    specific = _build_specific(days, trigger_time, variation)
    actions = _build_actions(device_ids, state)
    return {"name": name, "actions": [{"every": {"specific": specific, "actions": actions}}]}


def build_trigger_rules(name: str, device_ids: List[str], trigger: Trigger) -> List[Dict[str, Any]]:
    """Build all rules for a trigger."""
    on = build_rule("%s/on" % name, device_ids, trigger.days, trigger.on_time, trigger.variation, SwitchState.ON)
    off = build_rule("%s/off" % name, device_ids, trigger.days, trigger.off_time, trigger.variation, SwitchState.OFF)
    return [on, off]


def build_group_rules(name: str, group: DeviceGroup) -> List[Dict[str, Any]]:
    """Build all rules for a device group."""
    rules = []
    device_ids = [device_id(device) for device in group.devices]
    for index, trigger in enumerate(group.triggers):
        rules += build_trigger_rules("%s/%s/trigger[%d]" % (name, group.name, index), device_ids, trigger)
    return rules


def build_plan_rules(schema: PlanSchema) -> List[Dict[str, Any]]:
    """Build all rules for a plan."""
    rules = []
    for group in schema.plan.groups:
        rules += build_group_rules("%s/%s" % (VPLAN_RULE_PREFIX, schema.plan.name), group)
    return rules


def replace_rules(plan_name: str, schema: Optional[PlanSchema]) -> None:
    """Replace all existing rules for a plan with new rules based on the schema."""
    for rule_id in managed_rule_ids(plan_name):
        delete_rule(rule_id)
    created = []
    if schema:  # if there is no schema, that means it's been deleted or disabled
        rules = build_plan_rules(schema)
        logging.info("New plan has %d rules", len(rules))
        for rule in rules:
            created.append(create_rule(rule))
    else:
        logging.info("Plan is disabled or has been deleted; no rules will be added")
    replace_managed_rules(plan_name, created)


def delete_rule(rule_id: str) -> None:
    """Delete an existing rule."""
    url = _url("/rules/%s" % rule_id)
    params = {"locationId": location_id()}
    response = requests.delete(url=url, headers=_headers(), params=params)
    _raise_for_status(response)


def create_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    """Create a rule, returning the result from SmartThings."""
    url = _url("/rules")
    params = {"locationId": CONTEXT.get().location_id}
    response = requests.post(url=url, headers=_headers(), params=params, json=rule)
    _raise_for_status(response)
    return response.json()  # type: ignore[no-any-return]


def set_switch(device: Device, state: SwitchState) -> None:
    """Switch a device on or off."""
    command = "on" if state == SwitchState.ON else "off"
    request = {"commands": [{"component": "main", "capability": "switch", "command": command}]}
    url = _url("/devices/%s/commands" % device_id(device))
    response = requests.post(url=url, headers=_headers(), json=request)
    _raise_for_status(response)


def check_switch(device: Device) -> SwitchState:
    """Check the state of a switch."""
    url = _url("/devices/%s/components/main/capabilities/switch/status" % device_id(device))
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
