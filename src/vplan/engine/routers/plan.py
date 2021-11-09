# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Router for plan endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import Device, DeviceGroup, PlanSchema, Status

ROUTER = APIRouter()


@ROUTER.get("/plan", status_code=HTTP_200_OK)
def retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    return []


@ROUTER.get("/plan/{plan_name}", status_code=HTTP_200_OK)
def retrieve_plan() -> PlanSchema:
    """Return the plan definition stored in the plan engine."""
    return None  # type: ignore


@ROUTER.post("/plan", status_code=HTTP_201_CREATED, response_class=EmptyResponse)
def create_plan(plan: PlanSchema) -> None:
    """Create a plan in the plan engine."""


@ROUTER.put("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_plan(plan: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""


@ROUTER.delete("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""


@ROUTER.get("/plan/{plan_name}/status", status_code=HTTP_200_OK)
def retrieve_status() -> Status:
    """Return the enabled/disabled status of a plan in the plan engine."""


@ROUTER.put("/plan/{plan_name}/status", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_status(status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""


@ROUTER.post("/plan/{plan_name}/test/group", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_group(group: DeviceGroup, toggle_count: Optional[int]) -> None:
    """Test a device group that is part of a plan."""


@ROUTER.post("/plan/{plan_name}/test/device", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_device(device: Device, toggle_count: Optional[int]) -> None:
    """Test a device that is part of a plan."""