# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""

from importlib.metadata import version as metadata_version

from fastapi import FastAPI

from .config import config
from .interface import Health, Version

API_VERSION = "1.0.0"
API = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints


@API.on_event("startup")
async def startup_event() -> None:
    """Do setup at server start."""
    config()  # forces an immediate load, so either other code can rely on it, or we'll get an error now


@API.get("/health")
def api_health() -> Health:
    """Return an API health indicator."""
    return Health()


@API.get("/version")
def api_version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("vplan"), api=API.version)
