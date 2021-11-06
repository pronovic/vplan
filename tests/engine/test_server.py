# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import json
from datetime import datetime
from typing import Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vplan.engine.interface import PlanImplementation, PlanLocation, RefreshRequest, VacationPlan
from vplan.engine.server import API, API_VERSION

CLIENT = TestClient(API)

HEALTH_URL = "/health"
VERSION_URL = "/version"
REFRESH_URL = "/refresh"

NOW = datetime.now()
TIME_ZONE = "America/Chicago"
PAT_TOKEN = "xxx"
UNAUTHORIZED: Dict[str, str] = {}
AUTHORIZED = {"Authorization": "Bearer %s" % PAT_TOKEN}
LOCATION = PlanLocation(id="loc", name="location", time_zone=TIME_ZONE)
CURRENT = VacationPlan(id="current", location_name="location", last_modified=datetime.now())
NEW = VacationPlan(id="new", location_name="location", last_modified=NOW)
IMPLEMENTATION = PlanImplementation(id="result", finalized_date=NOW, location=LOCATION, rules=[])


class TestApi:

    """Test the public API endpoints via a client."""

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

    @pytest.mark.it("/refresh")
    @pytest.mark.parametrize(
        "headers,current,new,status,response",
        [
            (UNAUTHORIZED, CURRENT, NEW, 401, None),
            (AUTHORIZED, None, NEW, 200, IMPLEMENTATION),
            (AUTHORIZED, CURRENT, NEW, 200, IMPLEMENTATION),
        ],
        ids=["unauthorized", "no current", "with current"],
    )
    @patch("vplan.engine.server.refresh_plan")
    def test_api_refresh(self, refresh_plan, headers, current, new, status, response):
        refresh_plan.return_value = response
        request = RefreshRequest(current=current, new=new)
        response = CLIENT.post(url=REFRESH_URL, data=request.json(), headers=headers)
        assert response.status_code == status
        if status == 200:
            assert response.json() == json.loads(refresh_plan.return_value.json())
            refresh_plan.assert_called_once_with(pat_token=PAT_TOKEN, current=current, new=new)
