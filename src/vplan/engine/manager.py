# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
Manage high-level actions on behalf of the routers.
"""
import datetime
import time
from typing import List

from vplan.engine.config import config
from vplan.engine.interface import Device, SwitchState, parse_time
from vplan.engine.scheduler import schedule_daily_job, schedule_immediate_job, unschedule_daily_job
from vplan.engine.smartthings import LocationContext, set_switch


def schedule_daily_refresh(plan_name: str, refresh_time: str, time_zone: str) -> None:
    """Create or replace a job to periodically refresh the plan definition at SmartThings."""
    job_id = "daily/%s" % plan_name
    hour, minute = parse_time(refresh_time)
    trigger_time = datetime.time(hour=hour, minute=minute, second=0)
    func = refresh_plan
    kwargs = {"plan_name": plan_name}
    schedule_daily_job(job_id, trigger_time, func, kwargs, time_zone)


def unschedule_daily_refresh(plan_name: str) -> None:
    """Remove any existing daily refresh job."""
    job_id = "daily/%s" % plan_name
    unschedule_daily_job(job_id)


def schedule_immediate_refresh(plan_name: str) -> None:
    """Schedule a job to immediately refresh the plan definition at SmartThings."""
    job_id = "immediate/%s/%s" % (plan_name, datetime.datetime.now().isoformat())
    func = refresh_plan
    kwargs = {"plan_name": plan_name}
    schedule_immediate_job(job_id, func, kwargs)


def toggle_devices(pat_token: str, location: str, devices: List[Device], toggles: int) -> None:
    """Toggle group of devices, switching them on and off a certain number of times."""

    # This is sensitive to timing.  I've found that if you try to toggle the state
    # too quickly, even for local Zigbee devices, that sometimes the toggles don't work
    # as expected.  So, I recommend configuring at least a 5-second delay between toggles.

    with LocationContext(pat_token, location):
        for test in range(0, toggles):
            if test > 0:
                time.sleep(config().smartthings.toggle_delay_sec)
            for device in devices:
                set_switch(device, SwitchState.ON)
            time.sleep(config().smartthings.toggle_delay_sec)
            for device in devices:
                set_switch(device, SwitchState.OFF)


def refresh_plan(plan_name: str) -> None:
    """Refresh the plan definition at SmartThings, either replacing or removing all relevant rules."""
