# Vacation Plan Manager for SmartThings

[![license](https://img.shields.io/pypi/l/vplan.svg)](https://github.com/pronovic/vplan/blob/master/LICENSE)
[![Test Suite](https://github.com/pronovic/vplan/workflows/Test%20Suite/badge.svg)](https://github.com/pronovic/vplan/actions?query=workflow%3A%22Test+Suite%22)
[![coverage](https://coveralls.io/repos/github/pronovic/vplan/badge.svg?branch=master)](https://coveralls.io/github/pronovic/vplan?branch=master)
[![release](https://img.shields.io/github/v/release/pronovic/vplan)](https://github.com/pronovic/vplan/releases/latest)

Vacation Plan Manager is a platform that manages a vacation lighting plan for
one or more SmartThings locations tied to a single SmartThings user.  

The platform is written in Python 3.  It has two components: a daemon process
running as a systemd user service, and a command line tool.  The command line
tool communicates with the daemon via a RESTful API using a private UNIX socket.
You use the command line tool to configure your vacations plans, to enable or
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
and install it using `pip`, like:

```
$ pip install vplan-0.2.0-py3-none-any.whl
```

Next, configure the platform.  Download the configuration bundle for the latest
release.  Extract the tar file to your user configuration directory:

```
$ mkdir -p ~/.config 
$ tar zxvf vplan-config-0.2.0.tar.gz -C ~/.config
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
API is healthy, versions: package='0.2.0' api='1.0.0'
```

If necessary, you can check the logs from the service:

```
$ journalctl --user-unit vplan
```

If you do need to change any of the systemd config files (unlikely), make sure
to reload them afterwards, before trying to do any further testing:

```
$ systemctl --user daemon-reload
```

Finally, reboot and confirm that the service starts automatically.  After
reboot, use the same `vplan check` command shown above to confirm things are
working.

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
version: 1.0.0
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
      triggers:
        - days: [ weekdays ]
          on_time: "19:30"
          off_time: "22:45"
          variation: "+/- 30 minutes"
        - days: [ weekends ]
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
- a **device** - the human-readable name of the device, which must support the `switch` capability

Each trigger consists of:

- a list of **days** - days of week like `sun`, `tue`, or `thursday` or the special days `all`, `weekends` or `weekdays`
- an **on time** - either a time in HH24:MM format or special times `sunrise`, `sunset`, `midnight`, or `noon`
- an **off time** - either a time in HH24:MM format or special times `sunrise`, `sunset`, `midnight`, or `noon`
- a **variation** - either `none` or a specifier like `- 15 minutes` or `+/- 2 hours`

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
on the vplan daemon.  So, even if you stop the daemon or shut it off, the plan
will continue to execute.  However, there won't be any daily variations in the
trigger times, because the daemon is not around to make those changes.

See other plan commands using `vplan plan --help`.  In particular, you may want
to use the `test` command to confirm that your various device groups are
working like you intend, before you enable the plan.
