# Developer Notes

## Supported Platforms

This code runs as a daemon and is intended for use on Linux and UNIX-like platforms.

## Systemd and Daemon Notes

The systemd design is heavily based on the excellent [python-systemd-tutorial](https://github.com/torfsen/python-systemd-tutorial).  See also the [specifiers](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Specifiers) documentation (for constructs like `%h`).

Uvicorn is using a user-private UNIX socket rather than opening a port like 8080.  For the socket setup, I followed notes [here](https://gist.github.com/kylemanna/d193aaa6b33a89f649524ad27ce47c4b) and [here](https://stackoverflow.com/questions/52507089/running-uvicorn-with-unix-socket).

## Packaging and Dependencies

This project uses [Poetry v2](https://python-poetry.org/) to manage Python packaging and dependencies.  Most day-to-day tasks (such as running unit tests from the command line) are orchestrated through Poetry.

A coding standard is enforced using [Black](https://pypi.org/project/black/), [isort](https://pypi.org/project/isort/) and [Pylint](https://pypi.org/project/pylint/).  Python 3 type hinting is validated using [MyPy](https://pypi.org/project/mypy/).

## Pre-Commit Hooks

We rely on pre-commit hooks to ensure that the code is properly-formatted,
clean, and type-safe when it's checked in.  The `run install` step described
below installs the project pre-commit hooks into your repository.  These hooks
are configured in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

If necessary, you can temporarily disable a hook using Git's `--no-verify`
switch.  However, keep in mind that the CI build on GitHub enforces these
checks, so the build will fail.

## Line Endings

The [`.gitattributes`](.gitattributes) file controls line endings for the files
in this repository.  Instead of relying on automatic behavior, the
`.gitattributes` file forces most files to have UNIX line endings.

## Prerequisites

Nearly all prerequisites are managed by Poetry.  All you need to do is make
sure that you have a working Python 3 enviroment and install Poetry itself.

### Poetry Version

The project is designed to work with Poetry >= 2.0.0.  If you already have an older
version of Poetry installed on your system, upgrade it first.

### MacOS

On MacOS, it's easiest to use [Homebrew](https://brew.sh/) to install Python and pipx:

```
brew install python3 pipx
```

Once that's done, make sure the `python` on your `$PATH` is Python 3 from
Homebrew (in `/usr/local`), rather than the standard Python 2 that comes with
older versions of MacOS.

Finally, install Poetry itself and then verify your installation:

```
pipx install poetry
```

To upgrade this installation later, use:

```
pipx upgrade poetry
```

### Debian

First, install Python 3 and related tools:

```
sudo apt-get install python3 python-is-python3 pipx
```

Once that's done, make sure that the `python` interpreter on your `$PATH` is
Python 3.

Finally, install Poetry itself and then verify your installation:

```
pipx install poetry
```

To upgrade this installation later, use:

```
pipx upgrade poetry
```

## Developer Tasks

The [`run`](run) script provides shortcuts for common developer tasks:

```
$ ./run --help

------------------------------------
Shortcuts for common developer tasks
------------------------------------

Basic tasks:

- run install: Setup the virtualenv via Poetry and install pre-commit hooks
- run format: Run the code formatters
- run checks: Run the code checkers
- run test: Run the unit tests
- run test -c: Run the unit tests with coverage
- run test -ch: Run the unit tests with coverage and open the HTML report
- run suite: Run the complete test suite, as for the GitHub Actions CI build

Additional tasks:

- run build: Build artifacts in the dist/ directory
- run release: Tag and release the code, triggering GHA to publish artifacts
- run rmdb: Remove the sqlite database files used for local testing
- run server: Run the vplan REST server at localhost:8080
- run server -r: Run the vplan REST server, removing the database first
- run vplan: Run the vplan client against localhost:8080
```

## Integration with PyCharm

Currently, I use [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download) as 
my day-to-day IDE.  By integrating Black and Pylint, most everything important
that can be done from a shell environment can also be done right in PyCharm.

PyCharm offers a good developer experience.  However, the underlying configuration
on disk mixes together project policy (i.e. preferences about which test runner to
use) with system-specific settings (such as the name and version of the active Python 
interpreter). This makes it impossible to commit complete PyCharm configuration 
to the Git repository.  Instead, the repository contains partial configuration, and 
there are instructions below about how to manually configure the remaining items.

### Prerequisites

Before going any further, make sure sure that you have installed all of the system
prerequisites discussed above.  Then, make sure your environment is in working
order.  In particular, if you do not run the install step, there will be no
virtualenv for PyCharm to use:

```
./run install && ./run suite
```

### Open the Project

Once you have a working shell development environment, **Open** (do not
**Import**) the `vplan` directory in PyCharm, then follow the remaining
instructions below.  By using **Open**, the existing `.idea` directory will be
retained and all of the existing settings will be used.

### Interpreter

As a security precaution, PyCharm does not trust any virtual environment
installed within the repository, such as the Poetry `.venv` directory. In the
status bar on the bottom right, PyCharm will report _No interpreter_.  Click
on this error and select **Add Interpreter**.  In the resulting dialog, click
**Ok** to accept the selected environment, which should be the Poetry virtual
environment.

### Project Structure

Go to the PyCharm settings and find the `vplan` project.  Under **Project
Structure**, mark both `src` and `tests` as source folders.  In the **Exclude
Files** box, enter the following:

```
LICENSE;NOTICE;PyPI.md;build;dist;docs/_build;out;poetry.lock;poetry.toml;run;.coverage;.coverage.lcov;.coveragerc;.gitattributes;.github;.gitignore;.htmlcov;.idea;.mypy_cache;.poetry;.pre-commit-config.yaml;.pylintrc;.pytest_cache;.python-version;.readthedocs.yml;.run;.tabignore;.venv
```

When you're done, click **Ok**.  Then, go to the gear icon in the project panel 
and uncheck **Show Excluded Files**.  This will hide the files and directories 
in the list above.

### Tool Preferences

In the PyCharm settings, go to **Editor > Inspections** and be sure that the
**Project Default** profile is selected.

Unit tests are written using [Pytest](https://docs.pytest.org/en/latest/),
and API documentation is written
using [Google Style Python Docstring](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).  However, 
neither of these is the default in PyCharm.  In the PyCharm settings, go to 
**Tools > Python Integrated Tools**.  Under **Testing > Default test runner**, 
select _pytest_.  Under **Docstrings > Docstring format**, select _Google_.

### Running Unit Tests

Right click on the `tests` folder in the project explorer and choose **Run
'pytest in tests'**.  Make sure that all of the tests pass.  If you see a slightly
different option (i.e. for "Unittest" instead of "pytest") then you probably 
skipped the preferences setup discussed above.  You may need to remove the
run configuration before PyCharm will find the right test suite.

### External Tools

Optionally, you might want to set up external tools for some of common
developer tasks: code reformatting and the PyLint and MyPy checks.  One nice
advantage of doing this is that you can configure an output filter, which makes
the Pylint and MyPy errors clickable.  To set up external tools, go to PyCharm
settings and find **Tools > External Tools**.  Add the tools as described
below.

#### Shell Environment

For this to work, it's important that tools like `poetry` are on the system
path used by PyCharm.  On Linux, depending on how you start PyCharm, your
normal shell environment may or may not be inherited.  For instance, I had to
adjust the target of my LXDE desktop shortcut to be the script below, which
sources my profile before running the `pycharm.sh` shell script:

```sh
#!/bin/bash
source ~/.bash_profile
/opt/local/lib/pycharm/pycharm-community-2020.3.2/bin/pycharm.sh
```

#### Format Code

|Field|Value|
|-----|-----|
|Name|`Format Code`|
|Description|`Run the code formatters`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`format`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Checked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Unchecked_|
|Make console active on message in stderr|_Unchecked_|
|Output filters|_Empty_|

#### Run MyPy Checks

|Field|Value|
|-----|-----|
|Name|`Run MyPy Checks`|
|Description|`Run the MyPy code checks`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`mypy`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN$:.*`|

#### Run Pylint Checks

|Field|Value|
|-----|-----|
|Name|`Run Pylint Checks`|
|Description|`Run the Pylint code checks`|
|Group|`Developer Tools`|
|Program|`$ProjectFileDir$/run`|
|Arguments|`pylint`|
|Working directory|`$ProjectFileDir$`|
|Synchronize files after execution|_Unchecked_|
|Open console for tool outout|_Checked_|
|Make console active on message in stdout|_Checked_|
|Make console active on message in stderr|_Checked_|
|Output filters|`$FILE_PATH$:$LINE$:$COLUMN.*`|


## Release Process

There is a partially-automated process to publish a new release to GitHub.

> _Note:_ In order to publish code, you must must have push permissions to the
> GitHub repo.

Ensure that you are on the `main` branch.  Releases must always be done from
`main`.

Ensure that the `Changelog` is up-to-date and reflects all of the changes that
will be published.  The top line must show your version as unreleased:

```
Version 0.6.2     unreleased
```

Run the release command:

```
./run release 0.6.2
```

This command updates `NOTICE` and `Changelog` to reflect the release version
and release date, commits those changes, tags the code, and pushes to GitHub.
The new tag triggers a GitHub Actions build that runs the test suite, generates
the artifacts, and finally creates a release from the tag.
