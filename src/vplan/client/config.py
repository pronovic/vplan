# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Client configuration
"""
import os
from os import R_OK, access
from os.path import isfile
from typing import Any, Dict, Optional

from pydantic import Field, validator  # pylint: disable=no-name-in-module
from pydantic_yaml import YamlEnum, YamlModel

from vplan.engine.interface import ServerException
from vplan.util import homedir, replace_envvars

CONFIG_PATH = ".config/vplan/client/application.yaml"


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


# look up other value in values, set v accordingly.


_CONFIG: Optional[ClientConfig] = None


def _load_config(config_path: Optional[str] = None) -> ClientConfig:
    """Load client configuration from disk, substituting environment variables of the form {VAR}."""
    if not config_path:
        config_path = os.path.join(homedir(), CONFIG_PATH)
    if not (isfile(config_path) and access(config_path, R_OK)):
        raise ServerException("Client configuration is not readable: %s" % config_path)
    with open(config_path, "r", encoding="utf8") as fp:
        yaml = replace_envvars(fp.read())
        return ClientConfig.parse_raw(yaml)


def reset() -> None:
    """Reset the config singleton, forcing it to be reloaded when next used."""
    global _CONFIG  # pylint: disable=global-statement
    _CONFIG = None


def config(config_path: Optional[str] = None) -> ClientConfig:
    """Retrieve server configuration, loading it from disk once and caching it."""
    global _CONFIG  # pylint: disable=global-statement
    if _CONFIG is None:
        _CONFIG = _load_config(config_path)
    return _CONFIG
