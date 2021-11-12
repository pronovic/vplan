# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Manage SmartThings behaviors.
"""
import datetime
from typing import List

from vplan.engine.interface import Device, parse_time
from vplan.engine.scheduler import schedule_daily_job, schedule_immediate_job, unschedule_daily_job


def st_schedule_daily_refresh(plan_name: str, refresh_time: str, time_zone: str) -> None:
    """Create or replace a job to periodically refresh the plan definition at SmartThings."""
    job_id = "daily/%s" % plan_name
    hour, minute = parse_time(refresh_time)
    time = datetime.time(hour=hour, minute=minute, second=0)
    func = st_refresh_plan
    kwargs = {"plan_name": plan_name}
    schedule_daily_job(job_id, time, func, kwargs, time_zone)


def st_unschedule_daily_refresh(plan_name: str) -> None:
    """Remove any existing daily refresh job."""
    job_id = "daily/%s" % plan_name
    unschedule_daily_job(job_id)


def st_schedule_immediate_refresh(plan_name: str) -> None:
    """Schedule a job to immediately refresh the plan definition at SmartThings."""
    job_id = "immediate/%s/%s" % (plan_name, datetime.datetime.now().isoformat())
    func = st_refresh_plan
    kwargs = {"plan_name": plan_name}
    schedule_immediate_job(job_id, func, kwargs)


def st_toggle_devices(pat_token: str, location: str, devices: List[Device], toggles: int) -> None:
    """Test toggling a group of devices, switching them on and off a certain number of times."""


def st_refresh_plan(plan_name: str) -> None:
    """Refresh the plan definition at SmartThings, either replacing or removing all relevant rules."""
