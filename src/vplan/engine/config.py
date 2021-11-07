# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Server configuration
"""
from os import R_OK, access, getenv
from os.path import isfile
from typing import Optional

from pydantic import Field
from pydantic_yaml import YamlModel

# We read this environment variable to find the server configuration YAML file on disk
from vplan.engine.interface import ServerException

CONFIG_VAR = "VPLAN_CONFIG_PATH"


class SchedulerConfig(YamlModel):
    """Scheduler configuration."""

    database_url: str = Field(..., title="The SQLAlchemy database URL to use for the APScheduler job store")
    thread_pool_size: int = Field(..., title="The size of the APScheduler thread pool")


class ServerConfig(YamlModel):
    """Server configuration."""

    database_dir: str = Field(..., title="Directory where all server databases are stored")
    scheduler: SchedulerConfig = Field(..., title="Scheduler configuration")


_CONFIG: Optional[ServerConfig] = None


def _load_config(config_path: Optional[str] = None) -> ServerConfig:
    """Load server configuration from disk."""
    if not config_path:
        config_path = getenv(CONFIG_VAR, None)
        if not config_path:
            raise ServerException("Server is not properly configured, no $%s found" % CONFIG_VAR)
    if not (isfile(config_path) and access(config_path, R_OK)):
        raise ServerException("Server configuration is not readable: %s" % config_path)
    with open(config_path, "r", encoding="utf8") as fp:
        return ServerConfig.parse_raw(fp.read())


def reset() -> None:
    """Reset the config singleton, forcing it to be reloaded when next used."""
    global _CONFIG  # pylint: disable=global-statement
    _CONFIG = None


def config(config_path: Optional[str] = None) -> ServerConfig:
    """Retrieve server configuration, loading it from disk once and caching it."""
    global _CONFIG  # pylint: disable=global-statement
    if _CONFIG is None:
        _CONFIG = _load_config(config_path)
    return _CONFIG
