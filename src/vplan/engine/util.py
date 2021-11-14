# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from os import makedirs, stat
from stat import S_IMODE

from vplan.engine.config import config
from vplan.engine.exception import EngineError


def _create_and_check_dir(name: str, path: str) -> None:
    """Create a directory if needed, and check its permissions."""
    makedirs(path, mode=0o700, exist_ok=True)
    mode = S_IMODE(stat(path).st_mode)
    if mode != 0o700:
        raise EngineError("%s must have permissions 700, but has %o: %s" % (name, mode, path))


def setup_directories() -> None:
    """Set up and check permissions on required directories."""
    _create_and_check_dir("Database directory", config().database_dir)
