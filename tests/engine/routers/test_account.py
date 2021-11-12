# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import patch

from fastapi.testclient import TestClient

from vplan.engine.interface import Account
from vplan.engine.server import API

CLIENT = TestClient(API)


class TestRoutes:
    @patch("vplan.engine.routers.account.db_retrieve_account")
    def test_retrieve_account(self, db_retrieve_account):
        account = Account(pat_token="token")
        db_retrieve_account.return_value = account
        response = CLIENT.get(url="/account")
        assert response.status_code == 200
        assert Account.parse_raw(response.text) == account

    @patch("vplan.engine.routers.account.db_create_or_replace_account")
    def test_create_or_replace_account(self, db_create_or_replace_account):
        account = Account(pat_token="token")
        response = CLIENT.post(url="/account", data=account.json())
        assert response.status_code == 204
        assert not response.text
        db_create_or_replace_account.assert_called_once_with(account)

    @patch("vplan.engine.routers.account.schedule_immediate_refresh")
    @patch("vplan.engine.routers.account.db_update_plan_enabled")
    @patch("vplan.engine.routers.account.db_retrieve_all_plans")
    @patch("vplan.engine.routers.account.db_delete_account")
    def test_delete_account(self, db_delete_account, db_retrieve_all_plans, db_update_plan_enabled, schedule_immediate_refresh):
        plans = ["a"]
        db_retrieve_all_plans.return_value = plans
        response = CLIENT.delete(url="/account")
        assert response.status_code == 204
        db_update_plan_enabled.assert_called_once_with(plan_name="a", enabled=False)
        schedule_immediate_refresh.assert_called_once_with(plan_name="a")
        db_delete_account.assert_called_once()
