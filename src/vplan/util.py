# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
General utilities.
"""

import os
from pathlib import Path


def homedir() -> str:
    """Return the user's home directory."""
    return str(Path.home())


def replace_envvars(source: str) -> str:
    """Replace constructs like {VAR} with environment variables."""
    return source.format(**os.environ)
