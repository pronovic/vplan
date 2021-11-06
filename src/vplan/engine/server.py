# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API provided by the engine.
"""

from importlib.metadata import version as metadata_version

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer

from .interface import Health, RefreshRequest, RefreshResult, TriggerResult, VacationPlan, Version
from .plan import execute_trigger_actions, refresh_plan

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
def api_refresh(request: RefreshRequest, pat_token: str = Depends(BEARER_TOKEN)) -> RefreshResult:
    """
    Refresh the vacation plan in SmartThings.

    The refresh request includes a current vacation plan (which might be empty)
    and a new vacation plan.  The underlying business logic establishes the
    differences between the two plans and implements the result in the
    SmartThings infrastructure.

    Args:
        pat_token(str): The SmartThings PAT token (personal access token)
        request(RefreshRequest): The vacation plan refresh request

    Returns:
        RefreshResult: The result of the refresh action
    """
    return refresh_plan(pat_token=pat_token, current=request.current, new=request.new)


@API.put("/trigger/{trigger_id}")
def api_trigger(trigger_id: str, plan: VacationPlan, pat_token: str = Depends(BEARER_TOKEN)) -> TriggerResult:
    """
    Manually execute the actions associated with a trigger, for testing the device setup.

    Args:
        pat_token(str): The SmartThings PAT token (personal access token)
        trigger_id: The id of the trigger to test
        plan(VacationPlan): The vacation plan the trigger is a part of, assumed to be current

    Returns:
        TriggerResult: A status report about the trigger that was executed
    """
    return execute_trigger_actions(pat_token=pat_token, trigger_id=trigger_id, plan=plan)
