# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Router for plan endpoints.
"""
from typing import List

from fastapi import APIRouter
from sqlalchemy.exc import NoResultFound
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from vplan.engine.database import (
    db_create_plan,
    db_delete_plan,
    db_retrieve_account,
    db_retrieve_all_plans,
    db_retrieve_plan,
    db_retrieve_plan_enabled,
    db_update_plan,
    db_update_plan_enabled,
)
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import Device, PlanSchema, Status
from vplan.engine.manager import schedule_daily_refresh, schedule_immediate_refresh, toggle_devices, unschedule_daily_refresh

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
    schedule_immediate_refresh(plan_name=schema.plan.name, location=schema.plan.location)
    schedule_daily_refresh(
        plan_name=schema.plan.name,
        location=schema.plan.location,
        refresh_time=schema.plan.refresh_time,
        time_zone=schema.plan.refresh_zone,
    )


@ROUTER.put("/plan", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_plan(schema: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""
    db_update_plan(schema=schema)
    schedule_immediate_refresh(plan_name=schema.plan.name, location=schema.plan.location)
    schedule_daily_refresh(
        plan_name=schema.plan.name,
        location=schema.plan.location,
        refresh_time=schema.plan.refresh_time,
        time_zone=schema.plan.refresh_zone,
    )


@ROUTER.delete("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""
    schema = db_retrieve_plan(plan_name)
    db_delete_plan(plan_name=schema.plan.name)
    schedule_immediate_refresh(plan_name=schema.plan.name, location=schema.plan.location)
    unschedule_daily_refresh(plan_name=schema.plan.name)


@ROUTER.get("/plan/{plan_name}/status", status_code=HTTP_200_OK)
def retrieve_status(plan_name: str) -> Status:
    """Return the enabled/disabled status of a plan in the plan engine."""
    enabled = db_retrieve_plan_enabled(plan_name=plan_name)
    return Status(enabled=enabled)


@ROUTER.put("/plan/{plan_name}/status", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_status(plan_name: str, status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""
    schema = retrieve_plan(plan_name)
    db_update_plan_enabled(plan_name=schema.plan.name, enabled=status.enabled)
    schedule_immediate_refresh(plan_name=schema.plan.name, location=schema.plan.location)


@ROUTER.post("/plan/{plan_name}/refresh", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def refresh_plan(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""
    schema = retrieve_plan(plan_name)
    schedule_immediate_refresh(plan_name=schema.plan.name, location=schema.plan.location)


@ROUTER.post("/plan/{plan_name}/test/group/{group_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def toggle_group(plan_name: str, group_name: str, toggles: int = 2) -> None:
    """Test a device group that is part of a plan."""
    account = db_retrieve_account()
    schema = db_retrieve_plan(plan_name=plan_name)
    location = schema.plan.location
    devices = schema.devices(group_name=group_name)
    if not devices:
        raise NoResultFound("Group not found or no devices in group")
    toggle_devices(pat_token=account.pat_token, location=location, devices=devices, toggles=toggles)


@ROUTER.post("/plan/{plan_name}/test/device/{room}/{device}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def toggle_device(plan_name: str, room: str, device: str, toggles: int = 2) -> None:
    """Test a device that is part of a plan."""
    item = Device(room=room, device=device)
    account = db_retrieve_account()
    schema = db_retrieve_plan(plan_name=plan_name)
    location = schema.plan.location
    devices = schema.devices()
    if item not in devices:
        raise NoResultFound("Device not found in plan")
    toggle_devices(pat_token=account.pat_token, location=location, devices=[item], toggles=toggles)
