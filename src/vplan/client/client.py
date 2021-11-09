# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
API client written in terms of Python requests.
"""
from typing import List, Optional

from vplan.engine.interface import Account, PlanSchema, Status


def retrieve_account() -> Account:
    """Retrieve account information stored in the plan engine."""
    return Account()


def create_account(account: Account) -> None:
    """Create your account in the plan engine."""


def update_account(account: Account) -> None:
    """Update your account in the plan engine."""


def delete_account() -> None:
    """Delete account information stored in the plan engine."""


def retrieve_account_status() -> Status:
    """Retrieve the enabled/disabled status of your account in the plan engine."""
    return Status()


def update_account_status(status: Status) -> None:
    """Set the enabled/disabled status of your account in the plan engine."""


def retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    return []


def retrieve_plan(plan_name: str) -> PlanSchema:
    """Return the plan definition stored in the plan engine."""
    return PlanSchema()


def create_plan(plan: PlanSchema) -> None:
    """Create a plan in the plan engine."""


def update_plan(plan_name: str, plan: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""


def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""


def refresh_plan(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""


def retrieve_plan_status(plan_name: str) -> Status:
    """Return the enabled/disabled status of a plan in the plan engine."""
    return Status()


def update_plan_status(plan_name: str, status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""


def test_group(plan_name: str, group_name: str, toggle_count: Optional[int]) -> None:
    """Test a device group that is part of a plan."""


def test_device(plan_name: str, room: str, device: str, toggle_count: Optional[int]) -> None:
    """Test a device that is part of a plan."""
