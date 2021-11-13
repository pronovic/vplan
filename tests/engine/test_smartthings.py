# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name

import json
import os
from unittest.mock import MagicMock, call, patch

import pytest
from requests.models import HTTPError

from vplan.engine.interface import Device, SmartThingsClientError, SwitchState
from vplan.engine.smartthings import (
    CONTEXT,
    SmartThings,
    _base_api_url,
    _raise_for_status,
    check_switch,
    parse_day,
    parse_days,
    parse_time,
    parse_trigger_time,
    set_switch,
)

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


@pytest.fixture
@patch("vplan.engine.smartthings._base_api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
@patch("vplan.engine.smartthings.requests.get")
def test_context(requests_get, _):
    locations = fixture("locations.json")
    rooms = fixture("rooms.json")
    devices = fixture("devices.json")
    rules = fixture("rules.json")
    locations_response = _response(locations)
    rooms_response = _response(rooms)
    devices_response = _response(devices)
    rules_response = _response(rules)
    requests_get.side_effect = [locations_response, rooms_response, devices_response, rules_response]
    return SmartThings(PAT_TOKEN, LOCATION)


class TestUtil:
    @patch("vplan.engine.smartthings.config")
    def test_base_api_url(self, config):
        smartthings = MagicMock(base_api_url="url")
        config.return_value = MagicMock(smartthings=smartthings)
        assert _base_api_url() == "url"

    def test_raise_for_status(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = HTTPError("hello")
        with pytest.raises(SmartThingsClientError, match="^hello"):
            _raise_for_status(response)


class TestParsers:
    @pytest.mark.parametrize(
        "time,hour,minute",
        [("00:00", 0, 0), ("08:10", 8, 10), ("23:59", 23, 59)],
    )
    def test_parse_time_valid(self, time, hour, minute):
        assert parse_time(time) == (hour, minute)

    @pytest.mark.parametrize("time", [None, "", "1", "11", "1:", "11:", "1:1", "1:01", "10:1", "24:02", "11:67"])
    def test_parse_time_invalid(self, time):
        with pytest.raises(ValueError):
            parse_time(time)

    @pytest.mark.parametrize(
        "trigger,variation,expected",
        [
            # no variation always gets None
            ("noon", None, ("Noon", None)),
            ("midnight", None, ("Midnight", None)),
            ("sunrise", None, ("Sunrise", None)),
            ("sunset", None, ("Sunset", None)),
            ("00:00", None, ("Midnight", None)),
            # zero variation turns into None
            ("noon", 0, ("Noon", None)),
            ("midnight", 0, ("Midnight", None)),
            ("sunrise", 0, ("Sunrise", None)),
            ("sunset", 0, ("Sunset", None)),
            ("00:00", 0, ("Midnight", None)),
            # positive variation gets passed through
            ("noon", 1, ("Noon", 1)),
            ("midnight", 1, ("Midnight", 1)),
            ("sunrise", 1, ("Sunrise", 1)),
            ("sunset", 1, ("Sunset", 1)),
            ("00:00", 1, ("Midnight", 1)),
            # negative variation gets passed through, except for Midnight (can't be used there)
            ("noon", -1, ("Noon", -1)),
            ("midnight", -1, ("Midnight", None)),
            ("sunrise", -1, ("Sunrise", -1)),
            ("sunset", -1, ("Sunset", -1)),
            ("00:00", -1, ("Midnight", None)),
            # no variation and zero variation are equivalent in calculations
            ("00:01", None, ("Midnight", 1)),
            ("00:10", None, ("Midnight", 10)),
            ("01:00", None, ("Midnight", 60)),
            ("12:42", None, ("Midnight", 762)),
            ("22:10", None, ("Midnight", 1330)),
            ("00:01", 0, ("Midnight", 1)),
            ("00:10", 0, ("Midnight", 10)),
            ("01:00", 0, ("Midnight", 60)),
            ("12:42", 0, ("Midnight", 762)),
            ("22:10", 0, ("Midnight", 1330)),
            # positive variation always gets added
            ("00:01", 1, ("Midnight", 2)),
            ("00:10", 1, ("Midnight", 11)),
            ("01:00", 1, ("Midnight", 61)),
            ("12:42", 1, ("Midnight", 763)),
            ("22:10", 1, ("Midnight", 1331)),
            # negative variation gets subtracted, but a total at or below zero gets converted to None
            ("00:01", -1, ("Midnight", None)),
            ("00:10", -1, ("Midnight", 9)),
            ("01:00", -1, ("Midnight", 59)),
            ("12:42", -1, ("Midnight", 761)),
            ("22:10", -1, ("Midnight", 1329)),
            ("00:10", -10, ("Midnight", None)),
            ("01:00", -60, ("Midnight", None)),
            ("12:42", -762, ("Midnight", None)),
            ("22:10", -1330, ("Midnight", None)),
            ("00:01", -2, ("Midnight", None)),
            ("00:10", -11, ("Midnight", None)),
            ("01:00", -61, ("Midnight", None)),
            ("12:42", -763, ("Midnight", None)),
            ("22:10", -1331, ("Midnight", None)),
        ],
    )
    def test_parse_trigger_time(self, trigger, variation, expected):
        assert parse_trigger_time(trigger, variation) == expected

    @pytest.mark.parametrize("time", [None, "", "bogus"])
    def test_parse_trigger_time_invalid(self, time):
        with pytest.raises(ValueError):
            parse_trigger_time(time, None)

    @pytest.mark.parametrize("day", [None, "", "bogus"])
    def test_parse_day_invalid(self, day):
        with pytest.raises(ValueError):
            parse_day(day)

    @pytest.mark.parametrize(
        "days,expected",
        [
            # empty list is passed through
            ([], []),
            # individual days get translated 1-for-1
            (["sun"], ["Sun"]),
            (["mon"], ["Mon"]),
            (["tue"], ["Tue"]),
            (["wed"], ["Wed"]),
            (["thu"], ["Thu"]),
            (["fri"], ["Fri"]),
            (["sat"], ["Sat"]),
            (["sunday"], ["Sun"]),
            (["monday"], ["Mon"]),
            (["tuesday"], ["Tue"]),
            (["wednesday"], ["Wed"]),
            (["thursday"], ["Thu"]),
            (["friday"], ["Fri"]),
            (["saturday"], ["Sat"]),
            # weekend gets translated to 2 days
            (["weekend"], ["Sun", "Sat"]),
            (["weekends"], ["Sun", "Sat"]),
            # weekday gets translated to 5 days
            (["weekday"], ["Mon", "Tue", "Wed", "Thu", "Fri"]),
            (["weekdays"], ["Mon", "Tue", "Wed", "Thu", "Fri"]),
            # multiple can be combined together and the result is sorted appropriately
            (["fri", "tue"], ["Tue", "Fri"]),
            (["weekend", "weekdays"], ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]),
            # duplicates get merged out
            (["tue", "tue"], ["Tue"]),
            (["tue", "fri", "weekday"], ["Mon", "Tue", "Wed", "Thu", "Fri"]),
        ],
    )
    def test_parse_days(self, days, expected):
        assert parse_days(days) == expected  # also tests parse day

    @pytest.mark.parametrize("days", [None, ["bogus"]])
    def test_parse_days_invalid(self, days):
        with pytest.raises(ValueError):
            parse_days(days)


@patch("vplan.engine.smartthings._raise_for_status")
@patch("vplan.engine.smartthings._base_api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
@patch("vplan.engine.smartthings.requests.get")
class TestContext:
    def test_load_context(self, requests_get, _api_url, raise_for_status):
        locations = fixture("locations.json")
        rooms = fixture("rooms.json")
        devices = fixture("devices.json")
        rules = fixture("rules.json")

        locations_response = _response(locations)
        rooms_response = _response(rooms)
        devices_response = _response(devices)
        rules_response = _response(rules)
        requests_get.side_effect = [locations_response, rooms_response, devices_response, rules_response]

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
            assert len(context.rule_by_id) == 1
            assert context.rule_by_id["88c05897-xxxx-xxxx-xxxx-ae6451501c27"]["name"] == "vplan/plan/group/trigger[0]/on"

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
                    url="http://whatever/locations",
                    headers=HEADERS,
                    params={"limit": "100"},
                ),
                call(
                    url="http://whatever/locations/%s/rooms" % LOCATION_ID,
                    headers=HEADERS,
                    params={"limit": "250"},
                ),
                call(
                    url="http://whatever/devices",
                    headers=HEADERS,
                    params={"locationId": LOCATION_ID, "capability": "switch", "limit": "1000"},
                ),
                call(
                    url="http://whatever/rules",
                    headers=HEADERS,
                    params={"locationId": LOCATION_ID, "limit": "100"},
                ),
            ]
        )


