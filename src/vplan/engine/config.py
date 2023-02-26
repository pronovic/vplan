# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Server configuration
"""
import os
import re
from os import R_OK, access
from os.path import isfile
from typing import Optional

from pydantic import ConstrainedStr, Field, NonNegativeInt  # pylint: disable=no-name-in-module
from pydantic_yaml import YamlModel

from vplan.engine.exception import EngineError
from vplan.util import replace_envvars

# We read this environment variable to find the server configuration YAML file on disk
CONFIG_VAR = "VPLAN_CONFIG_PATH"


class LogLevel(ConstrainedStr):
    """Legal log levels."""

    strip_whitespace = True
    regex = re.compile(r"^(CRITICAL|ERROR|WARNING|INFO|DEBUG|NOTSET)$")


class DailyJobConfig(YamlModel):
    """Daily job configuration."""

    jitter_sec: NonNegativeInt = Field(..., description="Jitter in seconds for the daily job time")
    misfire_grace_sec: NonNegativeInt = Field(..., description="Misfire grace period in seconds, if job can't be run on time")


class RetryConfig(YamlModel):
    """Retry configuration."""

    max_attempts: NonNegativeInt = Field(..., description="Maximum number of attempts for the daily job, including initial attempt")
    min_sec: NonNegativeInt = Field(..., description="Minimum delay for the retry exponential backoff, in seconds")
    max_sec: NonNegativeInt = Field(..., description="Maximum delay for the retry exponential backoff, in seconds")


class SchedulerConfig(YamlModel):
    """Scheduler configuration."""

    database_url: str = Field(..., description="SQLAlchemy database URL to use for the APScheduler job store")
    daily_job: DailyJobConfig = Field(..., description="Daily job configuration")


class SmartThingsConfig(YamlModel):
    """SmartThings API configuration."""

    base_api_url: str = Field(..., description="URL for the SmartThings API")


class ServerConfig(YamlModel):
    """Server configuration."""

    database_dir: str = Field(..., description="Directory where all server databases are stored")
    database_url: str = Field(..., description="SQLAlchemy database URL to use for the application job store")
    database_log_level: LogLevel = Field(..., description="The log level to use for database messages from SQLAlchemy")
    smartthings: SmartThingsConfig = Field(..., description="Configuration for the SmartThings interface")
    scheduler: SchedulerConfig = Field(..., description="Scheduler configuration")
    retry: RetryConfig = Field(..., description="Retry configuration")


_CONFIG: Optional[ServerConfig] = None


def _load_config(config_path: Optional[str] = None) -> ServerConfig:
    """Load server configuration from disk, substituting environment variables of the form {VAR}."""
    if not config_path:
        config_path = os.environ[CONFIG_VAR] if CONFIG_VAR in os.environ else None
        if not config_path:
            raise EngineError("Server is not properly configured, no $%s found" % CONFIG_VAR)
    if not (isfile(config_path) and access(config_path, R_OK)):
        raise EngineError("Server configuration is not readable: %s" % config_path)
    with open(config_path, "r", encoding="utf8") as fp:
        yaml = replace_envvars(fp.read())
        return ServerConfig.parse_raw(yaml)  # type: ignore


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
