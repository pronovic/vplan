# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name

import json
import os
from unittest.mock import MagicMock, call, patch

import pytest
from requests.models import HTTPError

from vplan.engine.exception import InvalidPlanError, SmartThingsClientError
from vplan.engine.smartthings import (
    CONTEXT,
    SmartThings,
    _base_api_url,
    _raise_for_status,
    build_group_rules,
    build_plan_rules,
    build_rule,
    build_trigger_rules,
    check_switch,
    create_rule,
    delete_rule,
    device_id,
    location_id,
    managed_rule_ids,
    parse_days,
    parse_time,
    parse_trigger_time,
    parse_variation,
    replace_managed_rules,
    replace_rules,
    set_switch,
)
from vplan.interface import Device, DeviceGroup, SwitchState, Trigger

# This is the data we expect when loading the SmartThings location context
PAT_TOKEN = "AAA"
LOCATION = "My House"
LOCATION_ID = "15526d0a-xxxx-xxxx-xxxx-b6247aacbbb2"
RULE_ID = "88c05897-xxxx-xxxx-xxxx-ae6451501c27"
RULE_NAME = "vplan/winter/office/trigger[0]/on"
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
DTH_DEVICE_BY_NAME = {
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
EDGE_DEVICE_BY_NAME = {
    "Living Room/Sofa Table Lamp": "6498f80e-xxxx-xxxx-xxxx-d1b1916d48f2",
    "Living Room/Tree Outlet": "343345ca-xxxx-xxxx-xxxx-bd52e260583b",
    "Office/Desk Lamp": "54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc",
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
def test_context_dth(requests_get, _):
    locations = fixture("locations.json")
    rooms = fixture("rooms.json")
    devices = fixture("dth-devices.json")
    rules = fixture("rules.json")
    locations_response = _response(locations)
    rooms_response = _response(rooms)
    devices_response = _response(devices)
    rules_response = _response(rules)
    requests_get.side_effect = [locations_response, rooms_response, devices_response, rules_response]
    return SmartThings(PAT_TOKEN, LOCATION)


@pytest.fixture
@patch("vplan.engine.smartthings._base_api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
@patch("vplan.engine.smartthings.requests.get")
def test_context_edge(requests_get, _):
    locations = fixture("locations.json")
    rooms = fixture("rooms.json")
    devices = fixture("edge-devices.json")
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

    def test_device_id_dth(self, test_context_dth):
        with test_context_dth:
            assert device_id(Device(room="Office", device="Desk Lamp")) == "54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc"

    def test_device_id_edge(self, test_context_edge):
        with test_context_edge:
            assert device_id(Device(room="Living Room", device="Tree Outlet")) == "343345ca-xxxx-xxxx-xxxx-bd52e260583b"

    @pytest.mark.parametrize(
        "device",
        [
            Device(room="Office", device="Sauna"),
            Device(room="Patio", device="Desk Lamp"),
        ],
    )
    def test_device_id_invalid_dth(self, test_context_dth, device):
        with test_context_dth:
            with pytest.raises(InvalidPlanError):
                assert device_id(device)

    @pytest.mark.parametrize(
        "device",
        [
            Device(room="Office", device="Sauna"),
            Device(room="Patio", device="Desk Lamp"),
        ],
    )
    def test_device_id_invalid_edge(self, test_context_edge, device):
        with test_context_edge:
            with pytest.raises(InvalidPlanError):
                assert device_id(device)

    def test_location_id(self, test_context_dth):
        with test_context_dth:
            assert location_id() == LOCATION_ID

    def test_managed_rule_ids(self, test_context_dth):
        with test_context_dth:
            assert managed_rule_ids("winter") == [RULE_ID]
            assert managed_rule_ids("unknown") == []

    def test_replace_managed_rules(self, test_context_dth):
        rules = [
            {"id": "aaa", "name": "vplan/winter/A"},
            {"id": "bbb", "name": "vplan/winter/B"},
        ]
        with test_context_dth:
            assert managed_rule_ids("winter") == [RULE_ID]
            replace_managed_rules("winter", rules)
            assert managed_rule_ids("winter") == ["aaa", "bbb"]


class TestParsers:
    @pytest.mark.parametrize(
        "variation,minimum,maximum",
        [
            ("disabled", None, None),
            ("none", None, None),
            ("+ 5 minutes", 0, 5),
            ("- 5 minutes", -5, 0),
            ("+/- 5 minutes", -5, 5),
            ("+ 2 hours", 0, 120),
            ("- 2 hours", -120, 0),
            ("+/- 2 hours", -120, 120),
        ],
    )
    @patch("vplan.engine.smartthings.randint")
    def test_parse_variation_valid(self, randint, variation, minimum, maximum):
        if minimum is None or maximum is None:
            assert parse_variation(variation) is None
        else:
            randint.return_value = 999
            assert parse_variation(variation) == 999
            randint.assert_called_with(minimum, maximum)

    @pytest.mark.parametrize("variation", [None, "", "bogus"])
    def test_parse_variation_invalid(self, variation):
        with pytest.raises(ValueError):
            parse_variation(variation)

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
    def test_parse_trigger_time_valid(self, trigger, variation, expected):
        assert parse_trigger_time(trigger, variation) == expected

    @pytest.mark.parametrize("time", [None, "", "bogus"])
    def test_parse_trigger_time_invalid(self, time):
        with pytest.raises(ValueError):
            parse_trigger_time(time, None)

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
            # all or every gets translated to 7 days
            (["all"], ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]),
            (["every"], ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]),
            # multiple can be combined together and the result is sorted appropriately
            (["fri", "tue"], ["Tue", "Fri"]),
            (["weekend", "weekdays"], ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]),
            # duplicates get merged out
            (["tue", "tue"], ["Tue"]),
            (["tue", "fri", "weekday"], ["Mon", "Tue", "Wed", "Thu", "Fri"]),
        ],
    )
    def test_parse_days_valid(self, days, expected):
        assert parse_days(days) == expected  # also tests parse day

    @pytest.mark.parametrize(
        "days",
        [
            None,
            [""],
            [None],
            ["bogus"],
        ],
    )
    def test_parse_days_invalid(self, days):
        with pytest.raises(ValueError):
            parse_days(days)


