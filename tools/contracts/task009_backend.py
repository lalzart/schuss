#!/usr/bin/env python3
"""Bounded executable backend for the exact Task 009 Blend proof.

This module intentionally supports one graph and one legacy realization.  The
same lowering and Java/ARM adapters are used by the non-production conformance
probe and by the production handler behind the Task 008 invocation value.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any, Iterable, Mapping, Sequence

import validator_core as core


GRAPH_ID = "schuss-graph-000001"
GRAPH_REVISION = 1
GRAPH_HASH = "sha256:b38562dc2dcf80036e8fc1d78fe8ee425de01f4943495a23375bfb4e7f346e6e"
CONTRACT_ID = "schuss-component-contract-000003"
CONTRACT_REVISION = 1
CONTRACT_HASH = "sha256:96a29faf58769be5f2ac52de07aa80cae3dcdff28f0f3c158fb1fd12cc234a8d"
BINDING_ID = "schuss-implementation-000028"
BINDING_R1_HASH = "sha256:6f1a0268c40ca192435bcd7a66f201ab0577ff8786590d3c05bace4911726b59"
ENVIRONMENT_ID = "schuss-prerequisite-environment-000001"
ENVIRONMENT_HASH = "sha256:8c2021ba5cbbcc1cbb63ca5957baeba71cdedf6a987d5f7091f609858539b3e7"
PROCEDURE_ID = "schuss-procedure-000001"
PROCEDURE_HASH = "sha256:ca1fca9f18bedb533d192aa0e04f56a1b87ccd45188720f413e375025366cc73"

PATCHER_ARCHIVE_SHA256 = "2f2d6c9e985e5b8609c847a0b21ad7611e614e7dd2a0cb3c51d9b50a77a36f32"
FACTORY_ARCHIVE_SHA256 = "1f510801728dfe6218ae741e172d406a748ded0f290a9bc866493fea42916531"
CLASS_ARCHIVE_SHA256 = "d425431d6b97df0515f37ca822a9c8bdb1a51bf4bc3be654eec8744e42363fca"
FIRMWARE_ELF_SHA256 = "df65f2153eb999386cc1bc30b382cafeac63aea8495bf8cb4cdad1c01fca944b"
FIRMWARE_BIN_SHA256 = "fd61a6a109a234d1c72e445a0542ab59c407a6896b9aafe2bfcbcadaf775e258"

JAVA_SHA256 = "b56748e35a76328d8a33e52d298930806484e39fa4a68a10d7a54debf51a9151"
JAVAC_SHA256 = "7937caa17b49a97957cb0d2cc9ff18d148f4a20f98e49c8278cdc45b43a67ba4"
ARM_COMPONENTS = {
    "arm-none-eabi-as": "58acc8c96d8fb361c4feb1e04ef73f496b33c788edb39d518a268821c591dfb0",
    "arm-none-eabi-gcc": "475b81bfcec7787a411e3cb200150c1afb0ccd6d05ab0b1929bd933f2261328f",
    "arm-none-eabi-g++": "69fe197c81592ae356650437e315966cd592b1015ecbda53edddcde494dcc296",
    "arm-none-eabi-ld": "eaccfd337f8b955665168c8344d301e6441577a72739fc5a4116b9fdb072e67a",
    "arm-none-eabi-objcopy": "744e6a4c7b65059f0f4497a01304e7ad1d1edda1defc2af75f28a6574fb77d29",
    "arm-none-eabi-objdump": "d4d9369294ae583393fd9fdaa5ce039acf319c1e78623351f4864e04382b13c6",
    "arm-none-eabi-size": "377e2d38ba57ab5ee5a8e2b6933debeea5cda4249fd1ebc5355deb77c6d365b8",
}

PROBE_STAGES = ("backend-lowering", "artifact-generation", "target-compile-link")
ARTIFACT_ORDER = (
    "resolution-plan",
    "legacy-boundary-patch",
    "source-map",
    "generated-cpp",
    "arm-object",
    "target-executable",
    "link-map",
)

XFADE_UUID = "375dc91d218e96cdc9cbc7e92adb48f705ef701a"
INLET_A_UUID = "b577fe41e0a6bc7b5502ce33cb8a3129e2e28ee5"
INLET_F_UUID = "5c585d2dcd9c05631e345ac09626a22a639d7c13"
OUTLET_A_UUID = "abd8c5fd3b0524a6630f65cad6dc27f6c58e2a3e"


class Task009BackendError(RuntimeError):
    """One deterministic, fail-closed Task 009 diagnostic."""

    def __init__(self, code: str, stage: str, subject: str, message: str):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.subject = subject
        self.message = message

    def as_probe_diagnostic(self) -> dict[str, Any]:
        return {
            "diagnostic_id": "diagnostic-000001",
            "code": self.code,
            "severity": "error",
            "stage": self.stage,
            "subject": self.subject,
        }


@dataclasses.dataclass(frozen=True)
class ExecutionConfig:
    repository_root: Path
    content_store: Path
    java: Path
    javac: Path
    arm_bin: Path

    def normalized(self) -> "ExecutionConfig":
        return ExecutionConfig(*(
            Path(value).resolve()
            for value in dataclasses.astuple(self)
        ))


@dataclasses.dataclass(frozen=True)
class ArtifactFact:
    kind: str
    media_type: str
    producer_stage: str
    byte_sha256: str
    byte_length: int
    retained_path: Path

    @property
    def portable_locator(self) -> str:
        return f"sha256/{self.byte_sha256}"


@dataclasses.dataclass(frozen=True)
class ExecutionOutcome:
    status: str
    artifacts: tuple[ArtifactFact, ...]
    stage_statuses: tuple[tuple[str, str], ...]
    diagnostics: tuple[dict[str, Any], ...]
    bridge_result: dict[str, Any] | None
    command_vectors: tuple[dict[str, Any], ...]
    resource_facts: dict[str, Any] | None
    failure: Task009BackendError | None


def _sha256(path: Path) -> str:
    return core.sha256_file(path)


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8")


def _reference(identifier: str, revision: int, content_hash: str, field: str) -> dict[str, Any]:
    return {field: identifier, "revision": revision, "content_hash": content_hash}


def _require_equal(actual: Any, expected: Any, code: str, stage: str, subject: str) -> None:
    if actual != expected:
        raise Task009BackendError(code, stage, subject, "exact Task 009 closure mismatch")


def validate_probe_input(probe: Mapping[str, Any]) -> None:
    """Accept only the authorized immutable candidate-under-test envelope."""

    subject = f"{probe.get('conformance_probe_id', '<unknown>')}@{probe.get('revision', '?')}"
    expected = {
        "candidate_state": "candidate-under-test",
        "binding_reference": _reference(BINDING_ID, 1, BINDING_R1_HASH, "implementation_id"),
        "contract_reference": _reference(CONTRACT_ID, CONTRACT_REVISION, CONTRACT_HASH, "component_contract_id"),
        "graph_reference": _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "environment_reference": _reference(ENVIRONMENT_ID, 1, ENVIRONMENT_HASH, "prerequisite_environment_id"),
        "procedure_reference": _reference(PROCEDURE_ID, 1, PROCEDURE_HASH, "procedure_id"),
        "requested_stages": list(PROBE_STAGES),
        "execution_authorization": "task-009-authorized",
        "production_selection_authority": False,
    }
    for key, value in expected.items():
        _require_equal(
            probe.get(key), value, "TASK009_PROBE_INPUT_REJECTED",
            "backend-lowering", subject,
        )


def invocation_schema_closure(
    schema: Mapping[str, Any], build_request_schema: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind the public seam's one external reference without file discovery."""

    closed = copy.deepcopy(dict(schema))
    accepted = closed["properties"]["accepted_build_request"]
    if accepted != {"$ref": "build-request-v0.schema.json"}:
        raise Task009BackendError(
            "TASK009_INVOCATION_SCHEMA_DRIFT",
            "backend-lowering",
            "schuss-backend-invocation-input-v1",
            "public backend invocation schema reference changed",
        )
    closed["properties"]["accepted_build_request"] = {
        "type": "object",
        "x-schuss-domain-value": True,
    }
    return closed


