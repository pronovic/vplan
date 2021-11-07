# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

import datetime
from unittest.mock import MagicMock, patch

from busypie import SECOND, wait
from tzlocal import get_localzone

from vplan.engine.config import DailyJobConfig, SchedulerConfig
from vplan.engine.scheduler import schedule_daily_job, shutdown_scheduler, start_scheduler, unschedule_daily_job

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


class TestConfig:
    @patch("vplan.engine.scheduler.config")
    def test_schedule_daily_job(self, config, tmpdir):
        shutdown_scheduler()

        # this sets things up so the daily job is scheduled a few seconds from now, so we can check that it runs
        tz = get_localzone()
        database_url = "sqlite+pysqlite:///%s" % tmpdir.join("jobs.sqlite").realpath()
        daily = DailyJobConfig(time=in_future(seconds=JOB_DELAY_SEC, tz=tz), jitter_sec=0)
        scheduler_config = SchedulerConfig(database_url=database_url, thread_pool_size=10, daily_job=daily)
        config.return_value = MagicMock(scheduler=scheduler_config)

        try:
            start_scheduler()
            schedule_daily_job(job_id="test_job", func=job_function, kwargs={"message": "job ran"}, time_zone="%s" % tz)
            wait().at_most(JOB_DELAY_SEC, SECOND).until(lambda: INDICATOR == "job ran")
            unschedule_daily_job(job_id="test_job")  # just make sure it doesn't blow up
        finally:
            shutdown_scheduler()
