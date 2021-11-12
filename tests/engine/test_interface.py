# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os

import pytest

from vplan.engine.interface import (
    Account,
    Device,
    DeviceGroup,
    Health,
    Plan,
    PlanSchema,
    ServerException,
    Status,
    Trigger,
    Version,
    parse_time,
)

VALID_NAME = "abcd-1234-efgh-5678-ijkl-9012-mnop-3456-qrst-7890"
TOO_LONG_NAME = "%sX" % VALID_NAME  # one character too long


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "interface", filename)


PLAN_FILE = fixture("plan.yaml")
PLAN_EXPECTED = PlanSchema(
    version="1.0.0",
    plan=Plan(
        name="my-house",
        location="My House",
        refresh_time="00:30",
        groups=[
            DeviceGroup(
                name="first-floor-lights",
                devices=[
                    Device(room="Living Room", device="Sofa Table Lamp"),
                    Device(room="Living Room", device="China Cabinet"),
                ],
                triggers=[
                    Trigger(days=["weekdays"], on_time="19:30", off_time="22:45", variation="+/- 30 minutes"),
                    Trigger(days=["weekends"], on_time="sunset", off_time="sunrise", variation="none"),
                ],
            ),
            DeviceGroup(
                name="offices",
                devices=[
                    Device(room="Ken's Office", device="Desk Lamp"),
                    Device(room="Julie's Office", device="Dresser Lamp"),
                ],
                triggers=[
                    Trigger(days=["mon", "tue", "fri"], on_time="07:30", off_time="17:30", variation="- 1 hour"),
                    Trigger(days=["thu"], on_time="09:30", off_time="12:30", variation="+ 1 hour"),
                ],
            ),
            DeviceGroup(
                name="basement",
                devices=[
                    Device(room="Basement", device="Lamp Under Window"),
                ],
                triggers=[
                    Trigger(days=["friday", "weekend"], on_time="19:45", off_time="midnight", variation="+/- 45 seconds"),
                ],
            ),
        ],
    ),
)


class TestExceptions:
    def test_server_exception(self):
        exception = ServerException("hello")
        assert isinstance(exception, Exception)  # make sure parent class is right
        assert exception.message == "hello"


