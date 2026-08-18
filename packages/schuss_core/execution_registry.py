"""Exact product build-handler registry shared by CLI and desktop clients."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from .build_execution import ExecutionService


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ExecutionRegistryError(ValueError):
    """The exact retained handler registry cannot be constructed."""


def registered_execution_service(output_root: Path) -> ExecutionService:
    """Register retained, direct, and mapped handlers without fallback."""

    adapter_path = REPOSITORY_ROOT / "legacy/ksoloti-bridge/task011c_adapter.py"
    specification = importlib.util.spec_from_file_location(
        "schuss_task011c_product_adapter", adapter_path
    )
    if specification is None or specification.loader is None:
        raise ExecutionRegistryError(
            "exact Task 011C adapter cannot be loaded"
        )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    from .effects_profile_backend import registration as effects_registration
    from .gills_direct_backend import registration as direct_registration
    from .gills_mapped_backend import registration as mapped_registration
    from .gills_mapped_backend_v2 import registration as mapped_v2_registration

    return ExecutionService.from_values(
        (
            module.registration(),
            direct_registration(),
            mapped_registration(),
            mapped_v2_registration(),
            effects_registration(),
        ),
        Path(output_root),
    )
