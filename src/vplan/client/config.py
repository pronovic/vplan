# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Client configuration
"""
import os
from enum import Enum
from os import R_OK, access
from os.path import isfile
from typing import Optional

import click
from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_yaml import parse_yaml_raw_as

from vplan.util import homedir, replace_envvars

DEFAULT_CONFIG = os.path.join(homedir(), ".config/vplan/client/application.yaml")


class ConnectionMode(str, Enum):
    PORT = "port"
    SOCKET = "socket"


# noinspection PyNestedDecorators
class ClientConfig(BaseModel):
    """Client configuration."""

    mode: ConnectionMode = Field(..., title="Connection mode, either port or socket")
    api_endpoint: Optional[str] = Field(title="HTTP endpoint, used in port mode", default=None)
    api_socket: Optional[str] = Field(title="Path to a UNIX socket, used in socket mode", default=None)

    @field_validator("api_endpoint")
    @classmethod
    def _validate_api_endpoint(cls, api_endpoint: str, values: ValidationInfo) -> str:
        if values.data["mode"] == ConnectionMode.PORT.value and not api_endpoint:
            raise ValueError("api_endpoint required in PORT mode")
        return api_endpoint

    @field_validator("api_socket")
    @classmethod
    def _validate_api_socket(cls, api_socket: str, values: ValidationInfo) -> str:
        if values.data["mode"] == ConnectionMode.SOCKET.value and not api_socket:
            raise ValueError("api_socket required in SOCKET mode")
        return api_socket

    def api_url(self) -> str:
        """Return the correct API URL based on configuration."""
        if self.mode == ConnectionMode.PORT:
            # For port mode, we make normal HTTP connections on a TCP port
            return self.api_endpoint  # type: ignore
        else:
            # For socket mode, we use a special URL to send traffic using a unix socket on the filesystem
            return "http+unix://%s" % self.api_socket.replace("/", "%2F")  # type: ignore


_CONFIG_PATH: Optional[str] = None
_CONFIG: Optional[ClientConfig] = None


def _load_config(config_path: Optional[str]) -> ClientConfig:
    """Load client configuration from disk, substituting environment variables of the form {VAR}."""
    if not config_path:
        raise click.ClickException("Internal error: no config path set")
    if not (isfile(config_path) and access(config_path, R_OK)):
        raise click.UsageError("Client configuration is not readable: %s" % config_path)
    with open(config_path, "r", encoding="utf8") as fp:
        yaml = replace_envvars(fp.read())
        return parse_yaml_raw_as(ClientConfig, yaml)


# pylint: disable=global-statement
def reset() -> None:
    """Reset the config singleton, forcing it to be reloaded when next used."""
    global _CONFIG_PATH
    global _CONFIG
    _CONFIG_PATH = None
    _CONFIG = None


def set_config_path(config_path: Optional[str] = None) -> None:
    """Set the configuration path to be used for future lazy loading."""
    global _CONFIG_PATH
    _CONFIG_PATH = config_path


# pylint: disable=global-statement
def config() -> ClientConfig:
    """Retrieve client configuration, loading it from disk once and caching it."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load_config(_CONFIG_PATH)
    return _CONFIG


def api_url() -> str:
    """Return the correct API URL based on configuration."""
    return config().api_url()
