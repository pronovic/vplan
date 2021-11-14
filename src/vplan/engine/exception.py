# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Exceptions used across the engine implementation.
"""


class EngineError(Exception):
    """An error tied to the engine implementation."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class SmartThingsClientError(EngineError):
    """An error invoking the SmartThings API."""
