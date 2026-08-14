#!/usr/bin/env python3
"""Build the pinned legacy model and export Phase 3 in two fresh JVMs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from validate_resolved_inventory import (
    GRAPH_SCHEMA,
    InventoryValidationError,
    ISSUE_SCHEMA,
    OBJECT_SCHEMA,
    _reject_generated_uuid_leaks,
    _validate_graph_indexes,
    _validate_issue_indexes,
    _validate_object_indexes,
    _issue_sort_key,
    build_summary,
    load_json,
    load_jsonl,
    render_summary_markdown,
    sha256_file,
    validate_schema,
    validate_inventory,
)


SCHEMA_VERSION = "legacy-resolved-catalog-v0"
BRIDGE_MAIN = "org.schuss.legacy.ksoloti.ResolvedInventoryExporter"
GENERATOR_CLASS = "generatedobjects.GeneratedObjects"
LEGACY_SOURCE_ORDER = (
    "axoloti-factory",
    "axoloti-contrib",
    "ksoloti-objects",
    "ksoloti-contrib",
    "patcher",
)
OBJECT_SOURCE_IDS = LEGACY_SOURCE_ORDER[:-1]
ARTIFACTS = (
    Path("resolved/objects.jsonl"),
    Path("resolved/graphs.jsonl"),
    Path("resolved/issues.jsonl"),
)
PATCHER_BUILD_PROPERTIES = {
    "08d3e6e1e2b61230308c20a15ded58ffdaf4656c": (
        "-Dbuild.version=1.1.0-8-g08d3e6e1e",
        "-Dshort.version=1.1.0",
        "-Dbuild.time=1970-01-01T00:00:00Z",
        "-Dbuild.runtime=false",
        "-Dbuild.bundle=false",
    )
}
PINNED_ELIGIBLE_COUNTS = {"axo": 3139, "axs": 162, "axp": 995}
PINNED_OMISSION_COUNTS = {"axo": 143, "axs": 2, "axp": 1}
PINNED_ALL_AXO_COUNT = 3160
PINNED_GENERATOR_JAVA_COUNT = 38
PINNED_FILE_OBJECT_RECORDS = 3551
PINNED_AXO_DEFINITION_RECORDS = 3417
PINNED_CATALOG_SUBPATCH_RECORDS = 134
PINNED_RETAINED_OBJECT_RECORDS = 3548
PINNED_GENERATOR_EMISSIONS = 629
PINNED_PROVIDER_ONLY_RECORDS = 51


class ExportError(RuntimeError):
    """The pinned resolved export could not be proved safe and reproducible."""


@dataclass(frozen=True)
class LockedSource:
    source_id: str
    url: str
    commit: str
    path: Path
    status: bytes


def _command_text(command: Sequence[str]) -> str:
    return " ".join(command[:3]) + (" ..." if len(command) > 3 else "")


def run_checked(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        if len(detail) > 4000:
            detail = detail[-4000:]
        raise ExportError(
            f"command failed ({result.returncode}): {_command_text(command)}"
            + (f"\n{detail}" if detail else "")
        )
    return result


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"
    return env


def git_text(root: Path, *arguments: str) -> str:
    return run_checked(
        ("git", "-C", str(root), *arguments), env=_git_env()
    ).stdout.strip()


def git_status(root: Path) -> bytes:
    result = subprocess.run(
        (
            "git", "-C", str(root), "status", "--porcelain=v1", "-z",
            "--untracked-files=all",
        ),
        env=_git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ExportError(f"git status failed for {root}: {result.stderr.decode(errors='replace')}")
    return result.stdout


def parse_source(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("source must be ID=PATH")
    source_id, raw_path = value.split("=", 1)
    if not source_id or not raw_path:
        raise argparse.ArgumentTypeError("source must be ID=PATH")
    return source_id, Path(raw_path).expanduser()


def load_source_lock(path: Path) -> list[dict[str, str]]:
    value = load_json(path)
    if value.get("schema_version") != "schuss-source-lock-v1":
        raise ExportError(f"{path}: expected schuss-source-lock-v1")
    sources = value.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ExportError(f"{path}: missing locked sources")
    result: list[dict[str, str]] = []
    ids: set[str] = set()
    for source in sources:
        if set(source) != {"id", "url", "commit"}:
            raise ExportError(f"{path}: invalid locked source shape")
        if source["id"] in ids or re.fullmatch(r"[0-9a-f]{40}", source["commit"]) is None:
            raise ExportError(f"{path}: duplicate source ID or invalid commit")
        ids.add(source["id"])
        result.append(dict(source))
    if ids != set(LEGACY_SOURCE_ORDER):
        raise ExportError(
            "source lock changed; audit and define a new legacy load order before exporting"
        )
    return result


def verify_locked_sources(
    locked: list[dict[str, str]], mappings: list[tuple[str, Path]]
) -> list[LockedSource]:
    paths: dict[str, Path] = {}
    for source_id, path in mappings:
        if source_id in paths:
            raise ExportError(f"duplicate --source ID: {source_id}")
        paths[source_id] = path.resolve()
    locked_by_id = {source["id"]: source for source in locked}
    if set(paths) != set(locked_by_id):
        missing = sorted(set(locked_by_id) - set(paths))
        extra = sorted(set(paths) - set(locked_by_id))
        raise ExportError(f"--source IDs must exactly match lock; missing={missing}, extra={extra}")

    result: list[LockedSource] = []
    for source_id in LEGACY_SOURCE_ORDER:
        source = locked_by_id[source_id]
        path = paths[source_id]
        if not path.is_dir():
            raise ExportError(f"source directory does not exist: {source_id}={path}")
        top = Path(git_text(path, "rev-parse", "--show-toplevel")).resolve()
        if top != path:
            raise ExportError(f"{source_id}: source path must be its Git top level")
        head = git_text(path, "rev-parse", "HEAD")
        if head != source["commit"]:
            raise ExportError(
                f"{source_id}: HEAD {head} does not equal locked commit {source['commit']}"
            )
        git_text(path, "cat-file", "-e", f"{source['commit']}^{{commit}}")
        result.append(
            LockedSource(
                source_id=source_id,
                url=source["url"],
                commit=source["commit"],
                path=path,
                status=git_status(path),
            )
        )
    return result


def verify_sources_unchanged(sources: list[LockedSource]) -> None:
    for source in sources:
        if git_text(source.path, "rev-parse", "HEAD") != source.commit:
            raise ExportError(f"{source.source_id}: HEAD changed during export")
        if git_status(source.path) != source.status:
            raise ExportError(f"{source.source_id}: Git status changed during export")


def archive_commit(source: LockedSource, destination: Path) -> None:
    destination.mkdir(parents=True)
    with tempfile.TemporaryFile() as archive:
        result = subprocess.run(
            (
                "git", "-C", str(source.path), "archive", "--format=tar", source.commit,
            ),
            env=_git_env(),
            stdout=archive,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise ExportError(
                f"git archive failed for {source.source_id}: "
                f"{result.stderr.decode(errors='replace')}"
            )
        archive.seek(0)
        extract = subprocess.run(
            ("tar", "-xf", "-", "-C", str(destination)),
            stdin=archive,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if extract.returncode != 0:
            raise ExportError(
                f"tar extraction failed for {source.source_id}: "
                f"{extract.stderr.decode(errors='replace')}"
            )


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            digest.update(b"L\0" + relative + b"\0" + os.readlink(path).encode("utf-8") + b"\0")
        elif path.is_dir():
            digest.update(b"D\0" + relative + b"\0")
        elif path.is_file():
            digest.update(b"F\0" + relative + b"\0")
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            digest.update(b"\0")
    return digest.hexdigest()


def find_java_home(requested: Path | None) -> Path:
    candidates: list[Path] = []
    if requested is not None:
        candidates.append(requested.expanduser())
    else:
        if os.environ.get("JAVA_HOME"):
            candidates.append(Path(os.environ["JAVA_HOME"]))
        candidates.extend(
            (
                Path("/Applications/Ksoloti Local.app/Contents/Resources/jre"),
                Path("/opt/homebrew/opt/openjdk@21"),
            )
        )
    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / "bin/java").is_file() and (candidate / "bin/javac").is_file():
            javac_version = run_checked((str(candidate / "bin/javac"), "-version")).stdout.strip()
            if re.match(r"javac 21(?:\.|\s|$)", javac_version):
                return candidate
    raise ExportError("a Java 21 JDK with java and javac is required")


def java_version(java_home: Path) -> str:
    result = run_checked((str(java_home / "bin/java"), "-version"))
    lines = (result.stderr or result.stdout).splitlines()
    if not lines or re.search(r'(?<!\d)21(?:[.\s"]|$)', lines[0]) is None:
        raise ExportError("resolved export requires Java 21")
    return lines[0]


def build_patcher(
    patcher: LockedSource,
    build_root: Path,
    java_home: Path,
    ant: str,
) -> tuple[Path, list[Path]]:
    properties = PATCHER_BUILD_PROPERTIES.get(patcher.commit)
    if properties is None:
        raise ExportError("locked patcher commit has no audited fixed Ant build properties")
    archive_commit(patcher, build_root)
    isolated_home = build_root.parent / "ant-home"
    isolated_home.mkdir()
    env = os.environ.copy()
    env.update(
        {
            "JAVA_HOME": str(java_home),
            "HOME": str(isolated_home),
            "LC_ALL": "C",
            "TZ": "UTC",
            "ANT_OPTS": f"-Duser.home={isolated_home}",
        }
    )
    run_checked((ant, "-nouserlib", "-q", "compile", *properties), cwd=build_root, env=env)
    classes = build_root / "build/classes"
    if not classes.is_dir() or not any(classes.rglob("*.class")):
        raise ExportError("pinned Ant build produced no build/classes")
    jars = sorted(build_root.glob("lib/**/*.jar"), key=lambda path: path.relative_to(build_root).as_posix())
    if not jars:
        raise ExportError("pinned patcher archive contains no dependency JARs")
    return classes, jars


def classpath_fingerprint(classes: Path, jars: list[Path], patcher_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(classes.rglob("*.class"), key=lambda item: item.relative_to(classes).as_posix()):
        logical = f"build/classes/{path.relative_to(classes).as_posix()}"
        digest.update(logical.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    for jar in jars:
        logical = jar.relative_to(patcher_root).as_posix()
        digest.update(logical.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(sha256_file(jar)))
    return digest.hexdigest()


def compile_bridge(
    source_root: Path,
    output: Path,
    java_home: Path,
    legacy_classpath: list[Path],
) -> None:
    sources = sorted(source_root.rglob("*.java"), key=lambda path: path.relative_to(source_root).as_posix())
    if not sources:
        raise ExportError(f"bridge source root has no Java sources: {source_root}")
    output.mkdir(parents=True)
    run_checked(
        (
            str(java_home / "bin/javac"),
            "-encoding", "UTF-8",
            "-source", "21",
            "-target", "21",
            "-g:none",
            "-cp", os.pathsep.join(str(path) for path in legacy_classpath),
            "-d", str(output),
            *(str(path) for path in sources),
        )
    )


def eligible_source_files(archives: dict[str, Path]) -> dict[tuple[str, str], dict[str, str]]:
    """Enumerate Phase 3 inputs without Phase 2's directory-name pruning bug."""

    result: dict[tuple[str, str], dict[str, str]] = {}
    for source_id in LEGACY_SOURCE_ORDER:
        root = archives[source_id]
        candidates: list[Path] = []
        objects = root / "objects"
        if source_id in OBJECT_SOURCE_IDS and objects.is_dir():
            candidates.extend(objects.rglob("*.axo"))
        candidates.extend(root.rglob("*.axs"))
        candidates.extend(root.rglob("*.axp"))
        for path in sorted(set(candidates), key=lambda item: item.relative_to(root).as_posix()):
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            lowered_name = path.name.casefold()
            file_type = next(
                extension for extension in ("axo", "axs", "axp")
                if lowered_name.endswith("." + extension)
            )
            key = (source_id, relative)
            if key in result:
                raise ExportError(f"duplicate resolved source candidate: {key}")
            result[key] = {"file_type": file_type, "sha256": sha256_file(path)}
    return result


