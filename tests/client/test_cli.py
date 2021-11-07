# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from typing import List
from unittest.mock import patch

from click.testing import CliRunner, Result

from vplan.client.cli import vplan


# noinspection PyTypeChecker
def invoke(args: List[str]) -> Result:
    return CliRunner().invoke(vplan, args)


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
        assert result.output.startswith("Vacation Plan Manager, version 1234")

    def test_no_args(self):
        result = invoke([])
        assert result.exit_code == 0


class TestBootstrap:
    def test_h(self):
        result = invoke(["bootstrap", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["bootstrap", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.cli.bootstrap_config")
    @patch("vplan.client.cli.dump_instructions")
    def test_command_noforce(self, dump_instructions, bootstrap_config):
        result = invoke(["bootstrap"])
        assert result.exit_code == 0
        bootstrap_config.assert_called_once_with(force=False)
        dump_instructions.assert_called_once_with()

    @patch("vplan.client.cli.bootstrap_config")
    @patch("vplan.client.cli.dump_instructions")
    def test_command_force(self, dump_instructions, bootstrap_config):
        result = invoke(["bootstrap", "--force"])
        assert result.exit_code == 0
        bootstrap_config.assert_called_once_with(force=True)
        dump_instructions.assert_called_once_with()
