# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from vplan.engine.interface import Health, ServerException, Version


class TestExceptions:

    """Test exception classes."""

    def test_server_exception(self):
        exception = ServerException("hello")
        assert isinstance(exception, Exception)  # make sure parent class is right
        assert exception.message == "hello"


class TestModels:

    """Test model classes."""

    def test_api_health(self):
        model = Health()
        assert model.status == "OK"

    def test_api_version(self):
        model = Version(package="a", api="b")
        assert model.package == "a"
        assert model.api == "b"