def validate_pinned_candidate_oracle(
    archives: dict[str, Path],
    eligible: dict[tuple[str, str], dict[str, str]],
    raw_files: list[dict[str, Any]],
) -> None:
    eligible_counts = Counter(item["file_type"] for item in eligible.values())
    if {name: eligible_counts[name] for name in PINNED_ELIGIBLE_COUNTS} != PINNED_ELIGIBLE_COUNTS:
        raise ExportError(f"pinned source candidate counts changed: {dict(eligible_counts)}")
    all_axo = sum(
        1
        for root in archives.values()
        for path in root.rglob("*.axo")
        if path.is_file() and not path.is_symlink()
    )
    if all_axo != PINNED_ALL_AXO_COUNT:
        raise ExportError(f"pinned all-source .axo count changed: {all_axo}")
    generator_java = [
        path
        for path in (archives["patcher"] / "src/main/java/generatedobjects").glob("*.java")
        if path.is_file() and not path.is_symlink()
    ]
    if len(generator_java) != PINNED_GENERATOR_JAVA_COUNT:
        raise ExportError(f"pinned generatedobjects Java count changed: {len(generator_java)}")
    raw_keys = {(item["source_repository"], item["path"]) for item in raw_files}
    omissions = Counter(eligible[key]["file_type"] for key in set(eligible) - raw_keys)
    if {name: omissions[name] for name in PINNED_OMISSION_COUNTS} != PINNED_OMISSION_COUNTS:
        raise ExportError(f"Phase 2 omission counts changed: {dict(omissions)}")


