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


@patch("vplan.engine.config.getenv")
class TestConfig:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Reset configuration before and after tests."""
        reset()
        yield
        reset()

    def test_config_env(self, getenv):
        getenv.return_value = APPLICATION_YAML
        result = config()
        TestConfig._validate_config(result)
        getenv.assert_called_once_with("VPLAN_CONFIG_PATH", None)

    def test_config_path(self, getenv):
        getenv.return_value = None  # simulate no config in environment
        result = config(config_path=APPLICATION_YAML)
        TestConfig._validate_config(result)
        getenv.assert_not_called()

    def test_config_env_no_var(self, getenv):
        getenv.return_value = None  # simulate no config in environment
        with pytest.raises(ServerException, match=r"Server is not properly configured, no \$VPLAN_CONFIG_PATH found"):
            config()
        getenv.assert_called_once_with("VPLAN_CONFIG_PATH", None)

    def test_config_env_not_found(self, getenv):
        getenv.return_value = "bogus"  # simulate config file does not exist
        with pytest.raises(ServerException, match=r"Server configuration is not readable: bogus"):
            config()
        getenv.assert_called_once_with("VPLAN_CONFIG_PATH", None)

    @staticmethod
    def _validate_config(result):
        assert result.database_dir == ".runtime/db"
        assert result.scheduler.database_url == "sqlite+pysqlite:///.runtime/db/jobs.sqlite"
        assert result.scheduler.thread_pool_size == 10
        assert result.scheduler.daily_job.jitter_sec == 300
        assert result.scheduler.daily_job.misfire_grace_sec == 1800
