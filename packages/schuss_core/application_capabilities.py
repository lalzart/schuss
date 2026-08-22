"""Client-neutral Task 023 application capability description."""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping


APPLICATION_DESCRIPTION_VERSION = "schuss-application-capability-description-v0"
APPLICATION_DESCRIPTION_VERSION_V1 = "schuss-application-capability-description-v1"
APPLICATION_DESCRIPTION_VERSION_V2 = "schuss-application-capability-description-v2"
APPLICATION_DESCRIPTION_VERSION_V3 = "schuss-application-capability-description-v3"
APPLICATION_DESCRIPTION_VERSION_V4 = "schuss-application-capability-description-v4"
APPLICATION_DESCRIPTION_VERSION_V5 = "schuss-application-capability-description-v5"
APPLICATION_DESCRIPTION_VERSION_V6 = "schuss-application-capability-description-v6"
APPLICATION_DESCRIPTION_VERSION_V7 = "schuss-application-capability-description-v7"
APPLICATION_DESCRIPTION_VERSION_V8 = "schuss-application-capability-description-v8"
APPLICATION_DESCRIPTION_VERSION_V9 = "schuss-application-capability-description-v9"
APPLICATION_DESCRIPTION_VERSION_V10 = "schuss-application-capability-description-v10"
APPLICATION_DESCRIPTION_VERSION_V11 = "schuss-application-capability-description-v11"
APPLICATION_DESCRIPTION_VERSION_V12 = "schuss-application-capability-description-v12"


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

TASK030_CAPABILITY_ENTRIES = (
    _entry(
        "catalog.implementations.search",
        "catalog",
        "Search and filter individual implementations in the exact derived catalog.",
        10,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set",),
    ),
)

