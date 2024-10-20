# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic_yaml import parse_yaml_raw_as

from vplan.engine.server import API
from vplan.interface import Account

CLIENT = TestClient(API)


class TestRoutes:
    @patch("vplan.engine.routers.account.db_retrieve_account")
    def test_retrieve_account(self, db_retrieve_account):
        account = Account(pat_token="token")
        db_retrieve_account.return_value = account
        response = CLIENT.get(url="/account")
        assert response.status_code == 200
        assert parse_yaml_raw_as(Account, response.text) == account

    @patch("vplan.engine.routers.account.db_create_or_replace_account")
    def test_create_or_replace_account(self, db_create_or_replace_account):
        account = Account(pat_token="token")
        response = CLIENT.post(url="/account", content=account.model_dump_json())
        assert response.status_code == 204
        assert not response.text
        db_create_or_replace_account.assert_called_once_with(account)

    @patch("vplan.engine.routers.account.db_delete_account")
    def test_delete_account(self, db_delete_account):
        response = CLIENT.delete(url="/account")
        assert response.status_code == 204
        db_delete_account.assert_called_once()
