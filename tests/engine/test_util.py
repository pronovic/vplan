# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import MagicMock, patch

import pytest

from vplan.engine.exception import EngineError
from vplan.engine.util import setup_directories


class TestUtil:
    @patch("vplan.engine.util.S_IMODE")
    @patch("vplan.engine.util.stat")
    @patch("vplan.engine.util.makedirs")
    @patch("vplan.engine.util.config")
    def test_setup_directories_ok_permission(self, config, makedirs, stat, s_imode):
        config.return_value = MagicMock(database_dir="thedir")
        stat.return_value = MagicMock(st_mode=0o111)  # arbitrary value
        s_imode.return_value = 0o700
        setup_directories()
        makedirs.assert_called_once_with("thedir", mode=0o700, exist_ok=True)
        stat.assert_called_once_with("thedir")
        s_imode.assert_called_once_with(0o111)

    @patch("vplan.engine.util.S_IMODE")
    @patch("vplan.engine.util.stat")
    @patch("vplan.engine.util.makedirs")
    @patch("vplan.engine.util.config")
    def test_setup_directories_bad_permission(self, config, makedirs, stat, s_imode):
        config.return_value = MagicMock(database_dir="thedir")
        stat.return_value = MagicMock(st_mode=0o111)  # arbitrary value
        s_imode.return_value = 0o755  # fails because this is not mode 700
        with pytest.raises(EngineError, match=r".*must have permissions 700.*"):
            setup_directories()
        makedirs.assert_called_once_with("thedir", mode=0o700, exist_ok=True)
        stat.assert_called_once_with("thedir")
        s_imode.assert_called_once_with(0o111)
