# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vplan.engine.server import API, API_VERSION, lifespan

CLIENT = TestClient(API)


class TestLifecycle:
    pytestmark = pytest.mark.asyncio

    @patch("vplan.engine.server.shutdown_scheduler")
    @patch("vplan.engine.server.start_scheduler")
    @patch("vplan.engine.server.setup_database")
    @patch("vplan.engine.server.setup_directories")
    async def test_lifespan(self, setup_directories, setup_database, start_scheduler, shutdown_scheduler):
        async with lifespan(None):
            # these are called when the lifespan starts
            setup_directories.assert_called_once()
            setup_database.assert_called_once()
            start_scheduler.assert_called_once()
            shutdown_scheduler.assert_not_called()
        # and then this is called when the lifespan completes, after the yield
        shutdown_scheduler.assert_called_once()


class TestRoutes:
    def test_health(self):
        response = CLIENT.get(url="/health")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    @patch("vplan.engine.server.metadata_version")
    def test_version(self, metadata_version):
        metadata_version.return_value = "xxx"
        response = CLIENT.get(url="/version")
        assert response.status_code == 200
        assert response.json() == {"package": "xxx", "api": API_VERSION}
