# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Router for plan endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from vplan.engine.database import (
    db_create_plan,
    db_delete_plan,
    db_retrieve_all_plans,
    db_retrieve_plan,
    db_retrieve_plan_status,
    db_update_plan,
    db_update_plan_status,
)
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import PlanSchema, Status

ROUTER = APIRouter()


@ROUTER.get("/plan", status_code=HTTP_200_OK)
def retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    return db_retrieve_all_plans()


@ROUTER.get("/plan/{plan_name}", status_code=HTTP_200_OK)
def retrieve_plan(plan_name: str) -> PlanSchema:
    """Return the plan definition stored in the plan engine."""
    return db_retrieve_plan(plan_name)


@ROUTER.post("/plan", status_code=HTTP_201_CREATED, response_class=EmptyResponse)
def create_plan(plan: PlanSchema) -> None:
    """Create a plan in the plan engine."""
    db_create_plan(plan)


@ROUTER.put("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_plan(plan_name: str, plan: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""
    db_update_plan(plan, plan_name)
    # TODO: kick off work to update SmartThings, if the plan is enabled


@ROUTER.delete("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""
    db_delete_plan(plan_name)
    # TODO: kick off work to clean up SmartThings, removing rules for the deleted plan


@ROUTER.get("/plan/{plan_name}/status", status_code=HTTP_200_OK)
def retrieve_status(plan_name: str) -> Status:
    """Return the enabled/disabled status of a plan in the plan engine."""
    return db_retrieve_plan_status(plan_name)


@ROUTER.put("/plan/{plan_name}/status", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_status(plan_name: str, status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""
    db_update_plan_status(plan_name, status.enabled)
    # TODO: kick off work to update SmartThings, adding or removing rules


@ROUTER.post("/plan/{plan_name}/refresh", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def refresh_plan(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""
    # TODO: kick off work to update SmartThings based on current state of plan


@ROUTER.post("/plan/{plan_name}/test/group/{group_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_group(plan_name: str, group_name: str, toggle_count: Optional[int]) -> None:
    """Test a device group that is part of a plan."""
    # TODO: implement test_group()


@ROUTER.post("/plan/{plan_name}/test/device/{room}/{device}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_device(plan_name: str, room: str, device: str, toggle_count: Optional[int]) -> None:
    """Test a device that is part of a plan."""
    # TODO: implement test_group()
