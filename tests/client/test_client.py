# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument
import json
from unittest.mock import MagicMock, patch

import pytest
from click import ClickException
from requests import HTTPError, Timeout

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
    update_plan,
    update_plan_status,
)
from vplan.engine.interface import Account, Health, Plan, PlanSchema, Status, Version


def _response(model=None, data=None, status_code=None):
    """Build a mocked response for use with the requests library."""
    response = MagicMock()
    if model:
        response.text = model.json()
    if data:
        response.text = json.dumps(data)
    if status_code:
        response.status_code = status_code
    response.raise_for_status = MagicMock()
    return response


class TestUtil:
    def test_raise_for_status(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = HTTPError("hello")
        with pytest.raises(ClickException, match="^hello"):
            _raise_for_status(response)


@patch("vplan.client.client.api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
class TestHealthAndVersion:
    @patch("vplan.client.client.requests.get")
    def test_retrieve_health_error(self, requests_get, api_url):
        response = _response()
        response.raise_for_status.side_effect = HTTPError("error")
        requests_get.side_effect = [response]
        assert retrieve_health() is False
        requests_get.assert_called_once_with(url="http://whatever/health", timeout=1)

    @patch("vplan.client.client.requests.get")
    def test_retrieve_health_timeout(self, requests_get, api_url):
        response = _response()
        response.raise_for_status.side_effect = Timeout("error")
        requests_get.side_effect = [response]
        assert retrieve_health() is False
        requests_get.assert_called_once_with(url="http://whatever/health", timeout=1)

    @patch("vplan.client.client.requests.get")
    def test_retrieve_health_healthy(self, requests_get, api_url):
        response = _response(model=Health())
        requests_get.side_effect = [response]
        assert retrieve_health() is True
        requests_get.assert_called_once_with(url="http://whatever/health", timeout=1)

    @patch("vplan.client.client.requests.get")
    def test_retrieve_version_error(self, requests_get, api_url):
        response = _response()
        response.raise_for_status.side_effect = HTTPError("error")
        requests_get.side_effect = [response]
        result = retrieve_version()
        assert result is None
        requests_get.assert_called_once_with(url="http://whatever/version", timeout=1)

    @patch("vplan.client.client.requests.get")
    def test_retrieve_version_timeout(self, requests_get, api_url):
        response = _response()
        response.raise_for_status.side_effect = Timeout("error")
        requests_get.side_effect = [response]
        result = retrieve_version()
        assert result is None
        requests_get.assert_called_once_with(url="http://whatever/version", timeout=1)

    @patch("vplan.client.client.requests.get")
    def test_retrieve_version_healthy(self, requests_get, api_url):
        version = Version(package="a", api="b")
        response = _response(model=version)
        requests_get.side_effect = [response]
        result = retrieve_version()
        assert result == version
        requests_get.assert_called_once_with(url="http://whatever/version", timeout=1)


@patch("vplan.client.client._raise_for_status")
@patch("vplan.client.client.api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
class TestAccount:
    @patch("vplan.client.client.requests.get")
    def test_retrieve_account_not_found(self, requests_get, api_url, raise_for_status):
        response = _response(status_code=404)
        requests_get.side_effect = [response]
        result = retrieve_account()
        assert result is None
        raise_for_status.assert_not_called()
        requests_get.assert_called_once_with(url="http://whatever/account")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_account_found(self, requests_get, api_url, raise_for_status):
        account = Account(pat_token="token")
        response = _response(model=account)
        requests_get.side_effect = [response]
        result = retrieve_account()
        assert result == account
        raise_for_status.assert_called_once_with(response)
        requests_get.assert_called_once_with(url="http://whatever/account")

    @patch("vplan.client.client.requests.post")
    def test_create_or_replace_account(self, requests_post, api_url, raise_for_status):
        account = Account(pat_token="token")
        response = _response()
        requests_post.side_effect = [response]
        create_or_replace_account(account)
        raise_for_status.assert_called_once_with(response)
        requests_post.assert_called_once_with(url="http://whatever/account", data=account.json())

    @patch("vplan.client.client.requests.delete")
    def test_delete_account(self, requests_delete, api_url, raise_for_status):
        response = _response()
        requests_delete.side_effect = [response]
        delete_account()
        raise_for_status.assert_called_once_with(response)
        requests_delete.assert_called_once_with(url="http://whatever/account")


@patch("vplan.client.client._raise_for_status")
@patch("vplan.client.client.api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
class TestPlan:
    @patch("vplan.client.client.requests.get")
    def test_retrieve_all_plans(self, requests_get, api_url, raise_for_status):
        plans = ["one", "two"]
        response = _response(data=plans)
        requests_get.side_effect = [response]
        result = retrieve_all_plans()
        assert result == plans
        raise_for_status.assert_called_once_with(response)
        requests_get.assert_called_once_with(url="http://whatever/plan")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_not_found(self, requests_get, api_url, raise_for_status):
        response = _response(status_code=404)
        requests_get.side_effect = [response]
        result = retrieve_plan("xxx")
        assert result is None
        raise_for_status.assert_not_called()
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_found(self, requests_get, api_url, raise_for_status):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=[]))
        response = _response(model=schema)
        requests_get.side_effect = [response]
        result = retrieve_plan("xxx")
        assert result == schema
        raise_for_status.assert_called_once_with(response)
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx")

    @patch("vplan.client.client.requests.post")
    def test_create_plan(self, requests_post, api_url, raise_for_status):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=[]))
        response = _response()
        requests_post.side_effect = [response]
        create_plan(schema)
        raise_for_status.assert_called_once_with(response)
        requests_post.assert_called_once_with(url="http://whatever/plan", data=schema.json())

    @patch("vplan.client.client.requests.put")
    def test_update_plan(self, requests_put, api_url, raise_for_status):
        schema = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", refresh_time="00:30", groups=[]))
        response = _response()
        requests_put.side_effect = [response]
        update_plan(schema)
        raise_for_status.assert_called_once_with(response)
        requests_put.assert_called_once_with(url="http://whatever/plan", data=schema.json())

    @patch("vplan.client.client.requests.delete")
    def test_delete_plan(self, requests_delete, api_url, raise_for_status):
        response = _response()
        requests_delete.side_effect = [response]
        delete_plan("xxx")
        raise_for_status.assert_called_once_with(response)
        requests_delete.assert_called_once_with(url="http://whatever/plan/xxx")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_status_not_found(self, requests_get, api_url, raise_for_status):
        response = _response(status_code=404)
        requests_get.side_effect = [response]
        result = retrieve_plan_status("xxx")
        assert result is None
        raise_for_status.assert_not_called()
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx/status")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_status_found(self, requests_get, api_url, raise_for_status):
        status = Status(enabled=False)
        response = _response(model=status)
        requests_get.side_effect = [response]
        result = retrieve_plan_status("xxx")
        assert result == status
        raise_for_status.assert_called_once_with(response)
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx/status")

    @patch("vplan.client.client.requests.put")
    def test_update_plan_status(self, requests_put, api_url, raise_for_status):
        status = Status(enabled=False)
        response = _response()
        requests_put.side_effect = [response]
        update_plan_status("xxx", status)
        raise_for_status.assert_called_once_with(response)
        requests_put.assert_called_once_with(url="http://whatever/plan/xxx/status", data=status.json())

    @patch("vplan.client.client.requests.post")
    def test_refresh_plan(self, requests_post, api_url, raise_for_status):
        response = _response()
        requests_post.side_effect = [response]
        refresh_plan("xxx")
        raise_for_status.assert_called_once_with(response)
        requests_post.assert_called_once_with(url="http://whatever/plan/xxx/refresh")

    @patch("vplan.client.client.requests.post")
    def test_toggle_group(self, requests_post, api_url, raise_for_status):
        response = _response()
        requests_post.side_effect = [response]
        toggle_group("xxx", "yyy", 2)
        raise_for_status.assert_called_once_with(response)
        requests_post.assert_called_once_with(url="http://whatever/plan/xxx/test/group/yyy", params={"toggle_count": 2})

    @patch("vplan.client.client.requests.post")
    def test_toggle_device(self, requests_post, api_url, raise_for_status):
        response = _response()
        requests_post.side_effect = [response]
        toggle_device("xxx", "yyy", "zzz", 2)
        raise_for_status.assert_called_once_with(response)
        requests_post.assert_called_once_with(url="http://whatever/plan/xxx/test/device/yyy/zzz", params={"toggle_count": 2})
