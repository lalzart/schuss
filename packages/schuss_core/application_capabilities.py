"""Client-neutral Task 023 application capability description."""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping


APPLICATION_DESCRIPTION_VERSION = "schuss-application-capability-description-v0"
APPLICATION_DESCRIPTION_VERSION_V1 = "schuss-application-capability-description-v1"
APPLICATION_DESCRIPTION_VERSION_V2 = "schuss-application-capability-description-v2"


class CapabilityRegistryError(ValueError):
    """The static application capability registry violates its contract."""


def _entry(
    operation: str,
    domain_group: str,
    purpose: str,
    version: int,
    required_contexts: Iterable[str],
    effect_class: str,
    explicit_gates: Iterable[str],
) -> dict[str, Any]:
    return {
        "operation": operation,
        "domain_group": domain_group,
        "purpose": purpose,
        "request_schema_version": f"schuss-operation-request-v{version}",
        "result_schema_version": f"schuss-operation-result-v{version}",
        "required_contexts": sorted(set(required_contexts)),
        "effect_class": effect_class,
        "explicit_gates": sorted(set(explicit_gates)),
        "declared_support": "supported",
        "evidence_boundary": "operation-contract-only",
    }


CAPABILITY_ENTRIES = (
    _entry(
        "application.describe",
        "application",
        "Describe the exact client-neutral application operation surface.",
        7,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set",),
    ),
    _entry(
        "build.execute",
        "build",
        "Execute one exact accepted build plan through one exact handler.",
        5,
        ("exact-execution-service", "exact-record-set", "fresh-output-root"),
        "build-output-write",
        (
            "exact-handler",
            "exact-record-set",
            "exact-reference",
            "execute-intent",
            "fresh-output-root",
        ),
    ),
    _entry(
        "build.plan",
        "build",
        "Plan one exact build through the client-neutral compiler front half.",
        4,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
    _entry(
        "build.resolve",
        "build",
        "Resolve exact implementation bindings without executing a backend.",
        1,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
    _entry(
        "catalog.inspect",
        "catalog",
        "Inspect one exact function-first catalog family.",
        2,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
    _entry(
        "catalog.search",
        "catalog",
        "Search and filter the exact derived catalog projection.",
        2,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set",),
    ),
    _entry(
        "gills.inspect",
        "gills",
        "Inspect one exact Gills instrument, panel, mapping, and runtime closure.",
        6,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
    _entry(
        "graph.inspect",
        "graph",
        "Inspect one exact graph and component-contract closure.",
        1,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
    _entry(
        "graph.transact",
        "graph",
        "Propose and validate one in-memory graph successor without persistence.",
        1,
        ("exact-record-set",),
        "proposal-only",
        ("base-content-hash", "exact-record-set", "exact-reference"),
    ),
    _entry(
        "project.graph.commit",
        "project",
        "Persist one exact accepted graph and project successor.",
        3,
        ("explicit-project-workspace",),
        "workspace-write",
        (
            "base-content-hash",
            "expected-project-reference",
            "explicit-project-workspace",
            "write-intent",
        ),
    ),
    _entry(
        "project.init",
        "project",
        "Create one explicit project workspace from exact accepted references.",
        3,
        ("exact-record-set", "explicit-project-workspace"),
        "workspace-write",
        ("create-only-workspace", "exact-record-set", "explicit-project-workspace"),
    ),
    _entry(
        "project.inspect",
        "project",
        "Inspect one explicit accepted project workspace.",
        3,
        ("explicit-project-workspace",),
        "read-only",
        ("explicit-project-workspace",),
    ),
    _entry(
        "project.validate",
        "project",
        "Validate one exact base-plus-project closure.",
        3,
        ("explicit-project-workspace",),
        "read-only",
        ("explicit-project-workspace",),
    ),
    _entry(
        "records.validate",
        "records",
        "Validate the selected exact accepted record closure.",
        1,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set",),
    ),
)

TASK026_CAPABILITY_ENTRIES = (
    _entry(
        "project.history.inspect",
        "project",
        "Inspect deterministic immutable project ancestry.",
        8,
        ("explicit-project-workspace",),
        "read-only",
        ("explicit-project-workspace", "immutable-history"),
    ),
    _entry(
        "project.profile.fork",
        "project",
        "Allocate and persist one complete project-owned profile closure.",
        8,
        ("exact-record-set", "explicit-project-workspace"),
        "workspace-write",
        (
            "expected-project-reference",
            "explicit-project-workspace",
            "profile-template-reference",
            "write-intent",
        ),
    ),
    _entry(
        "project.profile.transact",
        "project",
        "Atomically version one project-owned graph, instrument, and build request.",
        8,
        ("explicit-project-workspace",),
        "workspace-write",
        (
            "base-content-hash",
            "expected-project-reference",
            "explicit-project-workspace",
            "exact-reference",
            "write-intent",
        ),
    ),
    _entry(
        "project.revert",
        "project",
        "Create a successor selecting one exact immutable ancestor state.",
        8,
        ("explicit-project-workspace",),
        "workspace-write",
        (
            "expected-project-reference",
            "explicit-project-workspace",
            "immutable-history",
            "target-project-reference",
            "write-intent",
        ),
    ),
)

TASK029_CAPABILITY_ENTRIES = (
    _entry(
        "machine.inspect",
        "machine",
        "Inspect one exact completed machine or inspection-only reference machine.",
        9,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
)


EXPECTED_OPERATIONS = tuple(sorted(entry["operation"] for entry in CAPABILITY_ENTRIES))
EXPECTED_OPERATIONS_V1 = tuple(
    sorted(
        entry["operation"]
        for entry in (*CAPABILITY_ENTRIES, *TASK026_CAPABILITY_ENTRIES)
    )
)
EXPECTED_OPERATIONS_V2 = tuple(
    sorted(
        entry["operation"]
        for entry in (
            *CAPABILITY_ENTRIES,
            *TASK026_CAPABILITY_ENTRIES,
            *TASK029_CAPABILITY_ENTRIES,
        )
    )
)


def _schema_key(version: str, kind: str) -> str:
    number = version.rsplit("v", 1)[1]
    return f"operation_{kind}_v{number}"


def _availability(
    entry: Mapping[str, Any],
    schemas: Mapping[str, Any],
    *,
    project_workspace_available: bool,
    execution_service_available: bool,
) -> str:
    operation = entry["operation"]
    if operation.startswith("project."):
        return (
            "available"
            if project_workspace_available
            else "requires-project-workspace"
        )
    request_key = _schema_key(entry["request_schema_version"], "request")
    result_key = _schema_key(entry["result_schema_version"], "result")
    if request_key not in schemas or result_key not in schemas:
        return "unavailable-in-selected-record-set"
    if operation == "build.execute" and not execution_service_available:
        return "requires-execution-service"
    return "available"


def build_application_description(
    *,
    record_set_reference: Mapping[str, Any],
    schemas: Mapping[str, Any],
    entries: Iterable[Mapping[str, Any]] | None = None,
    project_workspace_available: bool = False,
    execution_service_available: bool = False,
) -> dict[str, Any]:
    """Return the deterministic application description for one exact context."""

    uses_v2 = "application_capability_description_v2" in schemas
    uses_v1 = uses_v2 or "application_capability_description_v1" in schemas
    default_entries = (
        (*CAPABILITY_ENTRIES, *TASK026_CAPABILITY_ENTRIES, *TASK029_CAPABILITY_ENTRIES)
        if uses_v2
        else (*CAPABILITY_ENTRIES, *TASK026_CAPABILITY_ENTRIES)
        if uses_v1
        else CAPABILITY_ENTRIES
    )
    selected = list(default_entries if entries is None else entries)
    expected_operations = (
        EXPECTED_OPERATIONS_V2
        if uses_v2
        else EXPECTED_OPERATIONS_V1
        if uses_v1
        else EXPECTED_OPERATIONS
    )
    operations = [entry.get("operation") for entry in selected]
    if (
        len(operations) != len(set(operations))
        or tuple(sorted(operations)) != expected_operations
    ):
        raise CapabilityRegistryError(
            "application capability registry must contain every accepted operation exactly once"
        )
    described: list[dict[str, Any]] = []
    for source in sorted(selected, key=lambda item: item["operation"]):
        entry = copy.deepcopy(dict(source))
        entry["required_contexts"] = sorted(set(entry["required_contexts"]))
        entry["explicit_gates"] = sorted(set(entry["explicit_gates"]))
        entry["availability"] = _availability(
            entry,
            schemas,
            project_workspace_available=project_workspace_available,
            execution_service_available=execution_service_available,
        )
        described.append(entry)
    return {
        "schema_version": (
            "application-capability-description-v2"
            if uses_v2
            else "application-capability-description-v1"
            if uses_v1
            else "application-capability-description-v0"
        ),
        "canonical_profile": "schuss-canonical-json-v1",
        "description_version": (
            APPLICATION_DESCRIPTION_VERSION_V2
            if uses_v2
            else APPLICATION_DESCRIPTION_VERSION_V1
            if uses_v1
            else APPLICATION_DESCRIPTION_VERSION
        ),
        "record_set_reference": copy.deepcopy(dict(record_set_reference)),
        "operations": described,
    }
