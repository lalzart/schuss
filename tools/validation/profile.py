"""Small, dependency-free gates shared by validation tests and the runner."""

from __future__ import annotations

import os
import unittest
from pathlib import Path


PROFILE_ENVIRONMENT = "SCHUSS_VALIDATION_PROFILE"
VALID_PROFILES = frozenset(
    {"current", "compatibility", "configured-sources", "native", "reproduction"}
)


def active_profile() -> str:
    """Return the explicit profile, defaulting safely to ordinary validation."""

    profile = os.environ.get(PROFILE_ENVIRONMENT, "current")
    if profile not in VALID_PROFILES:
        raise ValueError(f"unknown validation profile: {profile}")
    return profile


def profile_enabled(profile: str) -> bool:
    if profile not in VALID_PROFILES:
        raise ValueError(f"unknown validation profile: {profile}")
    return active_profile() == profile


def requires_profile(profile: str):
    """Skip a non-ordinary test unless its owning profile selected it."""

    decorator = unittest.skipUnless(
        profile_enabled(profile),
        f"requires explicit {profile} validation profile",
    )

    def apply(function):
        wrapped = decorator(function)
        wrapped.__schuss_validation_profile__ = profile
        return wrapped

    return apply


def configured_sources_available(repository_root: Path) -> bool:
    return (repository_root / "catalog/sources.local.yml").is_file()
