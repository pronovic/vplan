# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""
from importlib.metadata import version as metadata_version

from fastapi import FastAPI, Request
from sqlalchemy.exc import NoResultFound
from starlette.responses import Response

from vplan.engine.database import setup_database
from vplan.engine.exception import AlreadyExistsError
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.routers import account, plan
from vplan.engine.scheduler import shutdown_scheduler, start_scheduler
from vplan.engine.util import setup_directories
from vplan.interface import Health, Version

API_VERSION = "1.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints
API.include_router(account.ROUTER)
API.include_router(plan.ROUTER)


@API.exception_handler(NoResultFound)
async def not_found_handler(request: Request, e: NoResultFound) -> Response:  # pylint: disable=unused-argument
    return EmptyResponse(status_code=404)


@API.exception_handler(AlreadyExistsError)
async def already_exists_handler(request: Request, e: AlreadyExistsError) -> Response:  # pylint: disable=unused-argument
    return EmptyResponse(status_code=409)


@API.on_event("startup")
async def startup_event() -> None:
    """Do setup at server startup."""
    setup_directories()
    setup_database()
    start_scheduler()


@API.on_event("shutdown")
async def shutdown_event() -> None:
    """Do cleanup at server shutdown."""
    shutdown_scheduler()


@API.get("/health")
def health() -> Health:
    """Return an API health indicator."""
    return Health()


@API.get("/version")
def version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("vplan"), api=API.version)