@patch("vplan.engine.smartthings._raise_for_status")
@patch("vplan.engine.smartthings._base_api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
@patch("vplan.engine.smartthings.requests.get")
class TestContext:
    def test_load_context_unknown_location(self, requests_get, _api_url, _):
        locations = fixture("locations.json")
        locations_response = _response(locations)
        requests_get.side_effect = [locations_response]
        with pytest.raises(SmartThingsClientError, match="^Configured location not found"):
            SmartThings(pat_token=PAT_TOKEN, location="bogus")

    @pytest.mark.parametrize(
        "devices_file,devices_expected",
        [
            ("dth-devices.json", DTH_DEVICE_BY_NAME),
            ("edge-devices.json", EDGE_DEVICE_BY_NAME),
        ],
    )
    def test_load_context(self, requests_get, _api_url, raise_for_status, devices_file, devices_expected):
        locations = fixture("locations.json")
        rooms = fixture("rooms.json")
        devices = fixture(devices_file)
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
            assert context.device_by_name == devices_expected
            assert len(context.rule_by_id) == 1  # only our managed rules, identified by name, will be included
            assert context.rule_by_id[RULE_ID]["name"] == RULE_NAME

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
                    timeout=5.0,
                ),
                call(
                    url="http://whatever/locations/%s/rooms" % LOCATION_ID,
                    headers=HEADERS,
                    params={"limit": "250"},
                    timeout=5.0,
                ),
                call(
                    url="http://whatever/devices",
                    headers=HEADERS,
                    params={"locationId": LOCATION_ID, "capability": "switch", "limit": "1000"},
                    timeout=5.0,
                ),
                call(
                    url="http://whatever/rules",
                    headers=HEADERS,
                    params={"locationId": LOCATION_ID, "limit": "100"},
                    timeout=5.0,
                ),
            ]
        )


