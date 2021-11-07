# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""
from importlib.metadata import version as metadata_version

from fastapi import FastAPI

from .interface import Health, Version
from .scheduler import shutdown_scheduler, start_scheduler
from .util import setup_directories

API_VERSION = "1.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints


@API.on_event("startup")
async def startup_event() -> None:
    """Do setup at server startup."""
    setup_directories()
    start_scheduler()


@API.on_event("shutdown")
async def shutdown_event() -> None:
    """Do cleanup at server shutdown."""
    shutdown_scheduler()


@API.get("/health")
def api_health() -> Health:
    """Return an API health indicator."""
    return Health()


@API.get("/version")
def api_version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("vplan"), api=API.version)
