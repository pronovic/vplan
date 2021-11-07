# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Classes that are part of the API public interface.
"""

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from vplan.config import VacationPlan


class Health(BaseModel):
    """API health data"""

    status: str = Field("OK")


class Version(BaseModel):
    """API version data"""

    package: str = Field(...)
    api: str = Field(...)


class TriggerRule(BaseModel):
    """Identifies a rule that implements a trigger."""

    trigger_id: str = Field(..., title="Id of the trigger this rule is associated with")
    rule_id: str = Field(..., title="Identifier for the rule at SmartThings")
    rule_name: str = Field(..., title="Name of the rule at SmartThings")


class RefreshRequest(BaseModel):
    """Vacation plan refresh request."""

    current: Optional[VacationPlan] = Field(default=None, title="Current vacation plan, possibly unset")
    new: VacationPlan = Field(..., title="New vacation plan")


class RefreshResult(BaseModel):
    """The result from a plan request refresh request."""

    id: str = Field(..., title="Plan identifier")
    location: str = Field(..., title="Name of the location")
    time_zone: str = Field(..., title="Time zone that the plan will execute in")
    finalized_date: datetime.datetime = Field(..., title="Date the plan was finalized in the SmartThings infrastructure")
    rules: List[TriggerRule] = Field(..., title="List of the SmartThings rules that implement the plan triggers")


class TriggerResult(BaseModel):
    """The result from a trigger test request."""

    id: str = Field(..., title="Plan identifier")
    location: str = Field(..., title="Name of the location")
    time_zone: str = Field(..., title="Time zone that the trigger was executed in")
    rule: TriggerRule = Field(..., title="The trigger rule that was tested")