def validate_pinned_resolved_object_oracle(
    objects: list[dict[str, Any]], issues: list[dict[str, Any]]
) -> None:
    """Bind v0 to the observed ordered catalog and generator seam."""

    file_records = [item for item in objects if item["origin"]["kind"] == "file"]
    provider_records = [item for item in objects if item["origin"]["kind"] == "provider"]
    axo_definitions = [
        item for item in file_records if item["origin"]["path"].casefold().endswith(".axo")
    ]
    subpatches = [
        item
        for item in file_records
        if item["legacy_kind"] == "subpatch_catalog_placeholder"
    ]
    retained = sum(item["legacy_object_list_index"] is not None for item in objects)
    matched_emissions = sum(
        item["origin"].get("generated_by") is not None for item in file_records
    )
    observed = {
        "file_records": len(file_records),
        "axo_definitions": len(axo_definitions),
        "catalog_subpatches": len(subpatches),
        "retained": retained,
        "generator_emissions": matched_emissions + len(provider_records),
        "provider_only": len(provider_records),
    }
    expected = {
        "file_records": PINNED_FILE_OBJECT_RECORDS,
        "axo_definitions": PINNED_AXO_DEFINITION_RECORDS,
        "catalog_subpatches": PINNED_CATALOG_SUBPATCH_RECORDS,
        "retained": PINNED_RETAINED_OBJECT_RECORDS,
        "generator_emissions": PINNED_GENERATOR_EMISSIONS,
        "provider_only": PINNED_PROVIDER_ONLY_RECORDS,
    }
    if observed != expected:
        raise ExportError(
            f"pinned resolved object oracle changed: observed={observed}, expected={expected}"
        )
    issue_codes = Counter(issue["code"] for issue in issues)
    expected_codes = {
        "GENERATED_DEFINITION_COUNT_MISMATCH": 3,
        "GENERATED_EMISSION_UNMATCHED": 51,
        "GENERATED_OUTPUT_REDEFINED": 1,
        "GENERATED_OUTPUT_REPEATED_IDENTICAL": 1,
        "LEGACY_OBJECT_LIST_COLLAPSE": 3,
        "OVERLOADED_NAME_CANDIDATES": 157,
    }
    changed = {
        code: issue_codes[code]
        for code, count in expected_codes.items()
        if issue_codes[code] != count
    }
    if changed:
        raise ExportError(
            f"pinned resolved catalog diagnostics changed: {changed}; expected={expected_codes}"
        )


