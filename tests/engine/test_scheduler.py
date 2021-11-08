# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import datetime
from unittest.mock import MagicMock, patch

from apscheduler.triggers.cron import CronTrigger
from busypie import SECOND, wait
from tzlocal import get_localzone

from vplan.engine.config import DailyJobConfig, SchedulerConfig
from vplan.engine.scheduler import schedule_daily_job, scheduler, shutdown_scheduler, start_scheduler, unschedule_daily_job

INDICATOR = None
JOB_DELAY_SEC = 2  # if the job is intermittently unreliable, increase this value slightly


def job_function(message):
    """Job function to be scheduled; it sets INDICATOR so we can tell that the job worked."""
    global INDICATOR  # pylint: disable=global-statement
    INDICATOR = message


def in_future(seconds, tz):
    """Return a time some number of seconds into the future"""
    now = datetime.datetime.now(tz=tz)
    future = now + datetime.timedelta(seconds=seconds)
    return future.time().replace(microsecond=0)


def assert_no_jobs():
    """Assert that there are no jobs"""
    assert len(scheduler().get_jobs()) == 0


def assert_job_definition(job_id, kwargs):
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


class TestLifecycle:
    @patch("vplan.engine.scheduler.config")
    def test_schedule_daily_job(self, config, tmpdir):
        shutdown_scheduler()

        # this sets things up so the daily job is scheduled a few seconds from now, so we can check that it runs
        tz = get_localzone()
        database_url = "sqlite+pysqlite:///%s" % tmpdir.join("jobs.sqlite").realpath()
        daily = DailyJobConfig(time=in_future(seconds=JOB_DELAY_SEC, tz=tz), jitter_sec=0, misfire_grace_sec=1)
        scheduler_config = SchedulerConfig(database_url=database_url, thread_pool_size=10, daily_job=daily)
        config.return_value = MagicMock(scheduler=scheduler_config)

        try:
            start_scheduler()

            # Create the job and make sure it executes
            schedule_daily_job(job_id="test_job", func=job_function, kwargs={"message": "job #1"}, time_zone="%s" % tz)
            assert_job_definition("test_job", {"message": "job #1"})
            wait().at_most(JOB_DELAY_SEC, SECOND).until(lambda: INDICATOR == "job #1")

            # Recreate the job and make sure updates are reflected (but this one won't be executed)
            schedule_daily_job(job_id="test_job", func=job_function, kwargs={"message": "job #2"}, time_zone="%s" % tz)
            assert_job_definition("test_job", {"message": "job #2"})

            # Remove the job and make sure the change takes effect
            unschedule_daily_job(job_id="test_job")
            assert_no_jobs()

        finally:
            shutdown_scheduler()
