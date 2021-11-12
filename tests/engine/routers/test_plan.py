# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import NoResultFound

from vplan.engine.interface import AlreadyExistsError, Plan, PlanSchema, Status
from vplan.engine.server import API

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
        assert PlanSchema.parse_raw(response.text) == schema
        db_retrieve_plan.assert_called_once_with(plan_name="xxx")

    @patch("vplan.engine.routers.plan.st_schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.db_create_plan")
    def test_create_plan(self, db_create_plan, st_schedule_daily_refresh):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        response = CLIENT.post(url="/plan", data=schema.json())
        assert response.status_code == 201
        assert not response.text
        db_create_plan.assert_called_once_with(schema=schema)
        st_schedule_daily_refresh.assert_called_once_with(plan_name="name", refresh_time="00:30", time_zone="UTC")

    @patch("vplan.engine.routers.plan.st_schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.db_create_plan")
    def test_create_plan_duplicate(self, db_create_plan, st_schedule_daily_refresh):
        db_create_plan.side_effect = AlreadyExistsError("hello")
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        response = CLIENT.post(url="/plan", data=schema.json())
        assert response.status_code == 409
        assert not response.text
        db_create_plan.assert_called_once_with(schema=schema)
        st_schedule_daily_refresh.assert_not_called()

    @pytest.mark.parametrize("enabled", [True, False])
    @patch("vplan.engine.routers.plan.st_schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.st_schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.db_retrieve_plan_enabled")
    @patch("vplan.engine.routers.plan.db_update_plan")
    def test_update_plan(
        self, db_update_plan, db_retrieve_plan_enabled, st_schedule_daily_refresh, st_schedule_immediate_refresh, enabled
    ):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_retrieve_plan_enabled.return_value = enabled
        response = CLIENT.put(url="/plan", data=schema.json())
        assert response.status_code == 204
        assert not response.text
        db_update_plan.assert_called_once_with(schema=schema)
        st_schedule_daily_refresh.assert_called_once_with(plan_name="name", refresh_time="00:30", time_zone="UTC")
        db_retrieve_plan_enabled.assert_called_once_with(plan_name="name")
        if enabled:
            st_schedule_immediate_refresh.assert_called_once_with(plan_name="name")
        else:
            st_schedule_immediate_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.st_schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.st_schedule_daily_refresh")
    @patch("vplan.engine.routers.plan.db_retrieve_plan_enabled")
    @patch("vplan.engine.routers.plan.db_update_plan")
    def test_update_plan_not_found(
        self, db_update_plan, db_retrieve_plan_enabled, st_schedule_daily_refresh, st_schedule_immediate_refresh
    ):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
        db_update_plan.side_effect = NoResultFound("hello")
        response = CLIENT.put(url="/plan", data=schema.json())
        assert response.status_code == 404
        assert not response.text
        db_update_plan.assert_called_once_with(schema=schema)
        st_schedule_daily_refresh.assert_not_called()
        db_retrieve_plan_enabled.assert_not_called()
        st_schedule_immediate_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.st_schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.st_unschedule_daily_refresh")
    @patch("vplan.engine.routers.plan.db_delete_plan")
    def test_delete_plan(self, db_delete_plan, st_unschedule_daily_refresh, st_schedule_immediate_refresh):
        response = CLIENT.delete(url="/plan/name")
        assert response.status_code == 204
        assert not response.text
        st_unschedule_daily_refresh.assert_called_once_with(plan_name="name")
        st_schedule_immediate_refresh.assert_called_once_with(plan_name="name")
        db_delete_plan.assert_called_once_with(plan_name="name")

    @patch("vplan.engine.routers.plan.st_schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.st_unschedule_daily_refresh")
    @patch("vplan.engine.routers.plan.db_delete_plan")
    def test_delete_plan_not_found(self, db_delete_plan, st_unschedule_daily_refresh, st_schedule_immediate_refresh):
        db_delete_plan.side_effect = NoResultFound("hello")
        response = CLIENT.delete(url="/plan/name")
        assert response.status_code == 404
        assert not response.text
        st_unschedule_daily_refresh.assert_called_once_with(plan_name="name")
        st_schedule_immediate_refresh.assert_called_once_with(plan_name="name")
        db_delete_plan.assert_called_once_with(plan_name="name")

    @pytest.mark.parametrize("enabled", [True, False])
    @patch("vplan.engine.routers.plan.db_retrieve_plan_enabled")
    def test_retrieve_status(self, db_retrieve_plan_enabled, enabled):
        db_retrieve_plan_enabled.return_value = enabled
        response = CLIENT.get(url="/plan/name/status")
        assert response.status_code == 200
        assert Status.parse_raw(response.text) == Status(enabled=enabled)
        db_retrieve_plan_enabled.assert_called_once_with(plan_name="name")

    @patch("vplan.engine.routers.plan.db_retrieve_plan_enabled")
    def test_retrieve_status_not_found(self, db_retrieve_plan_enabled):
        db_retrieve_plan_enabled.side_effect = NoResultFound("hello")
        response = CLIENT.get(url="/plan/name/status")
        assert response.status_code == 404
        assert not response.text
        db_retrieve_plan_enabled.assert_called_once_with(plan_name="name")

    @pytest.mark.parametrize("enabled", [True, False])
    @patch("vplan.engine.routers.plan.st_schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_update_plan_enabled")
    def test_update_status(self, db_update_plan_enabled, st_schedule_immediate_refresh, enabled):
        status = Status(enabled=enabled)
        response = CLIENT.put(url="/plan/name/status", data=status.json())
        assert response.status_code == 204
        assert not response.text
        db_update_plan_enabled.assert_called_once_with(plan_name="name", enabled=enabled)
        st_schedule_immediate_refresh.assert_called_once_with(plan_name="name")

    @patch("vplan.engine.routers.plan.st_schedule_immediate_refresh")
    @patch("vplan.engine.routers.plan.db_update_plan_enabled")
    def test_update_status_not_found(self, db_update_plan_enabled, st_schedule_immediate_refresh):
        db_update_plan_enabled.side_effect = NoResultFound("hello")
        status = Status(enabled=True)
        response = CLIENT.put(url="/plan/name/status", data=status.json())
        assert response.status_code == 404
        assert not response.text
        db_update_plan_enabled.assert_called_once_with(plan_name="name", enabled=True)
        st_schedule_immediate_refresh.assert_not_called()

    @patch("vplan.engine.routers.plan.st_schedule_immediate_refresh")
    def test_refresh_plan(self, st_schedule_immediate_refresh):
        response = CLIENT.post(url="/plan/name/refresh")
        assert response.status_code == 204
        assert not response.text
        st_schedule_immediate_refresh.assert_called_once_with(plan_name="name")

    @pytest.mark.parametrize("params,count", [({}, 2), ({"toggle_count": 4}, 4)], ids=["no param", "with param"])
    @patch("vplan.engine.routers.plan.st_toggle_group")
    def test_toggle_group(self, st_toggle_group, params, count):
        response = CLIENT.post(url="/plan/xxx/test/group/yyy", params=params)
        assert response.status_code == 204
        assert not response.text
        st_toggle_group.assert_called_once_with(plan_name="xxx", group_name="yyy", toggle_count=count)

    @pytest.mark.parametrize("params,count", [({}, 2), ({"toggle_count": 4}, 4)], ids=["no param", "with param"])
    @patch("vplan.engine.routers.plan.st_toggle_device")
    def test_toggle_device(self, st_toggle_device, params, count):
        response = CLIENT.post(url="/plan/xxx/test/device/yyy/zzz", params=params)
        assert response.status_code == 204
        assert not response.text
        st_toggle_device.assert_called_once_with(plan_name="xxx", room="yyy", device="zzz", toggle_count=count)
