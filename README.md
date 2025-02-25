# Vacation Plan Manager for SmartThings

[![license](https://img.shields.io/github/license/pronovic/vplan)](https://github.com/pronovic/vplan/blob/main/LICENSE)
[![release](https://img.shields.io/github/v/release/pronovic/vplan)](https://github.com/pronovic/vplan/releases/latest)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

_Note: As of January 2025, I have migrated my home automation infrastructure
from SmartThings to Home Assistant, so I no longer use this software.  It does
work, and is still a decent example of how to accomplish SmartThings automation
via the public API and a personal access token.  However, the repository is
archived and you should consider this code to be unmaintained._

---

Vacation Plan Manager is a platform that manages a vacation lighting plan for
one or more SmartThings locations tied to a single SmartThings user.  

The platform is written in Python 3.  It has two components: a daemon process
running as a systemd user service, and a command line tool.  The command line
tool communicates with the daemon via a RESTful API using a private UNIX socket.
You use the command line tool to configure your vacation plans, to enable or
disable vacation plans, and to test your devices.  

The platform is lightweight and will work on most Linux systems that have
internet access and are configured to run continuously, including low-cost
hardware such as the Raspberry Pi.

## What is a Vacation Lighting Plan?

A vacation lighting plan describes how to turn on and off various lighting
devices in a specific pattern when you are away from home.  The plan can be
varied by day of week (weekday, weekend, or particular day) and it also allows
for random variation in the timing, so your lights do not turn on or off at
exactly the same time every day.  It works for any device with the `switch`
capability.

Underneath, the vacation lighting plan is implemented in your SmartThings
account as a set of rules.  To operate within the SmartThings platform
restrictions, rules tied to your SmartThings account are updated on a daily
basis, to reflect the randomized plan for that day.  

## Cautions

**_This is a developer-focused tool._**

My goal was to write something I could use myself on my own hardware.  The code 
is well tested and functions properly, but I haven't spent a lot of effort on 
making the installation process simple or the error handling pretty.  If you're 
not already comfortable with the UNIX command line, you may have a hard time 
getting this to work.

**_This is not a general purpose, multi-user solution._**

This platform is intended for local use by a single Linux user.  Security is
based on simple UNIX filesystem permissions, which ensure that only the owner
can read the underlying sqlite database and make API calls via the private UNIX
socket.  If you run the API in some other way &mdash; especially if you run it
on some local port like :8080 instead of using the private UNIX socket &mdash;
you risk exposing secrets such as your SmartThings PAT token.

## Developer Documentation

Developer documentation is found in [DEVELOPER.md](DEVELOPER.md).  See that
file for notes about how the code is structured, how to set up a development
environment, etc.

## Installing the Platform

The platform is distributed at GitHub.  To install the software, download the `.whl` 
file for the [latest release](https://github.com/pronovic/vplan/releases/latest), 
and install it using [pipx](https://pypa.github.io/pipx/), like:

```
$ pipx install --force --include-deps ./vplan-0.7.1-py3-none-any.whl
```

> On Debian, I install pipx using: `apt-get install pipx --no-install-suggests --no-install-recommends`

Next, configure the platform.  Download the configuration bundle for the latest
release.  Extract the tar file to your user configuration directory:

```
$ mkdir -p ~/.config 
$ tar zxvf vplan-config-0.6.0.tar.gz -C ~/.config
```

This creates two directories within `~/.config`: `vplan` and `systemd`.  The
`systemd` directory contains configuration for the systemd user service that
you will create shortly:

```
systemd/user/vplan.service
systemd/user/vplan.socket
```

The `vplan` directory contains configuration for the vplan daemon process and
the command line client.  There are also two runtime directories, to contain
the UNIX socket and the small database that is used to maintain state.

```
vplan/client/application.yaml
vplan/server/application.yaml
vplan/server/logging.yaml
vplan/server/db
vplan/server/run
```

The default configuration should work for most people, so there is probably no
need to modify any of these files. 

Next, configure systemd:

```
$ sudo loginctl enable-linger <your-user>    # restart user services at reboot
$ systemctl --user enable vplan              # enable the vplan service
$ systemctl --user start vplan               # start the vplan service
$ systemctl --user status vplan              # show status for the vplan service
```

At this point, the systemd service should be running, and the command line
client should be operable.  Check connectivity.  If you get any errors, check
that you installed the software as described above.

```
$ vplan check
API is healthy, versions: package='0.6.0' api='2.0.0'
```

If necessary, you can check the logs from the service:

```
$ journalctl --pager-end --user-unit vplan
```

If you do need to change any of the systemd config files (unlikely), make sure
to reload them afterwards, before trying to do any further testing:

```
$ systemctl --user daemon-reload
```

Finally, reboot and confirm that the service starts automatically.  After
reboot, use the same `vplan check` command shown above to confirm things are
working.

## Upgrading the Platform

The process is similar to installing.  Download the `.whl` file for 
the [latest release](https://github.com/pronovic/vplan/releases/latest), and install it 
using [pipx](https://pypa.github.io/pipx/), like:

```
$ pipx install --force --include-deps ./vplan-0.7.1-py3-none-any.whl
```

> On Debian, I install pipx using: `apt-get install pipx --no-install-suggests --no-install-recommends`

Reload configuration and restart the systemd service::

```
$ systemctl --user daemon-reload
$ systemctl --user restart vplan
```

Finally, run the check and confirm what version you are running on:

```
$ vplan check
API is healthy, versions: package='0.6.0' api='2.0.0'
```

## Setting Up Your Account

The vacation plan manager needs a SmartThings PAT token.  The PAT token is used
to interact with the SmartThings API. 

Retrieve a token from: https://account.smartthings.com/tokens

Your PAT token requires the following scopes:

```
 Devices:
   List all devices (l:devices)
   See all devices (r:devices:*)
   Control all devices (x:devices:*)

 Locations
   See all locations (r:locations:*)

 Rules
   See all rules (r:rules:*)
   Manage all rules (w:rules:*)
   Control this rule (x:rules:*)
```

Once you have retrieved your PAT token, set up your account:

```
$ vplan account set
Enter PAT token: <your token>
Account created
```

You can spot-check that it was set properly using the `show` command:

```
$ vplan account show
PAT token: 0d14****************************3251
```

In the future, you can change your PAT token using the same `set` command shown
above.  See other account commands using `vplan account --help`.

## Developing a Vacation Plan

A vacation plan is defined in a YAML file.  Here is a very simple example:

```yaml
version: 1.1.0
plan:
  name: my-house
  location: My House
  refresh_time: "00:30"
  refresh_zone: "America/Chicago"   # if you don't specify a zone, it runs in UTC
  groups:
    - name: first-floor-lights
      devices:
        - room: Living Room
          device: Sofa Table Lamp
        - room: Dining Room
          device: China Cabinet
          component: leftOutlet
      triggers:
        - days: [ weekdays ]
          on_time: "19:30"
          off_time: "22:45"
          variation: "+/- 30 minutes"
        - days: [ tue, thu, sat ]
          on_time: sunset
          off_time: sunrise
          variation: none
```

All plans require:

- a **name** - an identifier matching the regex `[a-z0-9-]+`, unique among all of your plans
- a **location** - whatever it's called in your SmartThings infrastructure
- a **refresh time** - the HH24:MM time of day when rules will be refreshed at SmartThings
- one or more **device groups**

For the **refresh time**, pick a time of day when none of your groups will be changing state
from on to off or off to on &mdash; probably the middle of the night or the middle of the
day.

A **device group** consists of:

- a **name** - an identifier matching the regex `[a-z0-9-]+`, unique within this plan
- one or more **devices** - all devices in a device group will turn on and off together, like a scene
- one or more **triggers** - a trigger is in scope on certain days and describes the times when a device group will turn on and off

Each **device** consists of:

- a **room** - the human-readable name of the room where the device lives in your SmartThings infrastructure
- a **device** - the human-readable name of the device in SmartThings, which must support the `switch` capability
- a optional **component** - used for multi-component devices (see **Multi-Component Devices**, below)

Each trigger consists of:

- a list of **days** - days of week like `sun`, `tue`, or `thursday` or the special days `all`, `weekends` or `weekdays`
- an **on time** - either a time in HH24:MM format or special times `sunrise`, `sunset`, `midnight`, or `noon`
- an **off time** - either a time in HH24:MM format or special times `sunrise`, `sunset`, `midnight`, or `noon`
- a **variation** - either `none` or a specifier like described below

The **on time** and **off time** are in the timezone of your location, as
defined in SmartThings.  In the YAML, you should always quote times, like
`"18:30"`.

The **variation** controls how much random variation will be placed into the on
and off times.  If a variation is configured, each day will be slightly
different.  A specifier like `- 15 minutes` means that the device group will
turn on or off up to 15 minutes earlier than the given time.  Similarly, `+ 15
minutes` means 15 minutes later, and `+/- 15 minutes` means 15 minutes earlier
or later.  You can create specifiers using `minutes` or `hours`.
In the YAML, you should always quote these specifiers with double quotes, like
`"+/- 15 minutes"`.

## Multi-Component Devices

Historically, in the old DTH driver environment, devices that had multiple
components (i.e. smart outlets with two receptacles) would result in multiple
SmartThings devices that could be named and addressed independently. With the
move toward Edge drivers, that is no longer the case.

For instance, the custom DTH for the Zooz ZEN25 outlet used to generate one
device for each receptacle, plus one for the main power control, plus another
one for the USB port.  We could name each device individually and address those
devices in the vacation plan simply as `Living Room/Lamp Under Window`.

With the new Edge driver, we now get a single device for the ZEN25, but that
device has multiple components (`main`, `leftOutlet`, `rightOutlet`, `usb`)
that can be controlled indivdually.  Since there is only one device, the
vacation plan needs to address devices like `Living Room/Tree Outlet/leftOutlet`.

The best way to figure out what components you have available is by using
the [SmartThings CLI](https://github.com/SmartThingsCommunity/smartthings-cli)
in conjunction with [jq](https://stedolan.github.io/jq/).

In this example, I have a device called **Tree Outlet**, a ZEN25 that is behind
a fake tree in the living room.  Assuming the name of the device is unique in
your location, you can just do this:

```
$ smartthings devices --json | jq -r '.[] | select(.label=="Tree Outlet") | .components[].id'
leftOutlet
rightOutlet
usb
main
```

If the name of the device isn't unique, run `smartthings devices` to get a list
of your devices and pick the right one:

```
$ smartthings devices 
┌────┬────────────────────────┬───────────────────────────┬────────┬──────────────────────────────────────┐
│ #  │ Label                  │ Name                      │ Type   │ Device Id                            │
├────┼────────────────────────┼───────────────────────────┼────────┼──────────────────────────────────────┤
│ 1  │ Tree Outlet            │ zooz-zen25-double-plug    │ ZWAVE  │ c98330b5-xxxx-xxxx-xxxx-972b4372fcde │
└────┴────────────────────────┴───────────────────────────┴────────┴──────────────────────────────────────┘
```

Grab the device id out of the **Device Id** column and run a command like this
to pull out the components:

```
$ smartthings devices c98330b5-xxxx-xxxx-xxxx-972b4372fcde --json | jq -r '.components[].id'
leftOutlet
rightOutlet
usb
main
```

If you don't have `jq` installed, you can just save off the JSON and look
through it by hand.  Each device has a list of `components`, and you are
looking for the `id` of the component.

## Enabling Your Vacation Plan

Once you have created your YAML file, you will use it to create a plan in the
vacation plan manager.

```
$ vplan plan create file.yaml
Created plan: my-house
```

If there are any errors in your YAML file, you will get feedback at this point,
and you can correct your file.  If the create operation fails at the server,
you can look in the daemon log (`journalctl --user-unit vplan`) to get more
information.  The same is true for any other operation you might run via the
command line interface.

Any newly-created plan will be disabled by default.  You can enable a plan like
this:

```
$ vplan plan enable my-house
Plan my-house is enabled
```

Once a plan is enabled, rules will be written immediately into the SmartThings
infrastructure, and your plan will be operational.  

The plan is implemented underneath by SmartThings rules, and is not dependent
on the vplan daemon.  So, even if you stop the daemon or shut down your Linux
system, the plan will continue to execute.  However, there won't be any daily
variations in the trigger times, because the daemon is not around to make those
changes.

See other plan commands using `vplan plan --help`.  In particular, you may want
to use the `test` command to confirm that your various device groups are
working like you intend, before you enable the plan.
