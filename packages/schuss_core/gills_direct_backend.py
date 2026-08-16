"""Exact Task 016 direct handler and authenticated local ARM build boundary."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .build_execution import (
    HandlerRegistration,
    HandlerRequest,
    descriptor_content_hash,
)
from .gills_direct_frontend import (
    DIRECT_BACKEND_ID,
    GRAPH_REFERENCE,
    REQUEST_ID,
    REQUEST_REVISION,
    lower_gills_direct,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REQUEST_REFERENCE = {
    "build_request_id": REQUEST_ID,
    "revision": REQUEST_REVISION,
    # Filled by the Task 016 semantic-record generator and checked by tests.
    "content_hash": "sha256:c621de0376352c18f453b499fbe480f82e9e953d1fe193b8a1f982145beceaba",
}
BACKEND_REFERENCE = {
    "backend_id": DIRECT_BACKEND_ID,
    "revision": 1,
    # Filled by the Task 016 semantic-record generator and checked by tests.
    "content_hash": "sha256:fa20b9c8b5037f46435ab23517609c1111e122189ed92d18a6a2ff7cfb91d37c",
}

PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
FACTORY_COMMIT = "25d2615ed5233546d617017666a4ab1e60a8c506"
CONTRIB_COMMIT = "2e994478c0ab15fb1daa3bb4b86c88e22952d99c"
FIRMWARE_LINK_ELF_SHA256 = "df65f2153eb999386cc1bc30b382cafeac63aea8495bf8cb4cdad1c01fca944b"
ORACLE_CPP_SHA256 = "7877897b3112dcbb7ee1239f3187f535d6113875cacbb49c76bd30a0321bcfd3"

RUNTIME_SOURCE_HASHES = {
    "firmware/Makefile.patch.mk": "ab99b15be913083220621a785077945e6b35fe56fc7c2691afe36569a8f29a70",
    "firmware/axoloti_math.h": "95ccbdbea15078a6ef207e87749bb8defaa4662b6eebddfb40944f350b549191",
    "firmware/axoloti_math.c": "ba4e3146eb3e6cf436ee836d1f5c82d9b5c13606e3ab0f273ff43432ef3626c1",
    "firmware/patch.h": "fe64781fac09b82d6f45eafbb60efcfe7b1af655af5dcccaac232e29c31dad2c",
    "firmware/xpatch.h": "85e4abc70123952e8f47217751f2b6f7299e7cb978b6c994acf7b383425379a0",
    "firmware/ramlink_ksoloti.ld": "08ead427e297a4d66ea2b8d830563e7a2d8c683ad399c0809477b584eb70b1eb",
}
OBJECT_SOURCE_HASHES = {
    "factory:objects/mix/xfade.axo": "8169f5ec39eabe8f76bf5025ab2c68df0bed531c0c8aeb8c51bba3307859e361",
    "factory:objects/lfo/square.axo": "d417bd0e455e28c6af9988732f6406b2d3e3c94eea9338f76ab61df926463051",
    "factory:objects/logic/counter.axo": "fb61bbfeb9504cee015b093888fb8c6da237d12b760a5e6ebdb9b160447bd9e1",
    "factory:objects/osc/sine.axo": "bf865e647b2eea2ebe1ef852038994f2dea8f1e8b8e60e1133e1d580a3402a4b",
    "factory:objects/filter/multimode svf m.axo": "e73239cd072b9dc63debd2ec95a32ec0bf79ae1be1754336a1d5928d4e8af057",
    "factory:objects/audio/out stereo.axo": "d8392b522b54be3bdfa5e671975a2a675ac494e9d1dc8bee2586dcd1eaecc7e3",
    "contrib:objects/drj/seq/stepseq_16_pitch.axo": "45336e472f1e15a295617b0f4fd1e31e83203acf9ae37a067125459f66022b0f",
}
TOOL_HASHES = {
    "arm-none-eabi-g++": "69fe197c81592ae356650437e315966cd592b1015ecbda53edddcde494dcc296",
    "arm-none-eabi-gcc": "475b81bfcec7787a411e3cb200150c1afb0ccd6d05ab0b1929bd933f2261328f",
    "arm-none-eabi-objcopy": "744e6a4c7b65059f0f4497a01304e7ad1d1edda1defc2af75f28a6574fb77d29",
    "arm-none-eabi-objdump": "d4d9369294ae583393fd9fdaa5ce039acf319c1e78623351f4864e04382b13c6",
    "arm-none-eabi-size": "377e2d38ba57ab5ee5a8e2b6933debeea5cda4249fd1ebc5355deb77c6d365b8",
}


class DirectBackendError(RuntimeError):
    def __init__(self, code: str, stage: str, subject: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.subject = subject


@dataclass(frozen=True)
class DirectExecutionConfig:
    patcher_root: Path
    factory_root: Path
    contrib_root: Path
    arm_bin: Path
    installed_firmware_elf: Path

    @classmethod
    def local_default(cls) -> "DirectExecutionConfig":
        return cls(
            Path("/Users/lanceship/Projects/ksoloti"),
            Path("/Users/lanceship/ksoloti/1.1.0/axoloti-factory"),
            Path("/Users/lanceship/ksoloti/1.1.0/axoloti-contrib"),
            Path("/Applications/Ksoloti Local.app/Contents/Resources/platform_mac_x64/bin"),
            Path("/Applications/Ksoloti Local.app/Contents/Resources/firmware/build/ksoloti.elf"),
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _git_head(path: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise DirectBackendError(
            "DIRECT_SOURCE_IDENTITY_UNAVAILABLE", "execution-preflight", path.name,
            "source checkout identity is unavailable",
        )
    return completed.stdout.decode("ascii").strip()


def _require_hash(path: Path, expected: str, subject: str) -> None:
    if not path.is_file() or _sha256_file(path) != expected:
        raise DirectBackendError(
            "DIRECT_AUTHENTICATED_BYTE_MISMATCH", "execution-preflight", subject,
            "authenticated source or tool bytes differ",
        )


def verify_execution_config(config: DirectExecutionConfig) -> dict[str, Any]:
    config = DirectExecutionConfig(*map(Path, (
        config.patcher_root, config.factory_root, config.contrib_root,
        config.arm_bin, config.installed_firmware_elf,
    )))
    if _git_head(config.patcher_root) != PATCHER_COMMIT:
        raise DirectBackendError("DIRECT_PATCHER_COMMIT_MISMATCH", "execution-preflight", "patcher", "pinned patcher commit differs")
    if _git_head(config.factory_root) != FACTORY_COMMIT:
        raise DirectBackendError("DIRECT_FACTORY_COMMIT_MISMATCH", "execution-preflight", "factory", "pinned factory commit differs")
    if _git_head(config.contrib_root) != CONTRIB_COMMIT:
        raise DirectBackendError("DIRECT_CONTRIB_COMMIT_MISMATCH", "execution-preflight", "contrib", "pinned contrib commit differs")
    source_status = subprocess.run(
        ["git", "-C", str(config.patcher_root), "status", "--porcelain", "--", "firmware", "CMSIS", "chibios"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if source_status.returncode or source_status.stdout:
        raise DirectBackendError(
            "DIRECT_RUNTIME_SOURCE_DIRTY", "execution-preflight", "runtime-source",
            "authenticated runtime build inputs contain local changes",
        )
    for relative, digest in RUNTIME_SOURCE_HASHES.items():
        _require_hash(config.patcher_root / relative, digest, relative)
    for locator, digest in OBJECT_SOURCE_HASHES.items():
        source, relative = locator.split(":", 1)
        root = config.factory_root if source == "factory" else config.contrib_root
        _require_hash(root / relative, digest, locator)
    for name, digest in TOOL_HASHES.items():
        _require_hash(config.arm_bin / name, digest, name)
    _require_hash(
        REPOSITORY_ROOT / "evidence/task-011c-v1/artifacts/sha256" / ORACLE_CPP_SHA256,
        ORACLE_CPP_SHA256,
        "task011c-generated-cpp-oracle",
    )
    if not config.installed_firmware_elf.is_file():
        raise DirectBackendError(
            "DIRECT_RUNTIME_ELF_UNAVAILABLE", "execution-preflight", "runtime-elf",
            "installed authenticated runtime ELF is unavailable",
        )
    return {
        "schema_version": "task016-direct-preflight-v1",
        "status": "passed",
        "patcher_commit": PATCHER_COMMIT,
        "factory_commit": FACTORY_COMMIT,
        "contrib_commit": CONTRIB_COMMIT,
        "runtime_source_hashes": copy.deepcopy(RUNTIME_SOURCE_HASHES),
        "object_source_hashes": copy.deepcopy(OBJECT_SOURCE_HASHES),
        "tool_hashes": copy.deepcopy(TOOL_HASHES),
        "task011c_oracle_cpp_sha256": ORACLE_CPP_SHA256,
        "java_used": False,
        "legacy_boundary_patch_used": False,
    }


def descriptor() -> dict[str, Any]:
    value = {
        "schema_version": "build-handler-descriptor-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_handler_id": "schuss-build-handler-000002",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "backend_reference": copy.deepcopy(BACKEND_REFERENCE),
        "supported_build_request_reference": copy.deepcopy(REQUEST_REFERENCE),
        "execution_policy": "exact-request-only",
        "adapter_kind": "direct",
        "mid_handler_cancellation": False,
    }
    value["content_hash"] = descriptor_content_hash(value)
    return value


def _exact_record(
    values: Iterable[Mapping[str, Any]], reference: Mapping[str, Any], id_field: str
) -> dict[str, Any]:
    matches = [
        copy.deepcopy(dict(value))
        for value in values
        if all(value.get(key) == item for key, item in reference.items())
    ]
    if len(matches) != 1:
        raise DirectBackendError(
            "DIRECT_EXACT_RECORD_UNRESOLVED", "backend-lowering",
            str(reference.get(id_field, id_field)),
            f"expected one exact {id_field} record, found {len(matches)}",
        )
    return matches[0]


def _run(
    arguments: list[str], cwd: Path, environment: Mapping[str, str],
    code: str, subject: str, timeout: int = 300,
) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            arguments, cwd=cwd, env=dict(environment), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DirectBackendError(code, "target-compile-link", subject, "authenticated ARM command could not complete") from exc
    if completed.returncode:
        raise DirectBackendError(
            code, "target-compile-link", subject,
            "authenticated ARM command failed with exit status " + str(completed.returncode),
        )
    return completed


def _portable_command(component: str, arguments: list[str], cwd: str) -> dict[str, Any]:
    return {
        "component": component,
        "arguments": arguments,
        "working_directory": cwd,
        "exit_status": 0,
    }


def _artifact(
    kind: str, payload: bytes, media_type: str, producer_stage: str,
    output_root: Path,
) -> dict[str, Any]:
    digest = hashlib.sha256(payload).hexdigest()
    destination = output_root / "artifacts/sha256" / digest
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() != payload:
        raise DirectBackendError(
            "DIRECT_ARTIFACT_COLLISION", producer_stage, kind,
            "content-addressed artifact collision",
        )
    destination.write_bytes(payload)
    return {
        "artifact_kind": kind,
        "media_type": media_type,
        "producer_stage": producer_stage,
        "byte_sha256": digest,
        "byte_length": len(payload),
        "portable_locator": "sha256/" + digest,
    }


def _compile_arm(
    cpp: bytes, output_root: Path, config: DirectExecutionConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    build = output_root / "build"
    runtime_build = output_root / "runtime/build"
    link = output_root / "link"
    build.mkdir(parents=True)
    runtime_build.mkdir(parents=True)
    link.mkdir(parents=True)
    source = build / "gills-direct.cpp"
    source.write_bytes(cpp)
    shutil.copyfile(config.patcher_root / "firmware/xpatch.h", build / "xpatch.h")
    shutil.copyfile(config.patcher_root / "firmware/ramlink_ksoloti.ld", link / "ramlink_ksoloti.ld")
    objcopy = config.arm_bin / "arm-none-eabi-objcopy"
    gcc = config.arm_bin / "arm-none-eabi-gcc"
    objdump = config.arm_bin / "arm-none-eabi-objdump"
    size = config.arm_bin / "arm-none-eabi-size"
    base_environment = {
        "LANG": "C", "LC_ALL": "C", "TZ": "UTC", "SOURCE_DATE_EPOCH": "0",
        "PATH": os.pathsep.join([str(config.arm_bin), "/usr/bin", "/bin"]),
        "axoloti_home": str(config.patcher_root),
        "axoloti_firmware": str(config.patcher_root / "firmware"),
        "axoloti_link_firmware": str(output_root / "runtime"),
        "axoloti_libraries": str(output_root),
    }
    commands: list[dict[str, Any]] = []
    _run(
        [str(objcopy), "--strip-debug", str(config.installed_firmware_elf), str(runtime_build / "ksoloti.elf")],
        output_root, base_environment, "DIRECT_RUNTIME_ELF_NORMALIZATION_FAILED", "runtime-elf",
    )
    if _sha256_file(runtime_build / "ksoloti.elf") != FIRMWARE_LINK_ELF_SHA256:
        raise DirectBackendError(
            "DIRECT_RUNTIME_ELF_MISMATCH", "execution-preflight", "runtime-elf",
            "normalized installed runtime ELF differs from the authenticated link boundary",
        )
    commands.append(_portable_command(
        "arm-none-eabi-objcopy", ["arm-none-eabi-objcopy", "--strip-debug", "installed-runtime/ksoloti.elf", "runtime/build/ksoloti.elf"], "."
    ))
    make_arguments = [
        "/usr/bin/make", "-f", "Makefile.patch.mk", "BOARDDEF=BOARD_KSOLOTI_CORE",
        "FWOPTIONDEF=FW_NORMAL", "BUILDFILENAME=gills-direct", str(build / "gills-direct.elf"),
    ]
    _run(
        make_arguments, config.patcher_root / "firmware", base_environment,
        "DIRECT_ARM_COMPILE_FAILED", "generated-cpp",
    )
    commands.append(_portable_command(
        "make", ["make", "-f", "Makefile.patch.mk", "BOARDDEF=BOARD_KSOLOTI_CORE", "FWOPTIONDEF=FW_NORMAL", "BUILDFILENAME=gills-direct", "build/gills-direct.elf"], "authenticated-patcher/firmware"
    ))
    raw_object = build / "gills-direct.o"
    stripped_object = build / "gills-direct-stripped.o"
    if not raw_object.is_file():
        raise DirectBackendError("DIRECT_ARM_OBJECT_MISSING", "target-compile-link", "arm-object", "ARM compilation emitted no object")
    _run(
        [str(objcopy), "--strip-debug", "build/gills-direct.o", "build/gills-direct-stripped.o"],
        output_root, base_environment, "DIRECT_ARM_STRIP_FAILED", "arm-object",
    )
    commands.append(_portable_command(
        "arm-none-eabi-objcopy", ["arm-none-eabi-objcopy", "--strip-debug", "build/gills-direct.o", "build/gills-direct-stripped.o"], "."
    ))
    relink_arguments = [
        str(gcc), "-Tramlink_ksoloti.ld", "-Bsymbolic", "-Wl,--gc-sections",
        "-Wl,--print-memory-usage", "-fno-common", "-mcpu=cortex-m4",
        "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16", "-mno-thumb-interwork",
        "-mthumb", "-mtune=cortex-m4", "-nostartfiles",
        "../build/gills-direct-stripped.o", "-lm",
        "-Wl,-Map=../build/gills-direct.map,--cref,--build-id=none,--just-symbols=../runtime/build/ksoloti.elf",
        "-o", "../build/gills-direct-deterministic.elf",
    ]
    _run(relink_arguments, link, base_environment, "DIRECT_ARM_LINK_FAILED", "target-executable")
    commands.append(_portable_command("arm-none-eabi-gcc", ["arm-none-eabi-gcc", *relink_arguments[1:]], "link"))
    _run(
        [str(objcopy), "--strip-debug", "build/gills-direct-deterministic.elf", "build/gills-direct-stripped.elf"],
        output_root, base_environment, "DIRECT_ARM_STRIP_FAILED", "target-executable",
    )
    commands.append(_portable_command(
        "arm-none-eabi-objcopy", ["arm-none-eabi-objcopy", "--strip-debug", "build/gills-direct-deterministic.elf", "build/gills-direct-stripped.elf"], "."
    ))
    header = _run(
        [str(objdump), "-f", "build/gills-direct-stripped.elf"], output_root,
        base_environment, "DIRECT_ARM_INSPECTION_FAILED", "target-executable",
    )
    sizes = _run(
        [str(size), "-A", "-x", "build/gills-direct-stripped.elf"], output_root,
        base_environment, "DIRECT_ARM_INSPECTION_FAILED", "target-executable",
    )
    commands.extend([
        _portable_command("arm-none-eabi-objdump", ["arm-none-eabi-objdump", "-f", "build/gills-direct-stripped.elf"], "."),
        _portable_command("arm-none-eabi-size", ["arm-none-eabi-size", "-A", "-x", "build/gills-direct-stripped.elf"], "."),
    ])
    header_text = header.stdout.decode("utf-8")
    if "file format elf32-littlearm" not in header_text or "architecture: arm" not in header_text:
        raise DirectBackendError("DIRECT_TARGET_ABI_MISMATCH", "target-compile-link", "target-executable", "linked output is not little-endian ARM")
    artifact_inputs = [
        ("arm-object", stripped_object, "application/x-elf-object"),
        ("target-executable", build / "gills-direct-stripped.elf", "application/x-elf"),
        ("link-map", build / "gills-direct.map", "text/plain"),
    ]
    artifacts = [
        _artifact(kind, path.read_bytes(), media, "target-compile-link", output_root)
        for kind, path, media in artifact_inputs
    ]
    resource = {
        "schema_version": "task016-static-resource-facts-v1",
        "method": "compiler-link-map",
        "evidence_level": 5,
        "elf_header": [line.strip() for line in header_text.splitlines() if line.strip()],
        "size_output": [line.rstrip() for line in sizes.stdout.decode("utf-8").splitlines() if line.strip()],
        "limitations": [
            "Static compile and link observations are not connected-device measurements.",
            "No real-time timing, stability, or audible behavior was measured.",
        ],
    }
    return artifacts, commands, resource


def run_handler(
    request: HandlerRequest,
    config: DirectExecutionConfig | None = None,
) -> dict[str, Any]:
    config = config or DirectExecutionConfig.local_default()
    preflight = verify_execution_config(config)
    records = request.compilation_context.records()
    request_record = _exact_record(records["request"], REQUEST_REFERENCE, "build_request_id")
    if request_record["backend_reference"] != BACKEND_REFERENCE:
        raise DirectBackendError("DIRECT_BACKEND_REFERENCE_MISMATCH", "backend-lowering", DIRECT_BACKEND_ID, "build request does not name the exact direct backend")
    graph = _exact_record(records["graphs"], GRAPH_REFERENCE, "graph_id")
    contracts = list(records["contracts"])
    operation_specs = list(records.get("direct_operation_specs", []))
    result = lower_gills_direct(request.plan, graph, contracts, operation_specs)
    output_root = request.output_root
    if output_root.exists():
        raise DirectBackendError("DIRECT_OUTPUT_ROOT_NOT_FRESH", "backend-lowering", "output-root", "handler output root must not exist")
    output_root.mkdir(parents=True)
    resolution = next(
        item["payload"] for item in request.plan["artifacts"]
        if item["descriptor"]["artifact_kind"] == "resolution-plan"
    )
    resolution_bytes = _canonical_bytes(resolution)
    module_bytes = _canonical_bytes(result["module"])
    source_map_bytes = _canonical_bytes(result["source_map"])
    goldens_bytes = _canonical_bytes(result["semantic_goldens"])
    cpp_bytes = result["generated_cpp"]["text"].encode("utf-8")
    artifacts = [
        _artifact("resolution-plan", resolution_bytes, "application/vnd.schuss.resolution-plan+json", "implementation-resolution", output_root),
        _artifact("normalized-dsp", module_bytes, "application/vnd.schuss.normalized-dsp+json", "backend-lowering", output_root),
        _artifact("source-map", source_map_bytes, "application/vnd.schuss.source-map+json", "artifact-generation", output_root),
        _artifact("generated-cpp", cpp_bytes, "text/x-c++src", "artifact-generation", output_root),
        _artifact("semantic-goldens", goldens_bytes, "application/vnd.schuss.semantic-goldens+json", "artifact-generation", output_root),
    ]
    arm_artifacts, commands, resource = _compile_arm(cpp_bytes, output_root, config)
    artifacts.extend(arm_artifacts)
    resource_bytes = _canonical_bytes(resource)
    artifacts.append(_artifact(
        "resource-facts", resource_bytes,
        "application/vnd.schuss.resource-facts+json", "target-compile-link", output_root,
    ))
    command_bytes = _canonical_bytes(commands)
    artifacts.append(_artifact(
        "command-vector", command_bytes,
        "application/vnd.schuss.command-vector+json", "target-compile-link", output_root,
    ))
    preflight_bytes = _canonical_bytes(preflight)
    artifacts.append(_artifact(
        "authenticated-preflight", preflight_bytes,
        "application/vnd.schuss.authenticated-preflight+json", "backend-lowering", output_root,
    ))
    return {
        "status": "success",
        "stage_outcomes": [
            {"stage": "backend-lowering", "status": "success"},
            {"stage": "artifact-generation", "status": "success"},
            {"stage": "target-compile-link", "status": "success"},
        ],
        "artifacts": artifacts,
        "evidence_level": 5,
        "command_vectors": commands,
        "resource_facts": resource,
        "preflight": preflight,
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "ambient_discovery_used": False,
    }


def registration(config: DirectExecutionConfig | None = None) -> HandlerRegistration:
    return HandlerRegistration(descriptor(), lambda request: run_handler(request, config))
