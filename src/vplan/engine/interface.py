# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The public API model.
"""
from __future__ import annotations  # see: https://stackoverflow.com/a/33533514/2907667

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class ServerException(Exception):
    """A server exception."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Health(BaseModel):
    """API health data"""

    status: str = Field("OK", description="Health status")


class Version(BaseModel):
    """API version data"""

    package: str = Field(..., description="Python package version")
    api: str = Field(..., description="API interface version")


# TODO: start defining the public interface for the plan so we can define the public interface
# Seems interesting: https://pydantic-docs.helpmanual.io/usage/models/#orm-mode-aka-arbitrary-class-instances
#                    https://github.com/samuelcolvin/pydantic/issues/1522
# Not sure this is really applicable, because there are things in the database model that
# aren't in the API model, like the database identifiers, etc. Possibly that means my
# primary keys are wrong in the database model.  Maybe I should use natural keys rather
# than the generated integer keys.
