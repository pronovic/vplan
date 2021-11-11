# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from typing import List
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result

from vplan.client.cli import vplan as command
from vplan.engine.interface import Account


# noinspection PyTypeChecker
def invoke(args: List[str]) -> Result:
    return CliRunner().invoke(command, ["account"] + args)


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


class TestDelete:
    def test_h(self):
        result = invoke(["delete", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["delete", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.account.delete_account")
    def test_command(self, delete_account):
        result = invoke(["delete"])
        assert result.exit_code == 0
        assert result.output == "Account deleted\n"
        delete_account.assert_called_once()


class TestSet:
    def test_h(self):
        result = invoke(["set", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["set", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.account.create_or_replace_account")
    @patch("vplan.client.commands.account.click.prompt")
    def test_command_interactive(self, prompt, create_or_replace_account):
        prompt.return_value = "token"
        result = invoke(["set"])
        assert result.exit_code == 0
        assert result.output == "Account set\n"
        create_or_replace_account.assert_called_once_with(Account(pat_token="token"))

    @pytest.mark.parametrize("option", ["--token", "-t"])
    @patch("vplan.client.commands.account.create_or_replace_account")
    def test_command_token(self, create_or_replace_account, option):
        result = invoke(["set", option, "token"])
        assert result.exit_code == 0
        assert result.output == "Account set\n"
        create_or_replace_account.assert_called_once_with(Account(pat_token="token"))


class TestShow:
    def test_h(self):
        result = invoke(["show", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["show", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.account.retrieve_account")
    def test_command_does_not_exist(self, retrieve_account):
        retrieve_account.return_value = None
        result = invoke(["show"])
        assert result.exit_code == 0
        assert result.output == "Account is not set\n"

    @pytest.mark.parametrize(
        "token,output",
        [
            ("12345678", "PAT token: 12345678\n"),
            ("123456789", "PAT token: 1234*6789\n"),
            ("100d2d4e-1234-5678-31e22179", "PAT token: 100d*******************2179\n"),
        ],
    )
    @patch("vplan.client.commands.account.retrieve_account")
    def test_command_exists_masked(self, retrieve_account, token, output):
        retrieve_account.return_value = Account(pat_token=token)
        result = invoke(["show"])
        assert result.exit_code == 0
        assert result.output == output

    @pytest.mark.parametrize(
        "option",
        ["--unmask", "-u"],
    )
    @patch("vplan.client.commands.account.retrieve_account")
    def test_command_exists_unmasked(self, retrieve_account, option):
        retrieve_account.return_value = Account(pat_token="100d2d4e-1234-5678-31e22179")
        result = invoke(["show", option])
        assert result.exit_code == 0
        assert result.output == "PAT token: 100d2d4e-1234-5678-31e22179\n"