def run_bridge(
    *,
    run_root: Path,
    java_home: Path,
    bridge_classes: Path,
    legacy_classpath: list[Path],
    archives: dict[str, Path],
    main_class: str,
    generator_class: str | None,
    source_order: Sequence[str] = LEGACY_SOURCE_ORDER,
) -> Path:
    output = run_root / "output"
    home = run_root / "home"
    preferences = run_root / "preferences"
    temporary = run_root / "tmp"
    work = run_root / "work"
    for directory in (home, preferences / "user", preferences / "system", temporary, work):
        directory.mkdir(parents=True, exist_ok=True)
    classpath = [bridge_classes, *legacy_classpath]
    command = [
        str(java_home / "bin/java"),
        "-XX:-UsePerfData",
        "-Djava.awt.headless=true",
        "-Dfile.encoding=UTF-8",
        "-Duser.language=en",
        "-Duser.country=US",
        "-Duser.timezone=UTC",
        f"-Duser.home={home}",
        f"-Djava.util.prefs.userRoot={preferences / 'user'}",
        f"-Djava.util.prefs.systemRoot={preferences / 'system'}",
        f"-Djava.io.tmpdir={temporary}",
        "-cp", os.pathsep.join(str(path) for path in classpath),
        main_class,
        "--output-dir", str(output),
    ]
    for source_id in source_order:
        command.extend(("--source", f"{source_id}={archives[source_id]}"))
    if generator_class is not None:
        command.extend(("--generator-class", generator_class))
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "LC_ALL": "C",
            "TZ": "UTC",
        }
    )
    run_checked(command, cwd=work, env=env)
    expected = {output / artifact for artifact in ARTIFACTS}
    observed = {path for path in output.rglob("*") if path.is_file()}
    if observed != expected:
        missing = sorted(str(path.relative_to(output)) for path in expected - observed)
        extra = sorted(str(path.relative_to(output)) for path in observed - expected)
        raise ExportError(f"bridge artifact set mismatch; missing={missing}, extra={extra}")
    preference_files = [path for path in (home, preferences) for path in path.rglob("*") if path.is_file()]
    if preference_files:
        raise ExportError("bridge wrote to isolated user home or preferences")
    return output