def validate_invocation_input(
    invocation: Mapping[str, Any],
    schema: Mapping[str, Any],
    build_request_schema: Mapping[str, Any],
    expected_binding_reference: Mapping[str, Any],
    expected_build_request: Mapping[str, Any],
) -> None:
    """Revalidate the public Task 008 value before creating an output root."""

    closed_schema = invocation_schema_closure(schema, build_request_schema)
    errors = core.schema_errors(dict(invocation), closed_schema, closed_schema)
    request_value = invocation.get("accepted_build_request")
    if isinstance(request_value, dict):
        errors.extend(
            core.schema_errors(
                request_value,
                dict(build_request_schema),
                dict(build_request_schema),
                "$.accepted_build_request",
            )
        )
    if errors:
        raise Task009BackendError(
            "TASK009_INVOCATION_SCHEMA_INVALID", "backend-lowering",
            "schuss-backend-invocation-input-v1", "backend invocation violates its public schema",
        )
    if invocation.get("status") != "ready-for-backend-invocation":
        raise Task009BackendError(
            "TASK009_INVOCATION_NOT_READY", "backend-lowering",
            "schuss-backend-invocation-input-v1", "backend invocation is not ready",
        )
    request = invocation["accepted_build_request"]
    _require_equal(
        request,
        dict(expected_build_request),
        "TASK009_BUILD_REQUEST_STALE",
        "backend-lowering",
        request.get("build_request_id", "build-request"),
    )
    _require_equal(
        request["graph_reference"],
        _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "TASK009_GRAPH_UNSUPPORTED", "backend-lowering", request["build_request_id"],
    )
    selected = invocation.get("selected_bindings", [])
    _require_equal(
        selected,
        [{"node_id": "graph-node-000001", "binding_reference": dict(expected_binding_reference)}],
        "TASK009_BINDING_NOT_SELECTED", "backend-lowering", request["build_request_id"],
    )
    traces = invocation.get("resolution_traces", [])
    if len(traces) != 1:
        raise Task009BackendError(
            "TASK009_RESOLUTION_TRACE_INVALID",
            "backend-lowering",
            request["build_request_id"],
            "exact Task 009 resolution trace count differs",
        )
    trace = traces[0]
    selected_candidates = [
        candidate
        for candidate in trace.get("candidates", [])
        if candidate.get("binding_reference") == dict(expected_binding_reference)
    ]
    if (
        trace.get("node_id") != "graph-node-000001"
        or trace.get("status") != "selected"
        or trace.get("selected_binding_reference") != dict(expected_binding_reference)
        or len(selected_candidates) != 1
        or selected_candidates[0].get("exclusion_reasons") != []
        or selected_candidates[0].get("unresolved_reasons") != []
    ):
        raise Task009BackendError(
            "TASK009_RESOLUTION_TRACE_INVALID",
            "backend-lowering",
            request["build_request_id"],
            "exact Task 009 selected trace is absent or uncertain",
        )
    boundary = invocation["boundary"]
    _require_equal(
        boundary,
        {
            "completed_stage": "implementation-resolution",
            "next_stage": "backend-lowering",
            "next_stage_status": "not-run",
            "executable_handler_status": "absent",
        },
        "TASK009_INVOCATION_BOUNDARY_INVALID", "backend-lowering", request["build_request_id"],
    )


