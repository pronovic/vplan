# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os

import pytest

from vplan.engine.interface import Account, Device, DeviceGroup, Health, Plan, PlanSchema, Status, Trigger, Version

VALID_NAME = "abcd-1234-efgh-5678-ijkl-9012-mnop-3456-qrst-7890"
TOO_LONG_NAME = "%sX" % VALID_NAME  # one character too long


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "interface", filename)


VALID_PLAN_FILE = fixture("plan.yaml")
INVALID_PLAN_FILE = fixture("bad.yaml")

PLAN_EXPECTED = PlanSchema(
    version="1.0.0",
    plan=Plan(
        name="my-house",
        location="My House",
        refresh_time="00:30",
        refresh_zone="America/Chicago",
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
                    Trigger(days=["friday", "weekend"], on_time="19:45", off_time="midnight", variation="+/- 45 minutes"),
                ],
            ),
        ],
    ),
)

DEVICES_EXPECTED = [
    Device(room="Living Room", device="Sofa Table Lamp"),
    Device(room="Living Room", device="China Cabinet"),
    Device(room="Ken's Office", device="Desk Lamp"),
    Device(room="Julie's Office", device="Dresser Lamp"),
    Device(room="Basement", device="Lamp Under Window"),
]


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
        "name,location,refresh_time,refresh_zone",
        [
            ("n", "l", "00:00", "UTC"),
            (" n ", " l ", " 12:00 ", " America/Chicago "),
            (VALID_NAME, "location", "23:59", "US/Eastern"),
        ],
        ids=["short", "whitespace", "long"],
    )
    def test_plan_valid(self, name, location, refresh_time, refresh_zone):
        model = Plan(name=name, location=location, refresh_time=refresh_time, refresh_zone=refresh_zone)
        assert model.name == name.strip()
        assert model.location == location  # not stripped, it's a SmartThings identifier
        assert model.refresh_time == refresh_time.strip()
        assert model.groups == []

    @pytest.mark.parametrize(
        "name,location,refresh_time,refresh_zone",
        [
            ("", "location", "18:02", "UTC"),
            (None, "location", "18:02", "UTC"),
            (TOO_LONG_NAME, "location", "18:02", "UTC"),
            ("name", "", "18:02", "UTC"),
            ("name", None, "18:02", "UTC"),
            ("name", "location", "", "UTC"),
            ("name", "location", None, "UTC"),
            ("name", "location", "8:02", "UTC"),
            ("name", "location", "23:59", "bogus"),
        ],
        ids=[
            "empty name",
            "no name",
            "long name",
            "empty room",
            "no room",
            "empty refresh",
            "no refresh",
            "invalid refresh",
            "invalid zone",
        ],
    )
    def test_plan_invalid(self, name, location, refresh_time, refresh_zone):
        with pytest.raises(ValueError):
            Plan(name=name, location=location, refresh_time=refresh_time, refresh_zone=refresh_zone)

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
    def test_parsing_valid(self):
        schema = PlanSchema.parse_file(VALID_PLAN_FILE)
        assert schema == PLAN_EXPECTED
        assert schema.devices() == DEVICES_EXPECTED
        assert schema.devices("first-floor-lights") == schema.plan.groups[0].devices

    def test_parsing_invalid(self):
        with pytest.raises(ValueError):
            PlanSchema.parse_file(INVALID_PLAN_FILE)
