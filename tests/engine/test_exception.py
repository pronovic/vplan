# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from vplan.engine.exception import AlreadyExistsError, EngineError, SmartThingsClientError


class TestExceptions:
    def test_server_exception(self):
        exception = EngineError("hello")
        assert isinstance(exception, Exception)  # make sure parent class is right
        assert exception.message == "hello"

    def test_already_exists_error(self):
        exception = AlreadyExistsError("hello")
        assert isinstance(exception, EngineError)  # make sure parent class is right
        assert exception.message == "hello"

    def test_smartthings_client_error(self):
        exception = SmartThingsClientError("hello")
        assert isinstance(exception, EngineError)  # make sure parent class is right
        assert exception.message == "hello"
