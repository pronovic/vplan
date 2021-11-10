# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

from unittest.mock import MagicMock, patch

from vplan.client.client import (
    create_account,
    create_plan,
    delete_account,
    delete_plan,
    refresh_plan,
    retrieve_account,
    retrieve_account_status,
    retrieve_all_plans,
    retrieve_plan,
    retrieve_plan_status,
    toggle_device,
    toggle_group,
    update_account,
    update_account_status,
    update_plan,
    update_plan_status,
)
from vplan.engine.interface import Account, Plan, PlanSchema, Status


def _response(model=None, data=None, status_code=None):
    """Build a mocked response for use with the requests library."""
    response = MagicMock()
    if model:
        response.json = MagicMock()
        response.json.return_value = model.json()
    if data:
        response.json = MagicMock()
        response.json.return_value = data
    if status_code:
        response.status_code = status_code
    response.raise_for_status = MagicMock()
    return response


@patch("vplan.client.client.api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
class TestAccount:
    @patch("vplan.client.client.requests.get")
    def test_retrieve_account_not_found(self, requests_get, api_url):
        response = _response(status_code=404)
        requests_get.side_effect = [response]
        result = retrieve_account()
        assert result is None
        response.raise_for_status.assert_not_called()
        requests_get.assert_called_once_with(url="http://whatever/account")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_account_found(self, requests_get, api_url):
        account = Account(name="name", pat_token="token")
        response = _response(model=account)
        requests_get.side_effect = [response]
        result = retrieve_account()
        assert result == account
        response.raise_for_status.assert_called_once()
        requests_get.assert_called_once_with(url="http://whatever/account")

    @patch("vplan.client.client.requests.post")
    def test_create_account(self, requests_post, api_url):
        account = Account(name="name", pat_token="token")
        response = _response()
        requests_post.side_effect = [response]
        create_account(account)
        response.raise_for_status.assert_called_once()
        requests_post.assert_called_once_with(url="http://whatever/account", json=account.json())

    @patch("vplan.client.client.requests.put")
    def test_update_account(self, requests_put, api_url):
        account = Account(name="name", pat_token="token")
        response = _response()
        requests_put.side_effect = [response]
        update_account(account)
        response.raise_for_status.assert_called_once()
        requests_put.assert_called_once_with(url="http://whatever/account", json=account.json())

    @patch("vplan.client.client.requests.delete")
    def test_delete_account(self, requests_delete, api_url):
        response = _response()
        requests_delete.side_effect = [response]
        delete_account()
        response.raise_for_status.assert_called_once()
        requests_delete.assert_called_once_with(url="http://whatever/account")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_account_status_not_found(self, requests_get, api_url):
        response = _response(status_code=404)
        requests_get.side_effect = [response]
        result = retrieve_account_status()
        assert result is None
        response.raise_for_status.assert_not_called()
        requests_get.assert_called_once_with(url="http://whatever/account/status")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_account_status_found(self, requests_get, api_url):
        status = Status(enabled=True)
        response = _response(model=status)
        requests_get.side_effect = [response]
        result = retrieve_account_status()
        assert result == status
        response.raise_for_status.assert_called_once()
        requests_get.assert_called_once_with(url="http://whatever/account/status")

    @patch("vplan.client.client.requests.put")
    def test_update_account_status(self, requests_put, api_url):
        status = Status(enabled=True)
        response = _response()
        requests_put.side_effect = [response]
        update_account_status(status)
        response.raise_for_status.assert_called_once()
        requests_put.assert_called_once_with(url="http://whatever/account/status", json=status.json())


@patch("vplan.client.client.api_url", new_callable=MagicMock(return_value=MagicMock(return_value="http://whatever")))
class TestPlan:
    @patch("vplan.client.client.requests.get")
    def test_retrieve_all_plans(self, requests_get, api_url):
        plans = ["one", "two"]
        response = _response(data=plans)
        requests_get.side_effect = [response]
        result = retrieve_all_plans()
        assert result == plans
        response.raise_for_status.assert_called_once()
        requests_get.assert_called_once_with(url="http://whatever/plan")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_not_found(self, requests_get, api_url):
        response = _response(status_code=404)
        requests_get.side_effect = [response]
        result = retrieve_plan("xxx")
        assert result is None
        response.raise_for_status.assert_not_called()
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_found(self, requests_get, api_url):
        plan = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", groups=[]))
        response = _response(model=plan)
        requests_get.side_effect = [response]
        result = retrieve_plan("xxx")
        assert result == plan
        response.raise_for_status.assert_called_once()
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx")

    @patch("vplan.client.client.requests.post")
    def test_create_plan(self, requests_post, api_url):
        plan = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", groups=[]))
        response = _response()
        requests_post.side_effect = [response]
        create_plan(plan)
        response.raise_for_status.assert_called_once()
        requests_post.assert_called_once_with(url="http://whatever/plan", json=plan.json())

    @patch("vplan.client.client.requests.put")
    def test_update_plan(self, requests_put, api_url):
        plan = PlanSchema(version="1.0.0", plan=Plan(name="name", location="location", groups=[]))
        response = _response()
        requests_put.side_effect = [response]
        update_plan(plan)
        response.raise_for_status.assert_called_once()
        requests_put.assert_called_once_with(url="http://whatever/plan/name", json=plan.json())

    @patch("vplan.client.client.requests.delete")
    def test_delete_plan(self, requests_delete, api_url):
        response = _response()
        requests_delete.side_effect = [response]
        delete_plan("xxx")
        response.raise_for_status.assert_called_once()
        requests_delete.assert_called_once_with(url="http://whatever/plan/xxx")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_status_not_found(self, requests_get, api_url):
        response = _response(status_code=404)
        requests_get.side_effect = [response]
        result = retrieve_plan_status("xxx")
        assert result is None
        response.raise_for_status.assert_not_called()
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx/status")

    @patch("vplan.client.client.requests.get")
    def test_retrieve_plan_status_found(self, requests_get, api_url):
        status = Status(enabled=False)
        response = _response(model=status)
        requests_get.side_effect = [response]
        result = retrieve_plan_status("xxx")
        assert result == status
        response.raise_for_status.assert_called_once()
        requests_get.assert_called_once_with(url="http://whatever/plan/xxx/status")

    @patch("vplan.client.client.requests.put")
    def test_update_plan_status(self, requests_put, api_url):
        status = Status(enabled=False)
        response = _response()
        requests_put.side_effect = [response]
        update_plan_status("xxx", status)
        response.raise_for_status.assert_called_once()
        requests_put.assert_called_once_with(url="http://whatever/plan/xxx/status", json=status.json())

    @patch("vplan.client.client.requests.post")
    def test_refresh_plan(self, requests_post, api_url):
        response = _response()
        requests_post.side_effect = [response]
        refresh_plan("xxx")
        response.raise_for_status.assert_called_once()
        requests_post.assert_called_once_with(url="http://whatever/plan/xxx/refresh")

    @patch("vplan.client.client.requests.post")
    def test_toggle_group(self, requests_post, api_url):
        response = _response()
        requests_post.side_effect = [response]
        toggle_group("xxx", "yyy", 2)
        response.raise_for_status.assert_called_once()
        requests_post.assert_called_once_with(url="http://whatever/plan/xxx/test/group/yyy", params={"toggle_count": 2})

    @patch("vplan.client.client.requests.post")
    def test_toggle_device(self, requests_post, api_url):
        response = _response()
        requests_post.side_effect = [response]
        toggle_device("xxx", "yyy", "zzz", 2)
        response.raise_for_status.assert_called_once()
        requests_post.assert_called_once_with(url="http://whatever/plan/xxx/test/device/yyy/zzz", params={"toggle_count": 2})
