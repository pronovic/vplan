# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import json
from datetime import datetime
from typing import Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vplan.engine.interface import RefreshRequest, RefreshResult, TriggerResult, TriggerRule, VacationPlan
from vplan.engine.server import API, API_VERSION

CLIENT = TestClient(API)

HEALTH_URL = "/health"
VERSION_URL = "/version"
REFRESH_URL = "/refresh"
TRIGGER_URL = "/trigger/%s"

NOW = datetime.now()
TIME_ZONE = "America/Chicago"
PAT_TOKEN = "xxx"
UNAUTHORIZED: Dict[str, str] = {}
AUTHORIZED = {"Authorization": "Bearer %s" % PAT_TOKEN}
CURRENT = VacationPlan(id="current", location="location", last_modified=NOW, triggers=[])
NEW = VacationPlan(id="new", location="location", last_modified=NOW, triggers=[])
RULE = TriggerRule(trigger_id="trigger", rule_id="rule_id", rule_name="rule_name")
REFRESH_RESULT = RefreshResult(id="result", location="whatever", time_zone="America/Chicago", finalized_date=NOW, rules=[RULE])
TRIGGER_RESULT = TriggerResult(id="trigger-id", location="whatever", time_zone="America/Chicago", rule=RULE)


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
        "headers,current,new,status,result",
        [
            (UNAUTHORIZED, CURRENT, NEW, 401, None),
            (AUTHORIZED, None, NEW, 200, REFRESH_RESULT),
            (AUTHORIZED, CURRENT, NEW, 200, REFRESH_RESULT),
        ],
        ids=["unauthorized", "no current", "with current"],
    )
    @patch("vplan.engine.server.refresh_plan")
    def test_api_refresh(self, refresh_plan, headers, current, new, status, result):
        refresh_plan.return_value = result
        request = RefreshRequest(current=current, new=new)
        response = CLIENT.post(url=REFRESH_URL, data=request.json(), headers=headers)
        assert response.status_code == status
        if status == 200:
            assert response.json() == json.loads(refresh_plan.return_value.json())
            refresh_plan.assert_called_once_with(pat_token=PAT_TOKEN, current=current, new=new)

    @pytest.mark.it("/refresh")
    @pytest.mark.parametrize(
        "headers,trigger_id,plan,status,result",
        [(UNAUTHORIZED, "trigger-id", NEW, 401, None), (AUTHORIZED, "trigger-id", NEW, 200, TRIGGER_RESULT)],
        ids=["unauthorized", "authorized"],
    )
    @patch("vplan.engine.server.execute_trigger_actions")
    def test_api_trigger(self, execute_trigger_actions, headers, trigger_id, plan, status, result):
        execute_trigger_actions.return_value = result
        response = CLIENT.put(url=TRIGGER_URL % trigger_id, data=plan.json(), headers=headers)
        assert response.status_code == status
        if status == 200:
            assert response.json() == json.loads(result.json())
            execute_trigger_actions.assert_called_once_with(pat_token=PAT_TOKEN, trigger_id=trigger_id, plan=plan)
