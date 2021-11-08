# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Server configuration
"""
import datetime
from os import R_OK, access, getenv
from os.path import isfile
from typing import Optional

from pydantic import Field, NonNegativeInt  # pylint: disable=no-name-in-module
from pydantic_yaml import YamlModel

from vplan.engine.interface import ServerException

# We read this environment variable to find the server configuration YAML file on disk
CONFIG_VAR = "VPLAN_CONFIG_PATH"


class DailyJobConfig(YamlModel):
    """Daily job configuration."""

    time: datetime.time = Field(..., title="When to run the per-location daily job, HH:MM:SS in the location's tz")
    jitter_sec: NonNegativeInt = Field(..., title="Jitter in seconds for the daily job time")
    misfire_grace_sec: NonNegativeInt = Field(..., title="Misfire grace period in seconds, if job can't be run on time")


class SchedulerConfig(YamlModel):
    """Scheduler configuration."""

    database_url: str = Field(..., title="SQLAlchemy database URL to use for the APScheduler job store")
    thread_pool_size: int = Field(..., title="The size of the APScheduler thread pool")
    daily_job: DailyJobConfig = Field(..., title="Daily job configuration")


class ServerConfig(YamlModel):
    """Server configuration."""

    database_dir: str = Field(..., title="Directory where all server databases are stored")
    database_url: str = Field(..., title="SQLAlchemy database URL to use for the application job store")
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