def axp_bytes() -> bytes:
    """Return the one controlled legacy boundary; it is not graph truth."""

    lines = (
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<patch-1.0 appVersion="1.0.12">',
        f'   <obj type="patch/inlet a" uuid="{INLET_A_UUID}" name="schuss_a" x="14" y="28">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        f'   <obj type="patch/inlet a" uuid="{INLET_A_UUID}" name="schuss_b" x="14" y="98">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        f'   <obj type="patch/inlet f" uuid="{INLET_F_UUID}" name="schuss_blend" x="14" y="168">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        f'   <obj type="mix/xfade" uuid="{XFADE_UUID}" name="schuss_xfade" x="182" y="84">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        f'   <obj type="patch/outlet a" uuid="{OUTLET_A_UUID}" name="schuss_out" x="350" y="84">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        '   <nets>',
        '      <net>',
        '         <source obj="schuss_a" outlet="inlet"/>',
        '         <dest obj="schuss_xfade" inlet="i1"/>',
        '      </net>',
        '      <net>',
        '         <source obj="schuss_b" outlet="inlet"/>',
        '         <dest obj="schuss_xfade" inlet="i2"/>',
        '      </net>',
        '      <net>',
        '         <source obj="schuss_blend" outlet="inlet"/>',
        '         <dest obj="schuss_xfade" inlet="c"/>',
        '      </net>',
        '      <net>',
        '         <source obj="schuss_xfade" outlet="o"/>',
        '         <dest obj="schuss_out" inlet="outlet"/>',
        '      </net>',
        '   </nets>',
        '   <settings>',
        '      <subpatchmode>normal</subpatchmode>',
        '   </settings>',
        '   <notes><![CDATA[]]></notes>',
        '</patch-1.0>',
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def resolution_plan(binding_reference: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "task009-resolution-plan-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_request_graph_reference": _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "selected_binding_reference": copy.deepcopy(dict(binding_reference)),
        "nodes": [{
            "node_id": "graph-node-000001",
            "contract_reference": _reference(CONTRACT_ID, CONTRACT_REVISION, CONTRACT_HASH, "component_contract_id"),
            "realization_form": "generated-legacy-object",
            "legacy_object": {
                "type": "mix/xfade",
                "uuid": XFADE_UUID,
                "instance_name": "schuss_xfade",
            },
            "facet_mappings": [
                ["component-port-000001", "legacy-inlet", "i1"],
                ["component-port-000002", "legacy-inlet", "i2"],
                ["component-port-000003", "legacy-inlet", "c"],
                ["component-port-000004", "legacy-outlet", "o"],
            ],
        }],
        "public_boundary": [
            ["graph-facet-000002", "schuss_a", "inlet"],
            ["graph-facet-000003", "schuss_b", "inlet"],
            ["graph-facet-000001", "schuss_blend", "inlet"],
            ["graph-facet-000004", "schuss_out", "outlet"],
        ],
        "implicit_discovery": False,
        "unsupported_fallback": False,
    }


def source_map(binding_reference: Mapping[str, Any], generated: bytes) -> dict[str, Any]:
    text = generated.decode("utf-8")
    lines = text.splitlines()
    ranges = []
    for name in ("schuss_a", "schuss_b", "schuss_blend", "schuss_xfade", "schuss_out"):
        generated_name = name.replace("_", "__")
        matches = [index + 1 for index, line in enumerate(lines) if generated_name in line]
        if not matches:
            raise Task009BackendError(
                "TASK009_SOURCE_MAP_REGION_MISSING", "artifact-generation",
                name, "generated source contains no stable region for emitted object",
            )
        ranges.append({"legacy_instance": name, "first_line": min(matches), "last_line": max(matches)})
    return {
        "schema_version": "task009-source-map-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "graph_reference": _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "binding_reference": copy.deepcopy(dict(binding_reference)),
        "node_id": "graph-node-000001",
        "contract_facets": [
            "component-port-000001", "component-port-000002",
            "component-port-000003", "component-port-000004",
        ],
        "legacy_object_uuid": XFADE_UUID,
        "axp_locations": [
            ["graph-node-000001", "/patch-1.0/obj[@name='schuss_xfade']"],
            ["graph-facet-000001", "/patch-1.0/obj[@name='schuss_blend']"],
            ["graph-facet-000002", "/patch-1.0/obj[@name='schuss_a']"],
            ["graph-facet-000003", "/patch-1.0/obj[@name='schuss_b']"],
            ["graph-facet-000004", "/patch-1.0/obj[@name='schuss_out']"],
        ],
        "generated_cpp_sha256": hashlib.sha256(generated).hexdigest(),
        "generated_regions": ranges,
        "diagnostic_ids": [],
    }


def _safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    with tarfile.open(archive, "r:") as opened:
        for member in opened.getmembers():
            logical = Path(member.name)
            if logical.is_absolute() or ".." in logical.parts or not (member.isdir() or member.isfile()):
                raise Task009BackendError(
                    "TASK009_RETAINED_ARCHIVE_UNSAFE", "backend-lowering",
                    archive.name, "retained archive contains an unsupported member",
                )
            target = destination / logical
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                target.chmod(member.mode & 0o777)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source = opened.extractfile(member)
                if source is None:
                    raise Task009BackendError(
                        "TASK009_RETAINED_ARCHIVE_UNREADABLE", "backend-lowering",
                        archive.name, "retained archive member cannot be read",
                    )
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)


