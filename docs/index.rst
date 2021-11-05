Vacation Plan Manager 
=====================

Release v\ |version|

.. image:: https://img.shields.io/pypi/v/vacation-plan-manager.svg
    :target: https://pypi.org/project/vacation-plan-manager/

.. image:: https://img.shields.io/pypi/l/vacation-plan-manager.svg
    :target: https://github.com/pronovic/vacation-plan-manager/blob/master/LICENSE

.. image:: https://img.shields.io/pypi/wheel/vacation-plan-manager.svg
    :target: https://pypi.org/project/vacation-plan-manager/

.. image:: https://img.shields.io/pypi/pyversions/vacation-plan-manager.svg
    :target: https://pypi.org/project/vacation-plan-manager/

.. image:: https://github.com/pronovic/vacation-plan-manager/workflows/Test%20Suite/badge.svg
    :target: https://github.com/pronovic/vacation-plan-manager/actions?query=workflow%3A%22Test+Suite%22

.. image:: https://readthedocs.org/projects/vacation-plan-manager/badge/?version=stable&style=flat
    :target: https://vacation-plan-manager.readthedocs.io/en/stable/

.. image:: https://coveralls.io/repos/github/pronovic/vacation-plan-manager/badge.svg?branch=master
    :target: https://coveralls.io/github/pronovic/vacation-plan-manager?branch=master

This manages a vacation lighting plan for one or more SmartThings locations
tied to a single user.  A vacation lighting plan describes how to turn on and
off various lighting devices in a specific pattern when you are away from home.
The plan can be varied by day of week (weekday, weekend, or particular day) and
it also allows for random variation in the timing, so your lights do not turn
on or off at exactly the same time every day.  It works for any device with the
``switch`` capability.  Underneath, the vacation plan is implemented in your
SmartThings account as a set of rules. To work within limitations of the
SmartThings rules implementation, the plan manager runs as a Linux daemon and
updates the rules on a daily basis.


Installation
------------

Install the package with pip::

    $ pip install vacation-plan-manager


Documentation
-------------

.. toctree::
   :maxdepth: 1

