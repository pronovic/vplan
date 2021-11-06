# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API, a thin wrapper over business logic.
"""

from importlib.metadata import version as metadata_version

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer

from .interface import Health, PlanImplementation, RefreshRequest, Version
from .plan import refresh_plan

API_VERSION = "1.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints
BEARER_TOKEN = OAuth2PasswordBearer("")


@API.get("/health")
def api_health() -> Health:
    """Return an API health indicator."""
    return Health()


@API.get("/version")
def api_version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("vplan"), api=API.version)


@API.post("/refresh")
def api_refresh(request: RefreshRequest, pat_token: str = Depends(BEARER_TOKEN)) -> PlanImplementation:
    """
    Refresh the vacation plan in SmartThings.

    The refresh request includes a current vacation plan (which might be empty)
    and a new vacation plan.  The underlying business logic establishes the
    differences between the two plans and implements the result in the
    SmartThings infrastructure.

    Args:
        pat_token(str): The SmartThings PAT token (personal access token)
        request(RefreshRequest): The vacation plan refresh request
    """
    return refresh_plan(pat_token=pat_token, current=request.current, new=request.new)
