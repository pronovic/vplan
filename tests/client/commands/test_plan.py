# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner, Result

from vplan.client.cli import vplan as command
from vplan.interface import DeviceGroup, Plan, PlanSchema, Status


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "..", "fixtures", "interface", filename)


# noinspection PyTypeChecker
def invoke(args: List[str]) -> Result:
    return CliRunner().invoke(command, ["plan"] + args)


class TestCommon:
    def test_h(self):
        result = invoke(["-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["--help"])
        assert result.exit_code == 0

    @patch("importlib.metadata.version")  # this is used underneath by @click.version_option()
    def test_version(self, version):
        version.return_value = "1234"
        result = invoke(["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("vplan, version 1234")

    def test_no_args(self):
        result = invoke([])
        assert result.exit_code == 0


class TestCreate:
    def test_h(self):
        result = invoke(["create", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["create", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.create_plan")
    @patch("vplan.client.commands.plan.sys")
    def test_command_stdin(self, sys, create_plan):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        sys.stdin = MagicMock()
        sys.stdin.read = MagicMock()
        sys.stdin.read.return_value = schema.yaml()
        result = invoke(["create", "-"])
        assert result.exit_code == 0
        assert result.output == "Created plan: name\n"
        create_plan.assert_called_once_with(schema)

    @patch("vplan.client.commands.plan.create_plan")
    def test_command_file(self, create_plan, tmpdir):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        p = tmpdir.join("plan.yaml")
        p.write(schema.yaml())
        result = invoke(["create", "%s" % p])
        assert result.exit_code == 0
        assert result.output == "Created plan: name\n"
        create_plan.assert_called_once_with(schema)

    @patch("vplan.client.commands.plan.create_plan")
    def test_command_file_invalid(self, create_plan):
        p = fixture("bad.yaml")
        result = invoke(["create", p])
        assert result.exit_code == 1
        assert (
            result.output
            == r"""Error: 2 validation errors for PlanSchema
plan -> refresh_time
  string does not match regex "^((\d{2}):(\d{2}))$" (type=value_error.str.regex; pattern=^((\d{2}):(\d{2}))$)
plan -> groups -> 0 -> name
  string does not match regex "^[a-z0-9-]+$" (type=value_error.str.regex; pattern=^[a-z0-9-]+$)
"""
        )
        create_plan.assert_not_called()


class TestDelete:
    def test_h(self):
        result = invoke(["delete", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["delete", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.delete_plan")
    def test_command(self, delete_plan):
        result = invoke(["delete", "xxx"])
        assert result.exit_code == 0
        assert result.output == "Deleted plan: xxx\n"
        delete_plan.assert_called_once_with("xxx")


class TestDisable:
    def test_h(self):
        result = invoke(["disable", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["disable", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.retrieve_plan_status")
    @patch("vplan.client.commands.plan.update_plan_status")
    def test_command(self, update_plan_status, retrieve_plan_status):
        retrieve_plan_status.return_value = Status(enabled=False)
        result = invoke(["disable", "xxx"])
        assert result.exit_code == 0
        assert result.output == "Plan xxx is disabled\n"
        update_plan_status.assert_called_once_with("xxx", Status(enabled=False))


class TestEnable:
    def test_h(self):
        result = invoke(["enable", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["enable", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.retrieve_plan_status")
    @patch("vplan.client.commands.plan.update_plan_status")
    def test_command(self, update_plan_status, retrieve_plan_status):
        retrieve_plan_status.return_value = Status(enabled=True)
        result = invoke(["enable", "xxx"])
        assert result.exit_code == 0
        assert result.output == "Plan xxx is enabled\n"
        update_plan_status.assert_called_once_with("xxx", Status(enabled=True))


class TestExport:
    def test_h(self):
        result = invoke(["export", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["export", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_command_not_found(self, retrieve_plan):
        retrieve_plan.return_value = None
        result = invoke(["export", "plan-name"])
        assert result.exit_code == 1
        assert "Plan does not exist: plan-name" in result.output
        retrieve_plan.assert_called_once_with("plan-name")

    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_command_stdout(self, retrieve_plan):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        retrieve_plan.return_value = schema
        result = invoke(["export", "plan-name"])
        assert result.exit_code == 0
        assert result.output == "%s\n" % schema.yaml()
        retrieve_plan.assert_called_once_with("plan-name")

    @pytest.mark.parametrize(
        "option",
        ["--output", "-o"],
    )
    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_command_file(self, retrieve_plan, option, tmpdir):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        retrieve_plan.return_value = schema
        p = tmpdir.join("plan.yaml").realpath()
        result = invoke(["export", "plan-name", option, p])
        assert result.exit_code == 0
        assert result.output == "Plan written to: %s\n" % p
        assert p.read() == schema.yaml()
        retrieve_plan.assert_called_once_with("plan-name")


class TestList:
    def test_h(self):
        result = invoke(["list", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["list", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.retrieve_all_plans")
    def test_command(self, retrieve_all_plans):
        retrieve_all_plans.return_value = ["a", "b", "c"]
        result = invoke(["list"])
        assert result.exit_code == 0
        assert result.output == "a\nb\nc\n"


class TestRefresh:
    def test_h(self):
        result = invoke(["refresh", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["refresh", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.refresh_plan")
    def test_command(self, refresh_plan):
        result = invoke(["refresh", "xxx"])
        assert result.exit_code == 0
        assert result.output == "Refreshed plan: xxx\n"
        refresh_plan.assert_called_once_with("xxx")


class TestShow:
    def test_h(self):
        result = invoke(["show", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["show", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_command_not_found(self, retrieve_plan):
        retrieve_plan.return_value = None
        result = invoke(["show", "plan-name"])
        assert result.exit_code == 1
        assert "Plan does not exist: plan-name" in result.output
        retrieve_plan.assert_called_once_with("plan-name")

    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_command_found(self, retrieve_plan):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        retrieve_plan.return_value = schema
        result = invoke(["show", "plan-name"])
        assert result.exit_code == 0
        assert (
            result.output
            == """Schema.....: 1.0.0
Plan name..: name
Location...: location
Groups.....: 0
"""
        )
        retrieve_plan.assert_called_once_with("plan-name")


class TestStatus:
    def test_h(self):
        result = invoke(["status", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["status", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.retrieve_plan_status")
    def test_command_does_not_exist(self, retrieve_plan_status):
        retrieve_plan_status.return_value = None
        result = invoke(["status", "xxx"])
        assert result.exit_code == 0
        assert result.output == "Plan does not exist: xxx\n"

    @pytest.mark.parametrize(
        "enabled,output",
        [
            (True, "Plan xxx is enabled\n"),
            (False, "Plan xxx is disabled\n"),
        ],
        ids=["enabled", "disabled"],
    )
    @patch("vplan.client.commands.plan.retrieve_plan_status")
    def test_command_exists(self, retrieve_plan_status, enabled, output):
        retrieve_plan_status.return_value = Status(enabled=enabled)
        result = invoke(["status", "xxx"])
        assert result.exit_code == 0
        assert result.output == output


class TestTest:
    def test_h(self):
        result = invoke(["test", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["test", "--help"])
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "option",
        ["--device", "-d"],
    )
    @patch("vplan.client.commands.plan.toggle_device")
    def test_specific_device(self, toggle_device, option):
        result = invoke(["test", "xxx", option, "room/device"])
        assert result.exit_code == 0
        assert result.output == "Testing device: room/device/main\n"
        toggle_device.assert_called_once_with("xxx", "room", "device", "main", 2, 5)

    @pytest.mark.parametrize(
        "option",
        ["--device", "-d"],
    )
    @patch("vplan.client.commands.plan.toggle_device")
    def test_specific_device_with_component(self, toggle_device, option):
        result = invoke(["test", "xxx", option, "room/device/component"])
        assert result.exit_code == 0
        assert result.output == "Testing device: room/device/component\n"
        toggle_device.assert_called_once_with("xxx", "room", "device", "component", 2, 5)

    @pytest.mark.parametrize(
        "value",
        ["", "room"],
    )
    def test_specific_device_invalid(self, value):
        result = invoke(["test", "xxx", "-d", value])
        assert result.exit_code == 2
        assert "Device path must be either <room>/<device> or <room>/<device>/<component>" in result.output

    @pytest.mark.parametrize(
        "option",
        ["--group", "-g"],
    )
    @patch("vplan.client.commands.plan.toggle_group")
    def test_specific_group(self, toggle_group, option):
        result = invoke(["test", "xxx", option, "group"])
        assert result.exit_code == 0
        assert result.output == "Testing group: group\n"
        toggle_group.assert_called_once_with("xxx", "group", 2, 5)

    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_not_found(self, retrieve_plan):
        retrieve_plan.return_value = None
        result = invoke(["test", "xxx"])
        assert result.exit_code == 1
        assert "Plan does not exist: xxx" in result.output
        retrieve_plan.assert_called_once_with("xxx")

    @patch("vplan.client.commands.plan.click.confirm")
    @patch("vplan.client.commands.plan.toggle_group")
    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_entire_plan(self, retrieve_plan, toggle_group, confirm):
        groups = [DeviceGroup(name="group", devices=[], triggers=[])]
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=groups))
        retrieve_plan.return_value = schema
        result = invoke(["test", "xxx"])
        assert result.exit_code == 0
        assert (
            result.output
            == """Testing entire plan.
Toggles per device: 2
Delay between toggles: 5 seconds

"""
        )
        retrieve_plan.assert_called_once_with("xxx")
        toggle_group.assert_called_once_with("xxx", "group", 2, 5)
        confirm.assert_called_once_with("Press enter to test group group", show_default=False, prompt_suffix="")

    @pytest.mark.parametrize(
        "option",
        ["--auto", "-a"],
    )
    @patch("vplan.client.commands.plan.toggle_group")
    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_entire_plan_auto(self, retrieve_plan, toggle_group, option):
        groups = [DeviceGroup(name="group", devices=[], triggers=[])]
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=groups))
        retrieve_plan.return_value = schema
        result = invoke(["test", "xxx", option])
        assert result.exit_code == 0
        assert (
            result.output
            == """Testing entire plan.
Toggles per device: 2
Delay between toggles: 5 seconds

Testing group: group
"""
        )
        retrieve_plan.assert_called_once_with("xxx")
        toggle_group.assert_called_once_with("xxx", "group", 2, 5)

    @pytest.mark.parametrize(
        "option",
        ["--toggles", "-t"],
    )
    @patch("vplan.client.commands.plan.click.confirm")
    @patch("vplan.client.commands.plan.toggle_group")
    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_entire_plan_toggles(self, retrieve_plan, toggle_group, confirm, option):
        groups = [DeviceGroup(name="group", devices=[], triggers=[])]
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=groups))
        retrieve_plan.return_value = schema
        result = invoke(["test", "xxx", option, "99"])
        assert result.exit_code == 0
        assert (
            result.output
            == """Testing entire plan.
Toggles per device: 99
Delay between toggles: 5 seconds

"""
        )
        retrieve_plan.assert_called_once_with("xxx")
        toggle_group.assert_called_once_with("xxx", "group", 99, 5)
        confirm.assert_called_once_with("Press enter to test group group", show_default=False, prompt_suffix="")

    @pytest.mark.parametrize(
        "option",
        ["--delay-sec", "-s"],
    )
    @patch("vplan.client.commands.plan.click.confirm")
    @patch("vplan.client.commands.plan.toggle_group")
    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_entire_plan_delay(self, retrieve_plan, toggle_group, confirm, option):
        groups = [DeviceGroup(name="group", devices=[], triggers=[])]
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=groups))
        retrieve_plan.return_value = schema
        result = invoke(["test", "xxx", option, "99"])
        assert result.exit_code == 0
        assert (
            result.output
            == """Testing entire plan.
Toggles per device: 2
Delay between toggles: 99 seconds

"""
        )
        retrieve_plan.assert_called_once_with("xxx")
        toggle_group.assert_called_once_with("xxx", "group", 2, 99)
        confirm.assert_called_once_with("Press enter to test group group", show_default=False, prompt_suffix="")


class TestUpdate:
    def test_h(self):
        result = invoke(["update", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["update", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.plan.update_plan")
    @patch("vplan.client.commands.plan.sys")
    def test_command_stdin(self, sys, update_plan):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        sys.stdin = MagicMock()
        sys.stdin.read = MagicMock()
        sys.stdin.read.return_value = schema.yaml()
        result = invoke(["update", "-"])
        assert result.exit_code == 0
        assert result.output == "Updated plan: name\n"
        update_plan.assert_called_once_with(schema)

    @patch("vplan.client.commands.plan.update_plan")
    def test_command_file(self, update_plan, tmpdir):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        p = tmpdir.join("plan.yaml")
        p.write(schema.yaml())
        result = invoke(["update", "%s" % p])
        assert result.exit_code == 0
        assert result.output == "Updated plan: name\n"
        update_plan.assert_called_once_with(schema)

    @patch("vplan.client.commands.plan.update_plan")
    def test_command_file_invalid(self, update_plan):
        p = fixture("bad.yaml")
        result = invoke(["update", p])
        assert result.exit_code == 1
        assert (
            result.output
            == r"""Error: 2 validation errors for PlanSchema
plan -> refresh_time
  string does not match regex "^((\d{2}):(\d{2}))$" (type=value_error.str.regex; pattern=^((\d{2}):(\d{2}))$)
plan -> groups -> 0 -> name
  string does not match regex "^[a-z0-9-]+$" (type=value_error.str.regex; pattern=^[a-z0-9-]+$)
"""
        )
        update_plan.assert_not_called()


class TestOn:
    def test_h(self):
        result = invoke(["on", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["on", "--help"])
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "option",
        ["--device", "-d"],
    )
    @patch("vplan.client.commands.plan.turn_on_device")
    def test_specific_device(self, turn_on_device, option):
        result = invoke(["on", "xxx", option, "room/device"])
        assert result.exit_code == 0
        assert result.output == "Turning on device: room/device/main\n"
        turn_on_device.assert_called_once_with("xxx", "room", "device", "main")

    @pytest.mark.parametrize(
        "option",
        ["--device", "-d"],
    )
    @patch("vplan.client.commands.plan.turn_on_device")
    def test_specific_device_with_component(self, turn_on_device, option):
        result = invoke(["on", "xxx", option, "room/device/component"])
        assert result.exit_code == 0
        assert result.output == "Turning on device: room/device/component\n"
        turn_on_device.assert_called_once_with("xxx", "room", "device", "component")

    @pytest.mark.parametrize(
        "value",
        ["", "room"],
    )
    def test_specific_device_invalid(self, value):
        result = invoke(["on", "xxx", "-d", value])
        assert result.exit_code == 2
        assert "Device path must be either <room>/<device> or <room>/<device>/<component>" in result.output

    @pytest.mark.parametrize(
        "option",
        ["--group", "-g"],
    )
    @patch("vplan.client.commands.plan.turn_on_group")
    def test_specific_group(self, turn_on_group, option):
        result = invoke(["on", "xxx", option, "group"])
        assert result.exit_code == 0
        assert result.output == "Turning on group: group\n"
        turn_on_group.assert_called_once_with(
            "xxx",
            "group",
        )

    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_not_found(self, retrieve_plan):
        retrieve_plan.return_value = None
        result = invoke(["on", "xxx"])
        assert result.exit_code == 1
        assert "Plan does not exist: xxx" in result.output
        retrieve_plan.assert_called_once_with("xxx")

    @patch("vplan.client.commands.plan.turn_on_group")
    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_entire_plan(self, retrieve_plan, turn_on_group):
        groups = [DeviceGroup(name="group", devices=[], triggers=[])]
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=groups))
        retrieve_plan.return_value = schema
        result = invoke(["on", "xxx"])
        assert result.exit_code == 0
        assert (
            result.output
            == """Turning on entire plan.
"""
        )
        retrieve_plan.assert_called_once_with("xxx")
        turn_on_group.assert_called_once_with("xxx", "group")


class TestOff:
    def test_h(self):
        result = invoke(["off", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["off", "--help"])
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "option",
        ["--device", "-d"],
    )
    @patch("vplan.client.commands.plan.turn_off_device")
    def test_specific_device(self, turn_off_device, option):
        result = invoke(["off", "xxx", option, "room/device"])
        assert result.exit_code == 0
        assert result.output == "Turning off device: room/device/main\n"
        turn_off_device.assert_called_once_with("xxx", "room", "device", "main")

    @pytest.mark.parametrize(
        "option",
        ["--device", "-d"],
    )
    @patch("vplan.client.commands.plan.turn_off_device")
    def test_specific_device_with_component(self, turn_off_device, option):
        result = invoke(["off", "xxx", option, "room/device/component"])
        assert result.exit_code == 0
        assert result.output == "Turning off device: room/device/component\n"
        turn_off_device.assert_called_once_with("xxx", "room", "device", "component")

    @pytest.mark.parametrize(
        "value",
        ["", "room"],
    )
    def test_specific_device_invalid(self, value):
        result = invoke(["off", "xxx", "-d", value])
        assert result.exit_code == 2
        assert "Device path must be either <room>/<device> or <room>/<device>/<component>" in result.output

    @pytest.mark.parametrize(
        "option",
        ["--group", "-g"],
    )
    @patch("vplan.client.commands.plan.turn_off_group")
    def test_specific_group(self, turn_off_group, option):
        result = invoke(["off", "xxx", option, "group"])
        assert result.exit_code == 0
        assert result.output == "Turning off group: group\n"
        turn_off_group.assert_called_once_with(
            "xxx",
            "group",
        )

    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_not_found(self, retrieve_plan):
        retrieve_plan.return_value = None
        result = invoke(["off", "xxx"])
        assert result.exit_code == 1
        assert "Plan does not exist: xxx" in result.output
        retrieve_plan.assert_called_once_with("xxx")

    @patch("vplan.client.commands.plan.turn_off_group")
    @patch("vplan.client.commands.plan.retrieve_plan")
    def test_entire_plan(self, retrieve_plan, turn_off_group):
        groups = [DeviceGroup(name="group", devices=[], triggers=[])]
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=groups))
        retrieve_plan.return_value = schema
        result = invoke(["off", "xxx"])
        assert result.exit_code == 0
        assert (
            result.output
            == """Turning off entire plan.
"""
        )
        retrieve_plan.assert_called_once_with("xxx")
        turn_off_group.assert_called_once_with("xxx", "group")
