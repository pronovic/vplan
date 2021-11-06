# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API
"""

from http import HTTPStatus
from importlib.metadata import version as metadata_version
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .interface import ApiException, Error, FailureReason, Health, Version

API_VERSION = "1.0.0"

api = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc


def _build_error(status_code: int, content: Any) -> JSONResponse:
    """Build a JSONResponse to include error content."""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
    )


# noinspection PyUnusedLocal
@api.exception_handler(Exception)
async def general_exception_handler(r: Request, e: Exception) -> JSONResponse:  # pylint: disable=unused-argument
    """Override general exceptions to look like other errors."""
    return _build_error(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=Error(code=FailureReason.INTERNAL_ERROR.name, message=FailureReason.INTERNAL_ERROR.value),
    )


# noinspection PyUnusedLocal
@api.exception_handler(RequestValidationError)
async def validation_handler(r: Request, e: RequestValidationError) -> JSONResponse:  # pylint: disable=unused-argument
    """Override validation errors to look like other errors."""
    return _build_error(
        status_code=HTTPStatus.BAD_REQUEST,
        content=Error(code=FailureReason.INVALID_REQUEST.name, message=FailureReason.INVALID_REQUEST.value),
    )


# noinspection PyUnusedLocal
@api.exception_handler(ApiException)
async def api_exception_handler(r: Request, e: ApiException) -> JSONResponse:  # pylint: disable=unused-argument
    """Handle API exceptions."""
    return _build_error(
        status_code=e.status.value,
        content=Error(code=e.reason.name, message=e.reason.value),
    )


@api.get("/health")
def api_health() -> Health:
    """API health check."""
    return Health()


@api.get("/version")
def api_version() -> Version:
    """API version, including both the package version and the API version"""
    return Version(package=metadata_version("vplan"), api=api.version)