def _verify_file(path: Path, expected_sha256: str, code: str, subject: str) -> None:
    if not path.is_file() or _sha256(path) != expected_sha256:
        raise Task009BackendError(code, "backend-lowering", subject, "authenticated executable byte mismatch")


def verify_execution_config(config: ExecutionConfig) -> ExecutionConfig:
    config = config.normalized()
    _verify_file(config.java, JAVA_SHA256, "TASK009_JAVA_IDENTITY_MISMATCH", "java")
    _verify_file(config.javac, JAVAC_SHA256, "TASK009_JAVAC_IDENTITY_MISMATCH", "javac")
    for name, digest in ARM_COMPONENTS.items():
        _verify_file(config.arm_bin / name, digest, "TASK009_ARM_IDENTITY_MISMATCH", name)
    products = {
        PATCHER_ARCHIVE_SHA256, FACTORY_ARCHIVE_SHA256, CLASS_ARCHIVE_SHA256,
        FIRMWARE_ELF_SHA256, FIRMWARE_BIN_SHA256,
    }
    for digest in products:
        _verify_file(
            config.content_store / "sha256" / digest, digest,
            "TASK009_RETAINED_PRODUCT_MISMATCH", f"sha256/{digest}",
        )
    return config


def _classpath(source_root: Path, classes_root: Path, manifest_path: Path) -> str:
    manifest = core.load_json(manifest_path)
    jar_paths = [source_root / item["path"] for item in manifest["members"] if item["kind"] == "jar"]
    for path in jar_paths:
        if not path.is_file():
            raise Task009BackendError(
                "TASK009_JAVA_CLASSPATH_MISSING", "artifact-generation",
                path.name, "authenticated Java classpath member is missing",
            )
    return os.pathsep.join([str(classes_root / "build/classes"), *(str(path) for path in jar_paths)])


def _run(
    arguments: Sequence[str], cwd: Path, environment: Mapping[str, str],
    stage: str, code: str, subject: str, timeout: int = 180,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        list(arguments), cwd=cwd, env=dict(environment), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=timeout, check=False,
    )
    if completed.returncode:
        raise Task009BackendError(code, stage, subject, "isolated tool invocation failed")
    return completed


def _portable_command(
    component: str, arguments: Sequence[str], working_directory: str, exit_status: int = 0
) -> dict[str, Any]:
    return {
        "component": component,
        "arguments": list(arguments),
        "working_directory": working_directory,
        "exit_status": exit_status,
    }


