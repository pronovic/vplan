# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Manage SmartThings behaviors.
"""


def st_schedule_daily_refresh(plan_name: str, refresh_time: str) -> None:
    """Schedule the daily refresh job"""


def st_schedule_immediate_refresh(plan_name: str) -> None:
    """Schedule a job to immediately refresh the plan definition at SmartThings."""

    # The plan refresh action takes into account the current deleted/enabled/disabled
    # state of the plan.  Plans that are enabled will have their rules regenerated in
    # SmartThings.  Plans that are disabled or do not exist will have their rules
    # removed in SmartThings.  The action taken by the job is based on the state of
    # the plan at the time the job is executed.

    # TODO: if there is a refresh for this job already scheduled for immediate
    #       execution, then this is a no-op


def st_test_group(plan_name: str, group_name: str, toggle_count: int) -> None:
    """Test a device group that is part of a plan."""
    # TODO: implement st_test_group()


def st_test_device(plan_name: str, room: str, device: str, toggle_count: int) -> None:
    """Test a device that is part of a plan."""
    # TODO: implement test_device()
