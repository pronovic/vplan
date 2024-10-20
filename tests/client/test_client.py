# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=too-many-public-methods:

from unittest.mock import MagicMock, patch

import pytest
import responses
from click import ClickException
from requests import HTTPError, Timeout
from responses import matchers

from vplan.client.client import (
    _raise_for_status,
    create_or_replace_account,
    create_plan,
    delete_account,
    delete_plan,
    refresh_plan,
    retrieve_account,
    retrieve_all_plans,
    retrieve_health,
    retrieve_plan,
    retrieve_plan_status,
    retrieve_version,
    toggle_device,
    toggle_group,
    turn_off_device,
    turn_off_group,
    turn_on_device,
    turn_on_group,
    update_plan,
    update_plan_status,
)
from vplan.interface import Account, Health, Plan, PlanSchema, Status, Version

BASE_URL = MagicMock(return_value=MagicMock(return_value="http://whatever"))
TIMEOUT_MATCHER = matchers.request_kwargs_matcher({"timeout": 1.0})


class TestUtil:
    def test_raise_for_status(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = HTTPError("hello")
        with pytest.raises(ClickException, match="^hello"):
            _raise_for_status(response)


@patch("vplan.client.client.api_url", new_callable=BASE_URL)
class TestHealthAndVersion:
    def test_retrieve_health_error(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/health", status=500, match=[TIMEOUT_MATCHER])
            assert retrieve_health() is False

    def test_retrieve_health_timeout(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/health", body=Timeout("error"), match=[TIMEOUT_MATCHER])
            assert retrieve_health() is False

    def test_retrieve_health_healthy(self, _):
        with responses.RequestsMock() as r:
            health = Health()
            r.get(url="http://whatever/health", body=health.model_dump_json(), match=[TIMEOUT_MATCHER])
            assert retrieve_health() is True

    def test_retrieve_version_error(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/version", status=500, match=[TIMEOUT_MATCHER])
            assert retrieve_version() is None

    def test_retrieve_version_timeout(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/version", body=Timeout("error"), match=[TIMEOUT_MATCHER])
            assert retrieve_version() is None

    def test_retrieve_version_healthy(self, _):
        with responses.RequestsMock() as r:
            version = Version(package="a", api="b")
            r.get(url="http://whatever/version", body=version.model_dump_json(), match=[TIMEOUT_MATCHER])
            assert retrieve_version() == version


@patch("vplan.client.client.api_url", new_callable=BASE_URL)
class TestAccount:
    def test_retrieve_account_not_found(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/account", status=404)
            assert retrieve_account() is None

    def test_retrieve_account_found(self, _):
        with responses.RequestsMock() as r:
            account = Account(pat_token="token")
            r.get(url="http://whatever/account", body=account.model_dump_json())
            assert retrieve_account() == account

    def test_retrieve_account_error(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/account", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                retrieve_account()

    def test_create_or_replace_account(self, _):
        with responses.RequestsMock() as r:
            account = Account(pat_token="token")
            r.post(url="http://whatever/account", body=account.model_dump_json())
            create_or_replace_account(account)

    def test_create_or_replace_account_error(self, _):
        with responses.RequestsMock() as r:
            account = Account(pat_token="token")
            r.post(url="http://whatever/account", body=account.model_dump_json(), status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                create_or_replace_account(account)

    def test_delete_account(self, _):
        with responses.RequestsMock() as r:
            r.delete(url="http://whatever/account")
            delete_account()

    def test_delete_account_error(self, _):
        with responses.RequestsMock() as r:
            r.delete(url="http://whatever/account", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                delete_account()


@patch("vplan.client.client.api_url", new_callable=BASE_URL)
class TestPlan:
    def test_retrieve_all_plans(self, _):
        with responses.RequestsMock() as r:
            plans = ["one", "two"]
            r.get(url="http://whatever/plan", json=plans)
            assert retrieve_all_plans() == plans

    def test_retrieve_all_plans_error(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/plan", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                retrieve_all_plans()

    def test_retrieve_plan_not_found(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/plan/xxx", status=404)
            assert retrieve_plan("xxx") is None

    def test_retrieve_plan_found(self, _):
        with responses.RequestsMock() as r:
            schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
            r.get(url="http://whatever/plan/xxx", body=schema.model_dump_json())
            assert retrieve_plan("xxx") == schema

    def test_retrieve_plan_error(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/plan/xxx", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                retrieve_plan("xxx")

    def test_create_plan(self, _):
        with responses.RequestsMock() as r:
            schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
            r.post(url="http://whatever/plan", body=schema.model_dump_json())
            create_plan(schema)

    def test_create_plan_error(self, _):
        with responses.RequestsMock() as r:
            schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
            r.post(url="http://whatever/plan", body=schema.model_dump_json(), status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                create_plan(schema)

    def test_update_plan(self, _):
        with responses.RequestsMock() as r:
            schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
            r.put(url="http://whatever/plan", body=schema.model_dump_json())
            update_plan(schema)

    def test_update_plan_error(self, _):
        with responses.RequestsMock() as r:
            schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30"))
            r.put(url="http://whatever/plan", body=schema.model_dump_json(), status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                update_plan(schema)

    def test_delete_plan(self, _):
        with responses.RequestsMock() as r:
            r.delete(url="http://whatever/plan/xxx")
            delete_plan("xxx")

    def test_delete_plan_error(self, _):
        with responses.RequestsMock() as r:
            r.delete(url="http://whatever/plan/xxx", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                delete_plan("xxx")

    def test_retrieve_plan_status_not_found(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/plan/xxx/status", status=404)
            assert retrieve_plan_status("xxx") is None

    def test_retrieve_plan_status_found(self, _):
        with responses.RequestsMock() as r:
            status = Status(enabled=False)
            r.get(url="http://whatever/plan/xxx/status", body=status.model_dump_json())
            assert retrieve_plan_status("xxx") == status

    def test_retrieve_plan_status_error(self, _):
        with responses.RequestsMock() as r:
            r.get(url="http://whatever/plan/xxx/status", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                retrieve_plan_status("xxx")

    def test_update_plan_status(self, _):
        with responses.RequestsMock() as r:
            status = Status(enabled=False)
            r.put(url="http://whatever/plan/xxx/status", body=status.model_dump_json())
            update_plan_status("xxx", status)

    def test_update_plan_status_error(self, _):
        with responses.RequestsMock() as r:
            status = Status(enabled=False)
            r.put(url="http://whatever/plan/xxx/status", body=status.model_dump_json(), status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                update_plan_status("xxx", status)

    def test_refresh_plan(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/refresh")
            refresh_plan("xxx")

    def test_refresh_plan_error(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/refresh", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                refresh_plan("xxx")

    def test_toggle_group(self, _):
        with responses.RequestsMock() as r:
            r.post(
                url="http://whatever/plan/xxx/test/group/yyy",
                match=[matchers.query_param_matcher({"toggles": 2, "delay_sec": 5})],
            )
            toggle_group("xxx", "yyy", 2, 5)

    def test_toggle_group_error(self, _):
        with responses.RequestsMock() as r:
            r.post(
                url="http://whatever/plan/xxx/test/group/yyy",
                match=[matchers.query_param_matcher({"toggles": 2, "delay_sec": 5})],
                status=500,
            )
            with pytest.raises(ClickException, match=r"500 Server Error"):
                toggle_group("xxx", "yyy", 2, 5)

    def test_toggle_device(self, _):
        with responses.RequestsMock() as r:
            r.post(
                url="http://whatever/plan/xxx/test/device/yyy/zzz/ccc",
                match=[matchers.query_param_matcher({"toggles": 2, "delay_sec": 5})],
            )
            toggle_device("xxx", "yyy", "zzz", "ccc", 2, 5)

    def test_toggle_device_error(self, _):
        with responses.RequestsMock() as r:
            r.post(
                url="http://whatever/plan/xxx/test/device/yyy/zzz/ccc",
                match=[matchers.query_param_matcher({"toggles": 2, "delay_sec": 5})],
                status=500,
            )
            with pytest.raises(ClickException, match=r"500 Server Error"):
                toggle_device("xxx", "yyy", "zzz", "ccc", 2, 5)

    def test_turn_on_group(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/on/group/yyy")
            turn_on_group("xxx", "yyy")

    def test_turn_on_group_error(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/on/group/yyy", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                turn_on_group("xxx", "yyy")

    def test_turn_on_device(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/on/device/yyy/zzz/ccc")
            turn_on_device("xxx", "yyy", "zzz", "ccc")

    def test_turn_on_device_error(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/on/device/yyy/zzz/ccc", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                turn_on_device("xxx", "yyy", "zzz", "ccc")

    def test_turn_off_group(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/off/group/yyy")
            turn_off_group("xxx", "yyy")

    def test_turn_off_group_error(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/off/group/yyy", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                turn_off_group("xxx", "yyy")

    def test_turn_off_device(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/off/device/yyy/zzz/ccc")
            turn_off_device("xxx", "yyy", "zzz", "ccc")

    def test_turn_off_device_error(self, _):
        with responses.RequestsMock() as r:
            r.post(url="http://whatever/plan/xxx/off/device/yyy/zzz/ccc", status=500)
            with pytest.raises(ClickException, match=r"500 Server Error"):
                turn_off_device("xxx", "yyy", "zzz", "ccc")
