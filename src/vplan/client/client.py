# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=missing-timeout: # for the local server, we don't care about timeouts; some requests take a long time

"""
API client written in terms of Python requests.
"""
import json
from typing import List, Optional

import click
import requests
import requests_unixsocket
from pydantic_yaml import parse_yaml_raw_as
from requests import HTTPError, Response

from vplan.client.config import api_url
from vplan.interface import Account, PlanSchema, Status, Version

# Add support in requests for http+unix:// URLs to use a UNIX socket
requests_unixsocket.monkeypatch()  # type: ignore


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (api_url(), endpoint)


def _account(endpoint: str = "") -> str:
    """Build an account URL based on API configuration"""
    return _url("/account%s" % endpoint)


def _plan(endpoint: str = "") -> str:
    """Build a plan URL based on API configuration"""
    return _url("/plan%s" % endpoint)


def _raise_for_status(response: Response) -> None:
    """Check response status, raising ClickException for errors"""
    try:
        response.raise_for_status()
    except HTTPError as e:
        raise click.ClickException("%s" % e) from e


def retrieve_health() -> bool:
    """Check whether the API server is healthy."""
    url = _url("/health")
    try:
        response = requests.get(url=url, timeout=1)
        response.raise_for_status()
        return True
    except:  # pylint: disable=bare-except
        return False


def retrieve_version() -> Optional[Version]:
    """Retrieve version information from the API server."""
    url = _url("/version")
    try:
        response = requests.get(url=url, timeout=1)
        response.raise_for_status()
        return parse_yaml_raw_as(Version, response.text)
    except:  # pylint: disable=bare-except
        return None


def retrieve_account() -> Optional[Account]:
    """Retrieve account information stored in the plan engine."""
    url = _account()
    response = requests.get(url=url)
    if response.status_code == 404:
        return None
    _raise_for_status(response)
    return parse_yaml_raw_as(Account, response.text)


def create_or_replace_account(account: Account) -> None:
    """Create or replace account information stored in the plan engine."""
    url = _account()
    response = requests.post(url=url, data=account.model_dump_json())
    _raise_for_status(response)


def delete_account() -> None:
    """Delete account information stored in the plan engine."""
    url = _account()
    response = requests.delete(url=url)
    _raise_for_status(response)


def retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    url = _plan()
    response = requests.get(url=url)
    _raise_for_status(response)
    plans: List[str] = json.loads(response.text)
    return plans


def retrieve_plan(plan_name: str) -> Optional[PlanSchema]:
    """Return the plan definition stored in the plan engine."""
    url = _plan("/%s" % plan_name)
    response = requests.get(url=url)
    if response.status_code == 404:
        return None
    _raise_for_status(response)
    return parse_yaml_raw_as(PlanSchema, response.text)


def create_plan(schema: PlanSchema) -> None:
    """Create a plan in the plan engine."""
    url = _plan()
    response = requests.post(url=url, data=schema.model_dump_json())
    _raise_for_status(response)


def update_plan(schema: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""
    url = _plan()
    response = requests.put(url=url, data=schema.model_dump_json())
    _raise_for_status(response)


def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""
    url = _plan("/%s" % plan_name)
    response = requests.delete(url=url)
    _raise_for_status(response)


def retrieve_plan_status(plan_name: str) -> Optional[Status]:
    """Return the enabled/disabled status of a plan in the plan engine."""
    url = _plan("/%s/status" % plan_name)
    response = requests.get(url=url)
    if response.status_code == 404:
        return None
    _raise_for_status(response)
    return parse_yaml_raw_as(Status, response.text)


def update_plan_status(plan_name: str, status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""
    url = _plan("/%s/status" % plan_name)
    response = requests.put(url=url, data=status.model_dump_json())
    _raise_for_status(response)


def refresh_plan(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""
    url = _plan("/%s/refresh" % plan_name)
    response = requests.post(url=url)
    _raise_for_status(response)


def toggle_group(plan_name: str, group_name: str, toggles: int, delay_sec: int) -> None:
    """Test a device group that is part of a plan."""
    url = _plan("/%s/test/group/%s" % (plan_name, group_name))
    params = {"toggles": toggles, "delay_sec": delay_sec}
    response = requests.post(url=url, params=params)
    _raise_for_status(response)


def toggle_device(plan_name: str, room: str, device: str, component: str, toggles: int, delay_sec: int) -> None:
    """Test a device that is part of a plan."""
    url = _plan("/%s/test/device/%s/%s/%s" % (plan_name, room, device, component))
    params = {"toggles": toggles, "delay_sec": delay_sec}
    response = requests.post(url=url, params=params)
    _raise_for_status(response)


def turn_on_group(plan_name: str, group_name: str) -> None:
    """Turn on a device group that is part of a plan."""
    url = _plan("/%s/on/group/%s" % (plan_name, group_name))
    response = requests.post(url=url)
    _raise_for_status(response)


def turn_on_device(plan_name: str, room: str, device: str, component: str) -> None:
    """Turn on a device that is part of a plan."""
    url = _plan("/%s/on/device/%s/%s/%s" % (plan_name, room, device, component))
    response = requests.post(url=url)
    _raise_for_status(response)


def turn_off_group(plan_name: str, group_name: str) -> None:
    """Turn off a device group that is part of a plan."""
    url = _plan("/%s/off/group/%s" % (plan_name, group_name))
    response = requests.post(url=url)
    _raise_for_status(response)


def turn_off_device(plan_name: str, room: str, device: str, component: str) -> None:
    """Turn off a device that is part of a plan."""
    url = _plan("/%s/off/device/%s/%s/%s" % (plan_name, room, device, component))
    response = requests.post(url=url)
    _raise_for_status(response)
