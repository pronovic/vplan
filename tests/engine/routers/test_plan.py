# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=too-many-public-methods:

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic_yaml import parse_yaml_raw_as
from sqlalchemy.exc import IntegrityError, NoResultFound

from vplan.engine.exception import InvalidPlanError
from vplan.engine.server import API
from vplan.interface import Device, Plan, PlanSchema, Status, SwitchState

CLIENT = TestClient(API)

PLAN_URL = "/plan"


class TestRoutes:
    @patch("vplan.engine.routers.plan.db_retrieve_all_plans")
    def test_retrieve_all_plans(self, db_retrieve_all_plans):
        plans = ["a"]
        db_retrieve_all_plans.return_value = plans
        response = CLIENT.get(url="/plan")
        assert response.status_code == 200
        assert response.json() == plans

    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_retrieve_plan(self, db_retrieve_plan):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_retrieve_plan.return_value = schema
        response = CLIENT.get(url="/plan/xxx")
        assert response.status_code == 200
        assert parse_yaml_raw_as(PlanSchema, response.text) == schema
        db_retrieve_plan.assert_called_once_with(plan_name="xxx")

    @patch("vplan.engine.routers.plan.schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_create_plan")
    @patch("vplan.engine.routers.plan.validate_plan")
    def test_create_plan(self, validate_plan, db_create_plan, schedule_immediate_refresh, schedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        response = CLIENT.post(url="/plan", content=schema.model_dump_json())
        assert response.status_code == 201
        assert not response.text
        validate_plan.assert_called_once_with(schema=schema)
        db_create_plan.assert_called_once_with(schema=schema)
        schedule_immediate_refresh.assert_called_once_with(plan_name="name", location="location")
        schedule_daily_refresh.assert_called_once_with(plan_name="name", location="location", refresh_time="00:30", time_zone="UTC")

    @patch("vplan.engine.routers.plan.schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_create_plan")
    @patch("vplan.engine.routers.plan.validate_plan")
    def test_create_plan_invalid(self, validate_plan, db_create_plan, schedule_immediate_refresh, schedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        validate_plan.side_effect = InvalidPlanError("error")
        response = CLIENT.post(url="/plan", content=schema.model_dump_json())
        assert response.status_code == 422
        assert not response.text
        validate_plan.assert_called_once_with(schema=schema)
        db_create_plan.assert_not_called()
        schedule_immediate_refresh.assert_not_called()
        schedule_daily_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_create_plan")
    @patch("vplan.engine.routers.plan.validate_plan")
    def test_create_plan_duplicate(self, validate_plan, db_create_plan, schedule_immediate_refresh, schedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_create_plan.side_effect = IntegrityError("x", "y", "z")
        response = CLIENT.post(url="/plan", content=schema.model_dump_json())
        assert response.status_code == 409
        assert not response.text
        validate_plan.assert_called_once_with(schema=schema)
        db_create_plan.assert_called_once_with(schema=schema)
        schedule_immediate_refresh.assert_not_called()
        schedule_daily_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_update_plan")
    @patch("vplan.engine.routers.plan.validate_plan")
    def test_update_plan(self, validate_plan, db_update_plan, schedule_immediate_refresh, schedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        response = CLIENT.put(url="/plan", content=schema.model_dump_json())
        assert response.status_code == 204
        assert not response.text
        validate_plan.assert_called_once_with(schema=schema)
        db_update_plan.assert_called_once_with(schema=schema)
        schedule_immediate_refresh.assert_called_once_with(plan_name="name", location="location")
        schedule_daily_refresh.assert_called_once_with(plan_name="name", location="location", refresh_time="00:30", time_zone="UTC")

    @patch("vplan.engine.routers.plan.schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_update_plan")
    @patch("vplan.engine.routers.plan.validate_plan")
    def test_update_plan_invalid(self, validate_plan, db_update_plan, schedule_immediate_refresh, schedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        validate_plan.side_effect = InvalidPlanError("error")
        response = CLIENT.put(url="/plan", content=schema.model_dump_json())
        assert response.status_code == 422
        assert not response.text
        validate_plan.assert_called_once_with(schema=schema)
        db_update_plan.assert_not_called()
        schedule_immediate_refresh.assert_not_called()
        schedule_daily_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_update_plan")
    @patch("vplan.engine.routers.plan.validate_plan")
    def test_update_plan_not_found(self, validate_plan, db_update_plan, schedule_immediate_refresh, schedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_update_plan.side_effect = NoResultFound("hello")
        response = CLIENT.put(url="/plan", content=schema.model_dump_json())
        assert response.status_code == 404
        assert not response.text
        validate_plan.assert_called_once_with(schema=schema)
        db_update_plan.assert_called_once_with(schema=schema)
        schedule_immediate_refresh.assert_not_called()
        schedule_daily_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.unschedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    @patch("vplan.engine.routers.plan.db_delete_plan")
    def test_delete_plan(self, db_delete_plan, db_retrieve_plan, schedule_immediate_refresh, unschedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_retrieve_plan.return_value = schema
        response = CLIENT.delete(url="/plan/thename")
        assert response.status_code == 204
        assert not response.text
        db_retrieve_plan.assert_called_once_with("thename")
        db_delete_plan.assert_called_once_with(plan_name="name")
        schedule_immediate_refresh.assert_called_once_with(plan_name="name", location="location")
        unschedule_daily_refresh.assert_called_once_with(plan_name="name")

    @patch("vplan.engine.routers.plan.unschedule_daily_refresh")
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    @patch("vplan.engine.routers.plan.db_delete_plan")
    def test_delete_plan_not_found(self, db_delete_plan, db_retrieve_plan, schedule_immediate_refresh, unschedule_daily_refresh):
        db_retrieve_plan.side_effect = NoResultFound("hello")
        response = CLIENT.delete(url="/plan/thename")
        assert response.status_code == 404
        assert not response.text
        db_retrieve_plan.assert_called_once_with("thename")
        db_delete_plan.assert_not_called()
        schedule_immediate_refresh.assert_not_called()
        unschedule_daily_refresh.assert_not_called()

    @pytest.mark.parametrize("enabled", [True, False])
    @patch("vplan.engine.routers.plan.db_retrieve_plan_enabled")
    def test_retrieve_status(self, db_retrieve_plan_enabled, enabled):
        db_retrieve_plan_enabled.return_value = enabled
        response = CLIENT.get(url="/plan/name/status")
        assert response.status_code == 200
        assert parse_yaml_raw_as(Status, response.text) == Status(enabled=enabled)
        db_retrieve_plan_enabled.assert_called_once_with(plan_name="name")

    @patch("vplan.engine.routers.plan.db_retrieve_plan_enabled")
    def test_retrieve_status_not_found(self, db_retrieve_plan_enabled):
        db_retrieve_plan_enabled.side_effect = NoResultFound("hello")
        response = CLIENT.get(url="/plan/name/status")
        assert response.status_code == 404
        assert not response.text
        db_retrieve_plan_enabled.assert_called_once_with(plan_name="name")

    @pytest.mark.parametrize("enabled", [True, False])
    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    @patch("vplan.engine.routers.plan.db_update_plan_enabled")
    def test_update_status(self, db_update_plan_enabled, db_retrieve_plan, schedule_immediate_refresh, enabled):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_retrieve_plan.return_value = schema
        status = Status(enabled=enabled)
        response = CLIENT.put(url="/plan/thename/status", content=status.model_dump_json())
        assert response.status_code == 204
        assert not response.text
        db_retrieve_plan.assert_called_once_with(plan_name="thename")
        db_update_plan_enabled.assert_called_once_with(plan_name="name", enabled=enabled)
        schedule_immediate_refresh.assert_called_once_with(plan_name="name", location="location")

    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    @patch("vplan.engine.routers.plan.db_update_plan_enabled")
    def test_update_status_not_found(self, db_update_plan_enabled, db_retrieve_plan, schedule_immediate_refresh):
        db_retrieve_plan.side_effect = NoResultFound("hello")
        status = Status(enabled=True)
        response = CLIENT.put(url="/plan/thename/status", content=status.model_dump_json())
        assert response.status_code == 404
        assert not response.text
        db_retrieve_plan.assert_called_once_with(plan_name="thename")
        db_update_plan_enabled.assert_not_called()
        schedule_immediate_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_refresh_plan(self, db_retrieve_plan, schedule_immediate_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_retrieve_plan.return_value = schema
        response = CLIENT.post(url="/plan/thename/refresh")
        assert response.status_code == 204
        assert not response.text
        db_retrieve_plan.assert_called_once_with(plan_name="thename")
        schedule_immediate_refresh.assert_called_once_with(plan_name="name", location="location")

    @patch("vplan.engine.routers.plan.toggle_devices")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_toggle_group(
        self,
        db_retrieve_plan,
        toggle_devices,
    ):
        device = Device(room="yyy", device="zzz")
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[device])
        db_retrieve_plan.return_value = schema
        params = {
            "toggles": 4,
            "delay_sec": 10,
        }
        response = CLIENT.post(url="/plan/xxx/test/group/yyy", params=params)
        assert response.status_code == 204
        assert not response.text
        schema.devices.assert_called_once_with(group_name="yyy")
        toggle_devices.assert_called_once_with(location="bbb", devices=[device], toggles=4, delay_sec=10)

    @patch("vplan.engine.routers.plan.toggle_devices")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_toggle_group_not_found(self, db_retrieve_plan, toggle_devices):
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[])
        db_retrieve_plan.return_value = schema
        params = {
            "toggles": 4,
            "delay_sec": 10,
        }
        response = CLIENT.post(url="/plan/xxx/test/group/yyy", params=params)
        assert response.status_code == 404
        assert not response.text
        schema.devices.assert_called_once_with(group_name="yyy")
        toggle_devices.assert_not_called()

    @patch("vplan.engine.routers.plan.toggle_devices")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_toggle_device(self, db_retrieve_plan, toggle_devices):
        device = Device(room="yyy", device="zzz", component="ccc")
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[device])
        db_retrieve_plan.return_value = schema
        params = {
            "toggles": 4,
            "delay_sec": 10,
        }
        response = CLIENT.post(url="/plan/xxx/test/device/yyy/zzz/ccc", params=params)
        assert response.status_code == 204
        assert not response.text
        toggle_devices.assert_called_once_with(location="bbb", devices=[device], toggles=4, delay_sec=10)

    @patch("vplan.engine.routers.plan.toggle_devices")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_toggle_device_not_found(self, db_retrieve_plan, toggle_devices):
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[])  # our device is not in this list, by definition
        db_retrieve_plan.return_value = schema
        params = {
            "toggles": 4,
            "delay_sec": 10,
        }
        response = CLIENT.post(url="/plan/xxx/test/device/yyy/zzz/ccc", params=params)
        assert response.status_code == 404
        assert not response.text
        toggle_devices.assert_not_called()

    @pytest.mark.parametrize("state", ["on", "off"])
    @patch("vplan.engine.routers.plan.set_device_state")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_switch_group(self, db_retrieve_plan, set_device_state, state):
        device = Device(room="yyy", device="zzz")
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[device])
        db_retrieve_plan.return_value = schema
        response = CLIENT.post(url="/plan/xxx/%s/group/yyy" % state)
        assert response.status_code == 204
        assert not response.text
        schema.devices.assert_called_once_with(group_name="yyy")
        set_device_state.assert_called_once_with(location="bbb", devices=[device], state=SwitchState(state))

    @pytest.mark.parametrize("state", ["on", "off"])
    @patch("vplan.engine.routers.plan.set_device_state")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_switch_group_not_found(self, db_retrieve_plan, set_device_state, state):
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[])
        db_retrieve_plan.return_value = schema
        response = CLIENT.post(url="/plan/xxx/%s/group/yyy" % state)
        assert response.status_code == 404
        assert not response.text
        schema.devices.assert_called_once_with(group_name="yyy")
        set_device_state.assert_not_called()

    @pytest.mark.parametrize("state", ["ON", "OFF", "bad"])
    @patch("vplan.engine.routers.plan.set_device_state")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_switch_group_bad_state(self, db_retrieve_plan, set_device_state, state):
        device = Device(room="yyy", device="zzz")
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[device])
        db_retrieve_plan.return_value = schema
        response = CLIENT.post(url="/plan/xxx/%s/group/yyy" % state)
        assert response.status_code == 400
        assert not response.text
        schema.devices.assert_called_once_with(group_name="yyy")
        set_device_state.assert_not_called()

    @pytest.mark.parametrize("state", ["on", "off"])
    @patch("vplan.engine.routers.plan.set_device_state")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_switch_device(self, db_retrieve_plan, set_device_state, state):
        device = Device(room="yyy", device="zzz", component="ccc")
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[device])
        db_retrieve_plan.return_value = schema
        response = CLIENT.post(url="/plan/xxx/%s/device/yyy/zzz/ccc" % state)
        assert response.status_code == 204
        assert not response.text
        set_device_state.assert_called_once_with(location="bbb", devices=[device], state=SwitchState(state))

    @pytest.mark.parametrize("state", ["on", "off"])
    @patch("vplan.engine.routers.plan.set_device_state")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_switch_device_not_found(self, db_retrieve_plan, set_device_state, state):
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[])  # our device is not in this list, by definition
        db_retrieve_plan.return_value = schema
        response = CLIENT.post(url="/plan/xxx/%s/device/yyy/zzz/ccc" % state)
        assert response.status_code == 404
        assert not response.text
        set_device_state.assert_not_called()

    @pytest.mark.parametrize("state", ["ON", "OFF", "bad"])
    @patch("vplan.engine.routers.plan.set_device_state")
    @patch("vplan.engine.routers.plan.db_retrieve_plan")
    def test_switch_device_bad_state(self, db_retrieve_plan, set_device_state, state):
        device = Device(room="yyy", device="zzz", component="ccc")
        plan = MagicMock(location="bbb")
        schema = MagicMock(plan=plan)
        schema.devices = MagicMock(return_value=[device])
        db_retrieve_plan.return_value = schema
        response = CLIENT.post(url="/plan/xxx/%s/device/yyy/zzz/ccc" % state)
        assert response.status_code == 400
        assert not response.text
        set_device_state.assert_not_called()
