# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Router for account endpoints.
"""

from fastapi import APIRouter
from sqlalchemy import update
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from vplan.engine.database import dbsession
from vplan.engine.entity import DEFAULT_ACCOUNT, AccountEntity
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import Account, AlreadyExistsError, Status

ROUTER = APIRouter()


@ROUTER.get("/account", status_code=HTTP_200_OK)
def retrieve_account() -> Account:
    """Retrieve account information stored in the plan engine."""
    with dbsession() as session:
        entity = session.query(AccountEntity).where(AccountEntity.account_name == DEFAULT_ACCOUNT).one()
        return Account(name=entity.account_name, pat_token=entity.pat_token)


@ROUTER.post("/account", status_code=HTTP_201_CREATED, response_class=EmptyResponse)
def create_account(account: Account) -> None:
    """Create your account in the plan engine."""
    with dbsession() as session:
        if session.query(AccountEntity).where(AccountEntity.account_name == DEFAULT_ACCOUNT).first() is not None:
            raise AlreadyExistsError("Account already exists; update it instead")
        entity = AccountEntity()
        entity.account_name = DEFAULT_ACCOUNT  # we ignore anything that's passed in
        entity.pat_token = account.pat_token
        entity.enabled = True
        session.add(entity)


@ROUTER.put("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_account(account: Account) -> None:
    """Update your account in the plan engine."""
    with dbsession() as session:
        session.execute(
            update(AccountEntity).where(AccountEntity.account_name == DEFAULT_ACCOUNT).values(pat_token=account.pat_token)
        )


@ROUTER.delete("/account", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_account() -> None:
    """Delete account information stored in the plan engine."""
    with dbsession() as session:
        entity = session.query(AccountEntity).where(AccountEntity.account_name == DEFAULT_ACCOUNT).one()
        session.delete(entity)


@ROUTER.get("/account/status", status_code=HTTP_200_OK)
def retrieve_status() -> Status:
    """Retrieve the enabled/disabled status of your account in the plan engine."""
    with dbsession() as session:
        entity = session.query(AccountEntity).where(AccountEntity.account_name == DEFAULT_ACCOUNT).one()
        return Status(enabled=entity.enabled)


@ROUTER.put("/account/status", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_status(status: Status) -> None:
    """Set the enabled/disabled status of your account in the plan engine."""
    with dbsession() as session:
        session.execute(update(AccountEntity).where(AccountEntity.account_name == DEFAULT_ACCOUNT).values(enabled=status.enabled))
        # TODO: kick off the job that disables all plans (don't change status, just disable)
