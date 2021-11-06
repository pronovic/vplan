# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Configuration for the vacation plan manager.
"""

from typing import List

from pydantic import Field, SecretStr  # pylint: disable=no-name-in-module
from pydantic_yaml import SemVer, VersionedYamlModel, YamlModel

from .engine.interface import VacationPlan


class SmartThingsCredential(YamlModel):
    """A SmartThings PAT token credential."""

    id: str = Field("Credential identifier")
    token: SecretStr = Field("SmartThings PAT token")


class CredentialsConfig(VersionedYamlModel):
    """Credentials configuration."""

    class Config:
        min_version = "1.0.0"
        max_version = "1.0.0"

    version: SemVer = Field(..., title="Credential configuration version")
    credentials: List[SmartThingsCredential] = Field(..., title="Available credentials")

    def pat_token(self, credential_id: str) -> str:
        """Return the PAT token associated with a credential id"""
        for credential in self.credentials:
            if credential.id == credential_id:
                return credential.token.get_secret_value()
        raise ValueError("Unknown credential id")


class VacationConfig(VersionedYamlModel):
    """Vacation configuration."""

    class Config:
        min_version = "1.0.0"
        max_version = "1.0.0"

    version: SemVer = Field(..., title="Vacation configuration version")
    credential_id: SecretStr = Field(..., title="Identifier of the credential to use")
    plan: VacationPlan = Field(..., title="Vacation plan")
