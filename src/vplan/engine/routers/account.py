# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Router for account endpoints.
"""

from fastapi import APIRouter
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import Account, Status

ROUTER = APIRouter()


@ROUTER.get("/account", status_code=HTTP_200_OK)
def retrieve_account() -> Account:
    """Retrieve account information stored in the plan engine."""
    return None  # type: ignore


@ROUTER.post("/account", status_code=HTTP_201_CREATED, response_class=EmptyResponse)
def create_account(account: Account) -> None:
    """Create your account in the plan engine."""
    return None


@ROUTER.put("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_account(account: Account) -> None:
    """Update your account in the plan engine."""
    return None


@ROUTER.delete("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_account() -> None:
    """Delete account information stored in the plan engine."""


@ROUTER.get("/account/status", status_code=HTTP_200_OK)
def retrieve_status() -> Status:
    """Retrieve the enabled/disabled status of your account in the plan engine."""
    return None  # type: ignore


@ROUTER.put("/account/status", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_status(status: Status) -> None:
    """Set the enabled/disabled status of your account in the plan engine."""
    return None