class TestRules:
    @patch("vplan.engine.smartthings.parse_days")
    @patch("vplan.engine.smartthings.parse_trigger_time")
    @patch("vplan.engine.smartthings.parse_variation")
    def test_build_rule_no_offset(self, _parse_variation, _parse_trigger_time, _parse_days):
        # This tests a rule that has no offset time.
        # It mimics a test that I did manually via Insomnia

        _parse_variation.return_value = 999
        _parse_trigger_time.return_value = "Sunrise", None
        _parse_days.return_value = ["Sun", "Mon"]

        name = "Turn on Lamp"
        devices = {"6498f80e-2c39-4f06-bf5c-d1b1916d48f2": Device(room="yyy", device="zzz", component="ccc")}
        days = ["xxx"]
        trigger_time = "03:00"
        variation = "none"
        state = SwitchState.OFF

        rule = build_rule(name, devices, days, trigger_time, variation, state)

        _parse_variation.assert_called_once_with(variation)
        _parse_trigger_time.assert_called_once_with(trigger_time, 999)
        _parse_days.assert_called_once_with(days)

        assert rule == {
            "name": "Turn on Lamp",
            "actions": [
                {
                    "every": {
                        "specific": {"daysOfWeek": ["Sun", "Mon"], "reference": "Sunrise"},
                        "actions": [
                            {
                                "command": {
                                    "devices": ["6498f80e-2c39-4f06-bf5c-d1b1916d48f2"],
                                    "commands": [{"component": "ccc", "capability": "switch", "command": "off"}],
                                }
                            }
                        ],
                    }
                }
            ],
        }

    @patch("vplan.engine.smartthings.parse_days")
    @patch("vplan.engine.smartthings.parse_trigger_time")
    @patch("vplan.engine.smartthings.parse_variation")
    def test_build_rule_with_offset(self, _parse_variation, _parse_trigger_time, _parse_days):
        # This tests a rule that has an offset time.
        # It mimics a test that I did manually via Insomnia

        _parse_variation.return_value = 999
        _parse_trigger_time.return_value = "Midnight", 333
        _parse_days.return_value = ["Sun", "Mon"]

        name = "Turn on Lamp"
        devices = {"6498f80e-2c39-4f06-bf5c-d1b1916d48f2": Device(room="yyy", device="zzz", component="ccc")}
        days = ["xxx"]
        trigger_time = "03:00"
        variation = "none"
        state = SwitchState.ON

        rule = build_rule(name, devices, days, trigger_time, variation, state)

        _parse_variation.assert_called_once_with(variation)
        _parse_trigger_time.assert_called_once_with(trigger_time, 999)
        _parse_days.assert_called_once_with(days)

        assert rule == {
            "name": "Turn on Lamp",
            "actions": [
                {
                    "every": {
                        "specific": {
                            "daysOfWeek": ["Sun", "Mon"],
                            "reference": "Midnight",
                            "offset": {"value": {"integer": 333}, "unit": "Minute"},
                        },
                        "actions": [
                            {
                                "command": {
                                    "devices": ["6498f80e-2c39-4f06-bf5c-d1b1916d48f2"],
                                    "commands": [{"component": "ccc", "capability": "switch", "command": "on"}],
                                }
                            }
                        ],
                    }
                }
            ],
        }

    @patch("vplan.engine.smartthings.build_rule")
    def test_build_trigger_rules(self, _build_rule):
        name = "whatever"
        device_ids = ["id"]
        trigger = Trigger(days=["weekdays"], on_time="sunrise", off_time="03:00", variation="none")

        on = [{"fake": "on"}]
        off = [{"fake": "on"}]
        _build_rule.side_effect = [on, off]

        assert build_trigger_rules(name, device_ids, trigger) == [on, off]

        _build_rule.assert_has_calls(
            [
                call("whatever/on", device_ids, ["weekdays"], "sunrise", "none", SwitchState.ON),
                call("whatever/off", device_ids, ["weekdays"], "03:00", "none", SwitchState.OFF),
            ]
        )

    @patch("vplan.engine.smartthings.build_trigger_rules")
    @patch("vplan.engine.smartthings.device_id")
    def test_build_group_rules(self, _device_id, _build_trigger_rules):
        name = "whatever"
        device1 = Device(room="a", device="1")
        device2 = Device(room="a", device="2")
        devices = [device1, device2]
        trigger1 = Trigger(days=["weekdays"], on_time="sunrise", off_time="03:00", variation="none")
        trigger2 = Trigger(days=["tue"], on_time="09:00", off_time="12:30", variation="+ 5 minutes")
        triggers = [trigger1, trigger2]
        group = DeviceGroup(name="group", devices=devices, triggers=triggers)
        devices = {"id1": device1, "id2": device2}

        rules1 = [{"fake": "trigger1-1"}, {"fake": "trigger1-2"}]
        rules2 = [{"fake": "trigger2"}]
        _device_id.side_effect = ["id1", "id2"]  # maps to device1, device2
        _build_trigger_rules.side_effect = [rules1, rules2]

        assert build_group_rules(name, group) == rules1 + rules2

        _device_id.assert_has_calls([call(device1), call(device2)])
        _build_trigger_rules.assert_has_calls(
            [
                call("whatever/group/trigger[0]", devices, trigger1),
                call("whatever/group/trigger[1]", devices, trigger2),
            ]
        )

    @patch("vplan.engine.smartthings.build_group_rules")
    def test_build_plan_rules(self, _build_group_rules):
        group1 = MagicMock()
        group2 = MagicMock()
        plan = MagicMock()
        plan.name = "whatever"
        plan.groups = [group1, group2]
        schema = MagicMock(plan=plan)

        rules1 = [{"fake": "trigger1-1"}, {"fake": "trigger1-2"}]
        rules2 = [{"fake": "trigger2"}]
        _build_group_rules.side_effect = [rules1, rules2]

        assert build_plan_rules(schema) == rules1 + rules2

        _build_group_rules.assert_has_calls(
            [
                call("vplan/whatever", group1),
                call("vplan/whatever", group2),
            ]
        )

    @patch("vplan.engine.smartthings.replace_managed_rules")
    @patch("vplan.engine.smartthings.managed_rule_ids")
    @patch("vplan.engine.smartthings.build_plan_rules")
    @patch("vplan.engine.smartthings.create_rule")
    @patch("vplan.engine.smartthings.delete_rule")
    def test_replace_rules_disabled(self, _delete_rule, _create_rule, _build_plan_rules, _managed_rule_ids, _replace_managed_rules):
        _managed_rule_ids.return_value = ["managed"]

        replace_rules("plan", None)  # we'll get none if the plan is disabled or deleted

        _managed_rule_ids.assert_called_once_with("plan")
        _delete_rule.assert_called_once_with("managed")
        _build_plan_rules.assert_not_called()
        _create_rule.assert_not_called()
        _replace_managed_rules.assert_called_once_with("plan", [])

    @patch("vplan.engine.smartthings.replace_managed_rules")
    @patch("vplan.engine.smartthings.managed_rule_ids")
    @patch("vplan.engine.smartthings.build_plan_rules")
    @patch("vplan.engine.smartthings.create_rule")
    @patch("vplan.engine.smartthings.delete_rule")
    def test_replace_rules_enabled(self, _delete_rule, _create_rule, _build_plan_rules, _managed_rule_ids, _replace_managed_rules):
        schema = MagicMock()
        generated = MagicMock()
        returned = MagicMock()
        _managed_rule_ids.return_value = ["managed"]
        _build_plan_rules.return_value = [generated]
        _create_rule.return_value = returned

        replace_rules("plan", schema)

        _managed_rule_ids.assert_called_once_with("plan")
        _delete_rule.assert_called_once_with("managed")
        _build_plan_rules.assert_called_once_with(schema)
        _create_rule.assert_called_once_with(generated)
        _replace_managed_rules.assert_called_once_with("plan", [returned])


