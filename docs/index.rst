Vacation Plan Manager 
=====================

Release v\ |version|

.. image:: https://img.shields.io/pypi/v/vplan.svg
    :target: https://pypi.org/project/vplan/

.. image:: https://img.shields.io/pypi/l/vplan.svg
    :target: https://github.com/pronovic/vplan/blob/master/LICENSE

.. image:: https://img.shields.io/pypi/wheel/vplan.svg
    :target: https://pypi.org/project/vplan/

.. image:: https://img.shields.io/pypi/pyversions/vplan.svg
    :target: https://pypi.org/project/vplan/

.. image:: https://github.com/pronovic/vplan/workflows/Test%20Suite/badge.svg
    :target: https://github.com/pronovic/vplan/actions?query=workflow%3A%22Test+Suite%22

.. image:: https://readthedocs.org/projects/vplan/badge/?version=stable&style=flat
    :target: https://vplan.readthedocs.io/en/stable/

.. image:: https://coveralls.io/repos/github/pronovic/vplan/badge.svg?branch=master
    :target: https://coveralls.io/github/pronovic/vplan?branch=master

Vacation Plan Manager is a platform that manages a vacation lighting plan for
one or more SmartThings locations tied to a single user.  A vacation lighting
plan describes how to turn on and off various lighting devices in a specific
pattern when you are away from home.  The plan can be varied by day of week
(weekday, weekend, or particular day) and it also allows for random variation
in the timing, so your lights do not turn on or off at exactly the same time
every day.  It works for any device with the ``switch`` capability.

Underneath, the vacation plan is implemented in your SmartThings account as a
set of rules.  Rules tied to your SmartThings account are updated on a daily
basis, to reflect the plan for that day. The platform also includes a command
line client that is used to configure your vacation plan, enable or disable
vacation mode, and test your rules.

Installation
------------

Install the package with pip::

    $ pip install vplan


Documentation
-------------

.. toctree::
   :maxdepth: 1

