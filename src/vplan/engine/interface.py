# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Classes that are part of the API public interface.
"""

from __future__ import annotations  # so we can return a type from one of its own methods

from enum import Enum
from http import HTTPStatus
from typing import Union

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class FailureReason(Enum):
    """Failure reasons advertised to clients."""

    INVALID_REQUEST = "The request was invalid"
    INTERNAL_ERROR = "An internal error was encountered"


class ApiException(Exception):
    """
    Generic API exception.
    """

    def __init__(
        self,
        status: Union[int, HTTPStatus] = HTTPStatus.INTERNAL_SERVER_ERROR,
        reason: FailureReason = FailureReason.INTERNAL_ERROR,
    ):
        super().__init__()
        self.status = status if isinstance(status, HTTPStatus) else HTTPStatus(status)
        self.reason = reason


class Error(BaseModel):
    """
    An error returned from the API.
    """

    class Config:
        allow_mutation = False

    code: str = Field(...)
    message: str = Field(...)


class Health(BaseModel):
    """
    API health data.
    """

    class Config:
        allow_mutation = False

    status: str = Field("OK")


class Version(BaseModel):
    """
    API version data.

    We include both the package version and the API version, because
    they will vary independently.  We might release multiple versions
    of the Python package without changing the public interface of the
    API.
    """

    class Config:
        allow_mutation = False

    package: str = Field(...)
    api: str = Field(...)
