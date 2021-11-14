# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Router for account endpoints.
"""

from fastapi import APIRouter
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from vplan.engine.database import db_create_or_replace_account, db_delete_account, db_retrieve_account
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.interface import Account

ROUTER = APIRouter()


@ROUTER.get("/account", status_code=HTTP_200_OK)
def retrieve_account() -> Account:
    """Retrieve account information stored in the plan engine."""
    return db_retrieve_account()


@ROUTER.post("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def create_or_replace_account(account: Account) -> None:
    """Create or replace account information stored in the plan engine."""
    db_create_or_replace_account(account)


@ROUTER.delete("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_account() -> None:
    """Delete account information stored in the plan engine."""
    db_delete_account()
