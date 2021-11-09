# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import patch

import pytest

from vplan.client.config import ClientConfig, ConnectionMode, config, reset
from vplan.engine.interface import ServerException

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

    @patch("vplan.client.config.homedir")
    def test_config_homedir_port(self, homedir):
        homedir.return_value = PORT_FIXTURE_DIR
        result = config()
        TestConfig._validate_port_config(result)

    @patch("vplan.client.config.homedir")
    def test_config_override_port(self, homedir):
        homedir.return_value = ""  # not used
        result = config(config_path=PORT_YAML)
        TestConfig._validate_port_config(result)

    @patch("vplan.client.config.homedir")
    @patch.dict(os.environ, {"HOME": "/home/whatever"}, clear=True)
    def test_config_homedir_socket(self, homedir):
        homedir.return_value = SOCKET_FIXTURE_DIR
        result = config()
        TestConfig._validate_socket_config(result)

    @patch("vplan.client.config.homedir")
    @patch.dict(os.environ, {"HOME": "/home/whatever"}, clear=True)
    def test_config_override_socket(self, homedir):
        homedir.return_value = ""  # not used
        result = config(config_path=SOCKET_YAML)
        TestConfig._validate_socket_config(result)

    @patch("vplan.client.config.homedir")
    def test_config_not_found(self, homedir, tmpdir):
        homedir.return_value = tmpdir.realpath()
        with pytest.raises(ServerException, match="^Client configuration is not readable"):
            config()

    @staticmethod
    def _validate_port_config(result):
        assert result.mode == ConnectionMode.PORT
        assert result.api_endpoint == "http://localhost:8080"
        assert result.api_socket is None

    @staticmethod
    def _validate_socket_config(result):
        assert result.mode == ConnectionMode.SOCKET
        assert result.api_endpoint is None
        assert result.api_socket == "/home/whatever/.config/vplan/run/engine.sock"
