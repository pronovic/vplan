# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The RESTful API.
"""

from importlib.metadata import version as metadata_version

from fastapi import FastAPI

from .interface import Health, Version

API_VERSION = "1.0.0"
api = FastAPI(version=API_VERSION, docs_url=None, redoc_url=None)  # no Swagger or ReDoc endpoints


@api.get("/health")
def api_health() -> Health:
    """Return an API health indicator."""
    return Health()


@api.get("/version")
def api_version() -> Version:
    """Return the API version, including both the package version and the API version"""
    return Version(package=metadata_version("vplan"), api=api.version)