def validate_fixture_artifacts(output: Path, schema_root: Path) -> dict[str, int]:
    """Exercise the behavioral fixture through the real Java bridge."""

    objects = load_jsonl(output / "resolved/objects.jsonl")
    graphs = load_jsonl(output / "resolved/graphs.jsonl")
    issues = load_jsonl(output / "resolved/issues.jsonl")
    object_schema = load_json(schema_root / OBJECT_SCHEMA)
    graph_schema = load_json(schema_root / GRAPH_SCHEMA)
    issue_schema = load_json(schema_root / ISSUE_SCHEMA)
    for index, record in enumerate(objects):
        validate_schema(record, object_schema, f"fixture.objects[{index}]")
    for index, record in enumerate(graphs):
        validate_schema(record, graph_schema, f"fixture.graphs[{index}]")
    for index, record in enumerate(issues):
        validate_schema(record, issue_schema, f"fixture.issues[{index}]")
    _validate_object_indexes(objects)
    _validate_graph_indexes(graphs, len(objects))
    _validate_issue_indexes(issues, len(objects), len(graphs))
    _reject_generated_uuid_leaks(objects)

    if len(objects) != 7 or len(graphs) != 6:
        raise ExportError(
            f"resolved fixture cardinality changed: objects={len(objects)}, graphs={len(graphs)}"
        )
    codes = Counter(issue["code"] for issue in issues)
    for code in (
        "DUPLICATE_UUID_CANDIDATES",
        "OVERLOADED_NAME_CANDIDATES",
        "OBJECT_PARSE_RELAXED",
        "OBJECT_FILE_ZERO_DEFINITIONS",
        "UNSUPPORTED_GRAPH_ELEMENT",
        "SERIALIZED_HARD_ZOMBIE",
        "INSTANCE_BECAME_ZOMBIE",
    ):
        if not codes[code]:
            raise ExportError(f"resolved fixture did not exercise {code}")

    by_path = {graph["source"]["path"]: graph for graph in graphs}
    parent = by_path.get("patches/relative/relative-parent.axp")
    if parent is None or parent["export_status"] == "failed":
        raise ExportError("relative subpatch fixture did not survive graph resolution")
    relative = [
        instance
        for instance in parent["instances"]
        if instance["requested_type"]["name"] == "./relative-child"
    ]
    if len(relative) != 1 or relative[0]["resolution"]["method"] != "relative-axs":
        raise ExportError("relative .axs fixture did not record its resolution method")

    overload = by_path.get("patches/ambiguous-overload.axp")
    if overload is None:
        raise ExportError("ambiguous overload fixture graph is missing")
    promoted = [
        instance
        for instance in overload["instances"]
        if instance["instance_name"] == "promoted"
    ]
    if len(promoted) != 1 or promoted[0]["resolution"]["status"] != "ambiguous":
        raise ExportError("name-overload fixture did not remain explicitly ambiguous")
    if len(promoted[0]["resolution"]["candidates"]) != 2:
        raise ExportError("name-overload fixture did not retain both ordered candidates")
    if promoted[0]["post_resolution_index"] is None:
        raise ExportError("promoted overload replacement was not correlated post-resolution")
    if len(overload["nets"]) != 1 or overload["nets"][0]["status"] != "resolved":
        raise ExportError("promoted overload fixture net did not remain resolved")

    zombies = by_path.get("patches/zombies.axp")
    if zombies is None:
        raise ExportError("zombie fixture graph is missing")
    zombie_kinds = {instance["zombie_kind"] for instance in zombies["instances"]}
    if not {"serialized-hard", "created-by-resolution"} <= zombie_kinds:
        raise ExportError("zombie fixture did not preserve both zombie classes")
    endpoint_statuses = {
        endpoint["resolution_status"]
        for net in zombies["nets"]
        for endpoint in net["sources"] + net["destinations"]
    }
    if not {"missing_instance", "missing_port", "not_evaluated"} <= endpoint_statuses:
        raise ExportError("zombie fixture did not preserve malformed endpoint outcomes")

    unsupported = by_path.get("patches/unsupported-content.axp")
    if unsupported is None or not any(
        instance["legacy_element_kind"] == "unsupported"
        for instance in unsupported["instances"]
    ):
        raise ExportError("unsupported graph element was not retained fail-closed")
    if not any(
        instance["instance_name"] == "source-after"
        for instance in unsupported["instances"]
    ):
        raise ExportError("valid content after an unsupported graph element was lost")
    return {"objects": len(objects), "graphs": len(graphs), "issues": len(issues)}


