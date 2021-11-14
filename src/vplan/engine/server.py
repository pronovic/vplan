# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""
import logging
from importlib.metadata import version as metadata_version
from typing import Dict

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

API_VERSION = "1.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints
API.include_router(account.ROUTER)
API.include_router(plan.ROUTER)


def _status_reason(e: Exception) -> Dict[str, str]:
    """Build status reason headers for an error handler."""
    # Technically, this could leak private information, such as about our table structures.
    # In a public-facing application, I would care about this.  For my use case, I'd rather
    # have the information available for debugging purposes.
    reason = ("%s" % e)[0:80]
    return {"vplan-status-reason": reason}


@API.exception_handler(NoResultFound)
async def not_found_handler(_: Request, e: NoResultFound) -> Response:
    try:
        raise e
    except NoResultFound:
        logging.error("Resource not found")
    return EmptyResponse(status_code=404, headers=_status_reason(e))


@API.exception_handler(IntegrityError)
async def already_exists_handler(_: Request, e: IntegrityError) -> Response:
    try:
        raise e
    except IntegrityError:
        logging.error("Resource already exists")
    return EmptyResponse(status_code=409, headers=_status_reason(e))


@API.exception_handler(InvalidPlanError)
async def invalid_plan_handler(_: Request, e: InvalidPlanError) -> Response:
    try:
        raise e
    except InvalidPlanError:
        logging.error("Invalid plan")
    return EmptyResponse(status_code=422, headers=_status_reason(e))


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
