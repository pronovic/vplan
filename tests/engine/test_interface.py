# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import pytest

from vplan.engine.interface import Account, Device, DeviceGroup, Health, Plan, ServerException, Trigger, Version

VALID_NAME = "abcd-1234-efgh-5678-ijkl-9012-mnop-3456-qrst-7890"
TOO_LONG_NAME = "%sX" % VALID_NAME  # one carhacter too long


class TestExceptions:

    """Test exception classes."""

    def test_server_exception(self):
        exception = ServerException("hello")
        assert isinstance(exception, Exception)  # make sure parent class is right
        assert exception.message == "hello"


class TestModels:

    """Test model classes."""

    def test_health(self):
        model = Health()
        assert model.status == "OK"

    def test_version(self):
        model = Version(package="a", api="b")
        assert model.package == "a"
        assert model.api == "b"

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
        "name,room",
        [
            ("n", "r"),
            (" n ", " r "),
            ("name", "room"),
        ],
        ids=["short", "whitespace", "normal"],
    )
    def test_device_valid(self, name, room):
        model = Device(name=name, room=room)
        assert model.name == name
        assert model.room == room

    @pytest.mark.parametrize(
        "name,room",
        [
            ("", "room"),
            (None, "room"),
            ("name", ""),
            ("name", None),
        ],
        ids=["empty name", "no name", "empty room", "no room"],
    )
    def test_device_invalid(self, name, room):
        with pytest.raises(ValueError):
            Device(name=name, room=room)

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
        "name,location",
        [
            ("n", "l"),
            (" n ", " l "),
            (VALID_NAME, "location"),
        ],
        ids=["short", "whitespace", "long"],
    )
    def test_plan_valid(self, name, location):
        model = Plan(name=name, location=location, groups=[])
        assert model.name == name.strip()
        assert model.location == location  # not stripped, it's a SmartThings identifier
        assert model.groups == []

    @pytest.mark.parametrize(
        "name,location",
        [
            ("", "location"),
            (None, "location"),
            (TOO_LONG_NAME, "location"),
            ("name", ""),
            ("name", None),
        ],
        ids=["empty name", "no name", "long name", "empty room", "no room"],
    )
    def test_plan_invalid(self, name, location):
        with pytest.raises(ValueError):
            Plan(name=name, location=location, groups=[])

    @pytest.mark.parametrize(
        "name,pat_token",
        [
            ("n", "t"),
            (" n ", " t "),
            (VALID_NAME, "token"),
        ],
        ids=["short", "whitespace", "long"],
    )
    def test_account_valid(self, name, pat_token):
        model = Account(name=name, pat_token=pat_token)
        assert model.name == name.strip()
        assert model.pat_token == pat_token  # not stripped, it's a SmartThings identifier

    @pytest.mark.parametrize(
        "name,pat_token",
        [
            ("", "token"),
            (None, "token"),
            (TOO_LONG_NAME, "token"),
            ("name", ""),
            ("name", None),
        ],
        ids=["empty name", "no name", "long name", "empty token", "no token"],
    )
    def test_account_invalid(self, name, pat_token):
        with pytest.raises(ValueError):
            Account(name=name, pat_token=pat_token)
