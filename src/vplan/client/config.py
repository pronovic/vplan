# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Client configuration
"""
import os
from os import R_OK, access
from os.path import isfile
from typing import Any, Dict, Optional

import click
from pydantic import Field, validator  # pylint: disable=no-name-in-module
from pydantic_yaml import YamlEnum, YamlModel

from vplan.util import homedir, replace_envvars

DEFAULT_CONFIG = os.path.join(homedir(), ".config/vplan/client/application.yaml")


class ConnectionMode(str, YamlEnum):
    PORT = "port"
    SOCKET = "socket"


class ClientConfig(YamlModel):
    """Client configuration."""

    mode: ConnectionMode = Field(..., title="Connection mode, either port or socket")
    api_endpoint: Optional[str] = Field(title="HTTP endpoint, used in port mode")
    api_socket: Optional[str] = Field(title="Path to a UNIX socket, used in socket mode")

    @validator("api_endpoint")
    def _validate_api_endpoint(cls, api_endpoint: str, values: Dict[str, Any]) -> str:  # pylint: disable=no-self-argument
        if values["mode"] == ConnectionMode.PORT.value and not api_endpoint:
            raise ValueError("api_endpoint required in PORT mode")
        return api_endpoint

    @validator("api_socket")
    def _validate_api_socket(cls, api_socket: str, values: Dict[str, Any]) -> str:  # pylint: disable=no-self-argument
        if values["mode"] == ConnectionMode.SOCKET.value and not api_socket:
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
        return ClientConfig.parse_raw(yaml)


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
