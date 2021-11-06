# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Implements the plan-related business logic.

Whenever a refresh is requested, the following steps occur:

1. For each device that has been added to or deleted from the current vacation plan,
   toggle the device off
2. Regenerate all rules based on the new vacation plan, including any random variations in
   start or stop times
3. Delete all existing SmartThings rules controlled by the current vacation plan
4. Insert newly-generated SmartThings rules for the new vacation plan
5. For each device, determine its correct state based on the new plan and current time,
   and set that state

We need to be very careful about state, or we might inadvertently leave a
device on or off forever.  This could happen if the plan changes, or if we
happen to be executing the plan refresh during a window when the device state
was scheduled to change.  This is why we toggle off devices removed from
the plan and explicitly set the correct device state before finishing.
"""

from datetime import datetime
from typing import Optional

from vplan.engine.interface import PlanImplementation, PlanLocation, VacationPlan


# pylint: disable=unused-argument
def refresh_plan(pat_token: str, current: Optional[VacationPlan], new: VacationPlan) -> PlanImplementation:
    """
    Refresh the vacation plan in SmartThings.

    Args:
        pat_token(str): The SmartThings PAT token (personal access token)
        current(VacationPlan): The current vacation plan, possibly unset
        new(VacationPlan): The new vacation plan

    Returns:
        PlanImplementation: Description of the plan implementation at SmartThings
    """
    # TODO: implement refresh_plan()
    return PlanImplementation(
        id=new.id,
        finalized_date=datetime.utcnow(),
        location=PlanLocation(id=new.id, name=new.location_name, time_zone="America/Chicago"),
        rules=[],
    )
