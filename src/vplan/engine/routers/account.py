# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Router for account endpoints.
"""

from fastapi import APIRouter
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from vplan.engine.database import dbsession
from vplan.engine.entity import ONLY_ACCOUNT, AccountEntity
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import Account

ROUTER = APIRouter()


@ROUTER.get("/account", status_code=HTTP_200_OK)
def retrieve_account() -> Account:
    """Retrieve account information stored in the plan engine."""
    with dbsession() as session:
        entity = session.query(AccountEntity).where(AccountEntity.account_name == ONLY_ACCOUNT).one()
        return Account(pat_token=entity.pat_token)


@ROUTER.post("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def create_or_replace_account(account: Account) -> None:
    """Create or replace account information stored in the plan engine."""
    with dbsession() as session:
        entity = AccountEntity()
        entity.account_name = ONLY_ACCOUNT
        entity.pat_token = account.pat_token
        session.add(entity)


@ROUTER.delete("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_account() -> None:
    """Delete account information stored in the plan engine."""
    with dbsession() as session:
        session.query(AccountEntity).where(AccountEntity.account_name == ONLY_ACCOUNT).delete()
        # TODO: we should disable all plans at the same time we do this
