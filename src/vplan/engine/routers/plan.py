# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Router for plan endpoints.
"""
from typing import List

from fastapi import APIRouter
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from vplan.engine.database import (
    db_create_plan,
    db_delete_plan,
    db_retrieve_all_plans,
    db_retrieve_plan,
    db_retrieve_plan_enabled,
    db_update_plan,
    db_update_plan_enabled,
)
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import PlanSchema, Status
from vplan.engine.smartthings import st_schedule_daily_refresh, st_schedule_immediate_refresh, st_test_device, st_test_group

ROUTER = APIRouter()


@ROUTER.get("/plan", status_code=HTTP_200_OK)
def retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    return db_retrieve_all_plans()


@ROUTER.get("/plan/{plan_name}", status_code=HTTP_200_OK)
def retrieve_plan(plan_name: str) -> PlanSchema:
    """Return the plan definition stored in the plan engine."""
    return db_retrieve_plan(plan_name=plan_name)


@ROUTER.post("/plan", status_code=HTTP_201_CREATED, response_class=EmptyResponse)
def create_plan(schema: PlanSchema) -> None:
    """Create a plan in the plan engine."""
    db_create_plan(schema=schema)
    st_schedule_daily_refresh(plan_name=schema.plan.name, refresh_time=schema.plan.refresh_time)


@ROUTER.put("/plan", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_plan(schema: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""
    db_update_plan(schema=schema)
    st_schedule_daily_refresh(plan_name=schema.plan.name, refresh_time=schema.plan.refresh_time)
    if db_retrieve_plan_enabled(plan_name=schema.plan.name):
        st_schedule_immediate_refresh(plan_name=schema.plan.name)


@ROUTER.delete("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""
    db_delete_plan(plan_name=plan_name)
    st_schedule_immediate_refresh(plan_name=plan_name)


@ROUTER.get("/plan/{plan_name}/status", status_code=HTTP_200_OK)
def retrieve_status(plan_name: str) -> Status:
    """Return the enabled/disabled status of a plan in the plan engine."""
    enabled = db_retrieve_plan_enabled(plan_name=plan_name)
    return Status(enabled=enabled)


@ROUTER.put("/plan/{plan_name}/status", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_status(plan_name: str, status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""
    db_update_plan_enabled(plan_name=plan_name, enabled=status.enabled)
    st_schedule_immediate_refresh(plan_name=plan_name)


@ROUTER.post("/plan/{plan_name}/refresh", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def refresh_plan(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""
    st_schedule_immediate_refresh(plan_name=plan_name)


@ROUTER.post("/plan/{plan_name}/test/group/{group_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_group(plan_name: str, group_name: str, toggle_count: int) -> None:
    """Test a device group that is part of a plan."""
    st_test_group(plan_name=plan_name, group_name=group_name, toggle_count=toggle_count)


@ROUTER.post("/plan/{plan_name}/test/device/{room}/{device}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_device(plan_name: str, room: str, device: str, toggle_count: int) -> None:
    """Test a device that is part of a plan."""
    st_test_device(plan_name=plan_name, room=room, device=device, toggle_count=toggle_count)