def _compile_bridge(
    config: ExecutionConfig, output_root: Path, source_root: Path, classes_root: Path
) -> tuple[str, list[dict[str, Any]]]:
    repository = config.repository_root
    bridge_classes = output_root / "work/bridge-classes"
    bridge_classes.mkdir(parents=True)
    classpath = _classpath(
        source_root, classes_root,
        repository / "evidence/task-009-prerequisite-v0/java-classpath-members.json",
    )
    sources = [
        repository / "legacy/ksoloti-bridge/src/main/java/axoloti/object/SchussObjectAccess.java",
        repository / "legacy/ksoloti-bridge/src/main/java/axoloti/SchussPatchAccess.java",
        repository / "legacy/ksoloti-bridge/src/main/java/generatedobjects/SchussGeneratedCapture.java",
        repository / "legacy/ksoloti-bridge/src/main/java/org/schuss/legacy/ksoloti/StableJson.java",
        repository / "legacy/ksoloti-bridge/src/main/java/org/schuss/legacy/ksoloti/ExactSliceBridge.java",
    ]
    arguments = [
        str(config.javac), "-g:none", "-encoding", "UTF-8", "-source", "21",
        "-target", "21", "-cp", classpath, "-d", str(bridge_classes),
        *(str(path) for path in sources),
    ]
    environment = _tool_environment(output_root, config.arm_bin)
    _run(
        arguments, output_root, environment, "artifact-generation",
        "TASK009_BRIDGE_COMPILE_FAILED", "legacy/ksoloti-bridge",
    )
    portable = _portable_command(
        "javac", [
            "javac", "-g:none", "-encoding", "UTF-8", "-source", "21",
            "-target", "21", "-cp", "authenticated-java-closure",
            "-d", "work/bridge-classes", *(
                path.relative_to(repository).as_posix() for path in sources
            ),
        ], ".",
    )
    return os.pathsep.join([str(bridge_classes), classpath]), [portable]


def _tool_environment(output_root: Path, arm_bin: Path) -> dict[str, str]:
    home = output_root / "work/home"
    temporary = output_root / "work/tmp"
    home.mkdir(parents=True, exist_ok=True)
    temporary.mkdir(parents=True, exist_ok=True)
    return {
        "CLASSPATH": "",
        "HOME": str(home),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.pathsep.join([str(arm_bin), "/usr/bin", "/bin"]),
        "SOURCE_DATE_EPOCH": "0",
        "TZ": "UTC",
        "TMPDIR": str(temporary),
    }


