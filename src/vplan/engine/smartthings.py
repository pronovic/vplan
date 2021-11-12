# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
SmartThings API client
"""
import json
import logging
from contextvars import ContextVar
from typing import Any, Dict

import requests

from vplan.engine.config import config
from vplan.engine.interface import Device, ServerException, SwitchState

# Rather than dealing with pagination, I'm just getting really big pages
LOCATION_LIMIT = "100"
ROOM_LIMIT = "250"
DEVICE_LIMIT = "1000"

# JSON commands against the SmartThings API, stored as dictionaries
ON_COMMAND = {"commands": [{"component": "main", "capability": "switch", "command": "on"}]}
OFF_COMMAND = {"commands": [{"component": "main", "capability": "switch", "command": "off"}]}

# Context managed by the SmartThings context manager
PAT_TOKEN: ContextVar[str] = ContextVar("PAT_TOKEN")
HEADERS: ContextVar[Dict[str, Any]] = ContextVar("HEADERS")
LOCATION: ContextVar[str] = ContextVar("LOCATION")
ROOMS: ContextVar[Dict[str, str]] = ContextVar("ROOMS")
DEVICES: ContextVar[Dict[str, str]] = ContextVar("DEVICES")


class SmartThings:
    """Context manager for SmartThings API."""

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


def set_switch(device: Device, state: SwitchState) -> None:
    """Switch a device on or off."""
    url = _url("/devices/%s/commands" % _device_id(device))
    command = ON_COMMAND if state is SwitchState.ON else OFF_COMMAND
    response = requests.post(url, headers=HEADERS.get(), json=command)
    response.raise_for_status()


def check_switch(device: Device) -> SwitchState:
    """Check the state of a switch."""
    url = _url("/devices/%s/components/main/capabilities/switch/status" % _device_id(device))
    response = requests.get(url, headers=HEADERS.get())
    response.raise_for_status()
    return SwitchState.ON if response.json()["switch"]["value"] == "on" else SwitchState.OFF
