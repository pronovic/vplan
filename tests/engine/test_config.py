# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import patch

import pytest

from vplan.engine.config import config, reset
from vplan.engine.interface import ServerException


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "config", filename)


APPLICATION_YAML = fixture("application.yaml")


class TestConfig:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Reset configuration before and after tests."""
        reset()
        yield
        reset()

    @patch.dict(os.environ, {"VPLAN_CONFIG_PATH": APPLICATION_YAML, "VPLAN_DATABASE_PATH": ".runtime/db"}, clear=True)
    def test_config_env(self):
        result = config()
        TestConfig._validate_config(result)

    @patch.dict(os.environ, {"VPLAN_DATABASE_PATH": ".runtime/db"}, clear=True)
    def test_config_path(self):
        result = config(config_path=APPLICATION_YAML)
        TestConfig._validate_config(result)

    @patch.dict(os.environ, {"VPLAN_DATABASE_PATH": ".runtime/db"}, clear=True)
    def test_config_env_no_var(self):
        with pytest.raises(ServerException, match=r"Server is not properly configured, no \$VPLAN_CONFIG_PATH found"):
            config()

    @patch.dict(os.environ, {"VPLAN_CONFIG_PATH": "bogus", "VPLAN_DATABASE_PATH": ".runtime/db"}, clear=True)
    def test_config_env_not_found(self):
        with pytest.raises(ServerException, match=r"Server configuration is not readable: bogus"):
            config()

    @staticmethod
    def _validate_config(result):
        assert result.database_dir == ".runtime/db"
        assert result.scheduler.database_url == "sqlite+pysqlite:///.runtime/db/jobs.sqlite"
        assert result.scheduler.daily_job.jitter_sec == 300
        assert result.scheduler.daily_job.misfire_grace_sec == 1800
