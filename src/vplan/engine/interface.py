# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The public API model.
"""

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class ServerException(Exception):
    """A server exception."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Health(BaseModel):
    """API health data"""

    status: str = Field("OK", title="Health status")


class Version(BaseModel):
    """API version data"""

    package: str = Field(..., title="Python package version")
    api: str = Field(..., title="API interface version")
