# Since this file was taken from elsewhere, it does not adhere to our coding style
# type: ignore
# pylint: skip-file

from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, Union, no_type_check

from pydantic import BaseModel, errors, validator
from semver import VersionInfo

# This code was taken from the pydantic-yaml project.  In v1 of pydantic-yaml, the
# interface totally changed.  All of the YAML specific model types were removed in
# favor of a new mixin approach.  Unfortunately, there was effectively no replacement
# for VersionedYamlModel.  I took that code under the terms of its license, and
# imported it here as VersionedModel, which operates in terms of JSON instead of
# YAML.  Then I migrated everything that used it to the new approach.
#
# Sources:
#
#    - https://github.com/NowanIlfideme/pydantic-yaml/blob/54ff4bad7bca758a9dd22a791b707a2b9c27159e/src/pydantic_yaml/ext/semver.py
#    - https://github.com/NowanIlfideme/pydantic-yaml/blob/54ff4bad7bca758a9dd22a791b707a2b9c27159e/src/pydantic_yaml/ext/versioned_model.py
#
# Original license:
#
#   MIT License
#   Copyright (c) 2020 Anatoly Makarevich
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
# ---------------------------------------------------------------------------------

Comparator = Callable[["SemVer", Any], bool]


# noinspection PyBroadException
def _comparator(operator: Comparator) -> Comparator:
    """Wrap a Version binary op method in a type-check."""

    @wraps(operator)
    def wrapper(self: "SemVer", other: Any) -> bool:
        if not isinstance(other, SemVer):
            try:
                other = SemVer(other)
            except Exception:
                return NotImplemented
        return operator(self, other)

    return wrapper


class SemVer(str):
    """Semantic Version string for Pydantic."""

    allow_build: bool = True
    allow_prerelease: bool = True

    __slots__ = ["_info"]

    @no_type_check
    def __new__(cls, version: Optional[str], **kwargs) -> object:
        return str.__new__(cls, cls.parse(**kwargs) if version is None else version)

    def __init__(self, version: str):
        str.__init__(version)
        self._info = VersionInfo.parse(version)

    @classmethod
    def parse(
        cls,
        major: int,
        minor: int = 0,
        patch: int = 0,
        prerelease: Optional[str] = None,
        build: Optional[str] = None,
    ) -> str:
        return str(VersionInfo(major, minor, patch, prerelease, build))

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str, "SemVer"]) -> "SemVer":
        vi = VersionInfo.parse(value)
        if not cls.allow_build and (vi.build is None):
            raise errors.NotNoneError()
        if not cls.allow_prerelease and (vi.prerelease is None):
            raise errors.NotNoneError()
        return cls(value)

    @property
    def info(self) -> VersionInfo:
        return self._info

    @info.setter
    def info(self, value):
        raise AttributeError("attribute 'info' is readonly")

    @property
    def major(self) -> int:
        """The major part of a version (read-only)."""
        return self._info.major

    @major.setter
    def major(self, value):
        raise AttributeError("attribute 'major' is readonly")

    @property
    def minor(self) -> int:
        """The minor part of a version (read-only)."""
        return self._info.minor

    @minor.setter
    def minor(self, value):
        raise AttributeError("attribute 'minor' is readonly")

    @property
    def patch(self) -> int:
        """The patch part of a version (read-only)."""
        return self._info.patch

    @patch.setter
    def patch(self, value):
        raise AttributeError("attribute 'patch' is readonly")

    @property
    def prerelease(self) -> Optional[str]:
        """The prerelease part of a version (read-only)."""
        return self._info.prerelease

    @prerelease.setter
    def prerelease(self, value):
        raise AttributeError("attribute 'prerelease' is readonly")

    @property
    def build(self) -> Optional[str]:
        """The build part of a version (read-only)."""
        return self._info.build

    @build.setter
    def build(self, value):
        raise AttributeError("attribute 'build' is readonly")

    def __hash__(self) -> int:
        return super.__hash__(self)  # use string hashing

    @_comparator
    def __eq__(self, other: "SemVer"):
        return self._info == other._info

    @_comparator
    def __ne__(self, other: "SemVer"):
        return self._info != other._info

    @_comparator
    def __lt__(self, other: "SemVer"):
        return self._info < other._info

    @_comparator
    def __le__(self, other: "SemVer"):
        return self._info <= other._info

    @_comparator
    def __gt__(self, other: "SemVer"):
        return self._info > other._info

    @_comparator
    def __ge__(self, other: "SemVer"):
        return self._info >= other._info


def _chk_between(v, lo=None, hi=None):
    if v is None:
        return
    if (hi is not None) and (v > hi):
        raise ValueError(f"Default version higher than maximum: {v} > {hi}")
    if (lo is not None) and (v < lo):
        raise ValueError(f"Default version lower than minimum: {v} < {lo}")


def _get_minmax_robust(cls: Type["VersionedModel"]) -> Tuple[Optional[SemVer], Optional[SemVer]]:
    min_, max_ = None, None
    for supcls in cls.mro():
        Config = getattr(supcls, "Config", None)
        if Config is not None:
            if min_ is None:
                min_ = getattr(Config, "min_version", None)
            if max_ is None:
                max_ = getattr(Config, "max_version", None)
    return min_, max_


class VersionedModel(BaseModel):
    """Base model with versioning support.

    Usage
    -----
    Inherit from this class, and set a Config class with attributes
    `min_version` and/or `max_version`:

    ```python
    class MyModel(VersionedModel):
        class Config:
            min_version = "1.0.0"

        foo: str = "bar"
    ```

    By default, the minimum version is "0.0.0" and the maximum is unset.
    This pattern enables you to more easily version your YAML files and
    protect against accidentally using older (or newer) configuration file formats.

    Notes
    -----
    By default, a validator checks that the "version" field is between
    `Config.min_version` and `Config.max_version`, if those are not None.

    It's probably best not to even set the `version` field by hand, but rather
    in your configuration.
    """

    version: SemVer

    # noinspection PyTypeChecker
    def __init_subclass__(cls) -> None:
        # Check Config class types
        config = getattr(cls, "Config", None)
        if config is not None:
            # check one field
            minv = getattr(config, "min_version", None)
            if minv is not None:
                if not isinstance(minv, SemVer):
                    setattr(config, "min_version", SemVer(minv))
            # check other field
            maxv = getattr(config, "max_version", None)
            if maxv is not None:
                if not isinstance(maxv, SemVer):
                    setattr(config, "max_version", SemVer(maxv))

        # Check ranges
        min_, max_ = _get_minmax_robust(cls)
        if (min_ is not None) and (max_ is not None) and (min_ > max_):
            raise ValueError(f"Minimum version higher than maximum: {min_!r} > {max_!r}")

        # Check the default value of the "version" field
        fld = cls.__fields__["version"]
        d = fld.default
        if d is None:
            pass
        else:
            _chk_between(d, lo=min_, hi=max_)
        if not issubclass(fld.type_, SemVer):
            raise TypeError(f"Field type for `version` must be SemVer, got {fld.type_!r}")

    # noinspection PyTypeChecker
    @validator("version", always=True)
    def _check_semver(cls, v):
        min_, max_ = _get_minmax_robust(cls)
        _chk_between(v, lo=min_, hi=max_)
        return v

    class Config:
        min_version = SemVer("0.0.0")
        max_version = None
