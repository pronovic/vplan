# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import datetime
from unittest.mock import MagicMock, call, patch

from sqlalchemy.exc import NoResultFound

from vplan.engine.manager import (
    refresh_plan,
    schedule_daily_refresh,
    schedule_immediate_refresh,
    toggle_devices,
    unschedule_daily_refresh,
)
from vplan.interface import Account, Device, SwitchState


class TestScheduler:
    @patch("vplan.engine.manager.schedule_daily_job")
    def test_schedule_daily_refresh(self, schedule_daily_job):
        schedule_daily_refresh("plan", "loc", "00:30", "America/Chicago")
        schedule_daily_job.assert_called_once_with(
            "daily/plan",
            datetime.time(hour=0, minute=30),
            refresh_plan,
            {"plan_name": "plan", "location": "loc"},
            "America/Chicago",
        )

    @patch("vplan.engine.manager.unschedule_daily_job")
    def test_unschedule_daily_refresh(self, unschedule_daily_job):
        unschedule_daily_refresh("plan")
        unschedule_daily_job.assert_called_once_with("daily/plan")

    @patch("vplan.engine.manager.now")
    @patch("vplan.engine.manager.schedule_immediate_job")
    def test_schedule_immediate_refresh(self, schedule_immediate_job, now):
        now.return_value = MagicMock()
        now.return_value.isoformat = MagicMock(return_value="thetime")
        schedule_immediate_refresh("plan", "loc")
        schedule_immediate_job.assert_called_once_with(
            "immediate/plan/thetime",
            refresh_plan,
            {"plan_name": "plan", "location": "loc"},
        )


@patch("vplan.engine.manager.SmartThings")
class TestToggle:
    @patch("vplan.engine.manager.set_switch")
    @patch("vplan.engine.manager.sleep")
    @patch("vplan.engine.manager.config")
    @patch("vplan.engine.manager.db_retrieve_account")
    def test_toggle_devices(self, db_retrieve_account, config, sleep, set_switch, context):

        # See: https://stackoverflow.com/a/68578027
        call_order = []
        sleep.side_effect = lambda *a, **kw: call_order.append(sleep)
        set_switch.side_effect = lambda *a, **kw: call_order.append(set_switch)

        account = Account(pat_token="token")
        db_retrieve_account.return_value = account

        device1 = Device(room="r", device="d1")
        device2 = Device(room="r", device="d2")

        smartthings = MagicMock(base_api_url="http://whatever", toggle_delay_sec=10)
        config.return_value = MagicMock(smartthings=smartthings)

        toggle_devices(location="location", devices=[device1, device2], toggles=2)

        context.assert_called_once_with("token", "location")

        assert call_order == [
            set_switch,
            set_switch,
            sleep,
            set_switch,
            set_switch,
            sleep,
            set_switch,
            set_switch,
            sleep,
            set_switch,
            set_switch,
        ]

        sleep.assert_has_calls([call(10)] * 3)

        set_switch.assert_has_calls(
            [
                call(device1, SwitchState.ON),
                call(device2, SwitchState.ON),
                call(device1, SwitchState.OFF),
                call(device2, SwitchState.OFF),
            ]
        )


@patch("vplan.engine.manager.SmartThings")
@patch("vplan.engine.manager.replace_rules")
@patch("vplan.engine.manager.db_retrieve_plan")
@patch("vplan.engine.manager.db_retrieve_plan_enabled")
@patch("vplan.engine.manager.db_retrieve_account")
class TestRefresh:
    def test_refresh_plan_no_account(self, db_retrieve_account, db_retrieve_plan_enabled, db_retrieve_plan, replace_rules, context):
        db_retrieve_account.side_effect = NoResultFound("not found")

        refresh_plan("plan", "loc")

        db_retrieve_account.assert_called_once()
        db_retrieve_plan_enabled.assert_not_called()
        db_retrieve_plan.assert_not_called()
        context.assert_not_called()
        replace_rules.assert_not_called()

    def test_refresh_plan_no_plan(self, db_retrieve_account, db_retrieve_plan_enabled, db_retrieve_plan, replace_rules, context):
        account = MagicMock(pat_token="token")
        db_retrieve_account.return_value = account
        db_retrieve_plan_enabled.side_effect = NoResultFound("not found")

        refresh_plan("plan", "loc")

        db_retrieve_account.assert_called_once()
        db_retrieve_plan_enabled.assert_called_once_with("plan")
        db_retrieve_plan.assert_not_called()
        context.assert_called_once_with("token", "loc")
        replace_rules.assert_called_once_with("plan", None)

    def test_refresh_plan_disabled(self, db_retrieve_account, db_retrieve_plan_enabled, db_retrieve_plan, replace_rules, context):
        account = MagicMock(pat_token="token")
        db_retrieve_account.return_value = account
        db_retrieve_plan_enabled.return_value = False

        refresh_plan("plan", "loc")

        db_retrieve_account.assert_called_once()
        db_retrieve_plan_enabled.assert_called_once_with("plan")
        db_retrieve_plan.assert_not_called()
        context.assert_called_once_with("token", "loc")
        replace_rules.assert_called_once_with("plan", None)

    def test_refresh_plan_mismatch(self, db_retrieve_account, db_retrieve_plan_enabled, db_retrieve_plan, replace_rules, context):
        account = MagicMock(pat_token="token")
        schema = MagicMock(plan=MagicMock(location="different"))  # because this does not match passed-in "loc", we delete
        db_retrieve_account.return_value = account
        db_retrieve_plan_enabled.return_value = True
        db_retrieve_plan.return_value = schema

        refresh_plan("plan", "loc")

        db_retrieve_account.assert_called_once()
        db_retrieve_plan_enabled.assert_called_once_with("plan")
        db_retrieve_plan.assert_called_once_with("plan")
        context.assert_called_once_with("token", "loc")
        replace_rules.assert_called_once_with("plan", None)

    def test_refresh_plan_enabled(self, db_retrieve_account, db_retrieve_plan_enabled, db_retrieve_plan, replace_rules, context):
        account = MagicMock(pat_token="token")
        schema = MagicMock(plan=MagicMock(location="loc"))  # because matches the passed-in "loc", it's safe to refresh
        db_retrieve_account.return_value = account
        db_retrieve_plan_enabled.return_value = True
        db_retrieve_plan.return_value = schema

        refresh_plan("plan", "loc")

        db_retrieve_account.assert_called_once()
        db_retrieve_plan_enabled.assert_called_once_with("plan")
        db_retrieve_plan.assert_called_once_with("plan")
        context.assert_called_once_with("token", "loc")
        replace_rules.assert_called_once_with("plan", schema)
