# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from typing import List
from unittest.mock import patch

from click.testing import CliRunner, Result

from vplan.client.cli import vplan as command

# noinspection PyTypeChecker
from vplan.engine.interface import Version


def invoke(args: List[str]) -> Result:
    return CliRunner().invoke(command, args)


class TestCommon:
    def test_h(self):
        result = invoke(["-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["--help"])
        assert result.exit_code == 0

    @patch("importlib.metadata.version")  # this is used underneath by @click.version_option()
    def test_version(self, version):
        version.return_value = "1234"
        result = invoke(["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("vplan, version 1234")

    def test_no_args(self):
        result = invoke([])
        assert result.exit_code == 0

    @patch("vplan.client.cli.retrieve_health")
    def test_check_unhealthy(self, retrieve_health):
        retrieve_health.return_value = False
        result = invoke(["check"])
        assert result.exit_code == 1
        assert "Unable to connect to API" in result.output

    @patch("vplan.client.cli.retrieve_version")
    @patch("vplan.client.cli.retrieve_health")
    def test_check_no_version(self, retrieve_health, retrieve_version):
        retrieve_health.return_value = True
        retrieve_version.return_value = None
        result = invoke(["check"])
        assert result.exit_code == 1
        assert "Unable to retrieve API version" in result.output

    @patch("vplan.client.cli.retrieve_version")
    @patch("vplan.client.cli.retrieve_health")
    def test_check_healthy(self, retrieve_health, retrieve_version):
        version = Version(package="a", api="b")
        retrieve_health.return_value = True
        retrieve_version.return_value = version
        result = invoke(["check"])
        assert result.exit_code == 0
        assert result.output == "API is healthy, versions: package='a' api='b'\n"
