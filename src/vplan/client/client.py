# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
API client written in terms of Python requests.
"""
from typing import List, Optional

import requests
import requests_unixsocket

from vplan.client.config import api_url
from vplan.engine.interface import Account, PlanSchema, Status

# Add support in requests for http+unix:// URLs to use a UNIX socket
requests_unixsocket.monkeypatch()


def _url(endpoint: str) -> str:
    """Build a URL based on API configuration."""
    return "%s%s" % (api_url(), endpoint)


def _account(endpoint: str = "") -> str:
    """Build an account URL based on API configuration"""
    return _url("/account%s" % endpoint)


def _plan(endpoint: str = "") -> str:
    """Build a plan URL based on API configuration"""
    return _url("/plan%s" % endpoint)


def retrieve_account() -> Optional[Account]:
    """Retrieve account information stored in the plan engine."""
    url = _account()
    response = requests.get(url=url)
    if response.status_code == 404:
        return None
    else:
        response.raise_for_status()
        return Account.parse_raw(response.json())


def create_account(account: Account) -> None:
    """Create your account in the plan engine."""
    url = _account()
    response = requests.post(url=url, json=account.json())
    response.raise_for_status()


def update_account(account: Account) -> None:
    """Update your account in the plan engine."""
    url = _account()
    response = requests.put(url=url, json=account.json())
    response.raise_for_status()


def delete_account() -> None:
    """Delete account information stored in the plan engine."""
    url = _account()
    response = requests.delete(url=url)
    response.raise_for_status()


def retrieve_account_status() -> Optional[Status]:
    """Retrieve the enabled/disabled status of your account in the plan engine."""
    url = _account("/status")
    response = requests.get(url=url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return Status.parse_raw(response.json())


def update_account_status(status: Status) -> None:
    """Set the enabled/disabled status of your account in the plan engine."""
    url = _account("/status")
    response = requests.put(url=url, json=status.json())
    response.raise_for_status()


def retrieve_all_plans() -> List[str]:
    """Return the names of all plans stored in the plan engine."""
    url = _plan()
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()  # type: ignore


def retrieve_plan(plan_name: str) -> Optional[PlanSchema]:
    """Return the plan definition stored in the plan engine."""
    url = _plan("/%s" % plan_name)
    response = requests.get(url=url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return PlanSchema.parse_raw(response.json())


def create_plan(plan: PlanSchema) -> None:
    """Create a plan in the plan engine."""
    url = _plan()
    response = requests.post(url=url, json=plan.json())
    response.raise_for_status()


def update_plan(plan: PlanSchema) -> None:
    """Update an existing plan in the plan engine."""
    url = _plan("/%s" % plan.plan.name)
    response = requests.put(url=url, json=plan.json())
    response.raise_for_status()


def delete_plan(plan_name: str) -> None:
    """Delete a plan stored in the plan engine."""
    url = _plan("/%s" % plan_name)
    response = requests.delete(url=url)
    response.raise_for_status()


def retrieve_plan_status(plan_name: str) -> Optional[Status]:
    """Return the enabled/disabled status of a plan in the plan engine."""
    url = _plan("/%s/status" % plan_name)
    response = requests.get(url=url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return Status.parse_raw(response.json())


def update_plan_status(plan_name: str, status: Status) -> None:
    """Set the enabled/disabled status of a plan in the plan engine."""
    url = _plan("/%s/status" % plan_name)
    response = requests.put(url=url, json=status.json())
    response.raise_for_status()


def refresh_plan(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""
    url = _plan("/%s/refresh" % plan_name)
    response = requests.post(url=url)
    response.raise_for_status()


def toggle_group(plan_name: str, group_name: str, toggle_count: int) -> None:
    """Test a device group that is part of a plan."""
    url = _plan("/%s/test/group/%s" % (plan_name, group_name))
    params = {"toggle_count": toggle_count}
    response = requests.post(url=url, params=params)
    response.raise_for_status()


def toggle_device(plan_name: str, room: str, device: str, toggle_count: int) -> None:
    """Test a device that is part of a plan."""
    url = _plan("/%s/test/device/%s/%s" % (plan_name, room, device))
    params = {"toggle_count": toggle_count}
    response = requests.post(url=url, params=params)
    response.raise_for_status()
