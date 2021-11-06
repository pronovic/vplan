# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import pytest

from vplan.engine.interface import Health, Version


@pytest.mark.it("Interface Models")
class TestModels:

    """Test models."""

    def test_health(self):
        health = Health()
        assert health.status == "OK"

    def test_version(self):
        version = Version(package="xxx", api="yyy")
        assert version.package == "xxx"
        assert version.api == "yyy"