@patch("vplan.engine.smartthings._raise_for_status")
@patch("vplan.engine.smartthings._base_api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
class TestClient:
    @patch("vplan.engine.smartthings.requests.delete")
    def test_delete_rule(self, requests_delete, _, raise_for_status, test_context_dth):
        with test_context_dth:
            response = _response()
            requests_delete.side_effect = [response]
            delete_rule("id")
            raise_for_status.assert_called_once_with(response)
            requests_delete.assert_called_once_with(
                url="http://whatever/rules/id", headers=HEADERS, params={"locationId": LOCATION_ID}, timeout=5.0
            )

    @patch("vplan.engine.smartthings.requests.post")
    def test_create_rule(self, requests_post, _, raise_for_status, test_context_dth):
        with test_context_dth:
            input_rule = {"input": "value"}
            output_rule = {"output": "value"}
            response = _response(data=json.dumps(output_rule))
            requests_post.side_effect = [response]
            assert create_rule(input_rule) == output_rule
            raise_for_status.assert_called_once_with(response)
            requests_post.assert_called_once_with(
                url="http://whatever/rules",
                headers=HEADERS,
                params={"locationId": LOCATION_ID},
                json=input_rule,
                timeout=5.0,
            )

    @pytest.mark.parametrize(
        "state,command",
        [(SwitchState.ON, "on"), (SwitchState.OFF, "off")],
    )
    @patch("vplan.engine.smartthings.requests.post")
    def test_set_switch_dth(self, requests_post, _, raise_for_status, test_context_dth, state, command):
        with test_context_dth:
            response = _response()
            requests_post.side_effect = [response]
            set_switch(Device(room="Office", device="Desk Lamp"), state)
            raise_for_status.assert_called_once_with(response)
            requests_post.assert_called_once_with(
                url="http://whatever/devices/54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc/commands",
                headers=HEADERS,
                json={"commands": [{"component": "main", "capability": "switch", "command": command}]},
                timeout=5.0,
            )

    @pytest.mark.parametrize(
        "state,command",
        [(SwitchState.ON, "on"), (SwitchState.OFF, "off")],
    )
    @patch("vplan.engine.smartthings.requests.post")
    def test_set_switch_edge(self, requests_post, _, raise_for_status, test_context_edge, state, command):
        with test_context_edge:
            response = _response()
            requests_post.side_effect = [response]
            set_switch(Device(room="Living Room", device="Tree Outlet", component="leftOutlet"), state)
            raise_for_status.assert_called_once_with(response)
            requests_post.assert_called_once_with(
                url="http://whatever/devices/343345ca-xxxx-xxxx-xxxx-bd52e260583b/commands",
                headers=HEADERS,
                json={"commands": [{"component": "leftOutlet", "capability": "switch", "command": command}]},
                timeout=5.0,
            )

    @pytest.mark.parametrize("file,expected", [("switch_on.json", SwitchState.ON), ("switch_off.json", SwitchState.OFF)])
    @patch("vplan.engine.smartthings.requests.get")
    def test_check_switch_dth(self, requests_get, _, raise_for_status, test_context_dth, file, expected):
        with test_context_dth:
            response = _response(data=fixture(file))
            requests_get.side_effect = [response]
            status = check_switch(Device(room="Office", device="Desk Lamp"))
            assert status == expected
            raise_for_status.assert_called_once_with(response)
            requests_get.assert_called_once_with(
                url="http://whatever/devices/54e6a736-xxxx-xxxx-xxxx-febc0cacd2cc/components/main/capabilities/switch/status",
                headers=HEADERS,
                timeout=5.0,
            )

    @pytest.mark.parametrize("file,expected", [("switch_on.json", SwitchState.ON), ("switch_off.json", SwitchState.OFF)])
    @patch("vplan.engine.smartthings.requests.get")
    def test_check_switch_edge(self, requests_get, _, raise_for_status, test_context_edge, file, expected):
        with test_context_edge:
            response = _response(data=fixture(file))
            requests_get.side_effect = [response]
            status = check_switch(Device(room="Living Room", device="Tree Outlet", component="leftOutlet"))
            assert status == expected
            raise_for_status.assert_called_once_with(response)
            requests_get.assert_called_once_with(
                url="http://whatever/devices/343345ca-xxxx-xxxx-xxxx-bd52e260583b/components/leftOutlet/capabilities/switch/status",
                headers=HEADERS,
                timeout=5.0,
            )