def _run_bridge(
    config: ExecutionConfig, output_root: Path, source_root: Path,
    factory_root: Path, runtime_root: Path, classpath: str, axp: Path, generated: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    arguments = [
        str(config.java), "-XX:-UsePerfData", "-Djava.awt.headless=true",
        "-Dfile.encoding=UTF-8", "-Duser.language=en", "-Duser.country=US",
        "-Duser.timezone=UTC", f"-Duser.home={output_root / 'work/home'}",
        f"-Djava.io.tmpdir={output_root / 'work/tmp'}", "-cp", classpath,
        "org.schuss.legacy.ksoloti.ExactSliceBridge",
        f"--axp={axp}", f"--output={generated}",
        f"--factory-root={factory_root}", f"--patcher-root={source_root}",
        f"--runtime-root={runtime_root}",
    ]
    completed = _run(
        arguments, output_root, _tool_environment(output_root, config.arm_bin),
        "artifact-generation", "TASK009_JAVA_GENERATION_FAILED", "exact-slice-bridge",
    )
    if completed.stderr:
        raise Task009BackendError(
            "TASK009_BRIDGE_STDERR_INVALID", "artifact-generation",
            "exact-slice-bridge", "bridge emitted unstable or ambient stderr output",
        )
    try:
        result = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Task009BackendError(
            "TASK009_BRIDGE_OUTPUT_INVALID", "artifact-generation",
            "exact-slice-bridge", "bridge did not emit one canonical JSON value",
        ) from error
    if result.get("status") != "success" or result.get("axp_sha256") != _sha256(axp):
        raise Task009BackendError(
            "TASK009_BRIDGE_RESULT_MISMATCH", "artifact-generation",
            "exact-slice-bridge", "bridge result does not name the exact input/output",
        )
    portable = _portable_command(
        "java", [
            "java", "-XX:-UsePerfData", "-Djava.awt.headless=true",
            "-Dfile.encoding=UTF-8", "-Duser.language=en", "-Duser.country=US",
            "-Duser.timezone=UTC", "-Duser.home=work/home",
            "-Djava.io.tmpdir=work/tmp", "-cp", "authenticated-java-closure",
            "org.schuss.legacy.ksoloti.ExactSliceBridge",
            "--axp=proof/build/blend.axp", "--output=proof/build/blend.cpp",
            "--factory-root=factory-capsule", "--patcher-root=source-capsule",
            "--runtime-root=runtime",
        ], ".",
    )
    return result, portable


def _arm_build(
    config: ExecutionConfig, output_root: Path, source_root: Path,
    generated: Path,
) -> tuple[Path, Path, Path, dict[str, Any], list[dict[str, Any]]]:
    proof = output_root / "proof"
    build = proof / "build"
    runtime = output_root / "runtime/build"
    build.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)
    generated_target = build / "blend.cpp"
    if generated.resolve() != generated_target.resolve():
        shutil.copyfile(generated, generated_target)
    shutil.copyfile(source_root / "firmware/xpatch.h", build / "xpatch.h")
    shutil.copyfile(
        config.content_store / "sha256" / FIRMWARE_ELF_SHA256,
        runtime / "ksoloti.elf",
    )
    firmware = source_root / "firmware"
    environment = _tool_environment(output_root, config.arm_bin)
    environment.update({
        "axoloti_home": "..",
        "axoloti_firmware": ".",
        "axoloti_link_firmware": "../../runtime",
        "axoloti_libraries": "../../proof",
    })
    target = "../../proof/build/blend.elf"
    make_arguments = [
        "/usr/bin/make", "-f", "Makefile.patch.mk", "BOARDDEF=BOARD_KSOLOTI_CORE",
        "FWOPTIONDEF=FW_NORMAL", "BUILDFILENAME=blend", target,
    ]
    _run(
        make_arguments, firmware, environment, "target-compile-link",
        "TASK009_ARM_COMPILE_LINK_FAILED", "blend.cpp", timeout=300,
    )
    object_raw = build / "blend.o"
    elf_raw = build / "blend.elf"
    map_path = build / "blend.map"
    if not all(path.is_file() for path in (object_raw, elf_raw, map_path)):
        raise Task009BackendError(
            "TASK009_ARM_OUTPUT_MISSING", "target-compile-link",
            "blend.cpp", "ARM build did not emit its exact required outputs",
        )
    object_stripped = build / "blend-stripped.o"
    elf_relinked = build / "blend-deterministic.elf"
    elf_stripped = build / "blend-stripped.elf"
    objcopy = config.arm_bin / "arm-none-eabi-objcopy"
    gcc = config.arm_bin / "arm-none-eabi-gcc"
    objdump = config.arm_bin / "arm-none-eabi-objdump"
    size = config.arm_bin / "arm-none-eabi-size"
    commands: list[dict[str, Any]] = [
        _portable_command(
            "make", [
                "make", "-f", "Makefile.patch.mk", "BOARDDEF=BOARD_KSOLOTI_CORE",
                "FWOPTIONDEF=FW_NORMAL", "BUILDFILENAME=blend",
                "../../proof/build/blend.elf",
            ], "source-capsule/firmware",
        )
    ]
    _run(
        [str(objcopy), "--strip-debug", str(object_raw.relative_to(output_root)), str(object_stripped.relative_to(output_root))],
        output_root, environment, "target-compile-link",
        "TASK009_ARM_STRIP_FAILED", "arm-object",
    )
    commands.append(_portable_command(
        "arm-none-eabi-objcopy",
        ["arm-none-eabi-objcopy", "--strip-debug", "proof/build/blend.o", "proof/build/blend-stripped.o"],
        ".",
    ))
    relink_arguments = [
        str(gcc), "-Tramlink_ksoloti.ld", "-Bsymbolic", "-Wl,--gc-sections",
        "-Wl,--print-memory-usage", "-fno-common", "-mcpu=cortex-m4",
        "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16", "-mno-thumb-interwork",
        "-mthumb", "-mtune=cortex-m4", "-nostartfiles",
        "../../proof/build/blend-stripped.o", "-lm",
        "-Wl,-Map=../../proof/build/blend.map,--cref,--build-id=none,--just-symbols=../../runtime/build/ksoloti.elf",
        "-o", "../../proof/build/blend-deterministic.elf",
    ]
    _run(
        relink_arguments, firmware, environment, "target-compile-link",
        "TASK009_ARM_RELINK_FAILED", "target-executable",
    )
    commands.append(_portable_command(
        "arm-none-eabi-gcc",
        ["arm-none-eabi-gcc", *relink_arguments[1:]],
        "source-capsule/firmware",
    ))
    _run(
        [str(objcopy), "--strip-debug", str(elf_relinked.relative_to(output_root)), str(elf_stripped.relative_to(output_root))],
        output_root, environment, "target-compile-link",
        "TASK009_ARM_STRIP_FAILED", "target-executable",
    )
    commands.append(_portable_command(
        "arm-none-eabi-objcopy",
        ["arm-none-eabi-objcopy", "--strip-debug", "proof/build/blend-deterministic.elf", "proof/build/blend-stripped.elf"],
        ".",
    ))
    header = _run(
        [str(objdump), "-f", str(elf_stripped.relative_to(output_root))],
        output_root, environment, "target-compile-link",
        "TASK009_ARM_ELF_INSPECTION_FAILED", "target-executable",
    )
    sizes = _run(
        [str(size), "-A", "-x", str(elf_stripped.relative_to(output_root))],
        output_root, environment, "target-compile-link",
        "TASK009_ARM_SIZE_FAILED", "target-executable",
    )
    header_text = header.stdout.decode("utf-8", errors="strict")
    if "file format elf32-littlearm" not in header_text or "architecture: arm" not in header_text:
        raise Task009BackendError(
            "TASK009_TARGET_ABI_MISMATCH", "target-compile-link",
            "target-executable", "linked output is not the required little-endian ARM ELF",
        )
    commands.extend([
        _portable_command("arm-none-eabi-objdump", ["arm-none-eabi-objdump", "-f", "proof/build/blend-stripped.elf"], "."),
        _portable_command("arm-none-eabi-size", ["arm-none-eabi-size", "-A", "-x", "proof/build/blend-stripped.elf"], "."),
    ])
    resource = {
        "schema_version": "task009-static-resource-facts-v0",
        "method": "compiler-link-map",
        "evidence_level": 5,
        "elf_header": [line.strip() for line in header_text.splitlines() if line.strip()],
        "size_output": [line.rstrip() for line in sizes.stdout.decode("utf-8", errors="strict").splitlines() if line.strip()],
        "limitations": [
            "Static compiler and linker observations are not connected-runtime measurements.",
            "No real-time CPU, timing, or audible behavior was measured.",
        ],
    }
    return object_stripped, elf_stripped, map_path, resource, commands