def compare_artifacts(first: Path, second: Path) -> None:
    for relative in ARTIFACTS:
        if (first / relative).read_bytes() != (second / relative).read_bytes():
            raise ExportError(f"fresh JVM outputs differ: {relative.as_posix()}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for value in values:
            handle.write(
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n"
            )


def add_baseline_omission_issues(
    stage: Path,
    eligible: dict[tuple[str, str], dict[str, str]],
    raw_files: list[dict[str, Any]],
) -> None:
    raw_keys = {(item["source_repository"], item["path"]) for item in raw_files}
    issues = load_jsonl(stage / "resolved/issues.jsonl")
    graphs = load_jsonl(stage / "resolved/graphs.jsonl")
    graph_indexes = {
        (item["source"]["source_id"], item["source"]["path"]): item["graph_index"]
        for item in graphs
    }
    existing = {
        (item["location"]["source_id"], item["location"]["path"])
        for item in issues
        if item["code"] == "RAW_BASELINE_OMISSION"
    }
    for key in sorted(set(eligible) - raw_keys):
        if key in existing:
            continue
        source_id, path = key
        observation = eligible[key]
        graph_index = graph_indexes.get(key)
        issues.append(
            {
                "schema_version": "legacy-resolved-issue-v0",
                "issue_index": 0,
                "severity": "warning",
                "stage": "reconcile",
                "code": "RAW_BASELINE_OMISSION",
                "location": {
                    "kind": "graph" if graph_index is not None else "object",
                    "source_id": source_id,
                    "path": path,
                    "variant_index": None,
                    "graph_index": graph_index,
                    "instance_index": None,
                    "net_index": None,
                    "endpoint_role": None,
                    "endpoint_index": None,
                },
                "message": "Pinned source file was omitted from the retained Phase 2 raw baseline",
                "processing_continued": True,
                "facts": [
                    {"name": "file_type", "value_type": "string", "value": observation["file_type"]},
                    {"name": "sha256", "value_type": "string", "value": observation["sha256"]},
                ],
                "candidate_variant_indexes": [],
            }
        )
    issues.sort(key=_issue_sort_key)
    for index, issue in enumerate(issues):
        issue["issue_index"] = index
    write_jsonl(stage / "resolved/issues.jsonl", issues)


def create_manifest(
    *,
    locked: list[dict[str, str]],
    sources: list[LockedSource],
    raw_snapshot: Path,
    classpath_sha256: str,
    runtime_version: str,
) -> dict[str, Any]:
    states = {source.source_id: source for source in sources}
    patcher = next(source for source in locked if source["id"] == "patcher")
    return {
        "schema_version": SCHEMA_VERSION,
        "exporter": {"name": "export_resolved_inventory.py", "version": 1},
        "legacy_runtime": {
            "source_id": "patcher",
            "commit": patcher["commit"],
            "classpath_fingerprint_sha256": classpath_sha256,
            "java_version": runtime_version,
        },
        "raw_snapshot": {
            "schema_version": "legacy-catalog-v0",
            "manifest_sha256": sha256_file(raw_snapshot / "manifest.json"),
            "files_jsonl_sha256": sha256_file(raw_snapshot / "raw/files.jsonl"),
        },
        "sources": [
            {
                "id": source["id"],
                "url": source["url"],
                "commit": source["commit"],
                "observed_dirty": bool(states[source["id"]].status),
            }
            for source in locked
        ],
        "object_roots": [
            {"order": index, "source_id": source_id, "relative_path": "objects"}
            for index, source_id in enumerate(OBJECT_SOURCE_IDS)
        ],
        "graph_input_types": ["axs", "axp"],
        "options": {
            "phase": "java-resolved",
            "timestamp_included": False,
            "preference_writes": False,
            "subpatch_interface_projection": True,
            "target_artifact_generation": False,
            "target_compilation": False,
            "device_access": False,
        },
    }


def reject_path_leaks(root: Path, forbidden: Iterable[Path]) -> None:
    needles = {str(path.resolve()).encode("utf-8") for path in forbidden}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if any(needle and needle in data for needle in needles):
            raise ExportError(f"durable artifact contains an absolute execution path: {path}")


def materialize_output(stage: Path, output: Path) -> None:
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ExportError(f"refusing to overwrite non-empty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    for child in sorted(stage.iterdir(), key=lambda path: path.name):
        destination = output / child.name
        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)


def _export_verified_sources(
    *,
    output: Path,
    source_lock: Path,
    raw_snapshot: Path,
    bridge_source: Path,
    java_home: Path | None,
    ant: str,
    locked: list[dict[str, str]],
    sources: list[LockedSource],
    main_class: str = BRIDGE_MAIN,
    generator_class: str = GENERATOR_CLASS,
) -> dict[str, int]:
    source_lock = source_lock.resolve()
    raw_snapshot = raw_snapshot.resolve()
    bridge_source = bridge_source.resolve()
    for source in sources:
        try:
            output.resolve().relative_to(source.path)
        except ValueError:
            pass
        else:
            raise ExportError("output must not be inside a locked upstream checkout")
    java_home = find_java_home(java_home)
    runtime_version = java_version(java_home)

    raw_files = load_jsonl(raw_snapshot / "raw/files.jsonl")
    raw_manifest = load_json(raw_snapshot / "manifest.json")
    if raw_manifest.get("schema_version") != "legacy-catalog-v0":
        raise ExportError("retained raw snapshot has an unexpected schema version")

    with tempfile.TemporaryDirectory(prefix="schuss-resolved-") as raw_temp:
        temporary_root = Path(raw_temp)
        archive_root = temporary_root / "sources"
        archives: dict[str, Path] = {}
        for source in sources:
            destination = archive_root / source.source_id
            archive_commit(source, destination)
            archives[source.source_id] = destination
        eligible = eligible_source_files(archives)
        validate_pinned_candidate_oracle(archives, eligible, raw_files)

        patcher = next(source for source in sources if source.source_id == "patcher")
        runtime_root = temporary_root / "runtime/patcher"
        legacy_classes, jars = build_patcher(patcher, runtime_root, java_home, ant)
        legacy_classpath = [legacy_classes, *jars]
        fingerprint = classpath_fingerprint(legacy_classes, jars, runtime_root)
        bridge_classes = temporary_root / "bridge-classes"
        compile_bridge(bridge_source, bridge_classes, java_home, legacy_classpath)

        source_digests = {source_id: tree_digest(path) for source_id, path in archives.items()}
        runtime_digest = tree_digest(runtime_root)

        fixture_source = (
            bridge_source.parents[2]
            / "fixtures/resolved-inventory/axoloti-factory"
        )
        if not fixture_source.is_dir():
            raise ExportError(f"resolved behavioral fixture is missing: {fixture_source}")
        fixture_digest = tree_digest(fixture_source)
        fixture_first = run_bridge(
            run_root=temporary_root / "fixture-run-1",
            java_home=java_home,
            bridge_classes=bridge_classes,
            legacy_classpath=legacy_classpath,
            archives={"axoloti-factory": fixture_source},
            main_class=main_class,
            generator_class=None,
            source_order=("axoloti-factory",),
        )
        fixture_second = run_bridge(
            run_root=temporary_root / "fixture-run-2",
            java_home=java_home,
            bridge_classes=bridge_classes,
            legacy_classpath=legacy_classpath,
            archives={"axoloti-factory": fixture_source},
            main_class=main_class,
            generator_class=None,
            source_order=("axoloti-factory",),
        )
        compare_artifacts(fixture_first, fixture_second)
        validate_fixture_artifacts(fixture_first, source_lock.parent.parent / "schemas")
        reject_path_leaks(fixture_first, [temporary_root, fixture_source, java_home, bridge_source])
        if tree_digest(fixture_source) != fixture_digest:
            raise ExportError("Java bridge changed the resolved behavioral fixture tree")
        if tree_digest(runtime_root) != runtime_digest:
            raise ExportError("fixture JVM changed the pinned runtime build tree")

        first = run_bridge(
            run_root=temporary_root / "run-1",
            java_home=java_home,
            bridge_classes=bridge_classes,
            legacy_classpath=legacy_classpath,
            archives=archives,
            main_class=main_class,
            generator_class=generator_class,
        )
        if {source_id: tree_digest(path) for source_id, path in archives.items()} != source_digests:
            raise ExportError("first JVM changed an archived pinned source tree")
        if tree_digest(runtime_root) != runtime_digest:
            raise ExportError("first JVM changed the pinned runtime build tree")
        second = run_bridge(
            run_root=temporary_root / "run-2",
            java_home=java_home,
            bridge_classes=bridge_classes,
            legacy_classpath=legacy_classpath,
            archives=archives,
            main_class=main_class,
            generator_class=generator_class,
        )
        if {source_id: tree_digest(path) for source_id, path in archives.items()} != source_digests:
            raise ExportError("second JVM changed an archived pinned source tree")
        if tree_digest(runtime_root) != runtime_digest:
            raise ExportError("second JVM changed the pinned runtime build tree")
        compare_artifacts(first, second)

        stage = temporary_root / "stage"
        shutil.copytree(first / "resolved", stage / "resolved")
        add_baseline_omission_issues(stage, eligible, raw_files)
        objects = load_jsonl(stage / "resolved/objects.jsonl")
        graphs = load_jsonl(stage / "resolved/graphs.jsonl")
        issues = load_jsonl(stage / "resolved/issues.jsonl")
        validate_pinned_resolved_object_oracle(objects, issues)
        manifest = create_manifest(
            locked=locked,
            sources=sources,
            raw_snapshot=raw_snapshot,
            classpath_sha256=fingerprint,
            runtime_version=runtime_version,
        )
        write_json(stage / "manifest.json", manifest)
        summary = build_summary(
            raw_files,
            objects,
            graphs,
            issues,
            enabled_object_roots={(source_id, "objects") for source_id in OBJECT_SOURCE_IDS},
        )
        write_json(stage / "reports/summary.json", summary)
        (stage / "reports/summary.md").write_text(
            render_summary_markdown(summary), encoding="utf-8", newline="\n"
        )
        reject_path_leaks(
            stage,
            [temporary_root, java_home, bridge_source, *(source.path for source in sources)],
        )
        counts = validate_inventory(
            stage,
            source_lock=source_lock,
            raw_snapshot=raw_snapshot,
        )
        verify_sources_unchanged(sources)
        materialize_output(stage, output)
        return counts


def export_resolved(
    *,
    output: Path,
    source_lock: Path,
    raw_snapshot: Path,
    source_mappings: list[tuple[str, Path]],
    bridge_source: Path,
    java_home: Path | None,
    ant: str,
    main_class: str = BRIDGE_MAIN,
    generator_class: str = GENERATOR_CLASS,
) -> dict[str, int]:
    """Guard the entire operation with a live upstream-state recheck."""

    source_lock = source_lock.resolve()
    locked = load_source_lock(source_lock)
    sources = verify_locked_sources(locked, source_mappings)
    try:
        return _export_verified_sources(
            output=output,
            source_lock=source_lock,
            raw_snapshot=raw_snapshot,
            bridge_source=bridge_source,
            java_home=java_home,
            ant=ant,
            locked=locked,
            sources=sources,
            main_class=main_class,
            generator_class=generator_class,
        )
    finally:
        verify_sources_unchanged(sources)


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Build the locked Ksoloti Java model and export resolved evidence twice"
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--source-lock", type=Path, default=repository_root / "catalog/sources.lock.json"
    )
    parser.add_argument(
        "--raw-snapshot",
        type=Path,
        default=repository_root / "catalog/snapshots/legacy-catalog-v0",
    )
    parser.add_argument("--source", action="append", type=parse_source, required=True)
    parser.add_argument(
        "--bridge-source",
        type=Path,
        default=repository_root / "legacy/ksoloti-bridge/src/main/java",
    )
    parser.add_argument("--java-home", type=Path)
    parser.add_argument("--ant", default="ant")
    parser.add_argument("--bridge-main", default=BRIDGE_MAIN)
    parser.add_argument("--generator-class", default=GENERATOR_CLASS)
    args = parser.parse_args()
    try:
        counts = export_resolved(
            output=args.output,
            source_lock=args.source_lock,
            raw_snapshot=args.raw_snapshot,
            source_mappings=args.source,
            bridge_source=args.bridge_source,
            java_home=args.java_home,
            ant=args.ant,
            main_class=args.bridge_main,
            generator_class=args.generator_class,
        )
    except (ExportError, InventoryValidationError, OSError, KeyError, TypeError) as exc:
        print(f"resolved inventory export failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
