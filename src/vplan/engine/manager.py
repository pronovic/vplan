# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Manage high-level actions on behalf of the routers.
"""
import datetime
import logging
from time import sleep
from typing import List, Union

import pytz
from sqlalchemy.exc import NoResultFound

from vplan.engine.database import db_retrieve_account, db_retrieve_plan, db_retrieve_plan_enabled
from vplan.engine.scheduler import schedule_daily_job, schedule_immediate_job, unschedule_daily_job
from vplan.engine.smartthings import SmartThings, build_plan_rules, parse_time, replace_rules, set_switch
from vplan.interface import Device, PlanSchema, SimpleTime, SwitchState, TimeZone
from vplan.util import now


def schedule_daily_refresh(
    plan_name: str, location: str, refresh_time: Union[str, SimpleTime], time_zone: Union[str, TimeZone]
) -> None:
    """Create or replace a job to periodically refresh the plan definition at SmartThings."""
    job_id = "daily/%s" % plan_name
    hour, minute = parse_time(refresh_time)
    trigger_time = datetime.time(hour=hour, minute=minute, second=0)
    func = refresh_plan
    kwargs = {"plan_name": plan_name, "location": location}
    schedule_daily_job(job_id, trigger_time, func, kwargs, time_zone)


def unschedule_daily_refresh(plan_name: str) -> None:
    """Remove any existing daily refresh job."""
    job_id = "daily/%s" % plan_name
    unschedule_daily_job(job_id)


def schedule_immediate_refresh(plan_name: str, location: str) -> None:
    """Schedule a job to immediately refresh the plan definition at SmartThings."""
    job_id = "immediate/%s/%s" % (plan_name, now(pytz.UTC).isoformat())
    func = refresh_plan
    kwargs = {"plan_name": plan_name, "location": location}
    schedule_immediate_job(job_id, func, kwargs)


def validate_plan(schema: PlanSchema) -> None:
    """Validate a plan schema, throwing InvalidPlanError if there are problems."""

    account = db_retrieve_account()
    with SmartThings(account.pat_token, schema.plan.location):
        build_plan_rules(schema)


def set_device_state(location: str, devices: List[Device], state: SwitchState) -> None:
    """Set state for a group of devices."""
    account = db_retrieve_account()
    with SmartThings(account.pat_token, location):
        for device in devices:
            set_switch(device, state)


def toggle_devices(location: str, devices: List[Device], toggles: int, delay_sec: int) -> None:
    """Toggle group of devices, switching them on and off a certain number of times."""
    account = db_retrieve_account()
    with SmartThings(account.pat_token, location):
        for test in range(0, toggles):
            if test > 0:
                sleep(delay_sec)
            for device in devices:
                set_switch(device, SwitchState.ON)
            sleep(delay_sec)
            for device in devices:
                set_switch(device, SwitchState.OFF)


def refresh_plan(plan_name: str, location: str) -> None:
    """
    Refresh the plan definition at SmartThings, either replacing or removing rules.

    This is not intended to be run directly by other code.  Instead, it's a target
    for the refresh jobs, scheduled via the functions above.

    We need both the plan name and the location so that we can still interact
    with SmartThings to clear out the rules, even if the plan has been deleted
    when the job runs.  If the location of the retrieved plan does not match
    the location provided to the job, we treat this as removal from the job's
    location.

    Args:
        plan_name:  The name of the plan to refresh
        location:   The location where the plan will execute
    """

    logging.info("Refreshing plan %s at location %s", plan_name, location)

    try:

        try:
            account = db_retrieve_account()
        except NoResultFound:
            logging.error("Account not found; refresh cannot proceed")
            return

        try:
            enabled = db_retrieve_plan_enabled(plan_name)
            if not enabled:
                schema = None
            else:
                schema = db_retrieve_plan(plan_name)
                if location != schema.plan.location:
                    logging.error("Plan location does not match job location; treating this as a disabled plan")
                    schema = None
        except NoResultFound:
            logging.error("Plan not found; treating this as a disabled plan")
            schema = None

        with SmartThings(account.pat_token, location):
            replace_rules(plan_name, schema)

        logging.info("Completed refreshing plan %s at location %s", plan_name, location)

    except Exception:  # pylint: disable=broad-except

        # We want the job to always succeed, and just log information on failure
        logging.exception("Refresh failed")