def _retain(output_root: Path, kind: str, source: Path, media_type: str, producer_stage: str) -> ArtifactFact:
    digest = _sha256(source)
    destination = output_root / "content-addressed/sha256" / digest
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if _sha256(destination) != digest:
            raise Task009BackendError(
                "TASK009_CONTENT_STORE_COLLISION", producer_stage,
                kind, "content-addressed output collision",
            )
    else:
        shutil.copyfile(source, destination)
        destination.chmod(0o444)
    return ArtifactFact(kind, media_type, producer_stage, digest, source.stat().st_size, destination)


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise Task009BackendError(
            "TASK009_OUTPUT_ALREADY_EXISTS", "artifact-generation",
            path.name, "exact output already exists",
        )
    path.write_bytes(payload)


def execute_exact_slice(
    binding_reference: Mapping[str, Any], config: ExecutionConfig,
    output_root: Path, failure_stage: str | None = None,
) -> ExecutionOutcome:
    """Execute the exact slice in one fresh explicit root.

    ``failure_stage`` is a test-only injection point and never changes a
    successful artifact.  A terminal stage leaves all later stages not-run.
    """

    output_root = Path(output_root).resolve()
    if output_root.exists():
        raise Task009BackendError(
            "TASK009_OUTPUT_ROOT_NOT_FRESH", "backend-lowering",
            "output-root", "output root must not exist",
        )
    config = verify_execution_config(config)
    output_root.mkdir(parents=True)
    stages = {stage: "not-run" for stage in PROBE_STAGES}
    facts: list[ArtifactFact] = []
    commands: list[dict[str, Any]] = []
    bridge_result: dict[str, Any] | None = None
    resources: dict[str, Any] | None = None
    current_stage = "backend-lowering"
    try:
        if failure_stage == current_stage:
            raise Task009BackendError(
                "TASK009_INJECTED_LOWERING_FAILURE", current_stage,
                GRAPH_ID, "injected exact-slice lowering failure",
            )
        source_root = output_root / "source-capsule"
        factory_root = output_root / "factory-capsule"
        classes_root = output_root / "class-capsule"
        _safe_extract(config.content_store / "sha256" / PATCHER_ARCHIVE_SHA256, source_root)
        _safe_extract(config.content_store / "sha256" / FACTORY_ARCHIVE_SHA256, factory_root)
        _safe_extract(config.content_store / "sha256" / CLASS_ARCHIVE_SHA256, classes_root)
        runtime_root = output_root / "runtime"
        (runtime_root / "build").mkdir(parents=True)
        shutil.copyfile(
            config.content_store / "sha256" / FIRMWARE_BIN_SHA256,
            runtime_root / "build/ksoloti.bin",
        )
        plan_path = output_root / "proof/build/resolution-plan.json"
        _write_bytes(plan_path, _canonical_bytes(resolution_plan(binding_reference)))
        facts.append(_retain(
            output_root, "resolution-plan", plan_path,
            "application/vnd.schuss.resolution-plan+json", "implementation-resolution",
        ))
        stages[current_stage] = "success"

        current_stage = "artifact-generation"
        if failure_stage == current_stage:
            raise Task009BackendError(
                "TASK009_INJECTED_JAVA_FAILURE", current_stage,
                "exact-slice-bridge", "injected exact-slice Java-generation failure",
            )
        axp_path = output_root / "proof/build/blend.axp"
        generated_path = output_root / "proof/build/blend.cpp"
        _write_bytes(axp_path, axp_bytes())
        classpath, compile_commands = _compile_bridge(
            config, output_root, source_root, classes_root,
        )
        commands.extend(compile_commands)
        bridge_result, bridge_command = _run_bridge(
            config, output_root, source_root, factory_root, runtime_root,
            classpath, axp_path, generated_path,
        )
        commands.append(bridge_command)
        generated = generated_path.read_bytes()
        if hashlib.sha256(generated).hexdigest() != bridge_result["generated_cpp_sha256"]:
            raise Task009BackendError(
                "TASK009_GENERATED_SOURCE_HASH_MISMATCH", current_stage,
                "blend.cpp", "generated source differs from bridge result",
            )
        source_map_path = output_root / "proof/build/source-map.json"
        _write_bytes(source_map_path, _canonical_bytes(source_map(binding_reference, generated)))
        facts.extend([
            _retain(output_root, "legacy-boundary-patch", axp_path, "application/vnd.ksoloti.axp+xml", current_stage),
            _retain(output_root, "source-map", source_map_path, "application/vnd.schuss.source-map+json", current_stage),
            _retain(output_root, "generated-cpp", generated_path, "text/x-c++src", current_stage),
        ])
        stages[current_stage] = "success"

        current_stage = "target-compile-link"
        if failure_stage == current_stage:
            raise Task009BackendError(
                "TASK009_INJECTED_ARM_FAILURE", current_stage,
                "blend.cpp", "injected exact-slice ARM compile/link failure",
            )
        object_path, elf_path, map_path, resources, arm_commands = _arm_build(
            config, output_root, source_root, generated_path,
        )
        commands.extend(arm_commands)
        facts.extend([
            _retain(output_root, "arm-object", object_path, "application/x-elf-object", current_stage),
            _retain(output_root, "target-executable", elf_path, "application/x-elf", current_stage),
            _retain(output_root, "link-map", map_path, "text/plain", current_stage),
        ])
        stages[current_stage] = "success"

        ordered = tuple(sorted(facts, key=lambda item: ARTIFACT_ORDER.index(item.kind)))
        _reject_path_leaks(output_root, ordered)
        return ExecutionOutcome(
            "success", ordered, tuple(stages.items()), (), bridge_result,
            tuple(commands), resources, None,
        )
    except Task009BackendError as error:
        stages[current_stage] = "failed"
        terminal = False
        for stage in PROBE_STAGES:
            if stage == current_stage:
                terminal = True
            elif terminal:
                stages[stage] = "not-run"
        return ExecutionOutcome(
            "failed", tuple(facts), tuple(stages.items()),
            (error.as_probe_diagnostic(),), bridge_result, tuple(commands),
            resources, error,
        )


