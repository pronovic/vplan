# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=use-implicit-booleaness-not-comparison:

import os

import pytest
from pydantic_yaml import parse_yaml_file_as

from vplan.interface import (
    Account,
    Device,
    DeviceGroup,
    Health,
    Plan,
    PlanSchema,
    SemVer,
    SimpleTime,
    SmartThingsId,
    Status,
    TimeZone,
    Trigger,
    TriggerDay,
    TriggerTime,
    TriggerVariation,
    Version,
    VplanName,
)

VALID_NAME = "abcd-1234-efgh-5678-ijkl-9012-mnop-3456-qrst-7890"
TOO_LONG_NAME = "%sX" % VALID_NAME  # one character too long


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "interface", filename)


VALID_PLAN_FILE_V100 = fixture("plan-v1.0.0.yaml")
VALID_PLAN_FILE_V110 = fixture("plan-v1.1.0.yaml")

INVALID_PLAN_FILE_MIN_VER = fixture("plan-min-ver.yaml")  # less than minimum version
INVALID_PLAN_FILE_MAX_VER = fixture("plan-max-ver.yaml")  # more than maximum version
INVALID_PLAN_FILE_BAD_SYNTAX = fixture("plan-bad-syntax.yaml")  # bad syntax

PLAN_EXPECTED_V100 = PlanSchema(
    version=SemVer("1.0.0"),
    plan=Plan(
        name=VplanName("my-house"),
        location=SmartThingsId("My House"),
        refresh_time=SimpleTime("00:30"),
        refresh_zone=TimeZone("America/Chicago"),
        groups=[
            DeviceGroup(
                name=VplanName("first-floor-lights"),
                devices=[
                    Device(
                        room=SmartThingsId("Living Room"),
                        device=SmartThingsId("Sofa Table Lamp"),
                        component=SmartThingsId("main"),
                    ),
                    Device(
                        room=SmartThingsId("Living Room"),
                        device=SmartThingsId("China Cabinet"),
                        component=SmartThingsId("main"),
                    ),
                ],
                triggers=[
                    Trigger(
                        days=[TriggerDay("weekdays")],
                        on_time=TriggerTime("19:30"),
                        off_time=TriggerTime("22:45"),
                        variation=TriggerVariation("+/- 30 minutes"),
                    ),
                    Trigger(
                        days=[TriggerDay("weekends")],
                        on_time=TriggerTime("sunset"),
                        off_time=TriggerTime("sunrise"),
                        variation=TriggerVariation("none"),
                    ),
                ],
            ),
            DeviceGroup(
                name=VplanName("offices"),
                devices=[
                    Device(
                        room=SmartThingsId("Ken's Office"),
                        device=SmartThingsId("Desk Lamp"),
                        component=SmartThingsId("main"),
                    ),
                    Device(
                        room=SmartThingsId("Julie's Office"),
                        device=SmartThingsId("Dresser Lamp"),
                        component=SmartThingsId("main"),
                    ),
                ],
                triggers=[
                    Trigger(
                        days=[TriggerDay("mon"), TriggerDay("tue"), TriggerDay("fri")],
                        on_time=TriggerTime("07:30"),
                        off_time=TriggerTime("17:30"),
                        variation=TriggerVariation("- 1 hour"),
                    ),
                    Trigger(
                        days=[TriggerDay("thu")],
                        on_time=TriggerTime("09:30"),
                        off_time=TriggerTime("12:30"),
                        variation=TriggerVariation("+ 1 hour"),
                    ),
                ],
            ),
            DeviceGroup(
                name=VplanName("basement"),
                devices=[
                    Device(
                        room=SmartThingsId("Basement"),
                        device=SmartThingsId("Lamp Under Window"),
                        component=SmartThingsId("main"),
                    ),
                ],
                triggers=[
                    Trigger(
                        days=[TriggerDay("friday"), TriggerDay("weekend")],
                        on_time=TriggerTime("19:45"),
                        off_time=TriggerTime("midnight"),
                        variation=TriggerVariation("+/- 45 minutes"),
                    ),
                ],
            ),
        ],
    ),
)

