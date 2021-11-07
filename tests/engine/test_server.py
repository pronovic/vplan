# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from vplan.engine.server import API, API_VERSION, shutdown_event, startup_event

CLIENT = TestClient(API)

HEALTH_URL = "/health"
VERSION_URL = "/version"
REFRESH_URL = "/refresh"


class TestLifecycle:

    pytestmark = pytest.mark.asyncio

    @patch("vplan.engine.server.start_scheduler")
    @patch("vplan.engine.server.makedirs")
    @patch("vplan.engine.server.config")
    async def test_startup_event(self, config, makedirs, start_scheduler):
        config.return_value = MagicMock(database_dir="thedir")
        await startup_event()
        makedirs.assert_called_once_with("thedir", mode=0o700, exist_ok=True)
        start_scheduler.assert_called_once()

    @patch("vplan.engine.server.shutdown_scheduler")
    async def test_shutdown_event(self, shutdown_scheduler):
        await shutdown_event()
        shutdown_scheduler.assert_called_once()


class TestApi:
    @pytest.mark.it("/health")
    def test_api_health(self):
        response = CLIENT.get(url=HEALTH_URL)
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}

    @pytest.mark.it("/version")
    @patch("vplan.engine.server.metadata_version")
    def test_api_version(self, metadata_version):
        metadata_version.return_value = "xxx"
        response = CLIENT.get(url=VERSION_URL)
        assert response.status_code == 200
        assert response.json() == {"package": "xxx", "api": API_VERSION}