DESKTOP_PATCHER_CAPABILITY_ENTRIES = (
    _entry(
        "component.inspect",
        "component",
        "Inspect one exact governed component contract for client-neutral authoring.",
        11,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
)

DESKTOP_PATCHER_REPLACEMENTS = {
    "graph.transact": _entry(
        "graph.transact",
        "graph",
        "Propose and validate one in-memory graph successor without persistence.",
        11,
        ("exact-record-set",),
        "proposal-only",
        ("base-content-hash", "exact-record-set", "exact-reference"),
    ),
    "project.profile.transact": _entry(
        "project.profile.transact",
        "project",
        "Atomically version one project-owned graph, instrument, and build request.",
        11,
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
}


def _desktop_patcher_entries() -> tuple[dict[str, Any], ...]:
    inherited = (
        *CAPABILITY_ENTRIES,
        *TASK026_CAPABILITY_ENTRIES,
        *TASK029_CAPABILITY_ENTRIES,
        *TASK030_CAPABILITY_ENTRIES,
    )
    return tuple(
        copy.deepcopy(DESKTOP_PATCHER_REPLACEMENTS.get(entry["operation"], entry))
        for entry in inherited
    ) + tuple(copy.deepcopy(entry) for entry in DESKTOP_PATCHER_CAPABILITY_ENTRIES)


APPLICATION_CAPABILITY_ENTRIES_V4 = _desktop_patcher_entries()

DESKTOP_SESSION_CAPABILITY_ENTRIES = (
    _entry(
        "build.session.start",
        "build",
        "Start one process-local build job for an exact accepted project request.",
        12,
        ("exact-project-snapshot", "process-local-build-service"),
        "build-output-write",
        ("exact-handler", "exact-reference", "execute-intent", "fresh-output-root"),
    ),
    _entry(
        "build.session.inspect",
        "build",
        "Inspect progress, diagnostics, stages, and artifact facts for one build job.",
        12,
        ("process-local-build-service",),
        "read-only",
        ("exact-session",),
    ),
    _entry(
        "device.session.discover",
        "device",
        "Explicitly discover and inspect exact Ksoloti Core device identities.",
        12,
        ("explicit-project-workspace", "process-local-device-service"),
        "device-read",
        ("discovery-intent", "exact-reference"),
    ),
    _entry(
        "device.session.inspect",
        "device",
        "Inspect one process-local device identity and compatibility result.",
        12,
        ("process-local-device-service",),
        "read-only",
        ("exact-session",),
    ),
    _entry(
        "device.upload.start",
        "device",
        "Start one verified volatile-RAM upload from an exact successful build.",
        12,
        ("process-local-build-service", "process-local-device-service"),
        "device-volatile-write",
        ("exact-artifact", "exact-session", "volatile-upload-intent"),
    ),
    _entry(
        "device.upload.inspect",
        "device",
        "Inspect progress and verification for one volatile upload session.",
        12,
        ("process-local-device-service",),
        "read-only",
        ("exact-session",),
    ),
)

APPLICATION_CAPABILITY_ENTRIES_V5 = (
    *APPLICATION_CAPABILITY_ENTRIES_V4,
    *DESKTOP_SESSION_CAPABILITY_ENTRIES,
)

AI_SONIC_AUTHORING_CAPABILITY_ENTRIES = (
    _entry(
        "sonic.intent.plan",
        "authoring",
        "Plan parallel valid existing, compound, and native creation lanes without a cost objective.",
        13,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "sonic-validity-gate"),
    ),
    _entry(
        "authoring.draft.create",
        "authoring",
        "Create one process-local project-scoped object draft.",
        13,
        ("explicit-project-workspace", "process-local-authoring-service"),
        "authoring-draft",
        ("exact-reference", "sonic-validity-gate"),
    ),
    _entry(
        "authoring.draft.inspect",
        "authoring",
        "Inspect one process-local project-scoped object draft.",
        13,
        ("explicit-project-workspace", "process-local-authoring-service"),
        "read-only",
        ("draft-handle",),
    ),
    _entry(
        "authoring.draft.evaluate",
        "authoring",
        "Run bounded structural or native-kernel host evaluation and cache one audition artifact.",
        13,
        ("explicit-project-workspace", "process-local-authoring-service"),
        "workspace-cache-write",
        ("draft-handle", "sonic-validity-gate"),
    ),
    _entry(
        "authoring.change.preview",
        "authoring",
        "Preview exact project-local object and optional graph successor bytes without acceptance.",
        13,
        ("explicit-project-workspace", "process-local-authoring-service"),
        "proposal-only",
        ("draft-handle", "expected-project-reference", "sonic-validity-gate"),
    ),
    _entry(
        "authoring.change.accept",
        "authoring",
        "Atomically accept one exact previewed project-local object and optional graph insertion.",
        13,
        ("explicit-project-workspace", "process-local-authoring-service"),
        "workspace-write",
        (
            "confirmation-fingerprint",
            "expected-project-reference",
            "preview-handle",
            "write-intent",
        ),
    ),
    _entry(
        "project.objects.list",
        "project",
        "List exact project-local object definitions in the accepted project closure.",
        13,
        ("explicit-project-workspace", "process-local-authoring-service"),
        "read-only",
        ("explicit-project-workspace",),
    ),
    _entry(
        "project.object.inspect",
        "project",
        "Inspect one exact accepted project-local object definition.",
        13,
        ("explicit-project-workspace", "process-local-authoring-service"),
        "read-only",
        ("exact-reference", "explicit-project-workspace"),
    ),
)

APPLICATION_CAPABILITY_ENTRIES_V6 = (
    *APPLICATION_CAPABILITY_ENTRIES_V5,
    *AI_SONIC_AUTHORING_CAPABILITY_ENTRIES,
)

HOST_RUNTIME_CAPABILITY_ENTRIES = (
    _entry(
        "host.render.start",
        "build",
        "Lower and render one exact accepted project through the portable host runtime.",
        14,
        ("exact-project-snapshot", "process-local-host-runtime-service"),
        "host-artifact-write",
        ("exact-package", "offline-render-intent"),
    ),
    _entry(
        "host.render.inspect",
        "build",
        "Inspect one process-local offline host render.",
        14,
        ("process-local-host-runtime-service",),
        "read-only",
        ("exact-session",),
    ),
    _entry(
        "audio.devices.inspect",
        "device",
        "Explicitly enumerate local CoreAudio and CoreMIDI devices.",
        14,
        ("process-local-audio-session-service",),
        "audio-device-read",
        ("audio-device-intent",),
    ),
    _entry(
        "audio.session.start",
        "device",
        "Start one process-local host audio session for an exact accepted project.",
        14,
        ("exact-project-snapshot", "process-local-audio-session-service"),
        "audio-device-control",
        ("audio-device-intent", "exact-package"),
    ),
    _entry(
        "audio.session.inspect",
        "device",
        "Inspect one process-local host audio session.",
        14,
        ("process-local-audio-session-service",),
        "read-only",
        ("exact-session",),
    ),
    _entry(
        "audio.session.stop",
        "device",
        "Stop one process-local host audio session.",
        14,
        ("process-local-audio-session-service",),
        "audio-device-control",
        ("audio-device-intent", "exact-session"),
    ),
)

APPLICATION_CAPABILITY_ENTRIES_V7 = (
    *APPLICATION_CAPABILITY_ENTRIES_V6,
    *HOST_RUNTIME_CAPABILITY_ENTRIES,
)

WORKSPACE_LIBRARY_CAPABILITY_ENTRIES = (
    _entry(
        "workspace.projects.list",
        "project",
        "List validated accepted projects directly below one explicit projects root.",
        15,
        ("explicit-projects-root",),
        "read-only",
        ("explicit-projects-root",),
    ),
    _entry(
        "workspace.project.create",
        "project",
        "Create one template-backed accepted project below one explicit projects root.",
        15,
        ("explicit-projects-root",),
        "workspace-write",
        ("create-only-child-workspace", "explicit-projects-root", "write-intent"),
    ),
)

APPLICATION_CAPABILITY_ENTRIES_V8 = (
    *APPLICATION_CAPABILITY_ENTRIES_V7,
    *WORKSPACE_LIBRARY_CAPABILITY_ENTRIES,
)

VARIABLE_HOST_RUNTIME_CAPABILITY_ENTRIES = tuple(
    {
        **copy.deepcopy(entry),
        "request_schema_version": "schuss-operation-request-v16",
        "result_schema_version": "schuss-operation-result-v16",
    }
    for entry in HOST_RUNTIME_CAPABILITY_ENTRIES
) + (
    _entry(
        "audio.session.replace",
        "device",
        "Prepare one exact successor host graph and activate it at a block boundary with reset state.",
        16,
        ("exact-project-snapshot", "process-local-audio-session-service"),
        "audio-device-control",
        (
            "expected-active-package",
            "expected-engine-generation",
            "exact-session",
            "exact-successor-project",
            "reset-state-replacement-intent",
        ),
    ),
)

_HOST_RUNTIME_OPERATION_NAMES = {
    entry["operation"] for entry in HOST_RUNTIME_CAPABILITY_ENTRIES
}
APPLICATION_CAPABILITY_ENTRIES_V9 = tuple(
    entry
    for entry in APPLICATION_CAPABILITY_ENTRIES_V8
    if entry["operation"] not in _HOST_RUNTIME_OPERATION_NAMES
) + VARIABLE_HOST_RUNTIME_CAPABILITY_ENTRIES

PERFORMANCE_CONTROL_CAPABILITY_ENTRIES = (
    _entry(
        "performance.inspect",
        "performance",
        "Inspect one exact controller, performance graph, instrument, and DSP graph closure.",
        17,
        ("exact-record-set",),
        "read-only",
        ("exact-record-set", "exact-reference"),
    ),
)

APPLICATION_CAPABILITY_ENTRIES_V10 = (
    *APPLICATION_CAPABILITY_ENTRIES_V9,
    *PERFORMANCE_CONTROL_CAPABILITY_ENTRIES,
)

COLLECTION_PROVIDER_CAPABILITY_ENTRIES = (
    _entry(
        "collections.inspect",
        "catalog",
        "Inspect exact object collections through one explicit machine-local discovery profile.",
        18,
        ("exact-record-set", "explicit-local-collection-profile"),
        "read-only",
        ("exact-record-set", "explicit-local-collection-profile"),
    ),
    _entry(
        "implementation.availability.inspect",
        "catalog",
        "Inspect one exact catalog implementation for one exact target/backend and local provider profile.",
        18,
        ("exact-record-set", "explicit-local-collection-profile"),
        "read-only",
        (
            "exact-record-set",
            "exact-reference",
            "explicit-local-collection-profile",
        ),
    ),
)

APPLICATION_CAPABILITY_ENTRIES_V11 = (
    *APPLICATION_CAPABILITY_ENTRIES_V10,
    *COLLECTION_PROVIDER_CAPABILITY_ENTRIES,
)

INSTRUMENT_LIBRARY_CAPABILITY_ENTRIES = (
    _entry(
        "instrument.library.list",
        "instrument",
        "List the exact noncanonical Instrument Lab audition library and current verified-build availability.",
        19,
        ("exact-record-set", "repository-instrument-library"),
        "read-only",
        ("exact-record-set",),
    ),
    _entry(
        "instrument.session.inspect",
        "instrument",
        "Inspect one process-local native instrument audition session.",
        19,
        ("process-local-instrument-session-service",),
        "read-only",
        ("exact-session",),
    ),
    _entry(
        "instrument.session.start",
        "instrument",
        "Launch one exact verified native JUCE audition application through a process-local session.",
        19,
        (
            "exact-record-set",
            "process-local-instrument-session-service",
            "repository-instrument-library",
        ),
        "native-application-launch",
        (
            "exact-prototype-revision",
            "native-application-launch-intent",
            "verified-executable",
        ),
    ),
)

APPLICATION_CAPABILITY_ENTRIES_V12 = (
    *APPLICATION_CAPABILITY_ENTRIES_V11,
    *INSTRUMENT_LIBRARY_CAPABILITY_ENTRIES,
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
EXPECTED_OPERATIONS_V3 = tuple(
    sorted(
        entry["operation"]
        for entry in (
            *CAPABILITY_ENTRIES,
            *TASK026_CAPABILITY_ENTRIES,
            *TASK029_CAPABILITY_ENTRIES,
            *TASK030_CAPABILITY_ENTRIES,
        )
    )
)
EXPECTED_OPERATIONS_V4 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V4)
)
EXPECTED_OPERATIONS_V5 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V5)
)
EXPECTED_OPERATIONS_V6 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V6)
)
EXPECTED_OPERATIONS_V7 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V7)
)
EXPECTED_OPERATIONS_V8 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V8)
)
EXPECTED_OPERATIONS_V9 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V9)
)
EXPECTED_OPERATIONS_V10 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V10)
)
EXPECTED_OPERATIONS_V11 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V11)
)
EXPECTED_OPERATIONS_V12 = tuple(
    sorted(entry["operation"] for entry in APPLICATION_CAPABILITY_ENTRIES_V12)
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
    session_services_available: bool,
    authoring_service_available: bool,
    workspace_library_available: bool,
    host_runtime_service_available: bool,
    audio_session_service_available: bool,
    instrument_library_service_available: bool,
) -> str:
    operation = entry["operation"]
    if operation.startswith("workspace.") and not workspace_library_available:
        return "requires-projects-root"
    if operation.startswith("host.render.") and not host_runtime_service_available:
        return "requires-host-runtime-service"
    if operation.startswith("audio.") and not audio_session_service_available:
        return "requires-audio-session-service"
    if operation.startswith("instrument.") and not instrument_library_service_available:
        return "requires-instrument-library-service"
    if operation.startswith("authoring.") or operation in {
        "project.objects.list",
        "project.object.inspect",
    }:
        if not project_workspace_available:
            return "requires-project-workspace"
        if not authoring_service_available:
            return "requires-authoring-service"
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
    if (
        operation.startswith("build.session.")
        or operation.startswith("device.session.")
        or operation.startswith("device.upload.")
    ) and not session_services_available:
        return "requires-session-services"
    return "available"


