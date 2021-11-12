# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock, call, patch

from vplan.engine.interface import Device, SwitchState
from vplan.engine.manager import toggle_devices


class TestScheduler:
    @patch("vplan.engine.manager.schedule_daily_job")
    def test_schedule_daily_refresh(self, schedule_daily_job):
        pass

    @patch("vplan.engine.manager.unschedule_daily_job")
    def test_unschedule_daily_refresh(self, unschedule_daily_job):
        pass

    @patch("vplan.engine.manager.schedule_immediate_job")
    def test_schedule_immediate_refresh(self, schedule_immediate_job):
        pass


@patch("vplan.engine.manager.SmartThings")
class TestToggle:
    @patch("vplan.engine.manager.set_switch")
    @patch("vplan.engine.manager.sleep")
    @patch("vplan.engine.manager.config")
    def test_toggle_devices(self, config, sleep, set_switch, _):

        # See: https://stackoverflow.com/a/68578027
        call_order = []
        sleep.side_effect = lambda *a, **kw: call_order.append(sleep)
        set_switch.side_effect = lambda *a, **kw: call_order.append(set_switch)

        device1 = Device(room="r", device="d1")
        device2 = Device(room="r", device="d2")

        smartthings = MagicMock(base_api_url="http://whatever", toggle_delay_sec=10)
        config.return_value = MagicMock(smartthings=smartthings)

        toggle_devices(pat_token="token", location="location", devices=[device1, device2], toggles=2)

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


class TestRefresh:
    def test_refresh_plan(self):
        pass
