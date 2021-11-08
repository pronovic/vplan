# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import pytest

from vplan.engine.interface import Account, Device, DeviceGroup, Health, Plan, ServerException, Trigger, Version


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
            ([], "midnight", "noon", "none"),
            ([], "sunrise", "noon", "disabled"),
            ([], "00:00", "23:59", "Disabled"),
            ([], "00:00", "23:59", "+ 5 minutes"),
            ([], "00:00", "23:59", "- 2 HOURS"),
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
        assert trigger.days == [day.lower() for day in days]
        assert trigger.on_time == on_time.lower()
        assert trigger.off_time == off_time.lower()
        assert trigger.variation == variation.lower()

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

    def test_device_valid(self):
        model = Device(name="name", room="room")
        assert model.name == "name"
        assert model.room == "room"

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

    def test_device_group_valid(self):
        model = DeviceGroup(name="name", devices=[], triggers=[])
        assert model.name == "name"
        assert model.devices == []
        assert model.triggers == []

    @pytest.mark.parametrize(
        "name",
        ["", None],
        ids=["empty name", "no name"],
    )
    def test_device_group_invalid(self, name):
        with pytest.raises(ValueError):
            DeviceGroup(name=name, devices=[], triggers=[])

    def test_plan_valid(self):
        model = Plan(name="name", location="location", groups=[])
        assert model.name == "name"
        assert model.location == "location"
        assert model.groups == []

    @pytest.mark.parametrize(
        "name,location",
        [
            ("", "location"),
            (None, "location"),
            ("name", ""),
            ("name", None),
        ],
        ids=["empty name", "no name", "empty room", "no room"],
    )
    def test_plan_invalid(self, name, location):
        with pytest.raises(ValueError):
            Plan(name=name, location=location, groups=[])

    def test_account_valid(self):
        model = Account(name="name", pat_token="token")
        assert model.name == "name"
        assert model.pat_token == "token"

    @pytest.mark.parametrize(
        "name,pat_token",
        [
            ("", "token"),
            (None, "token"),
            ("name", ""),
            ("name", None),
        ],
        ids=["empty name", "no name", "empty token", "no token"],
    )
    def test_account_invalid(self, name, pat_token):
        with pytest.raises(ValueError):
            Account(name=name, pat_token=pat_token)
