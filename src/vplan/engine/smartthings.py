# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Manage SmartThings behaviors.
"""
import datetime
import json
import logging
import time
from contextvars import ContextVar
from typing import Any, Dict, List

import requests

from vplan.engine.config import config
from vplan.engine.interface import Device, ServerException, SwitchState, parse_time
from vplan.engine.scheduler import schedule_daily_job, schedule_immediate_job, unschedule_daily_job

PAT_TOKEN: ContextVar[str] = ContextVar("PAT_TOKEN")
HEADERS: ContextVar[Dict[str, Any]] = ContextVar("HEADERS")
LOCATION: ContextVar[str] = ContextVar("LOCATION")
ROOMS: ContextVar[Dict[str, str]] = ContextVar("ROOMS")
DEVICES: ContextVar[Dict[str, str]] = ContextVar("DEVICES")

# Rather than dealing with pagination, I'm just getting really big pages
LOCATION_LIMIT = "100"
ROOM_LIMIT = "250"
DEVICE_LIMIT = "1000"

ON_COMMAND = {"commands": [{"component": "main", "capability": "switch", "command": "on"}]}
OFF_COMMAND = {"commands": [{"component": "main", "capability": "switch", "command": "off"}]}


class LocationContext:
    """Manages the context associated with a SmartThings location."""

    def __init__(self, pat_token: str, location: str):
        self.pat_token = PAT_TOKEN.set(pat_token)
        self.headers = HEADERS.set(_headers())
        self.location = LOCATION.set(_derive_location(location))
        self.rooms = ROOMS.set(_derive_rooms())
        self.devices = DEVICES.set(_derive_devices())

    def __enter__(self) -> None:
        return None

    def __exit__(self, _type, value, traceback) -> None:  # type: ignore[no-untyped-def]
        PAT_TOKEN.reset(self.pat_token)
        HEADERS.reset(self.headers)
        LOCATION.reset(self.location)
        ROOMS.reset(self.rooms)
        DEVICES.reset(self.devices)


def _device_id(device: Device) -> str:
    """Get the device id for a room/device in the DEVICES mapping."""
    return DEVICES.get()["%s/%s" % (device.room, device.device)]


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (config().smartthings.base_api_url, endpoint)


def _headers() -> Dict[str, str]:
    """Fill standard headers for API requests."""
    return {
        "Accept": "application/vnd.smartthings+json;v=1",
        "Accept-Language": "en_US",
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % PAT_TOKEN.get(),
    }


def _derive_location(location: str) -> str:
    """Derive the location id for a location name."""
    logging.debug("Deriving the location id")
    locations = {}
    url = _url("/locations")
    params = {"limit": LOCATION_LIMIT}
    response = requests.get(url, headers=HEADERS.get(), params=params)
    response.raise_for_status()
    for item in response.json()["items"]:
        locations[item["name"]] = item["locationId"]
    if not location in locations:
        raise ServerException("Configured location not found.")
    logging.debug("Locations: %s", json.dumps(locations, indent=2))
    location_id: str = locations[location]
    logging.info("Location id: %s", location_id)
    return location_id


def _derive_rooms() -> Dict[str, str]:
    """Derive the mapping from room id to room name for the location."""
    logging.debug("Deriving the room mapping")
    rooms = {}
    url = _url("/locations/%s/rooms" % LOCATION.get())
    params = {"limit": ROOM_LIMIT}
    response = requests.get(url, headers=HEADERS.get(), params=params)
    response.raise_for_status()
    for item in response.json()["items"]:
        rooms[item["roomId"]] = item["name"]
    logging.info("This location has %d rooms", len(rooms))
    logging.debug("Rooms: %s", json.dumps(rooms, indent=2))
    return rooms


def _derive_devices() -> Dict[str, str]:
    """Derive the mapping from room/device to device id for the location."""
    logging.debug("Deriving the device mapping")
    devices = {}
    url = _url("/devices")
    params = {"locationId": LOCATION.get(), "capability": "switch", "limit": DEVICE_LIMIT}
    response = requests.get(url, headers=HEADERS.get(), params=params)
    response.raise_for_status()
    for item in response.json()["items"]:
        device = item["label"] if item["label"] else item["name"]  # users see the label, if there is one
        room = ROOMS.get()[item["roomId"]]
        device_id = item["deviceId"]
        devices["%s/%s" % (room, device)] = device_id
    logging.info("This location has %d devices", len(devices))
    logging.debug("Devices:\n%s", json.dumps(devices, indent=2))
    return devices


def _set_switch(device: Device, state: SwitchState) -> None:
    """Switch a device on or off."""
    url = _url("/devices/%s/commands" % _device_id(device))
    command = ON_COMMAND if state is SwitchState.ON else OFF_COMMAND
    response = requests.post(url, headers=HEADERS.get(), json=command)
    response.raise_for_status()


def _check_switch(device: Device) -> SwitchState:
    """Check the state of a switch."""
    url = _url("/devices/%s/components/main/capabilities/switch/status" % _device_id(device))
    response = requests.get(url, headers=HEADERS.get())
    response.raise_for_status()
    return SwitchState.ON if response.json()["switch"]["value"] == "on" else SwitchState.OFF


def st_schedule_daily_refresh(plan_name: str, refresh_time: str, time_zone: str) -> None:
    """Create or replace a job to periodically refresh the plan definition at SmartThings."""
    job_id = "daily/%s" % plan_name
    hour, minute = parse_time(refresh_time)
    trigger_time = datetime.time(hour=hour, minute=minute, second=0)
    func = st_refresh_plan
    kwargs = {"plan_name": plan_name}
    schedule_daily_job(job_id, trigger_time, func, kwargs, time_zone)


def st_unschedule_daily_refresh(plan_name: str) -> None:
    """Remove any existing daily refresh job."""
    job_id = "daily/%s" % plan_name
    unschedule_daily_job(job_id)


def st_schedule_immediate_refresh(plan_name: str) -> None:
    """Schedule a job to immediately refresh the plan definition at SmartThings."""
    job_id = "immediate/%s/%s" % (plan_name, datetime.datetime.now().isoformat())
    func = st_refresh_plan
    kwargs = {"plan_name": plan_name}
    schedule_immediate_job(job_id, func, kwargs)


def st_toggle_devices(pat_token: str, location: str, devices: List[Device], toggles: int) -> None:
    """Toggle group of devices, switching them on and off a certain number of times."""

    # This sort of test is sensitive.  I've found that if you try to toggle the state
    # too quickly, even for local Zigbee devices, that sometimes the toggles don't work
    # as expected.  So, I recommend at least a 5-second delay between toggles in config.
    # It might work better to check the state before toggling the next time.

    with LocationContext(pat_token, location):
        for test in range(0, toggles):
            if test > 0:
                time.sleep(config().smartthings.toggle_delay_sec)
            for device in devices:
                _set_switch(device, SwitchState.ON)
            time.sleep(config().smartthings.toggle_delay_sec)
            for device in devices:
                _set_switch(device, SwitchState.OFF)


def st_refresh_plan(plan_name: str) -> None:
    """Refresh the plan definition at SmartThings, either replacing or removing all relevant rules."""
