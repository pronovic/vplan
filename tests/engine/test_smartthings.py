# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import json
import os
from unittest.mock import MagicMock, call, patch

import pytest
from requests.models import HTTPError

from vplan.engine.interface import Device, SmartThingsClientError
from vplan.engine.smartthings import CONTEXT, SmartThings, _raise_for_status

# This is the data we expect when loading the SmartThings location context
PAT_TOKEN = "AAA"
LOCATION = "My House"
LOCATION_ID = "15526d0a-xxxx-xxxx-xxxx-b6247aacbbb2"
HEADERS = {
    "Accept": "application/vnd.smartthings+json;v=1",
    "Accept-Language": "en_US",
    "Content-Type": "application/json",
    "Authorization": "Bearer AAA",
}
ROOM_BY_ID = {
    "d948d523-xxxx-xxxx-xxxx-eb9a3a7bca62": "Office",
    "3a10416c-xxxx-xxxx-xxxx-a69e78a82ae4": "Living Room",
    "6ab1824d-xxxx-xxxx-xxxx-eafb1596336d": "Basement",
}
ROOM_BY_NAME = {
    "Office": "d948d523-xxxx-xxxx-xxxx-eb9a3a7bca62",
    "Living Room": "3a10416c-xxxx-xxxx-xxxx-a69e78a82ae4",
    "Basement": "6ab1824d-xxxx-xxxx-xxxx-eafb1596336d",
}
DEVICE_BY_ID = {
    "5b012baf-xxxx-xxxx-xxxx-097f8b847cd2": Device(room="Basement", device="Lamp Under Window"),
    "f079ee62-xxxx-xxxx-xxxx-59dce7db1d0d": Device(room="Living Room", device="Zooz Outlet #2 - Right"),
    "54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc": Device(room="Office", device="Desk Lamp"),
    "e25f022a-xxxx-xxxx-xxxx-3385cb2ef6c0": Device(room="Living Room", device="China Cabinet"),
    "6498f80e-xxxx-xxxx-xxxx-d1b1916d48f2": Device(room="Living Room", device="Sofa Table Lamp"),
    "a5967b9a-xxxx-xxxx-xxxx-864989ecba8d": Device(room="Living Room", device="Loveseat Lamp"),
    "ff237cb5-xxxx-xxxx-xxxx-591d5c2e71c1": Device(room="Basement", device="Corner Lamp"),
    "4461fbe1-xxxx-xxxx-xxxx-081ed04a3e01": Device(room="Living Room", device="Front Window Lamp"),
    "99ca768e-xxxx-xxxx-xxxx-cf2f7e27c09d": Device(room="Living Room", device="Zooz Outlet #1 - Left"),
}
DEVICE_BY_NAME = {
    "Basement/Lamp Under Window": "5b012baf-xxxx-xxxx-xxxx-097f8b847cd2",
    "Living Room/Zooz Outlet #2 - Right": "f079ee62-xxxx-xxxx-xxxx-59dce7db1d0d",
    "Office/Desk Lamp": "54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc",
    "Living Room/China Cabinet": "e25f022a-xxxx-xxxx-xxxx-3385cb2ef6c0",
    "Living Room/Sofa Table Lamp": "6498f80e-xxxx-xxxx-xxxx-d1b1916d48f2",
    "Living Room/Loveseat Lamp": "a5967b9a-xxxx-xxxx-xxxx-864989ecba8d",
    "Basement/Corner Lamp": "ff237cb5-xxxx-xxxx-xxxx-591d5c2e71c1",
    "Living Room/Front Window Lamp": "4461fbe1-xxxx-xxxx-xxxx-081ed04a3e01",
    "Living Room/Zooz Outlet #1 - Left": "99ca768e-xxxx-xxxx-xxxx-cf2f7e27c09d",
}


def fixture(filename: str) -> str:
    """Load fixture JSON data from disk."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", "smartthings", filename)
    with open(path, "r", encoding="utf8") as fp:
        return fp.read()


def _response(data=None, status_code=None):
    """Build a mocked response for use with the requests library."""
    response = MagicMock()
    if data:
        response.json = MagicMock(return_value=json.loads(data))
    if status_code:
        response.status_code = status_code
    response.raise_for_status = MagicMock()
    return response


class TestUtil:
    def test_raise_for_status(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = HTTPError("hello")
        with pytest.raises(SmartThingsClientError, match="^hello"):
            _raise_for_status(response)


@patch("vplan.engine.smartthings._raise_for_status")
@patch("vplan.engine.smartthings._base_api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
@patch("vplan.engine.smartthings.requests.get")
class TestContext:
    def test_load_context(self, requests_get, _api_url, raise_for_status):
        locations = fixture("locations.json")
        rooms = fixture("rooms.json")
        devices = fixture("devices.json")

        locations_response = _response(locations)
        rooms_response = _response(rooms)
        devices_response = _response(devices)
        requests_get.side_effect = [locations_response, rooms_response, devices_response]

        with SmartThings(pat_token=PAT_TOKEN, location=LOCATION):
            context = CONTEXT.get()
            assert context.pat_token == PAT_TOKEN
            assert context.location == LOCATION
            assert context.location_id == LOCATION_ID
            assert context.headers == HEADERS
            assert context.room_by_id == ROOM_BY_ID
            assert context.room_by_name == ROOM_BY_NAME
            assert context.device_by_id == DEVICE_BY_ID
            assert context.device_by_name == DEVICE_BY_NAME

        with pytest.raises(LookupError):
            CONTEXT.get()  # the context should not be available outside the SmartThings() block above

        raise_for_status.assert_has_calls(
            [
                call(locations_response),
                call(rooms_response),
                call(devices_response),
            ]
        )
        requests_get.assert_has_calls(
            [
                call(
                    "http://whatever/locations",
                    headers=HEADERS,
                    params={"limit": "100"},
                ),
                call(
                    "http://whatever/locations/%s/rooms" % LOCATION_ID,
                    headers=HEADERS,
                    params={"limit": "250"},
                ),
                call(
                    "http://whatever/devices",
                    headers=HEADERS,
                    params={"locationId": LOCATION_ID, "capability": "switch", "limit": "1000"},
                ),
            ]
        )
