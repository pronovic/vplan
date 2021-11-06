# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from http import HTTPStatus

import pytest

from vplan.engine.interface import ApiException, Error, FailureReason, Health, Version


class TestExceptions:

    """Test exception classes."""

    @pytest.mark.it("ApiException, defaults")
    def test_api_exception_defaults(self):
        exception = ApiException()
        assert isinstance(exception, Exception)  # make sure parent class is right
        assert exception.status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert exception.reason == FailureReason.INTERNAL_ERROR

    @pytest.mark.it("ApiException, with reason")
    def test_api_exception_reason(self):
        exception = ApiException(status=HTTPStatus.NOT_FOUND, reason=FailureReason.INVALID_REQUEST)
        assert isinstance(exception, Exception)  # make sure parent class is right
        assert exception.status == HTTPStatus.NOT_FOUND
        assert exception.reason == FailureReason.INVALID_REQUEST


class TestModels:

    """Test models."""

    def test_error(self):
        error = Error(code="c", message="m")
        assert error.code == "c"
        assert error.message == "m"

    def test_health(self):
        health = Health()
        assert health.status == "OK"

    def test_version(self):
        version = Version(package="xxx", api="yyy")
        assert version.package == "xxx"
        assert version.api == "yyy"