def build_application_description(
    *,
    record_set_reference: Mapping[str, Any],
    schemas: Mapping[str, Any],
    entries: Iterable[Mapping[str, Any]] | None = None,
    project_workspace_available: bool = False,
    execution_service_available: bool = False,
    session_services_available: bool = False,
    authoring_service_available: bool = False,
    workspace_library_available: bool = False,
    host_runtime_service_available: bool = False,
    audio_session_service_available: bool = False,
    instrument_library_service_available: bool = False,
) -> dict[str, Any]:
    """Return the deterministic application description for one exact context."""

    uses_v12 = "application_capability_description_v12" in schemas
    uses_v11 = uses_v12 or "application_capability_description_v11" in schemas
    uses_v10 = uses_v11 or "application_capability_description_v10" in schemas
    uses_v9 = uses_v10 or "application_capability_description_v9" in schemas
    uses_v8 = uses_v9 or "application_capability_description_v8" in schemas
    uses_v7 = uses_v8 or "application_capability_description_v7" in schemas
    uses_v6 = uses_v7 or "application_capability_description_v6" in schemas
    uses_v5 = uses_v6 or "application_capability_description_v5" in schemas
    uses_v4 = uses_v5 or "application_capability_description_v4" in schemas
    uses_v3 = uses_v4 or "application_capability_description_v3" in schemas
    uses_v2 = uses_v3 or "application_capability_description_v2" in schemas
    uses_v1 = uses_v2 or "application_capability_description_v1" in schemas
    if uses_v12:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V12
        expected_operations = EXPECTED_OPERATIONS_V12
    elif uses_v11:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V11
        expected_operations = EXPECTED_OPERATIONS_V11
    elif uses_v10:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V10
        expected_operations = EXPECTED_OPERATIONS_V10
    elif uses_v9:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V9
        expected_operations = EXPECTED_OPERATIONS_V9
    elif uses_v8:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V8
        expected_operations = EXPECTED_OPERATIONS_V8
    elif uses_v7:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V7
        expected_operations = EXPECTED_OPERATIONS_V7
    elif uses_v6:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V6
        expected_operations = EXPECTED_OPERATIONS_V6
    elif uses_v5:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V5
        expected_operations = EXPECTED_OPERATIONS_V5
    elif uses_v4:
        default_entries = APPLICATION_CAPABILITY_ENTRIES_V4
        expected_operations = EXPECTED_OPERATIONS_V4
    elif uses_v3:
        default_entries = (
            *CAPABILITY_ENTRIES,
            *TASK026_CAPABILITY_ENTRIES,
            *TASK029_CAPABILITY_ENTRIES,
            *TASK030_CAPABILITY_ENTRIES,
        )
        expected_operations = EXPECTED_OPERATIONS_V3
    elif uses_v2:
        default_entries = (
            *CAPABILITY_ENTRIES,
            *TASK026_CAPABILITY_ENTRIES,
            *TASK029_CAPABILITY_ENTRIES,
        )
        expected_operations = EXPECTED_OPERATIONS_V2
    elif uses_v1:
        default_entries = (*CAPABILITY_ENTRIES, *TASK026_CAPABILITY_ENTRIES)
        expected_operations = EXPECTED_OPERATIONS_V1
    else:
        default_entries = CAPABILITY_ENTRIES
        expected_operations = EXPECTED_OPERATIONS
    selected = list(default_entries if entries is None else entries)
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
            session_services_available=session_services_available,
            authoring_service_available=authoring_service_available,
            workspace_library_available=workspace_library_available,
            host_runtime_service_available=host_runtime_service_available,
            audio_session_service_available=audio_session_service_available,
            instrument_library_service_available=instrument_library_service_available,
        )
        described.append(entry)
    return {
        "schema_version": (
            "application-capability-description-v12"
            if uses_v12
            else "application-capability-description-v11"
            if uses_v11
            else "application-capability-description-v10"
            if uses_v10
            else "application-capability-description-v9"
            if uses_v9
            else "application-capability-description-v8"
            if uses_v8
            else "application-capability-description-v7"
            if uses_v7
            else "application-capability-description-v6"
            if uses_v6
            else "application-capability-description-v5"
            if uses_v5
            else "application-capability-description-v4"
            if uses_v4
            else "application-capability-description-v3"
            if uses_v3
            else "application-capability-description-v2"
            if uses_v2
            else "application-capability-description-v1"
            if uses_v1
            else "application-capability-description-v0"
        ),
        "canonical_profile": "schuss-canonical-json-v1",
        "description_version": (
            APPLICATION_DESCRIPTION_VERSION_V12
            if uses_v12
            else APPLICATION_DESCRIPTION_VERSION_V11
            if uses_v11
            else APPLICATION_DESCRIPTION_VERSION_V10
            if uses_v10
            else APPLICATION_DESCRIPTION_VERSION_V9
            if uses_v9
            else APPLICATION_DESCRIPTION_VERSION_V8
            if uses_v8
            else APPLICATION_DESCRIPTION_VERSION_V7
            if uses_v7
            else APPLICATION_DESCRIPTION_VERSION_V6
            if uses_v6
            else APPLICATION_DESCRIPTION_VERSION_V5
            if uses_v5
            else APPLICATION_DESCRIPTION_VERSION_V4
            if uses_v4
            else APPLICATION_DESCRIPTION_VERSION_V3
            if uses_v3
            else APPLICATION_DESCRIPTION_VERSION_V2
            if uses_v2
            else APPLICATION_DESCRIPTION_VERSION_V1
            if uses_v1
            else APPLICATION_DESCRIPTION_VERSION
        ),
        "record_set_reference": copy.deepcopy(dict(record_set_reference)),
        "operations": described,
    }
