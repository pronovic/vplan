# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
import os
from datetime import time

from vplan.config import CredentialsConfig, SmartThingsCredential, VacationConfig
from vplan.engine.interface import (
    Trigger,
    TriggerAction,
    TriggerDay,
    TriggerDevice,
    TriggerTime,
    TriggerVariation,
    VacationPlan,
    VariationDirection,
    VariationUnit,
)


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "config", filename)


CREDS_FILE = fixture("credentials.yaml")
CREDS_EXPECTED = CredentialsConfig(
    version="1.0.0",
    credentials=[
        SmartThingsCredential(id="firstid", token="thebiglongtokenstringthatisopaque"),
        SmartThingsCredential(id="can-be-email@whatever.com", token="another string that can contain anything"),
    ],
)

PLAN_FILE = fixture("plan.yaml")
PLAN_EXPECTED = VacationConfig(
    version="1.0.0",
    credential_id="whatever",
    plan=VacationPlan(
        id="my-house",
        location="My House",
        enabled=False,
        triggers=[
            Trigger(
                id="living-room-on",
                days=[TriggerDay.ALL],
                time=TriggerTime.SUNRISE,
                action=TriggerAction.SWITCH_ON,
                variation=TriggerVariation(period=5, unit=VariationUnit.MINUTES, direction=VariationDirection.BEFORE),
                devices=[
                    TriggerDevice(room="Living Room", device="Sofa Table Lamp"),
                    TriggerDevice(room="Dining Room", device="China Cabinet"),
                ],
            ),
            Trigger(
                id="ken-office-off",
                days=[TriggerDay.WEEKDAYS],
                time=TriggerTime.SUNSET,
                action=TriggerAction.SWITCH_OFF,
                variation=TriggerVariation(period=0, unit=VariationUnit.MINUTES, direction=VariationDirection.BOTH),
                devices=[
                    TriggerDevice(room="Ken's Office", device="Desk Lamp"),
                ],
            ),
            Trigger(
                id="basement-on",
                days=[TriggerDay.WEEKENDS],
                time=TriggerTime.NOON,
                action=TriggerAction.SWITCH_ON,
                variation=TriggerVariation(period=30, unit=VariationUnit.SECONDS, direction=VariationDirection.BOTH),
                devices=[
                    TriggerDevice(room="Basement", device="Lamp Under Window"),
                ],
            ),
            Trigger(
                id="julie-office-off",
                days=[TriggerDay.MONDAY, TriggerDay.TUESDAY, TriggerDay.FRIDAY],
                time=TriggerTime.MIDNIGHT,
                action=TriggerAction.SWITCH_OFF,
                variation=TriggerVariation(period=0, unit=VariationUnit.MINUTES, direction=VariationDirection.BOTH),
                devices=[
                    TriggerDevice(room="Julie's Office", device="Dresser Lamp"),
                ],
            ),
            Trigger(
                id="christmas-lights-off",
                days=[TriggerDay.THURSDAY, TriggerDay.WEEKENDS],
                time=time(hour=14, minute=32, second=18),
                action=TriggerAction.SWITCH_OFF,
                variation=TriggerVariation(period=3, unit=VariationUnit.HOURS, direction=VariationDirection.AFTER),
                devices=[
                    TriggerDevice(room="Front Porch", device="Christmas Lights"),
                ],
            ),
        ],
    ),
)


class TestCredentialConfig:
    def test_parsing(self):
        with open(CREDS_FILE, "r", encoding="utf8") as fp:
            config = CredentialsConfig.parse_raw(fp.read())
            assert config == CREDS_EXPECTED


class TestVacationConfig:
    def test_parsing(self):
        with open(PLAN_FILE, "r", encoding="utf8") as fp:
            config = VacationConfig.parse_raw(fp.read())
            assert config == PLAN_EXPECTED