@patch("vplan.engine.smartthings._raise_for_status")
@patch("vplan.engine.smartthings._base_api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
class TestSwitch:
    @pytest.mark.parametrize(
        "state,command",
        [(SwitchState.ON, "on"), (SwitchState.OFF, "off")],
    )
    @patch("vplan.engine.smartthings.requests.post")
    def test_set_switch(self, requests_post, _, raise_for_status, test_context, state, command):
        with test_context:
            response = _response()
            requests_post.side_effect = [response]
            set_switch(Device(room="Office", device="Desk Lamp"), state)
            raise_for_status.assert_called_once_with(response)
            requests_post.assert_called_once_with(
                url="http://whatever/devices/54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc/commands",
                headers=HEADERS,
                json={"commands": [{"component": "main", "capability": "switch", "command": command}]},
            )

    @pytest.mark.parametrize("file,expected", [("switch_on.json", SwitchState.ON), ("switch_off.json", SwitchState.OFF)])
    @patch("vplan.engine.smartthings.requests.get")
    def test_check_switch(self, requests_get, _, raise_for_status, test_context, file, expected):
        with test_context:
            response = _response(data=fixture(file))
            requests_get.side_effect = [response]
            status = check_switch(Device(room="Office", device="Desk Lamp"))
            assert status == expected
            raise_for_status.assert_called_once_with(response)
            requests_get.assert_called_once_with(
                url="http://whatever/devices/54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc/components/main/capabilities/switch/status",
                headers=HEADERS,
            )
