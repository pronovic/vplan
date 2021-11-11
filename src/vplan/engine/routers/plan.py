# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Router for plan endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter
from sqlalchemy import update
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from vplan.engine.database import dbsession
from vplan.engine.entity import PlanEntity
from vplan.engine.fastapi.extensions import EmptyResponse
from vplan.engine.interface import PlanSchema, Status

ROUTER = APIRouter()


@ROUTER.get("/plan", status_code=HTTP_200_OK)
def retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    with dbsession() as session:
        return [entity.plan_name for entity in session.query(PlanEntity).all()]


@ROUTER.get("/plan/{plan_name}", status_code=HTTP_200_OK)
def retrieve_plan(plan_name: str) -> PlanSchema:
    """Return the plan definition stored in the plan engine."""
    with dbsession() as session:
        entity = session.query(PlanEntity).where(PlanEntity.plan_name == plan_name).one()
        return PlanSchema.parse_raw(entity.definition)


@ROUTER.post("/plan", status_code=HTTP_201_CREATED, response_class=EmptyResponse)
def create_plan(plan: PlanSchema) -> None:
    """Create a plan in the plan engine."""
    with dbsession() as session:
        entity = PlanEntity()
        entity.plan_name = plan.plan.name
        entity.enabled = False
        entity.definition = plan.yaml()
        session.add(entity)


@ROUTER.put("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_plan(plan_name: str, plan: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""
    with dbsession() as session:
        session.execute(update(PlanEntity).where(PlanEntity.plan_name == plan_name).values(definition=plan.yaml()))
        # TODO: there should be a warning if we enable a plan and no account is set
        # TODO: kick off work to update SmartThings, if the plan is enabled


@ROUTER.delete("/plan/{plan_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""
    with dbsession() as session:
        session.query(PlanEntity).where(PlanEntity.plan_name == plan_name).delete()
        # TODO: kick off work to clean up SmartThings


@ROUTER.get("/plan/{plan_name}/status", status_code=HTTP_200_OK)
def retrieve_status(plan_name: str) -> Status:
    """Return the enabled/disabled status of a plan in the plan engine."""
    with dbsession() as session:
        entity = session.query(PlanEntity).where(PlanEntity.plan_name == plan_name).one()
        return Status(enabled=entity.enabled)


@ROUTER.put("/plan/{plan_name}/status", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def update_status(plan_name: str, status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""
    with dbsession() as session:
        session.execute(update(PlanEntity).where(PlanEntity.plan_name == plan_name).values(enabled=status.enabled))
        # TODO: kick off work to update SmartThings


@ROUTER.post("/plan/{plan_name}/refresh", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def refresh_plan(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""
    # TODO: kick off work to update SmartThings


@ROUTER.post("/plan/{plan_name}/test/group/{group_name}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_group(plan_name: str, group_name: str, toggle_count: Optional[int]) -> None:
    """Test a device group that is part of a plan."""
    # TODO: implement test_group()


@ROUTER.post("/plan/{plan_name}/test/device/{room}/{device}", status_code=HTTP_204_NO_CONTENT, response_class=EmptyResponse)
def test_device(plan_name: str, room: str, device: str, toggle_count: Optional[int]) -> None:
    """Test a device that is part of a plan."""
    # TODO: implement test_group()
