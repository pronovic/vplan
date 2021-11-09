# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vplan.engine.server import API, API_VERSION, shutdown_event, startup_event

CLIENT = TestClient(API)

HEALTH_URL = "/health"
VERSION_URL = "/version"


class TestLifecycle:

    pytestmark = pytest.mark.asyncio

    @patch("vplan.engine.server.start_scheduler")
    @patch("vplan.engine.server.setup_database")
    @patch("vplan.engine.server.setup_directories")
    async def test_startup_event(self, setup_directories, setup_database, start_scheduler):
        await startup_event()
        setup_directories.assert_called_once()
        setup_database.assert_called_once()
        start_scheduler.assert_called_once()

    @patch("vplan.engine.server.shutdown_scheduler")
    async def test_shutdown_event(self, shutdown_scheduler):
        await shutdown_event()
        shutdown_scheduler.assert_called_once()


class TestSystemEndpoints:
    @pytest.mark.it("/health")
    def test_health(self):
        response = CLIENT.get(url=HEALTH_URL)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    @pytest.mark.it("/version")
    @patch("vplan.engine.server.metadata_version")
    def test_version(self, metadata_version):
        metadata_version.return_value = "xxx"
        response = CLIENT.get(url=VERSION_URL)
        assert response.status_code == 200
        assert response.json() == {"package": "xxx", "api": API_VERSION}