PLAN_EXPECTED_V110 = PlanSchema(
    version=SemVer("1.1.0"),
    plan=Plan(
        name=VplanName("my-house"),
        location=SmartThingsId("My House"),
        refresh_time=SimpleTime("00:30"),
        refresh_zone=TimeZone("America/Chicago"),
        groups=[
            DeviceGroup(
                name=VplanName("first-floor-lights"),
                devices=[
                    Device(
                        room=SmartThingsId("Living Room"),
                        device=SmartThingsId("Sofa Table Lamp"),
                        component=SmartThingsId("main"),
                    ),
                    Device(
                        room=SmartThingsId("Living Room"),
                        device=SmartThingsId("China Cabinet"),
                        component=SmartThingsId("main"),
                    ),
                ],
                triggers=[
                    Trigger(
                        days=[TriggerDay("weekdays")],
                        on_time=TriggerTime("19:30"),
                        off_time=TriggerTime("22:45"),
                        variation=TriggerVariation("+/- 30 minutes"),
                    ),
                    Trigger(
                        days=[TriggerDay("weekends")],
                        on_time=TriggerTime("sunset"),
                        off_time=TriggerTime("sunrise"),
                        variation=TriggerVariation("none"),
                    ),
                ],
            ),
            DeviceGroup(
                name=VplanName("offices"),
                devices=[
                    Device(
                        room=SmartThingsId("Ken's Office"),
                        device=SmartThingsId("Desk Lamp"),
                        component=SmartThingsId("main"),
                    ),
                    Device(
                        room=SmartThingsId("Julie's Office"),
                        device=SmartThingsId("Dresser Lamp"),
                        component=SmartThingsId("main"),
                    ),
                ],
                triggers=[
                    Trigger(
                        days=[TriggerDay("mon"), TriggerDay("tue"), TriggerDay("fri")],
                        on_time=TriggerTime("07:30"),
                        off_time=TriggerTime("17:30"),
                        variation=TriggerVariation("- 1 hour"),
                    ),
                    Trigger(
                        days=[TriggerDay("thu")],
                        on_time=TriggerTime("09:30"),
                        off_time=TriggerTime("12:30"),
                        variation=TriggerVariation("+ 1 hour"),
                    ),
                ],
            ),
            DeviceGroup(
                name=VplanName("basement"),
                devices=[
                    Device(
                        room=SmartThingsId("Basement"),
                        device=SmartThingsId("Lamp Under Window"),
                        component=SmartThingsId("rightOutlet"),
                    ),
                ],
                triggers=[
                    Trigger(
                        days=[TriggerDay("friday"), TriggerDay("weekend")],
                        on_time=TriggerTime("19:45"),
                        off_time=TriggerTime("midnight"),
                        variation=TriggerVariation("+/- 45 minutes"),
                    ),
                ],
            ),
        ],
    ),
)

DEVICES_EXPECTED_V100 = [
    Device(room=SmartThingsId("Living Room"), device=SmartThingsId("Sofa Table Lamp"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Living Room"), device=SmartThingsId("China Cabinet"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Ken's Office"), device=SmartThingsId("Desk Lamp"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Julie's Office"), device=SmartThingsId("Dresser Lamp"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Basement"), device=SmartThingsId("Lamp Under Window"), component=SmartThingsId("main")),
]

DEVICES_EXPECTED_V110 = [
    Device(room=SmartThingsId("Living Room"), device=SmartThingsId("Sofa Table Lamp"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Living Room"), device=SmartThingsId("China Cabinet"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Ken's Office"), device=SmartThingsId("Desk Lamp"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Julie's Office"), device=SmartThingsId("Dresser Lamp"), component=SmartThingsId("main")),
    Device(room=SmartThingsId("Basement"), device=SmartThingsId("Lamp Under Window"), component=SmartThingsId("rightOutlet")),
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
    def test_parsing_valid_v100(self):
        schema = parse_yaml_file_as(PlanSchema, VALID_PLAN_FILE_V100)
        assert schema == PLAN_EXPECTED_V100
        assert schema.devices() == DEVICES_EXPECTED_V100
        assert schema.devices("first-floor-lights") == schema.plan.groups[0].devices

    def test_parsing_valid_v110(self):
        schema = parse_yaml_file_as(PlanSchema, VALID_PLAN_FILE_V110)
        assert schema == PLAN_EXPECTED_V110
        assert schema.devices() == DEVICES_EXPECTED_V110
        assert schema.devices("first-floor-lights") == schema.plan.groups[0].devices

    def test_parsing_invalid_minimum_version(self):
        with pytest.raises(ValueError, match=r"Invalid plan schema version"):
            parse_yaml_file_as(PlanSchema, INVALID_PLAN_FILE_MIN_VER)

    def test_parsing_invalid_maximum_version(self):
        with pytest.raises(ValueError, match=r"Invalid plan schema version"):
            parse_yaml_file_as(PlanSchema, INVALID_PLAN_FILE_MIN_VER)

    def test_parsing_invalid_bad_syntax(self):
        with pytest.raises(ValueError, match=r"2 validation errors for PlanSchema"):
            parse_yaml_file_as(PlanSchema, INVALID_PLAN_FILE_BAD_SYNTAX)
