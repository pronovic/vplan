# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from typing import List
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner, Result

from vplan.client.cli import vplan as command
from vplan.engine.interface import Account, Status


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


class TestDisable:
    def test_h(self):
        result = invoke(["disable", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["disable", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.account.retrieve_account_status")
    @patch("vplan.client.commands.account.update_account_status")
    def test_command(self, update_account_status, retrieve_account_status):
        retrieve_account_status.return_value = Status(enabled=False)
        result = invoke(["disable"])
        assert result.exit_code == 0
        assert result.output == "Account is disabled\n"
        update_account_status.assert_called_once_with(Status(enabled=False))


class TestEnable:
    def test_h(self):
        result = invoke(["enable", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["enable", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.account.retrieve_account_status")
    @patch("vplan.client.commands.account.update_account_status")
    def test_command(self, update_account_status, retrieve_account_status):
        retrieve_account_status.return_value = Status(enabled=True)
        result = invoke(["enable"])
        assert result.exit_code == 0
        assert result.output == "Account is enabled\n"
        update_account_status.assert_called_once_with(Status(enabled=True))


class TestSet:
    def test_h(self):
        result = invoke(["set", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["set", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.account.create_account")
    @patch("vplan.client.commands.account.retrieve_account")
    @patch("vplan.client.commands.account.click.prompt")
    def test_command_create_interactive_new(self, prompt, retrieve_account, create_account):
        prompt.return_value = "token"
        retrieve_account.return_value = None
        result = invoke(["set"])
        assert result.exit_code == 0
        assert result.output == "Account created\n"
        create_account.assert_called_once_with(Account(name="default", pat_token="token"))

    @patch("vplan.client.commands.account.update_account")
    @patch("vplan.client.commands.account.retrieve_account")
    @patch("vplan.client.commands.account.click.prompt")
    def test_command_create_interactive_existing(self, prompt, retrieve_account, update_account):
        prompt.return_value = "token"
        retrieve_account.return_value = MagicMock()  # actual contents don't matter
        result = invoke(["set"])
        assert result.exit_code == 0
        assert result.output == "Account updated\n"
        update_account.assert_called_once_with(Account(name="default", pat_token="token"))

    @pytest.mark.parametrize("option", ["--token", "-t"])
    @patch("vplan.client.commands.account.create_account")
    @patch("vplan.client.commands.account.retrieve_account")
    def test_command_create_token_new(self, retrieve_account, create_account, option):
        retrieve_account.return_value = None
        result = invoke(["set", option, "token"])
        assert result.exit_code == 0
        assert result.output == "Account created\n"
        create_account.assert_called_once_with(Account(name="default", pat_token="token"))

    @pytest.mark.parametrize(
        "option",
        ["--token", "-t"],
    )
    @patch("vplan.client.commands.account.update_account")
    @patch("vplan.client.commands.account.retrieve_account")
    def test_command_create_token_existing(self, retrieve_account, update_account, option):
        retrieve_account.return_value = MagicMock()  # actual contents don't matter
        result = invoke(["set", option, "token"])
        assert result.exit_code == 0
        assert result.output == "Account updated\n"
        update_account.assert_called_once_with(Account(name="default", pat_token="token"))


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
        assert result.output == "Account does not exist\n"

    @patch("vplan.client.commands.account.retrieve_account")
    def test_command_exists(self, retrieve_account):
        retrieve_account.return_value = Account(name="name", pat_token="token")
        result = invoke(["show"])
        assert result.exit_code == 0
        assert result.output == "Account name: name\nPAT token: token\n"


class TestStatus:
    def test_h(self):
        result = invoke(["status", "-h"])
        assert result.exit_code == 0

    def test_help(self):
        result = invoke(["status", "--help"])
        assert result.exit_code == 0

    @patch("vplan.client.commands.account.retrieve_account_status")
    def test_command_does_not_exist(self, retrieve_account_status):
        retrieve_account_status.return_value = None
        result = invoke(["status"])
        assert result.exit_code == 0
        assert result.output == "Account does not exist\n"

    @pytest.mark.parametrize(
        "enabled,output",
        [
            (True, "Account is enabled\n"),
            (False, "Account is disabled\n"),
        ],
        ids=["enabled", "disabled"],
    )
    @patch("vplan.client.commands.account.retrieve_account_status")
    def test_command_exists(self, retrieve_account_status, enabled, output):
        retrieve_account_status.return_value = Status(enabled=enabled)
        result = invoke(["status"])
        assert result.exit_code == 0
        assert result.output == output
