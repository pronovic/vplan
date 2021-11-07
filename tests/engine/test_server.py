# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vplan.engine.server import API, API_VERSION, startup_event

CLIENT = TestClient(API)

HEALTH_URL = "/health"
VERSION_URL = "/version"
REFRESH_URL = "/refresh"


class TestStartup:

    pytestmark = pytest.mark.asyncio

    @pytest.mark.it("startup_event()")
    @patch("vplan.engine.server.config")
    async def test_startup_event(self, config):
        await startup_event()
        config.assert_called_once()


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
