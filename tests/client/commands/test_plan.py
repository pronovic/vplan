# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from typing import List
from unittest.mock import patch

from click.testing import CliRunner, Result

from vplan.client.cli import vplan as command


# noinspection PyTypeChecker
def invoke(args: List[str]) -> Result:
    return CliRunner().invoke(command, ["plan"] + args)


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
