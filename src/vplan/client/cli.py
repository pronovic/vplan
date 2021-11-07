# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Command line interface for the client.
"""
import getpass
import importlib.resources
import os
from pathlib import Path
from typing import Optional

import click

_CONFIG_PACKAGE = "vplan.client.data"

_CONFIG_DIR = os.path.join(str(Path.home()), ".config")
_VPLAN_DIR = os.path.join(_CONFIG_DIR, "vplan")
_RUN_DIR = os.path.join(_VPLAN_DIR, "run")
_SYSTEMD_DIR = os.path.join(_CONFIG_DIR, "systemd", "user")

_CONFIG_DIRS = [_CONFIG_DIR, _VPLAN_DIR, _RUN_DIR, _SYSTEMD_DIR]
_CONFIG_FILES = ["credentials.yaml", "plan.yaml"]
_SYSTEMD_FILES = ["vplan_engine.socket", "vplan_engine.service"]
_SYSTEMD_SERVICES = ["vplan_engine"]


def _copy_datafile(source_file: str, target_dir: str, target_file: Optional[str] = None, force: bool = False) -> None:
    """Copy a file from the data package to a target directory"""
    target = os.path.join(target_dir, target_file if target_file else source_file)
    with importlib.resources.open_text(_CONFIG_PACKAGE, source_file) as reader:
        if force or not os.path.isfile(target):
            with open(target, "w", encoding="utf8") as writer:
                writer.writelines(reader.readlines())


def _init_config(force: bool) -> None:
    """Initialize configuration files in the user's home directory."""
    for path in _CONFIG_DIRS:
        os.makedirs(path)
    for path in _CONFIG_FILES:
        _copy_datafile(path, _VPLAN_DIR, force=force)
    for path in _SYSTEMD_FILES:
        _copy_datafile(path, _SYSTEMD_DIR, force=force)


def _check_systemd() -> None:
    """Check whether systemd is the init on this system."""
    if not (os.path.exists("/sbin/init") and "systemd" in "%s" % Path("/sbin/init").resolve()):
        raise click.UsageError("This tool is designed for Linux systems running systemd as init.")


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(package_name="vplan", prog_name="Vacation Plan Manager")
def vplan() -> None:
    """
    Vacation plan manager client.
    """


@vplan.command()
@click.option(
    "--force",
    "-f",
    "force",
    metavar="<force>",
    is_flag=True,
    required=False,
    default=False,
    help="Force-overwrite any files that already exist",
)
def bootstrap(force: bool) -> None:
    """
    Bootstrap local configuration.
    """
    _check_systemd()
    _init_config(force=force)
    click.secho("")
    click.secho("Configuration has been bootstrapped:")
    click.secho("")
    click.secho("  Vacation plan config...: %s/*.yaml" % _VPLAN_DIR)
    click.secho("  Shared run directory...: %s" % _RUN_DIR)
    click.secho("  User systemd services..: %s" % _SYSTEMD_DIR)
    click.secho("")
    click.secho("Next, get a PAT token from: https://account.smartthings.com/token")
    click.secho("Add your token to the credentials configuration file and adjust")
    click.secho("vacation plan configuration to reflect your location.")
    click.secho("")
    click.secho("When you are done, enable the related systemd services: ")
    click.secho("")
    click.secho("  $ systemctl --user daemon-reload")
    for service in _SYSTEMD_SERVICES:
        click.secho("  $ systemctl --user enable %s" % service)
        click.secho("  $ systemctl --user start %s" % service)
    click.secho("  $ sudo loginctl enable-linger %s" % getpass.getuser())
    click.secho("")
