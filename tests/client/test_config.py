# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import patch

import pytest
from click import ClickException, UsageError

from vplan.client.config import ClientConfig, ConnectionMode, api_url, config, reset, set_config_path

PORT_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "config", "port")
PORT_YAML = os.path.join(PORT_FIXTURE_DIR, ".config", "vplan", "client", "application.yaml")

SOCKET_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "config", "socket")
SOCKET_YAML = os.path.join(SOCKET_FIXTURE_DIR, ".config", "vplan", "client", "application.yaml")


class TestValidation:
    @pytest.mark.parametrize(
        "mode,endpoint,socket,valid",
        [
            ("port", None, None, False),
            ("port", None, "socket", False),
            ("port", "endpoint", None, True),
            ("port", "endpoint", "socket", True),
            ("socket", None, None, False),
            ("socket", "endpoint", None, False),
            ("socket", None, "socket", True),
            ("socket", "endpoint", "socket", True),
        ],
    )
    def test_required_fields(self, mode, endpoint, socket, valid):
        if valid:
            ClientConfig(mode=mode, api_endpoint=endpoint, api_socket=socket)
        else:
            with pytest.raises(ValueError):
                ClientConfig(mode=mode, api_endpoint=endpoint, api_socket=socket)


class TestConfig:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Reset configuration before and after tests."""
        reset()
        yield
        reset()

    def test_config_port(self):
        set_config_path(config_path=PORT_YAML)
        TestConfig._validate_port_config(config())
        TestConfig._validate_port_config(config())

    @patch.dict(os.environ, {"HOME": "/home/whatever"}, clear=True)
    def test_config_socket(self):
        set_config_path(config_path=SOCKET_YAML)
        TestConfig._validate_socket_config(config())
        TestConfig._validate_socket_config(config())

    def test_config_unset(self):
        set_config_path(config_path=None)
        with pytest.raises(ClickException, match="^Internal error: no config path set"):
            config()

    def test_config_not_found(self, tmpdir):
        set_config_path(config_path=tmpdir.join("bogus.yaml"))
        with pytest.raises(UsageError, match="^.*Client configuration is not readable.*"):
            config()

    @patch.dict(os.environ, {"HOME": "/home/whatever"}, clear=True)
    def test_api_url(self):
        set_config_path(config_path=SOCKET_YAML)
        config()
        assert api_url() == config().api_url()

    @staticmethod
    def _validate_port_config(result):
        assert result.mode == ConnectionMode.PORT
        assert result.api_endpoint == "http://localhost:8080"
        assert result.api_socket is None
        assert result.api_url() == "http://localhost:8080"

    @staticmethod
    def _validate_socket_config(result):
        assert result.mode == ConnectionMode.SOCKET
        assert result.api_endpoint is None
        assert result.api_socket == "/home/whatever/.config/vplan/server/run/engine.sock"
        assert result.api_url() == "http+unix://%2Fhome%2Fwhatever%2F.config%2Fvplan%2Frun%2Fengine.sock"
