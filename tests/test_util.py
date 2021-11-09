# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from unittest.mock import patch

import pytest

from vplan.util import homedir, replace_envvars


class TestUtil:
    def test_homedir(self):
        assert homedir()

    @patch.dict(os.environ, {"VAR1": "var1", "VAR2": "var2"}, clear=True)
    def test_replace_envvars(self):
        assert replace_envvars("{VAR1} then {VAR2}") == "var1 then var2"
        with pytest.raises(KeyError, match="'VAR3'"):
            replace_envvars("{VAR1} then {VAR2} then {VAR3}")
