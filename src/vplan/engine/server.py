# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""
import logging
from importlib.metadata import version as metadata_version

from fastapi import FastAPI, Request
from sqlalchemy.exc import IntegrityError, NoResultFound
from starlette.responses import Response

from vplan.engine.database import setup_database
from vplan.engine.exception import InvalidPlanError
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.routers import account, plan
from vplan.engine.scheduler import shutdown_scheduler, start_scheduler
from vplan.engine.util import setup_directories
from vplan.interface import Health, Version

API_VERSION = "2.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints
API.include_router(account.ROUTER)
API.include_router(plan.ROUTER)


@API.exception_handler(NoResultFound)
async def not_found_handler(_: Request, e: NoResultFound) -> Response:
    logging.error("Resource not found: %s", e)
    return EmptyResponse(status_code=404)


@API.exception_handler(ValueError)  # this happens for things like a bad enumeration value
async def value_error_handler(_: Request, e: ValueError) -> Response:
    logging.error("Bad request: %s", e)
    return EmptyResponse(status_code=400)


@API.exception_handler(IntegrityError)
async def already_exists_handler(_: Request, e: IntegrityError) -> Response:
    logging.error("Resource already exists: %s", e)
    return EmptyResponse(status_code=409)


@API.exception_handler(InvalidPlanError)
async def invalid_plan_handler(_: Request, e: InvalidPlanError) -> Response:
    logging.error("Invalid plan: %s", e)
    return EmptyResponse(status_code=422)


@API.on_event("startup")
async def startup_event() -> None:
    """Do setup at server startup."""
    setup_directories()
    setup_database()
    start_scheduler()
    logging.info("Server startup complete")


@API.on_event("shutdown")
async def shutdown_event() -> None:
    """Do cleanup at server shutdown."""
    shutdown_scheduler()
    logging.info("Server shutdown complete")


@API.get("/health")
def health() -> Health:
    """Return an API health indicator."""
    return Health()


@API.get("/version")
def version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("vplan"), api=API.version)
