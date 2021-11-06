# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from vplan.engine.interface import ApiException, Error, FailureReason
from vplan.engine.server import API_VERSION, _build_error, api, api_exception_handler, general_exception_handler, validation_handler

CLIENT = TestClient(api)

HEALTH_URL = "/health"
VERSION_URL = "/version"


class TestFunctions:

    """Test non-API functions."""

    @pytest.mark.it("_build_error()")
    @patch("vplan.engine.server.JSONResponse")
    @patch("vplan.engine.server.jsonable_encoder")
    def test_build_error(self, jsonable_encoder, json_response):
        encoder_stub = jsonable_encoder.return_value
        response_stub = json_response.return_value
        content = MagicMock()
        response = _build_error(status_code=999, content=content)
        assert response is response_stub
        jsonable_encoder.assert_called_once_with(content)
        json_response.assert_called_once_with(status_code=999, content=encoder_stub)

    @pytest.mark.it("general_exception_handler()")
    @patch("vplan.engine.server._build_error")
    async def test_general_exception_handler(self, build_error):
        stub = build_error.return_value
        request = MagicMock()
        exception = ValueError("hello")
        response = await general_exception_handler(request, exception)
        assert response is stub
        build_error.assert_called_once_with(
            status_code=500, content=Error(code="INTERNAL_ERROR", message="An internal error was encountered")
        )

    @pytest.mark.it("validation_handler()")
    @patch("vplan.engine.server._build_error")
    async def test_validation_handler(self, build_error):
        stub = build_error.return_value
        request = MagicMock()
        exception = RequestValidationError("hello")
        response = await validation_handler(request, exception)
        assert response is stub
        build_error.assert_called_once_with(
            status_code=400, content=Error(code="INVALID_REQUEST", message="The request was invalid")
        )

    @pytest.mark.it("api_exception_handler()")
    @patch("vplan.engine.server._build_error")
    async def test_api_exception_handler(self, build_error):
        stub = build_error.return_value
        request = MagicMock()
        exception = ApiException(status=HTTPStatus.BAD_REQUEST, reason=FailureReason.INVALID_REQUEST)
        response = await api_exception_handler(request, exception)
        assert response is stub
        build_error.assert_called_once_with(
            status_code=400, content=Error(code="INVALID_REQUEST", message="The request was invalid")
        )


class TestApi:

    """Test the public API endpoints via a client."""

    @pytest.mark.it("/health")
    def test_application_health(self):
        response = CLIENT.get(HEALTH_URL)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    @pytest.mark.it("/version")
    @patch("vplan.engine.server.metadata_version")
    def test_application_version(self, metadata_version):
        metadata_version.return_value = "xxx"
        response = CLIENT.get(VERSION_URL)
        assert response.status_code == 200
        assert response.json() == {"package": "xxx", "api": API_VERSION}