def run_backend_handler(
    invocation: Mapping[str, Any],
    invocation_schema: Mapping[str, Any],
    build_request_schema: Mapping[str, Any],
    expected_binding_reference: Mapping[str, Any],
    expected_build_request: Mapping[str, Any],
    config: ExecutionConfig,
    output_root: Path,
    failure_stage: str | None = None,
) -> ExecutionOutcome:
    """Run the exact production slice behind the unchanged Task 008 seam.

    Validation deliberately happens before :func:`execute_exact_slice`, whose
    first mutation is creation of the caller-supplied fresh output root.
    """

    validate_invocation_input(
        invocation,
        invocation_schema,
        build_request_schema,
        expected_binding_reference,
        expected_build_request,
    )
    return execute_exact_slice(
        expected_binding_reference,
        config,
        output_root,
        failure_stage=failure_stage,
    )


def _reject_path_leaks(output_root: Path, facts: Iterable[ArtifactFact]) -> None:
    forbidden = (
        str(output_root).encode(), b"/Users/", b"/private/", b"/tmp/",
        b"file://", b"Generated:",
    )
    for fact in facts:
        payload = fact.retained_path.read_bytes()
        if any(fragment in payload for fragment in forbidden):
            raise Task009BackendError(
                "TASK009_ARTIFACT_PATH_OR_TIME_LEAK", fact.producer_stage,
                fact.kind, "retained artifact contains a forbidden local or time-dependent identity",
            )


def compare_deterministic_outcomes(first: ExecutionOutcome, second: ExecutionOutcome) -> dict[str, Any]:
    first_hashes = {item.kind: [item.byte_sha256, item.byte_length] for item in first.artifacts}
    second_hashes = {item.kind: [item.byte_sha256, item.byte_length] for item in second.artifacts}
    if first.status != "success" or second.status != "success" or first_hashes != second_hashes:
        raise Task009BackendError(
            "TASK009_FRESH_ROOT_NONDETERMINISM", "target-compile-link",
            GRAPH_ID, "fresh-root artifact identities differ",
        )
    return {
        "schema_version": "task009-fresh-root-equality-v0",
        "status": "passed",
        "artifacts": dict(sorted(first_hashes.items())),
        "command_vectors_equal": first.command_vectors == second.command_vectors,
        "bridge_results_equal": first.bridge_result == second.bridge_result,
        "resource_facts_equal": first.resource_facts == second.resource_facts,
    }


def artifact_reference(fact: ArtifactFact, artifact_id: str, content_hash: str) -> dict[str, Any]:
    del fact
    return {"artifact_id": artifact_id, "revision": 1, "content_hash": content_hash}
