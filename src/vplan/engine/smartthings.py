# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
SmartThings API client
"""

from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

import json
import logging
from contextvars import ContextVar
from typing import Dict, Tuple

import requests

from vplan.engine.config import config
from vplan.engine.interface import Device, ServerException, SwitchState

# Rather than dealing with pagination, I'm just getting really big pages
LOCATION_LIMIT = "100"
ROOM_LIMIT = "250"
DEVICE_LIMIT = "1000"

# JSON commands to turn switches on and off
ON_COMMAND = {"commands": [{"component": "main", "capability": "switch", "command": "on"}]}
OFF_COMMAND = {"commands": [{"component": "main", "capability": "switch", "command": "off"}]}


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
    via a Python context manager.
    """

    def __init__(self, pat_token: str, location: str):
        self.pat_token = pat_token
        self.location = location
        self.headers = self._derive_headers(pat_token)
        self.location_id = self._derive_location_id(location)
        self.rooms_by_id, self.rooms_by_name = self._derive_rooms()
        self.device_by_id, self.device_by_name = self._derive_devices()

    def _derive_headers(self, pat_token: str) -> Dict[str, str]:
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
        params = {"limit": LOCATION_LIMIT}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        for item in response.json()["items"]:
            locations[item["name"]] = item["locationId"]
        if not location in locations:
            raise ServerException("Configured location not found.")
        location_id: str = locations[location]
        logging.info("Location id: %s", location_id)
        return location_id

    def _derive_rooms(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Derive the mapping from room id->name and name->id for the location."""
        room_by_id = {}
        room_by_name = {}
        url = _url("/locations/%s/rooms" % self.location)
        params = {"limit": ROOM_LIMIT}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
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
        params = {"locationId": self.location, "capability": "switch", "limit": DEVICE_LIMIT}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        for item in response.json()["items"]:
            device_id = item["deviceId"]
            device_name = item["label"] if item["label"] else item["name"]  # users see the label, if there is one
            room_name = self.rooms_by_id[item["roomId"]]
            device = Device(room=room_name, device=device_name)
            device_by_id[device_id] = device
            device_by_name["%s/%s" % (room_name, device)] = device_id
        logging.info("Location [%s] has %d devices", self.location, len(device_by_id))
        logging.debug("Devices by id:\n%s", json.dumps(device_by_id, indent=2))
        return device_by_id, device_by_name


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


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (config().smartthings.base_api_url, endpoint)


def _device_id(device: Device) -> str:
    """Get the device id for a device."""
    return CONTEXT.get().device_by_name["%s/%s" % (device.room, device.device)]


def _device(device_id: str) -> Device:
    """Get the device for a device id."""
    return CONTEXT.get().device_by_id[device_id]


def _headers() -> Dict[str, str]:
    """Get the headers to use for requests."""
    return CONTEXT.get().headers


def set_switch(device: Device, state: SwitchState) -> None:
    """Switch a device on or off."""
    url = _url("/devices/%s/commands" % _device_id(device))
    command = ON_COMMAND if state is SwitchState.ON else OFF_COMMAND
    response = requests.post(url, headers=_headers(), json=command)
    response.raise_for_status()


def check_switch(device: Device) -> SwitchState:
    """Check the state of a switch."""
    url = _url("/devices/%s/components/main/capabilities/switch/status" % _device_id(device))
    response = requests.get(url, headers=_headers())
    response.raise_for_status()
    return SwitchState.ON if response.json()["switch"]["value"] == "on" else SwitchState.OFF
