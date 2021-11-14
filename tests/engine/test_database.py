# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=redefined-outer-name,unused-argument
import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, NoResultFound

from vplan.engine.database import (
    db_create_or_replace_account,
    db_create_plan,
    db_delete_account,
    db_delete_plan,
    db_retrieve_account,
    db_retrieve_all_plans,
    db_retrieve_all_tables,
    db_retrieve_plan,
    db_retrieve_plan_enabled,
    db_update_plan,
    db_update_plan_enabled,
    setup_database,
)
from vplan.interface import Account, Plan, PlanSchema


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "interface", filename)


PLAN_FILE = fixture("plan.yaml")


@pytest.fixture
@patch("vplan.engine.database.config")
def database(config, tmpdir):
    database_url = "sqlite+pysqlite:///%s" % tmpdir.join("vplan.sqlite").realpath()
    database_log_level = "DEBUG"
    config.return_value = MagicMock(database_url=database_url, database_log_level=database_log_level)
    setup_database()


class TestDatabase:
    def test_tables_exist(self, database):
        assert db_retrieve_all_tables() == ["account", "plan"]

    def test_account_roundtrip(self, database):
        with pytest.raises(NoResultFound):
            db_retrieve_account()

        account1 = Account(pat_token="111")
        db_create_or_replace_account(account1)
        assert db_retrieve_account() == account1

        account2 = Account(pat_token="222")
        db_create_or_replace_account(account2)
        assert db_retrieve_account() == account2

        db_delete_account()
        with pytest.raises(NoResultFound):
            db_retrieve_account()

    def test_plan_roundtrip(self, database):
        assert db_retrieve_all_plans() == []
        with pytest.raises(NoResultFound):
            db_retrieve_plan("name")

        schema_a1 = PlanSchema(version="1.0.0", plan=Plan(name="aaa", location="location1", refresh_time="00:11"))
        db_create_plan(schema_a1)
        assert db_retrieve_all_plans() == ["aaa"]
        assert db_retrieve_plan("aaa") == schema_a1

        schema_a2 = PlanSchema(version="1.0.0", plan=Plan(name="aaa", location="location2", refresh_time="00:22"))
        with pytest.raises(IntegrityError):
            db_create_plan(schema_a2)  # duplicate key
        db_update_plan(schema_a2)
        assert db_retrieve_all_plans() == ["aaa"]
        assert db_retrieve_plan("aaa") == schema_a2

        assert db_retrieve_plan_enabled("aaa") is False
        db_update_plan_enabled("aaa", True)
        assert db_retrieve_plan_enabled("aaa") is True
        db_update_plan_enabled("aaa", False)
        assert db_retrieve_plan_enabled("aaa") is False

        schema_b1 = PlanSchema(version="1.0.0", plan=Plan(name="bbb", location="locationB", refresh_time="00:33"))
        with pytest.raises(NoResultFound):
            db_update_plan(schema_b1)
        db_create_plan(schema_b1)
        assert db_retrieve_all_plans() == ["aaa", "bbb"]
        assert db_retrieve_plan("bbb") == schema_b1

        db_delete_plan("aaa")
        assert db_retrieve_all_plans() == ["bbb"]
        with pytest.raises(NoResultFound):
            db_retrieve_plan("aaa")
        assert db_retrieve_plan("bbb") == schema_b1

        db_delete_plan("bbb")
        assert db_retrieve_all_plans() == []
        with pytest.raises(NoResultFound):
            db_retrieve_plan("aaa")
        with pytest.raises(NoResultFound):
            db_retrieve_plan("bbb")

    def test_plan_full_yaml(self, database):
        schema = PlanSchema.parse_file(PLAN_FILE)
        db_create_plan(schema)
        assert db_retrieve_plan(schema.plan.name) == schema