class TestModelsAndValidation:
    def test_health(self):
        model = Health()
        assert model.status == "OK"

    def test_version(self):
        model = Version(package="a", api="b")
        assert model.package == "a"
        assert model.api == "b"

    def test_status(self):
        model = Status(enabled=True)
        assert model.enabled

    @pytest.mark.parametrize(
        "days,on_time,off_time,variation",
        [
            ([], "midnight", "noon ", "none"),
            ([], "sunrise", "noon", " disabled  "),
            ([], "00:00", " 23:59", "Disabled"),
            ([], "00:00 ", "23:59", "+ 5 minutes"),
            ([], " 00:00 ", "23:59", "- 2 HOURS "),
            ([], "midnight", "noon", "+/- 45 Seconds"),
            (["weekday"], "midnight", "noon", "none"),
            (["Weekdays"], "midnight", "noon", "none"),
            (["WEEKEND"], "midnight", "noon", "none"),
            (["weekends"], "midnight", "noon", "none"),
            (["ALL"], "midnight", "noon", "none"),
            (["every"], "midnight", "noon", "none"),
            (["SUN"], "midnight", "noon", "none"),
            (["Sunday"], "midnight", "noon", "none"),
            (["mon"], "midnight", "noon", "none"),
            (["monday"], "midnight", "noon", "none"),
            (["tue"], "midnight", "noon", "none"),
            (["tuesday"], "midnight", "noon", "none"),
            (["wed"], "midnight", "noon", "none"),
            (["wednesday"], "midnight", "noon", "none"),
            (["thu"], "midnight", "noon", "none"),
            (["thursday"], "midnight", "noon", "none"),
            (["fri"], "midnight", "noon", "none"),
            (["friday"], "midnight", "noon", "none"),
            (["sat"], "midnight", "noon", "none"),
            (["saturday"], "midnight", "noon", "none"),
        ],
    )
    def test_trigger_valid(self, days, on_time, off_time, variation):
        trigger = Trigger(days=days, on_time=on_time, off_time=off_time, variation=variation)
        assert trigger.days == [day.strip().lower() for day in days]
        assert trigger.on_time == on_time.strip().lower()
        assert trigger.off_time == off_time.strip().lower()
        assert trigger.variation == variation.strip().lower()

    @pytest.mark.parametrize(
        "days,on_time,off_time,variation",
        [
            ([], "bogus", "noon", "none"),
            ([], "midnight", "bogus", "none"),
            ([], "midnight", "noon", "bogus"),
            (["bogus"], "midnight", "noon", "none"),
        ],
    )
    def test_trigger_invalid(self, days, on_time, off_time, variation):
        with pytest.raises(ValueError):
            Trigger(days=days, on_time=on_time, off_time=off_time, variation=variation)

    @pytest.mark.parametrize(
        "room,device",
        [
            ("r", "d"),
            (" r ", " d "),
            ("room", "device"),
        ],
        ids=["short", "whitespace", "normal"],
    )
    def test_device_valid(self, room, device):
        model = Device(room=room, device=device)
        assert model.device == device
        assert model.room == room

    @pytest.mark.parametrize(
        "room,device",
        [
            ("", "device"),
            (None, "device"),
            ("room", ""),
            ("room", None),
        ],
        ids=["empty room", "no room", "empty device", "no device"],
    )
    def test_device_invalid(self, room, device):
        with pytest.raises(ValueError):
            Device(room=room, device=device)

    @pytest.mark.parametrize(
        "name",
        [
            "n",
            " n ",
            VALID_NAME,
        ],
        ids=["short", "whitespace", "long"],
    )
    def test_device_group_valid(self, name):
        model = DeviceGroup(name=name, devices=[], triggers=[])
        assert model.name == name.strip()
        assert model.devices == []
        assert model.triggers == []

    @pytest.mark.parametrize(
        "name",
        ["", None, TOO_LONG_NAME],
        ids=["empty name", "no name", "long name"],
    )
    def test_device_group_invalid(self, name):
        with pytest.raises(ValueError):
            DeviceGroup(name=name, devices=[], triggers=[])

    @pytest.mark.parametrize(
        "name,location,refresh_time",
        [
            ("n", "l", "00:00"),
            (" n ", " l ", " 12:00 "),
            (VALID_NAME, "location", "23:59"),
        ],
        ids=["short", "whitespace", "long"],
    )
    def test_plan_valid(self, name, location, refresh_time):
        model = Plan(name=name, location=location, refresh_time=refresh_time)
        assert model.name == name.strip()
        assert model.location == location  # not stripped, it's a SmartThings identifier
        assert model.refresh_time == refresh_time.strip()
        assert model.groups == []

    @pytest.mark.parametrize(
        "name,location,refresh_time",
        [
            ("", "location", "18:02"),
            (None, "location", "18:02"),
            (TOO_LONG_NAME, "location", "18:02"),
            ("name", "", "18:02"),
            ("name", None, "18:02"),
            ("name", "location", ""),
            ("name", "location", None),
            ("name", "location", "8:02"),
        ],
        ids=["empty name", "no name", "long name", "empty room", "no room", "empty refresh", "no refresh", "invalid refresh"],
    )
    def test_plan_invalid(self, name, location, refresh_time):
        with pytest.raises(ValueError):
            Plan(name=name, location=location, refresh_time=refresh_time)

    @pytest.mark.parametrize(
        "pat_token",
        [
            "t",
            " t ",
            "token",
        ],
        ids=["short", "whitespace", "long"],
    )
    def test_account_valid(self, pat_token):
        model = Account(pat_token=pat_token)
        assert model.pat_token == pat_token  # not stripped, it's a SmartThings identifier

    @pytest.mark.parametrize(
        "pat_token",
        ["", None],
        ids=["empty token", "no token"],
    )
    def test_account_invalid(self, pat_token):
        with pytest.raises(ValueError):
            Account(pat_token=pat_token)


class TestYamlParsing:
    def test_parsing(self):
        with open(PLAN_FILE, "r", encoding="utf8") as fp:
            schema = PlanSchema.parse_raw(fp.read())
            assert schema == PLAN_EXPECTED


class TestUtil:
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
