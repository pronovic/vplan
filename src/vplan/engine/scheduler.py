# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Manage the runtime scheduler for periodic jobs.
"""
import datetime
from typing import Any, Callable, Dict, Optional

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from vplan.engine.config import SchedulerConfig, config
from vplan.engine.interface import ServerException

_SCHEDULER: Optional[BackgroundScheduler] = None


def _init_scheduler(scheduler_config: SchedulerConfig) -> BackgroundScheduler:
    """Initialize the scheduler."""
    # Note that we're seeing up a thread pool with one thread, so that we only
    # have one job running at a time.  That way, we only have to deal with
    # rate-limiting behavior for the SmartThings API for a single thread at
    # a time, which simplifies the code.
    jobstores = {"sqlite": SQLAlchemyJobStore(url=scheduler_config.database_url)}
    executors = {"default": ThreadPoolExecutor(max_workers=1)}
    job_defaults = {"coalesce": True, "max_instances": 1}
    return BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone="UTC")


def scheduler() -> BackgroundScheduler:
    """Retrieve the scheduler, intended mostly for unit testing purposes."""
    if not _SCHEDULER:
        raise ServerException("Scheduler is not available")
    return _SCHEDULER


# pylint: disable=global-statement
def start_scheduler() -> None:
    """Start the scheduler, if it is not alrady started."""
    global _SCHEDULER
    if _SCHEDULER is None:
        _SCHEDULER = _init_scheduler(config().scheduler)
        _SCHEDULER.start()


# pylint: disable=global-statement
def shutdown_scheduler() -> None:
    """Shutdown the scheduler, if it is started."""
    global _SCHEDULER
    if _SCHEDULER is not None:
        _SCHEDULER.shutdown(wait=True)
        _SCHEDULER = None


def schedule_immediate_job(
    job_id: str,
    func: Callable[..., None],
    kwargs: Dict[str, Any],
) -> None:
    """
    Create a new job that will run immediately.

    Args:
        job_id(str): Job identifier, unique across the entire system
        func(Callable): Job function to invoke on the schedule
        kwargs(Dict[str, Any]): Keyword arguments to pass to the job function when invoked
    """
    if not _SCHEDULER:
        raise ServerException("Scheduler has not been started.")
    _SCHEDULER.add_job(id=job_id, jobstore="sqlite", func=func, kwargs=kwargs)


def schedule_daily_job(
    job_id: str,
    trigger_time: datetime.time,
    func: Callable[..., None],
    kwargs: Dict[str, Any],
    time_zone: str,
) -> None:
    """
    Create or replace a daily job that will run at a standard time forever, until removed.

    Args:
        job_id(str): Job identifier, unique across the entire system
        trigger_time(str): The time when the job should be executed
        func(Callable): Job function to invoke on the schedule
        kwargs(Dict[str, Any]): Keyword arguments to pass to the job function when invoked
        time_zone: Time zone in which to execute the job
    """
    if not _SCHEDULER:
        raise ServerException("Scheduler has not been started.")
    jitter = config().scheduler.daily_job.jitter_sec
    grace = config().scheduler.daily_job.misfire_grace_sec
    hour, minute, second = trigger_time.hour, trigger_time.minute, trigger_time.second
    trigger = CronTrigger(hour=hour, minute=minute, second=second, timezone=time_zone, jitter=jitter)
    _SCHEDULER.add_job(
        id=job_id,
        jobstore="sqlite",
        func=func,
        trigger=trigger,
        kwargs=kwargs,
        replace_existing=True,
        misfire_grace_time=grace,
    )


def unschedule_daily_job(job_id: str) -> None:
    """Unschedule a daily job, which stops it from running"""
    if not _SCHEDULER:
        raise ServerException("Scheduler has not been started.")
    try:
        _SCHEDULER.remove_job(job_id=job_id)
    except JobLookupError:
        pass
