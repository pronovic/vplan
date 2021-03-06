# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import datetime
from unittest.mock import MagicMock, patch

import pytest
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from busypie import SECOND, wait
from tzlocal import get_localzone

from vplan.engine.config import DailyJobConfig, SchedulerConfig
from vplan.engine.exception import EngineError
from vplan.engine.scheduler import (
    schedule_daily_job,
    schedule_immediate_job,
    scheduler,
    shutdown_scheduler,
    start_scheduler,
    unschedule_daily_job,
)
from vplan.util import now

INDICATOR = None
JOB_DELAY_SEC = 2  # if the job is intermittently unreliable, increase this value slightly


def job_function(message):
    """Job function to be scheduled; it sets INDICATOR so we can tell that the job worked."""
    global INDICATOR  # pylint: disable=global-statement
    INDICATOR = message


def in_future(seconds, tz):
    """Return a time some number of seconds into the future"""
    timestamp = now(tz=tz)
    future = timestamp + datetime.timedelta(seconds=seconds)
    return future.time().replace(microsecond=0)


def assert_no_jobs():
    """Assert that there are no jobs"""
    assert len(scheduler().get_jobs()) == 0


def assert_daily_job_definition(job_id, kwargs):
    """Assert that the job definition matches expectations."""
    jobs = scheduler().get_jobs()
    assert len(jobs) > 0  # there should be at least one job
    job = jobs[0]
    assert job.id == job_id
    assert job.func is job_function
    assert job.kwargs == kwargs
    assert job.misfire_grace_time == 1
    assert isinstance(job.trigger, CronTrigger)
    assert job.trigger.jitter == 0
    # we can't confirm much about the schedule, but the actual execution behavior should prove that's ok


def assert_immediate_job_definition(job_id, kwargs):
    """Assert that the job definition matches expectations."""
    jobs = scheduler().get_jobs()
    assert len(jobs) > 0  # there should be at least one job
    job = jobs[0]
    assert job.id == job_id
    assert job.func is job_function
    assert job.kwargs == kwargs
    assert isinstance(job.trigger, DateTrigger)
    # we can't confirm much about the schedule, but the actual execution behavior should prove that's ok


class TestLifecycle:
    @patch("vplan.engine.scheduler.config")
    def test_scheduler_lifecycle(self, config, tmpdir):
        shutdown_scheduler()

        # this sets things up so the daily job is scheduled a few seconds from now, so we can check that it runs
        tz = get_localzone()
        time1 = in_future(seconds=JOB_DELAY_SEC, tz=tz)
        time2 = in_future(seconds=JOB_DELAY_SEC * 2, tz=tz)
        database_url = "sqlite+pysqlite:///%s" % tmpdir.join("jobs.sqlite").realpath()
        daily = DailyJobConfig(jitter_sec=0, misfire_grace_sec=1)
        scheduler_config = SchedulerConfig(database_url=database_url, daily_job=daily)
        config.return_value = MagicMock(scheduler=scheduler_config)

        try:
            start_scheduler()
            assert scheduler() is not None

            # Create a daily job and make sure it executes
            schedule_daily_job(
                job_id="test_job", trigger_time=time1, func=job_function, kwargs={"message": "job #1"}, time_zone="%s" % tz
            )
            assert_daily_job_definition("test_job", {"message": "job #1"})
            wait().at_most(JOB_DELAY_SEC, SECOND).until(lambda: INDICATOR == "job #1")

            # Recreate the daily job and make sure updates are reflected
            schedule_daily_job(
                job_id="test_job", trigger_time=time2, func=job_function, kwargs={"message": "job #2"}, time_zone="%s" % tz
            )
            assert_daily_job_definition("test_job", {"message": "job #2"})
            wait().at_most(JOB_DELAY_SEC, SECOND).until(lambda: INDICATOR == "job #2")

            # Remove the daily job and make sure the change takes effect
            unschedule_daily_job(job_id="test_job")
            assert_no_jobs()

            # Confirm that we don't get an error removing a nonexistent job
            unschedule_daily_job(job_id="test_job")

            # Schedule an immediate job, make sure it runs immediately, and make sure it goes away when done
            schedule_immediate_job(job_id="immediate_job", func=job_function, kwargs={"message": "job #3"})
            assert_immediate_job_definition("immediate_job", {"message": "job #3"})
            wait().at_most(JOB_DELAY_SEC, SECOND).until(lambda: INDICATOR == "job #3")
            assert_no_jobs()

        finally:
            shutdown_scheduler()
            with pytest.raises(EngineError, match=r"Scheduler is not available"):
                scheduler()
