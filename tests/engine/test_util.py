# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import MagicMock, patch

import pytest

from vplan.engine.interface import ServerException
from vplan.engine.util import setup_directories


class TestUtil:
    @patch("vplan.engine.util.stat")
    @patch("vplan.engine.util.makedirs")
    @patch("vplan.engine.util.config")
    def test_setup_directories_ok_permission(self, config, makedirs, stat):
        config.return_value = MagicMock(database_dir="thedir")
        stat.return_value = MagicMock(st_mode=0o700)
        setup_directories()
        makedirs.assert_called_once_with("thedir", mode=0o700, exist_ok=True)
        stat.assert_called_once_with("thedir")

    @patch("vplan.engine.util.stat")
    @patch("vplan.engine.util.makedirs")
    @patch("vplan.engine.util.config")
    def test_setup_directories_bad_permission(self, config, makedirs, stat):
        config.return_value = MagicMock(database_dir="thedir")
        stat.return_value = MagicMock(st_mode=0o755)
        with pytest.raises(ServerException, match=r".*must have permissions 700.*"):
            setup_directories()
        makedirs.assert_called_once_with("thedir", mode=0o700, exist_ok=True)
        stat.assert_called_once_with("thedir")
