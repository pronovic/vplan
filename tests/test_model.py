# pylint: disable=line-too-long:

import os

import pytest
from pydantic import ValidationError

from vplan.model import SemVer, VersionedModel

# ---------------------------------------------------------------------------------
# This code was taken from the pydantic-yaml project.  In v1 of pydantic-yaml, the
# interface totally changed.  All of the YAML specific model types were removed in
# favor of a different approach.  Unfortunately, there was effectively no replacement
# for VersionedYamlModel.  I took that code under the terms of its license, and
# imported it here as VersionedModel, which operates in terms of JSON instead of
# YAML.  Then I migrated everything that used it to the new-style mixin approach.
#
# Source: https://github.com/NowanIlfideme/pydantic-yaml/blob/54ff4bad7bca758a9dd22a791b707a2b9c27159e/src/pydantic_yaml/test/test_versioned.py
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


def fixture(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "model", filename)


def test_versioned_model():
    """Test VersionedModel."""

    file = fixture("versioned.json")

    class A(VersionedModel):
        foo: str = "bar"  # type: ignore[annotation-unchecked]

    class B(VersionedModel):
        foo: str = "bar"  # type: ignore[annotation-unchecked]

        class Config:
            min_version = "2.0.0"

    class C(VersionedModel):
        foo: str = "baz"  # type: ignore[annotation-unchecked]

        class Config:
            max_version = "0.5.0"

    A.parse_file(file)

    with pytest.raises(ValidationError):
        B.parse_file(file)

    with pytest.raises(ValidationError):
        C.parse_file(file)

    with pytest.raises(ValueError):

        class BadVersionConstraint(VersionedModel):  # pylint: disable=unused-variable:
            class Config:
                min_version = "3.0.0"
                max_version = "2.1.0"


def test_versioned_docs():
    """Test docs for versioned model."""

    class A(VersionedModel):
        """Model with min, max constraints as None."""

        foo: str = "bar"  # type: ignore[annotation-unchecked]

    class B(VersionedModel):
        """Model with a maximum version set."""

        foo: str = "bar"  # type: ignore[annotation-unchecked]

        class Config:
            min_version = "2.0.0"

    ex_json = """
{
  "version": "1.0.0",
  "foo": "baz"
}
    """

    a = A.parse_raw(ex_json)
    assert a.version == SemVer("1.0.0")
    assert a.foo == "baz"

    with pytest.raises(ValidationError):
        B.parse_raw(ex_json)
