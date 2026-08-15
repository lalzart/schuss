#!/usr/bin/env python3
"""Capture the offline Task 009 prerequisite environment deterministically."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
INVENTORY_TOOLS = ROOT / "tools/inventory"
if str(INVENTORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(INVENTORY_TOOLS))

import export_resolved_inventory as resolved_export


PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
PATCHER_TREE = "75b75dba0c3734a8a53464ac93cdc20ec7203bb6"
EXPECTED_FIRMWARE_BIN = "fd61a6a109a234d1c72e445a0542ab59c407a6896b9aafe2bfcbcadaf775e258"
SMOKE_CLASS = "org.schuss.legacy.ksoloti.ExplicitCompileEnvironmentSmoke"
ARM_COMPONENTS = ("gcc", "g++", "as", "ld", "objcopy", "objdump", "size")
SOURCE_PREFIXES = ("CMSIS/", "chibios/", "firmware/")


class CaptureError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def run(command: Iterable[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).decode("utf-8", errors="replace")
        raise CaptureError(f"command failed ({result.returncode}): {list(command)[:3]}\n{detail[-4000:]}")
    return result


def version_line(executable: Path) -> str:
    for flag in ("--version", "-version"):
        result = subprocess.run(
            (str(executable), flag),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        text = (result.stdout or result.stderr).decode("utf-8", errors="replace").splitlines()
        if result.returncode == 0 and text:
            return text[0]
    raise CaptureError(f"no version output from {executable.name}")


def manifest_members(root: Path) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            payload = os.readlink(path).encode("utf-8")
            kind = "symlink"
        elif path.is_file():
            payload = path.read_bytes()
            kind = "file"
        else:
            continue
        members.append({
            "byte_length": len(payload),
            "byte_sha256": sha256_bytes(payload),
            "kind": kind,
            "mode": f"{mode:04o}",
            "path": relative,
        })
    return members


def member_fingerprint(members: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical_bytes({"members": members}))


def archive_source(checkout: Path, destination: Path) -> tuple[Path, list[dict[str, Any]]]:
    archive = destination.parent / f"{destination.name}.tar"
    destination.mkdir(parents=True)
    run(("git", "-C", str(checkout), "archive", "--format=tar", f"--output={archive}", PATCHER_COMMIT))
    run(("tar", "-xf", str(archive), "-C", str(destination)))
    return archive, manifest_members(destination)


def build_java(checkout: Path, java_home: Path, ant: Path, root: Path) -> tuple[Path, list[Path], list[dict[str, Any]]]:
    source = resolved_export.LockedSource(
        "patcher",
        "https://github.com/lalzart/ksoloti.git",
        PATCHER_COMMIT,
        checkout,
        resolved_export.git_status(checkout),
    )
    runtime = root / "runtime"
    classes, jars = resolved_export.build_patcher(source, runtime, java_home, str(ant))
    members: list[dict[str, Any]] = []
    for path in sorted(classes.rglob("*.class"), key=lambda item: item.relative_to(classes).as_posix()):
        members.append({
            "byte_length": path.stat().st_size,
            "byte_sha256": sha256_file(path),
            "kind": "class",
            "path": f"build/classes/{path.relative_to(classes).as_posix()}",
        })
    for path in jars:
        members.append({
            "byte_length": path.stat().st_size,
            "byte_sha256": sha256_file(path),
            "kind": "jar",
            "path": path.relative_to(runtime).as_posix(),
        })
    return classes, jars, sorted(members, key=lambda item: (item["kind"], item["path"]))


def build_firmware(source_root: Path, toolchain_root: Path) -> tuple[Path, Path, Path, bytes]:
    firmware = source_root / "firmware"
    build_relative = Path("build/ksoloti/normal")
    build = firmware / build_relative
    for child in (".dep", "lst", "obj"):
        (build / child).mkdir(parents=True, exist_ok=True)
    environment = {
        "BUILDDIR": build_relative.as_posix(),
        "LC_ALL": "C",
        "PATH": f"{toolchain_root / 'bin'}:/usr/bin:/bin",
        "TZ": "UTC",
    }
    result = run(
        ("/usr/bin/make", "-j8", "BOARDDEF=BOARD_KSOLOTI_CORE"),
        cwd=firmware,
        env=environment,
    )
    raw_elf = build / "ksoloti.elf"
    firmware_bin = build / "ksoloti.bin"
    link_elf = build / "ksoloti-link.elf"
    objcopy = toolchain_root / "bin/arm-none-eabi-objcopy"
    run((str(objcopy), "--strip-debug", str(raw_elf), str(link_elf)))
    if sha256_file(firmware_bin) != EXPECTED_FIRMWARE_BIN:
        raise CaptureError("reproduced firmware bin does not match the authenticated installed bytes")
    return raw_elf, firmware_bin, link_elf, result.stdout


def symbol_manifest(objdump: Path, link_elf: Path) -> bytes:
    output = run((str(objdump), "-t", str(link_elf))).stdout.decode("utf-8", errors="strict")
    lines = []
    for line in output.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.endswith(":     file format elf32-littlearm") or stripped == "SYMBOL TABLE:":
            continue
        lines.append(stripped)
    return ("\n".join(sorted(lines)) + "\n").encode("utf-8")


def firmware_command_manifest(
    output: bytes,
    source_root: Path,
    toolchain_root: Path,
) -> dict[str, Any]:
    normalized = output.decode("utf-8", errors="strict")
    replacements = {
        str(source_root.resolve()): "source-capsule",
        str(toolchain_root.resolve()): "arm-toolchain",
    }
    for local, portable in sorted(replacements.items(), key=lambda item: -len(item[0])):
        normalized = normalized.replace(local, portable)
    lines = sorted(line.rstrip() for line in normalized.splitlines() if line.strip())
    return {
        "schema_version": "firmware-build-command-vectors-v0",
        "build_invocation": {
            "arguments": ["make", "-j8", "BOARDDEF=BOARD_KSOLOTI_CORE"],
            "environment": [
                "BUILDDIR=build/ksoloti/normal",
                "LC_ALL=C",
                "PATH=arm-toolchain/bin:/usr/bin:/bin",
                "TZ=UTC",
            ],
            "orchestrator": {
                "byte_sha256": sha256_file(Path("/usr/bin/make")),
                "portable_locator": f"sha256/{sha256_file(Path('/usr/bin/make'))}",
                "version": version_line(Path("/usr/bin/make")),
            },
            "working_directory": "source-capsule/firmware",
        },
        "normalized_command_lines": lines,
    }


def smoke(java_home: Path, classes: Path, jars: list[Path], bridge_root: Path, temporary: Path, locators: dict[str, str]) -> tuple[bytes, str]:
    bridge_classes = temporary / "bridge-classes"
    resolved_export.compile_bridge(bridge_root, bridge_classes, java_home, [classes, *jars])
    classpath = os.pathsep.join(str(path) for path in [bridge_classes, classes, *jars])
    arguments = [f"--{key}={value}" for key, value in sorted(locators.items())]
    command = (
        str(java_home / "bin/java"),
        "-Djava.awt.headless=true",
        "-Duser.language=en",
        "-Dfile.encoding=UTF-8",
        "-cp",
        classpath,
        SMOKE_CLASS,
        *arguments,
    )
    environment = {"LC_ALL": "C", "TZ": "UTC"}
    first = run(command, cwd=temporary, env=environment)
    second = run(command, cwd=temporary, env=environment)
    if first.stdout != second.stdout or first.stderr or second.stderr:
        raise CaptureError("explicit environment smoke output is not clean and byte-identical")
    smoke_class = bridge_classes / Path(*SMOKE_CLASS.split(".")).with_suffix(".class")
    return first.stdout, sha256_file(smoke_class)


def artifact(path: str, data: bytes) -> dict[str, Any]:
    digest = sha256_bytes(data)
    return {
        "byte_length": len(data),
        "byte_sha256": digest,
        "portable_locator": f"sha256/{digest}",
        "portable_path": path,
    }


def capture(arguments: argparse.Namespace) -> dict[str, Any]:
    checkout = arguments.patcher_checkout.resolve()
    java_home = arguments.java_home.resolve()
    toolchain_root = arguments.toolchain_root.resolve()
    output = arguments.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise CaptureError("output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)

    commit = run(("git", "-C", str(checkout), "rev-parse", f"{PATCHER_COMMIT}^{{commit}}")).stdout.decode().strip()
    tree = run(("git", "-C", str(checkout), "rev-parse", f"{PATCHER_COMMIT}^{{tree}}")).stdout.decode().strip()
    if commit != PATCHER_COMMIT or tree != PATCHER_TREE:
        raise CaptureError("locked patcher Git object identity changed")

    with tempfile.TemporaryDirectory(prefix="schuss-task009p-capture-") as temporary_name:
        temporary = Path(temporary_name)
        archive_a, source_a = archive_source(checkout, temporary / "source-a")
        archive_b, source_b = archive_source(checkout, temporary / "source-b")
        if source_a != source_b or sha256_file(archive_a) != sha256_file(archive_b):
            raise CaptureError("two pinned source capsules are not byte-identical")

        classes_a, jars_a, classpath_a = build_java(checkout, java_home, arguments.ant, temporary / "java-a")
        _, _, classpath_b = build_java(checkout, java_home, arguments.ant, temporary / "java-b")
        if classpath_a != classpath_b:
            raise CaptureError("two Java classpath closures are not byte-identical")

        raw_a, bin_a, link_a, command_output_a = build_firmware(temporary / "source-a", toolchain_root)
        raw_b, bin_b, link_b, command_output_b = build_firmware(temporary / "source-b", toolchain_root)
        if sha256_file(bin_a) != sha256_file(bin_b) or sha256_file(link_a) != sha256_file(link_b):
            raise CaptureError("two canonical firmware closures are not byte-identical")
        command_document_a = firmware_command_manifest(
            command_output_a,
            temporary / "source-a",
            toolchain_root,
        )
        command_document_b = firmware_command_manifest(
            command_output_b,
            temporary / "source-b",
            toolchain_root,
        )
        if command_document_a != command_document_b:
            lines_a = Counter(command_document_a["normalized_command_lines"])
            lines_b = Counter(command_document_b["normalized_command_lines"])
            detail = {
                "only_a": sorted((lines_a - lines_b).items())[:10],
                "only_b": sorted((lines_b - lines_a).items())[:10],
            }
            raise CaptureError(
                "two normalized firmware command manifests are not byte-identical: "
                + json.dumps(detail, sort_keys=True)
            )

        tools = []
        for name in ARM_COMPONENTS:
            executable = toolchain_root / f"bin/arm-none-eabi-{name}"
            tools.append({
                "byte_sha256": sha256_file(executable),
                "component": name.replace("+", "x"),
                "version": version_line(executable),
            })

        source_document = {"schema_version": "source-capsule-members-v0", "members": source_a}
        classpath_document = {"schema_version": "java-classpath-members-v0", "members": classpath_a}
        jre_document = {"schema_version": "java-runtime-members-v0", "members": manifest_members(java_home)}
        toolchain_document = {"schema_version": "arm-toolchain-members-v0", "members": manifest_members(toolchain_root)}
        firmware_inputs = [member for member in source_a if member["path"].startswith(SOURCE_PREFIXES)]
        firmware_input_document = {"schema_version": "firmware-source-input-members-v0", "members": firmware_inputs}
        symbols = symbol_manifest(toolchain_root / "bin/arm-none-eabi-objdump", link_a)

        documents = {
            "source-capsule-members.json": canonical_bytes(source_document),
            "java-classpath-members.json": canonical_bytes(classpath_document),
            "java-runtime-members.json": canonical_bytes(jre_document),
            "arm-toolchain-members.json": canonical_bytes(toolchain_document),
            "firmware-source-input-members.json": canonical_bytes(firmware_input_document),
            "firmware-build-commands.json": canonical_bytes(command_document_a),
            "firmware-symbols.txt": symbols,
        }
        for name, data in documents.items():
            (output / name).write_bytes(data)

        locators = {
            "compute-target": "ksoloti-core",
            "device": "disabled",
            "encoding": "UTF-8",
            "firmware-bin": f"sha256/{sha256_file(bin_a)}",
            "firmware-link-elf": f"sha256/{sha256_file(link_a)}",
            "flash": "disabled",
            "gui": "disabled",
            "java-classpath": f"sha256/{resolved_export.classpath_fingerprint(classes_a, jars_a, temporary / 'java-a/runtime')}",
            "locale": "C",
            "object-registry": f"sha256/{sha256_file(temporary / 'source-a/src/main/java/generatedobjects/Mixer.java')}",
            "preferences": "disabled",
            "source-capsule": f"sha256/{sha256_file(archive_a)}",
            "target-triple": "arm-none-eabi",
            "toolchain": f"sha256/{member_fingerprint(toolchain_document['members'])}",
            "upload": "disabled",
        }
        smoke_output, smoke_class_sha256 = smoke(
            java_home,
            classes_a,
            jars_a,
            ROOT / "legacy/ksoloti-bridge/src/main/java",
            temporary / "smoke",
            locators,
        )
        (output / "explicit-environment-smoke.json").write_bytes(smoke_output)
        documents["explicit-environment-smoke.json"] = smoke_output

        summary = {
            "schema_version": "task009-prerequisite-environment-capture-v0",
            "source": {
                "archive_sha256": sha256_file(archive_a),
                "commit": commit,
                "manifest_fingerprint_sha256": member_fingerprint(source_a),
                "member_count": len(source_a),
                "tree": tree,
            },
            "java": {
                "ant_sha256": sha256_file(arguments.ant.resolve()),
                "ant_version": version_line(arguments.ant.resolve()),
                "class_count": sum(member["kind"] == "class" for member in classpath_a),
                "classpath_fingerprint_sha256": resolved_export.classpath_fingerprint(classes_a, jars_a, temporary / "java-a/runtime"),
                "jar_count": sum(member["kind"] == "jar" for member in classpath_a),
                "java_sha256": sha256_file(java_home / "bin/java"),
                "javac_sha256": sha256_file(java_home / "bin/javac"),
                "runtime_version": resolved_export.java_version(java_home),
                "smoke_class_sha256": smoke_class_sha256,
            },
            "arm_toolchain": {
                "identity": "GNU Arm Embedded Toolchain 9-2020-q2-update",
                "manifest_fingerprint_sha256": member_fingerprint(toolchain_document["members"]),
                "member_count": len(toolchain_document["members"]),
                "target_triple": "arm-none-eabi",
                "tools": tools,
            },
            "firmware": {
                "bin_byte_length": bin_a.stat().st_size,
                "bin_sha256": sha256_file(bin_a),
                "input_manifest_fingerprint_sha256": member_fingerprint(firmware_inputs),
                "input_member_count": len(firmware_inputs),
                "installed_bundle_match": sha256_file(arguments.installed_firmware_bin.resolve()) == sha256_file(bin_a),
                "link_elf_byte_length": link_a.stat().st_size,
                "link_elf_sha256": sha256_file(link_a),
                "raw_elf_status": "excluded-debug-path-dependent",
                "symbol_count": len(symbols.splitlines()),
                "symbol_manifest_sha256": sha256_bytes(symbols),
            },
            "artifacts": {
                name: artifact(f"evidence/task-009-prerequisite-v0/{name}", data)
                for name, data in sorted(documents.items())
            },
            "limitations": [
                "No Schuss graph was lowered and no patch source was generated.",
                "No generated patch was compiled or linked.",
                "No device, firmware installation, real-time, or audible procedure ran.",
                "Raw firmware ELF files contain temporary DWARF paths and are excluded from canonical identity.",
            ],
        }
        write_json(output / "environment-capture-summary.json", summary)
        return summary


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--patcher-checkout", required=True, type=Path)
    result.add_argument("--java-home", required=True, type=Path)
    result.add_argument("--ant", required=True, type=Path)
    result.add_argument("--toolchain-root", required=True, type=Path)
    result.add_argument("--installed-firmware-bin", required=True, type=Path)
    result.add_argument("--output", required=True, type=Path)
    return result


def main() -> int:
    try:
        result = capture(parser().parse_args())
    except (CaptureError, OSError, ValueError) as exc:
        print(f"task009 prerequisite environment capture failed: {exc}", file=sys.stderr)
        return 1
    print(canonical_bytes({
        "firmware_bin_sha256": result["firmware"]["bin_sha256"],
        "java_classpath_sha256": result["java"]["classpath_fingerprint_sha256"],
        "ok": True,
        "source_archive_sha256": result["source"]["archive_sha256"],
    }).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
