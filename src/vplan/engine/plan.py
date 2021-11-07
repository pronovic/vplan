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

import datetime
from typing import Optional

from vplan.config import VacationPlan
from vplan.engine.interface import RefreshResult, TriggerResult, TriggerRule


# pylint: disable=unused-argument
def refresh_plan(pat_token: str, current: Optional[VacationPlan], new: VacationPlan) -> RefreshResult:
    """Refresh the vacation plan in SmartThings."""
    # TODO: implement refresh_plan()
    return RefreshResult(
        id=new.id,
        location=new.location,
        time_zone="America/Chicago",  # TODO: fix this to come from retrieved data
        finalized_date=datetime.datetime.utcnow(),
        rules=[],
    )


# pylint: disable=unused-argument
def execute_trigger_actions(pat_token: str, trigger_id: str, plan: VacationPlan) -> TriggerResult:
    """Manually execute the actions associated with a trigger, for testing the device setup."""
    # TODO: implement execute_trigger_actions()
    return TriggerResult(
        id=plan.id,
        locatin=plan.location,
        time_zone="America/Chicago",  # TODO: fix this to come from retrieved data
        rule=TriggerRule(trigger_id=trigger_id, rule_id="XXX", rule_name="YYY"),  # TODO: fix trigger rule
    )
