#!/usr/bin/env python3
"""Repair and re-authenticate the local executable closure required by Task 009."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
INVENTORY_TOOLS = ROOT / "tools/inventory"
if str(INVENTORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(INVENTORY_TOOLS))

import export_resolved_inventory as resolved_export


PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
PATCHER_TREE = "75b75dba0c3734a8a53464ac93cdc20ec7203bb6"
FACTORY_COMMIT = "25d2615ed5233546d617017666a4ab1e60a8c506"
FACTORY_TREE = "f92b3d4103e600b161f26545b362ac260b5eb1b7"
EXPECTED_SOURCE_ARCHIVE = "2f2d6c9e985e5b8609c847a0b21ad7611e614e7dd2a0cb3c51d9b50a77a36f32"
EXPECTED_FIRMWARE_BIN = "fd61a6a109a234d1c72e445a0542ab59c407a6896b9aafe2bfcbcadaf775e258"
EXPECTED_LINK_ELF = "df65f2153eb999386cc1bc30b382cafeac63aea8495bf8cb4cdad1c01fca944b"
EXPECTED_CLASSPATH = "5ebd2f2b7f2aa6dc1d3d10a04edb5f2bbedd97cfb4372dab56dc22c778b17710"
EXPECTED_CLASS_COUNT = 896
ARM_TOOLS = ("gcc", "g++", "as", "ld", "objcopy", "objdump", "size")
PROBE_CLASS = "org.schuss.legacy.ksoloti.ExplicitLegacyIsolationProbe"
FORBIDDEN_PROBE_REFERENCES = (
    "HeadlessPatchCompiler",
    "MainFrame",
    "QCmdCompilePatch",
    "QCmdUpload",
    "SavePrefs",
    "LoadPreferences",
    "Usb",
)


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


def run(
    command: Iterable[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        [str(item) for item in command],
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_success and result.returncode != 0:
        detail = (result.stderr or result.stdout).decode("utf-8", errors="replace")
        raise CaptureError(f"command failed ({result.returncode}): {list(command)[:4]}\n{detail[-5000:]}")
    return result


def portable_member(path: Path, root: Path, prefix: str = "") -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    logical = f"{prefix}/{relative}" if prefix else relative
    payload = path.read_bytes()
    return {
        "byte_length": len(payload),
        "byte_sha256": sha256_bytes(payload),
        "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
        "path": logical,
    }


def member_fingerprint(members: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical_bytes({"members": members}))


def archive(checkout: Path, commit: str, tree: str, output: Path, extract: Path) -> str:
    observed_commit = run(("git", "-C", checkout, "rev-parse", f"{commit}^{{commit}}")).stdout.decode().strip()
    observed_tree = run(("git", "-C", checkout, "rev-parse", f"{commit}^{{tree}}")).stdout.decode().strip()
    if observed_commit != commit or observed_tree != tree:
        raise CaptureError("locked Git object identity changed")
    extract.mkdir()
    run(("git", "-C", checkout, "archive", "--format=tar", f"--output={output}", commit))
    run(("tar", "-xf", output, "-C", extract))
    return sha256_file(output)


def deterministic_tar(files: list[tuple[Path, str]], output: Path) -> None:
    with tarfile.open(output, "w", format=tarfile.USTAR_FORMAT) as archive_file:
        for source, logical in sorted(files, key=lambda item: item[1]):
            data = source.read_bytes()
            info = tarfile.TarInfo(logical)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive_file.addfile(info, io.BytesIO(data))


def retain(source: Path, store: Path, kind: str) -> dict[str, Any]:
    digest = sha256_file(source)
    destination = store / "sha256" / digest
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != digest:
            raise CaptureError(f"retained {kind} has corrupt existing content")
    else:
        shutil.copyfile(source, destination)
        destination.chmod(0o444)
    return {
        "byte_length": source.stat().st_size,
        "byte_sha256": digest,
        "kind": kind,
        "portable_locator": f"sha256/{digest}",
    }


def accepted_preservation() -> dict[str, Any]:
    paths: set[str] = set()
    for record_set_path in (
        "contracts/record-sets/task005-008-accepted-v0.json",
        "contracts/record-sets/task009-prospective-v0.json",
    ):
        document = json.loads((ROOT / record_set_path).read_text(encoding="utf-8"))
        paths.add(record_set_path)
        for section in ("record_members", "schema_members"):
            for member in document[section]:
                paths.add(member["portable_path"])
    paths.update(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "evidence/task-009-prerequisite-v0").iterdir()
        if path.is_file()
    )
    paths.add("evidence/task-009-v0/preflight-stop-report.json")
    members = []
    for logical in sorted(paths):
        path = ROOT / logical
        members.append({
            "byte_length": path.stat().st_size,
            "byte_sha256": sha256_file(path),
            "portable_path": logical,
        })
    return {
        "member_count": len(members),
        "members": members,
        "root_fingerprint_sha256": member_fingerprint(members),
        "schema_version": "task009-prerequisite-repair-preservation-v0",
    }


def ant_members(ant_home: Path) -> list[dict[str, Any]]:
    lib = ant_home / "lib"
    members = [portable_member(path, ant_home, "ant-home") for path in lib.rglob("*") if path.is_file()]
    return sorted(members, key=lambda item: item["path"])


def build_java(source: Path, java_home: Path, ant_home: Path, run_root: Path) -> dict[str, Any]:
    home = run_root / "home"
    temporary = run_root / "tmp"
    empty_lib = run_root / "empty-ant-lib"
    for directory in (home, temporary, empty_lib):
        directory.mkdir(parents=True)
    launcher = ant_home / "lib/ant-launcher.jar"
    properties = resolved_export.PATCHER_BUILD_PROPERTIES[PATCHER_COMMIT]
    command = [
        java_home / "bin/java",
        "-XX:-UsePerfData",
        "-Djava.awt.headless=true",
        "-Dfile.encoding=UTF-8",
        "-Duser.language=en",
        "-Duser.country=US",
        "-Duser.timezone=UTC",
        f"-Duser.home={home}",
        f"-Djava.io.tmpdir={temporary}",
        f"-Dant.home={ant_home}",
        "-cp", launcher,
        "org.apache.tools.ant.launch.Launcher",
        "-nouserlib",
        "-lib", empty_lib,
        "-q",
        "compile",
        *properties,
    ]
    environment = {
        "CLASSPATH": "",
        "HOME": str(home),
        "JAVA_HOME": str(java_home),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
    }
    result = run(command, cwd=source, env=environment)
    classes = source / "build/classes"
    jars = sorted(source.glob("lib/**/*.jar"), key=lambda path: path.relative_to(source).as_posix())
    class_members = [
        {
            "byte_length": path.stat().st_size,
            "byte_sha256": sha256_file(path),
            "path": f"build/classes/{path.relative_to(classes).as_posix()}",
        }
        for path in sorted(classes.rglob("*.class"), key=lambda path: path.relative_to(classes).as_posix())
    ]
    if len(class_members) != EXPECTED_CLASS_COUNT:
        raise CaptureError(f"expected {EXPECTED_CLASS_COUNT} compiled classes")
    fingerprint = resolved_export.classpath_fingerprint(classes, jars, source)
    if fingerprint != EXPECTED_CLASSPATH:
        raise CaptureError("compiled Java classpath fingerprint changed")
    class_tar = run_root / "patcher-classes.tar"
    deterministic_tar(
        [(path, f"build/classes/{path.relative_to(classes).as_posix()}") for path in classes.rglob("*.class")],
        class_tar,
    )
    normalized_command = []
    replacements = (
        (str(source.resolve()), "source-capsule"),
        (str(source), "source-capsule"),
        (str(java_home.resolve()), "java-runtime"),
        (str(java_home), "java-runtime"),
        (str(ant_home.resolve()), "ant-home"),
        (str(ant_home), "ant-home"),
        (str(run_root.resolve()), "capture-root"),
        (str(run_root), "capture-root"),
    )
    for item in command:
        value = str(item)
        for local, portable in replacements:
            value = value.replace(local, portable)
        normalized_command.append(value)
    return {
        "ant_stderr_empty": not result.stderr,
        "ant_stdout_sha256": sha256_bytes(result.stdout),
        "classes": classes,
        "class_members": class_members,
        "class_tar": class_tar,
        "classpath_fingerprint_sha256": fingerprint,
        "command": {
            "arguments": normalized_command,
            "environment": [
                "CLASSPATH=",
                "HOME=capture-root/home",
                "JAVA_HOME=java-runtime",
                "LANG=C",
                "LC_ALL=C",
                "PATH=system-tools/bin",
                "TZ=UTC",
            ],
            "exit_status": 0,
            "working_directory": "source-capsule",
        },
        "jars": jars,
    }


def compile_bridge(java: dict[str, Any], java_home: Path, run_root: Path) -> Path:
    output = run_root / "bridge-classes"
    output.mkdir(parents=True)
    sources = sorted((ROOT / "legacy/ksoloti-bridge/src/main/java").rglob("*.java"))
    classpath = os.pathsep.join(str(path) for path in [java["classes"], *java["jars"]])
    environment = {
        "HOME": str(run_root / "home"),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
    }
    run((
        java_home / "bin/javac", "-encoding", "UTF-8", "-source", "21", "-target", "21",
        "-g:none", "-cp", classpath, "-d", output, *sources,
    ), env=environment)
    return output


def files_under(*roots: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for root in roots for path in root.rglob("*") if path.is_file())


def run_probe(
    source: Path,
    factory: Path,
    java: dict[str, Any],
    bridge_classes: Path,
    java_home: Path,
    run_root: Path,
) -> dict[str, Any]:
    home = run_root / "probe-home"
    prefs_user = run_root / "probe-prefs-user"
    prefs_system = run_root / "probe-prefs-system"
    temporary = run_root / "probe-tmp"
    work = run_root / "probe-work"
    for directory in (home, prefs_user, prefs_system, temporary, work):
        directory.mkdir(parents=True)
    classpath = os.pathsep.join(str(path) for path in [bridge_classes, java["classes"], *java["jars"]])
    base = [
        java_home / "bin/java", "-XX:-UsePerfData", "-Djava.awt.headless=true",
        "-Dfile.encoding=UTF-8", "-Duser.language=en", "-Duser.country=US",
        "-Duser.timezone=UTC", f"-Duser.home={home}",
        f"-Djava.util.prefs.userRoot={prefs_user}", f"-Djava.util.prefs.systemRoot={prefs_system}",
        f"-Djava.io.tmpdir={temporary}", "-cp", classpath, PROBE_CLASS,
        f"--factory-root={factory}", f"--patcher-root={source}",
    ]
    environment = {"HOME": str(home), "LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"}
    first = run(base, cwd=work, env=environment)
    second = run(base, cwd=work, env=environment)
    if first.stdout != second.stdout or first.stderr or second.stderr:
        raise CaptureError("legacy isolation probe was not byte-identical and quiet")
    if files_under(home, prefs_user, prefs_system, work):
        raise CaptureError("legacy isolation probe wrote user, preference, or working files")
    missing_headless = [item for item in base if str(item) != "-Djava.awt.headless=true"]
    negative_headless = run(missing_headless, cwd=work, env=environment, expect_success=False)
    negative_extra = run((*base, "--gui=enabled"), cwd=work, env=environment, expect_success=False)
    if negative_headless.returncode == 0 or negative_extra.returncode == 0:
        raise CaptureError("legacy isolation negative control unexpectedly passed")
    probe_class = bridge_classes / Path(*PROBE_CLASS.split(".")).with_suffix(".class")
    javap = run((java_home / "bin/javap", "-c", "-p", probe_class)).stdout.decode("utf-8", errors="strict")
    found = [token for token in FORBIDDEN_PROBE_REFERENCES if token in javap]
    if found:
        raise CaptureError(f"probe bytecode directly references forbidden entrypoints: {found}")
    return {
        "bytecode_forbidden_reference_count": 0,
        "bytecode_sha256": sha256_file(probe_class),
        "negative_controls": {
            "extra_authority_argument_rejected": True,
            "headless_requirement_enforced": True,
        },
        "output": json.loads(first.stdout),
        "output_bytes": first.stdout,
        "output_sha256": sha256_bytes(first.stdout),
        "user_preference_work_files_written": 0,
    }


def normalize(value: str, replacements: list[tuple[str, str]]) -> str:
    for local, portable in sorted(replacements, key=lambda item: -len(item[0])):
        value = value.replace(local, portable)
    return value


def command_role(arguments: list[str]) -> str:
    tool = Path(arguments[0]).name
    if tool == "arm-none-eabi-objcopy":
        return "binary-or-strip"
    if tool == "arm-none-eabi-objdump":
        return "symbol-inspection"
    if tool == "arm-none-eabi-size":
        return "size-inspection"
    if "-c" in arguments:
        if any(item.endswith((".s", ".S")) for item in arguments):
            return "assembler-driver"
        return "compiler-driver"
    if tool in ("arm-none-eabi-gcc", "arm-none-eabi-g++", "arm-none-eabi-ld"):
        return "linker-driver"
    return "arm-tool"


def firmware_build(source: Path, toolchain: Path, run_root: Path) -> dict[str, Any]:
    build_relative = Path("build/ksoloti/normal")
    build = source / "firmware" / build_relative
    for child in (".dep", "lst", "obj"):
        (build / child).mkdir(parents=True, exist_ok=True)
    wrapper_bin = run_root / "arm-wrapper-bin"
    wrapper_bin.mkdir(parents=True)
    wrapper = run_root / "task009-arm-tool-wrapper.py"
    shutil.copyfile(ROOT / "tools/contracts/task009_arm_tool_wrapper.py", wrapper)
    wrapper.chmod(0o755)
    for name in ARM_TOOLS:
        (wrapper_bin / f"arm-none-eabi-{name}").symlink_to(wrapper)
    command_log = run_root / "arm-command-log.jsonl"
    temporary = run_root / "firmware-tmp"
    temporary.mkdir()
    environment = {
        "BUILDDIR": build_relative.as_posix(),
        "HOME": str(run_root / "firmware-home"),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": f"{wrapper_bin}:{toolchain / 'bin'}:/usr/bin:/bin",
        "SCHUSS_ARM_COMMAND_LOG": str(command_log),
        "SCHUSS_REAL_ARM_BIN": str(toolchain / "bin"),
        "TMPDIR": str(temporary),
        "TZ": "UTC",
    }
    Path(environment["HOME"]).mkdir()
    make_command = ("/usr/bin/make", "-j1", "BOARDDEF=BOARD_KSOLOTI_CORE", "USE_VERBOSE_COMPILE=yes")
    make_result = run(make_command, cwd=source / "firmware", env=environment)
    raw_elf = build / "ksoloti.elf"
    firmware_bin = build / "ksoloti.bin"
    link_elf = build / "ksoloti-link.elf"
    run((wrapper_bin / "arm-none-eabi-objcopy", "--strip-debug", raw_elf, link_elf), cwd=source / "firmware", env=environment)
    symbols_result = run((wrapper_bin / "arm-none-eabi-objdump", "-t", link_elf), cwd=source / "firmware", env=environment)
    if sha256_file(firmware_bin) != EXPECTED_FIRMWARE_BIN or sha256_file(link_elf) != EXPECTED_LINK_ELF:
        raise CaptureError("firmware product identity changed")
    replacements = [
        (str(source.resolve()), "source-capsule"),
        (str(source), "source-capsule"),
        (str(toolchain.resolve()), "arm-toolchain"),
        (str(toolchain), "arm-toolchain"),
        (str(wrapper_bin.resolve()), "capture-wrapper-bin"),
        (str(wrapper_bin), "capture-wrapper-bin"),
        (str(run_root.resolve()), "capture-root"),
        (str(run_root), "capture-root"),
    ]
    vectors = []
    for index, line in enumerate(command_log.read_text(encoding="utf-8").splitlines()):
        raw = json.loads(line)
        arguments = [normalize(item, replacements) for item in raw["arguments"]]
        vectors.append({
            "arguments": arguments,
            "exit_status": raw["exit_status"],
            "index": index,
            "role": command_role(arguments),
            "working_directory": normalize(raw["working_directory"], replacements),
        })
    if len(vectors) < 180 or any(item["exit_status"] != 0 for item in vectors):
        raise CaptureError("expanded ARM command capture is incomplete or contains failure")
    roles = {item["role"] for item in vectors}
    if not {"compiler-driver", "assembler-driver", "linker-driver", "binary-or-strip", "symbol-inspection"}.issubset(roles):
        raise CaptureError(f"expanded ARM command roles are incomplete: {sorted(roles)}")
    symbols = []
    for line in symbols_result.stdout.decode("utf-8", errors="strict").splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.endswith(":     file format elf32-littlearm") or stripped == "SYMBOL TABLE:":
            continue
        symbols.append(stripped)
    symbol_bytes = ("\n".join(sorted(symbols)) + "\n").encode("utf-8")
    manifest = {
        "build_invocation": {
            "arguments": ["system-tools/bin/make", *make_command[1:]],
            "environment": [
                "BUILDDIR=build/ksoloti/normal", "HOME=capture-root/firmware-home", "LANG=C", "LC_ALL=C",
                "PATH=capture-wrapper-bin:arm-toolchain/bin:system-tools/bin",
                "TMPDIR=capture-root/firmware-tmp", "TZ=UTC",
            ],
            "exit_status": make_result.returncode,
            "orchestrator": {
                "byte_sha256": sha256_file(Path("/usr/bin/make")),
                "portable_locator": f"sha256/{sha256_file(Path('/usr/bin/make'))}",
                "version": run(("/usr/bin/make", "--version")).stdout.decode().splitlines()[0],
            },
            "working_directory": "source-capsule/firmware",
        },
        "command_count": len(vectors),
        "commands": vectors,
        "schema_version": "firmware-expanded-command-vectors-v1",
    }
    return {
        "bin": firmware_bin,
        "command_manifest": manifest,
        "link_elf": link_elf,
        "symbol_bytes": symbol_bytes,
    }


def one_capture(
    label: str,
    root: Path,
    patcher_checkout: Path,
    factory_checkout: Path,
    java_home: Path,
    ant_home: Path,
    toolchain: Path,
) -> dict[str, Any]:
    root.mkdir(parents=True)
    patcher_archive = root / "patcher-source.tar"
    patcher_source = root / "patcher-source"
    factory_archive = root / "factory-source.tar"
    factory_source = root / "factory-source"
    patcher_archive_sha = archive(patcher_checkout, PATCHER_COMMIT, PATCHER_TREE, patcher_archive, patcher_source)
    factory_archive_sha = archive(factory_checkout, FACTORY_COMMIT, FACTORY_TREE, factory_archive, factory_source)
    if patcher_archive_sha != EXPECTED_SOURCE_ARCHIVE:
        raise CaptureError("pinned patcher source archive identity changed")
    java = build_java(patcher_source, java_home, ant_home, root / "java")
    bridge_classes = compile_bridge(java, java_home, root / "bridge")
    probe = run_probe(patcher_source, factory_source, java, bridge_classes, java_home, root / "probe")
    firmware = firmware_build(patcher_source, toolchain, root / "firmware")
    ant_tar = root / "ant-libraries.tar"
    deterministic_tar(
        [(path, f"ant-home/lib/{path.relative_to(ant_home / 'lib').as_posix()}")
         for path in (ant_home / "lib").rglob("*") if path.is_file()],
        ant_tar,
    )
    return {
        "ant_tar": ant_tar,
        "class_members": java["class_members"],
        "class_tar": java["class_tar"],
        "classpath_fingerprint_sha256": java["classpath_fingerprint_sha256"],
        "factory_archive": factory_archive,
        "factory_archive_sha256": factory_archive_sha,
        "firmware": firmware,
        "java_command": java["command"],
        "label": label,
        "patcher_archive": patcher_archive,
        "patcher_archive_sha256": patcher_archive_sha,
        "probe": probe,
    }


def compare(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    comparisons = {
        "ant_library_tar": sha256_file(first["ant_tar"]) == sha256_file(second["ant_tar"]),
        "class_members": first["class_members"] == second["class_members"],
        "compiled_class_tar": sha256_file(first["class_tar"]) == sha256_file(second["class_tar"]),
        "expanded_command_vectors": first["firmware"]["command_manifest"] == second["firmware"]["command_manifest"],
        "factory_source_archive": first["factory_archive_sha256"] == second["factory_archive_sha256"],
        "firmware_bin": sha256_file(first["firmware"]["bin"]) == sha256_file(second["firmware"]["bin"]),
        "firmware_symbols": first["firmware"]["symbol_bytes"] == second["firmware"]["symbol_bytes"],
        "java_build_vector": first["java_command"] == second["java_command"],
        "legacy_isolation_probe": first["probe"]["output_bytes"] == second["probe"]["output_bytes"],
        "patcher_source_archive": first["patcher_archive_sha256"] == second["patcher_archive_sha256"],
        "stripped_link_elf": sha256_file(first["firmware"]["link_elf"]) == sha256_file(second["firmware"]["link_elf"]),
    }
    if not all(comparisons.values()):
        raise CaptureError(f"two clean captures differ: {comparisons}")
    return {
        "capture_labels": [first["label"], second["label"]],
        "comparisons": comparisons,
        "schema_version": "task009-prerequisite-reproduction-equality-v0",
        "status": "passed",
    }


def reject_machine_paths(documents: dict[str, bytes]) -> None:
    forbidden = (
        b"/Users/", b"/private", b"/tmp/", b"/Applications/", b"/opt/homebrew/",
        b'\"/usr/', b'\"/bin/',
    )
    for name, payload in documents.items():
        matches = [item.decode() for item in forbidden if item in payload]
        if matches:
            raise CaptureError(f"canonical artifact {name} contains machine paths: {matches}")


def write_evidence_manifest(output: Path) -> dict[str, Any]:
    members = [
        {
            "byte_length": path.stat().st_size,
            "byte_sha256": sha256_file(path),
            "portable_path": f"evidence/task-009-prerequisite-repair-v1/{path.name}",
        }
        for path in sorted(output.iterdir(), key=lambda item: item.name)
        if path.is_file() and path.name != "repair-evidence-manifest.json"
    ]
    document = {
        "member_count": len(members),
        "members": members,
        "schema_version": "task009-prerequisite-repair-evidence-manifest-v0",
    }
    write_json(output / "repair-evidence-manifest.json", document)
    return document


def capture(arguments: argparse.Namespace) -> dict[str, Any]:
    output = arguments.output.resolve()
    store = arguments.content_store.resolve()
    if output.exists() and any(output.iterdir()):
        raise CaptureError("output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    before = accepted_preservation()
    write_json(output / "pre-repair-preservation.json", before)

    ant_closure_members = ant_members(arguments.ant_home.resolve())
    with tempfile.TemporaryDirectory(prefix="schuss-task009-prerequisite-repair-") as temporary_name:
        temporary = Path(temporary_name)
        first = one_capture(
            "clean-root-a", temporary / "capture-a", arguments.patcher_checkout.resolve(),
            arguments.factory_checkout.resolve(), arguments.java_home.resolve(), arguments.ant_home.resolve(),
            arguments.toolchain_root.resolve())
        second = one_capture(
            "clean-root-b", temporary / "capture-b", arguments.patcher_checkout.resolve(),
            arguments.factory_checkout.resolve(), arguments.java_home.resolve(), arguments.ant_home.resolve(),
            arguments.toolchain_root.resolve())
        equality = compare(first, second)

        retained = [
            retain(first["patcher_archive"], store, "pinned-patcher-source-archive"),
            retain(first["factory_archive"], store, "pinned-factory-source-archive"),
            retain(first["class_tar"], store, "compiled-java-class-tar"),
            retain(first["ant_tar"], store, "ant-library-closure-tar"),
            retain(first["firmware"]["link_elf"], store, "canonical-stripped-firmware-link-elf"),
            retain(first["firmware"]["bin"], store, "canonical-firmware-bin"),
        ]
        retained_document = {
            "content_address_rule": "content-store/sha256/<byte_sha256>",
            "products": sorted(retained, key=lambda item: item["kind"]),
            "schema_version": "task009-prerequisite-retained-products-v0",
        }
        class_document = {
            "class_count": len(first["class_members"]),
            "classpath_fingerprint_sha256": first["classpath_fingerprint_sha256"],
            "members": first["class_members"],
            "schema_version": "task009-retained-java-class-members-v0",
        }
        ant_document = {
            "ambient_classpath": "disabled",
            "ant_home_library_member_count": len(ant_closure_members),
            "ant_home_library_members": ant_closure_members,
            "ant_home_library_fingerprint_sha256": member_fingerprint(ant_closure_members),
            "java_build_command": first["java_command"],
            "launcher_class": "org.apache.tools.ant.launch.Launcher",
            "user_libraries": "disabled",
            "schema_version": "task009-java-ant-executable-closure-v0",
        }
        bridge_report = {
            "actual_generated_definition": first["probe"]["output"],
            "direct_bytecode_forbidden_references": 0,
            "negative_controls": first["probe"]["negative_controls"],
            "probe_class_byte_sha256": first["probe"]["bytecode_sha256"],
            "probe_output_sha256": first["probe"]["output_sha256"],
            "scope": "memory-only preferences plus generatedobjects.Mixer emission interception; no Schuss graph or patch compile",
            "schema_version": "task009-legacy-isolation-report-v0",
            "user_preference_work_files_written": 0,
        }
        stop_verdicts = {
            "restart_verdict": "ready-for-task009-preflight-restart",
            "schema_version": "task009-prerequisite-stop-code-verdicts-v0",
            "stop_codes": [
                {"code": "PREREQUISITE_EXPANDED_COMMAND_PROVENANCE_ABSENT", "status": "closed", "evidence": "firmware-expanded-command-vectors.json"},
                {"code": "PREREQUISITE_CANONICAL_LINK_ELF_ABSENT", "status": "closed", "evidence": "retained-products.json"},
                {"code": "PREREQUISITE_JAVA_CLASS_OUTPUT_ABSENT", "status": "closed", "evidence": "java-class-members.json and retained-products.json"},
                {"code": "PREREQUISITE_JAVA_BUILD_ORCHESTRATOR_CLOSURE_INCOMPLETE", "status": "closed", "evidence": "java-ant-executable-closure.json"},
                {"code": "PREREQUISITE_REAL_GENERATION_ISOLATION_UNPROVED", "status": "closed", "evidence": "legacy-isolation-report.json"},
            ],
        }
        summary = {
            "accepted_revision_1_bytes_preserved": True,
            "ant_library_member_count": len(ant_closure_members),
            "class_count": len(first["class_members"]),
            "classpath_fingerprint_sha256": first["classpath_fingerprint_sha256"],
            "command_count": first["firmware"]["command_manifest"]["command_count"],
            "firmware_bin_sha256": sha256_file(first["firmware"]["bin"]),
            "limitations": [
                "No Schuss graph was lowered and no legacy patch source or .axp was generated.",
                "No generated patch was compiled or linked.",
                "No device, upload, flash, firmware installation, real-time, or audible procedure ran.",
                "The isolation claim is bounded to the explicit probe bytecode and intercepted Mixer generation path.",
            ],
            "link_elf_sha256": sha256_file(first["firmware"]["link_elf"]),
            "reproduction_equality": "passed",
            "restart_verdict": stop_verdicts["restart_verdict"],
            "schema_version": "task009-prerequisite-closure-repair-capture-v0",
        }
        documents = {
            "closure-capture-summary.json": canonical_bytes(summary),
            "explicit-legacy-isolation-probe.json": first["probe"]["output_bytes"],
            "firmware-expanded-command-vectors.json": canonical_bytes(first["firmware"]["command_manifest"]),
            "firmware-symbols.txt": first["firmware"]["symbol_bytes"],
            "java-ant-executable-closure.json": canonical_bytes(ant_document),
            "java-class-members.json": canonical_bytes(class_document),
            "legacy-isolation-report.json": canonical_bytes(bridge_report),
            "reproduction-equality.json": canonical_bytes(equality),
            "retained-products.json": canonical_bytes(retained_document),
            "stop-code-verdicts.json": canonical_bytes(stop_verdicts),
        }
        reject_machine_paths(documents)
        for name, payload in documents.items():
            (output / name).write_bytes(payload)

    after = accepted_preservation()
    post = {
        "before_fingerprint_sha256": before["root_fingerprint_sha256"],
        "member_count": before["member_count"],
        "schema_version": "task009-prerequisite-repair-post-preservation-v0",
        "status": "passed" if before == after else "failed",
    }
    if before != after:
        raise CaptureError("accepted revision-1 or prerequisite-v0 bytes changed during repair")
    write_json(output / "post-repair-preservation.json", post)
    write_evidence_manifest(output)
    return summary


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--patcher-checkout", required=True, type=Path)
    result.add_argument("--factory-checkout", required=True, type=Path)
    result.add_argument("--java-home", required=True, type=Path)
    result.add_argument("--ant-home", required=True, type=Path)
    result.add_argument("--toolchain-root", required=True, type=Path)
    result.add_argument("--content-store", required=True, type=Path)
    result.add_argument("--output", required=True, type=Path)
    return result


def main() -> int:
    try:
        result = capture(parser().parse_args())
    except (CaptureError, KeyError, OSError, ValueError) as exception:
        print(f"task009 prerequisite repair capture failed: {exception}", file=sys.stderr)
        return 1
    print(canonical_bytes({
        "firmware_bin_sha256": result["firmware_bin_sha256"],
        "ok": True,
        "restart_verdict": result["restart_verdict"],
    }).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
