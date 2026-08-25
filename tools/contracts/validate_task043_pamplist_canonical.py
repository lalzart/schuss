#!/usr/bin/env python3
"""Validate the bounded Task 043 Pamplist canonical-instrument promotion."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.instrument_library import (  # noqa: E402
    InstrumentLibraryService,
)
from packages.schuss_core.product_cli import catalog_search_request  # noqa: E402
from tools.contracts import generate_task043_pamplist_canonical as generator  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task043-pamplist-canonical-v1.json"
EXPECTED_PARENT = {
    "record_set_id": "schuss-record-set-000033",
    "revision": 1,
    "content_hash": "sha256:01dc913b0d637573adda283f84985e7196ee7162b6f2eaadf76b1d3a2890b786",
    "status": "included",
}
EXPECTED_ROLES = {
    f"schuss-component-contract-{number:06d}" for number in range(42, 49)
}


def _exact_reference(value: Mapping[str, Any], identifier: str) -> dict[str, Any]:
    return {
        identifier: value[identifier],
        "revision": value["revision"],
        "content_hash": value["content_hash"],
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    generation_summary: dict[str, Any] = {}

    try:
        expected_files, expected_manifest, generation_summary = generator.generated()
        for relative, expected in sorted(expected_files.items()):
            path = root / relative
            if not path.is_file() or path.read_bytes() != expected:
                errors.append(f"generated file is stale: {relative}")
        if not RECORD_SET.is_file() or RECORD_SET.read_bytes() != expected_manifest:
            errors.append("generated record set is stale")
    except (KeyError, OSError, TypeError, ValueError) as exc:
        errors.append(f"generation closure is invalid: {exc}")

    try:
        context = load_repository_context(root, record_set_path=RECORD_SET)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        errors.append(f"record-set closure is invalid: {exc}")
        context = None

    graph: dict[str, Any] | None = None
    instrument: dict[str, Any] | None = None
    family: dict[str, Any] | None = None
    library_entry: dict[str, Any] | None = None
    if context is not None:
        manifest = context.loaded_record_set.manifest
        if manifest.get("parent_reference") != EXPECTED_PARENT:
            errors.append("record-set parent differs")
        if context.record_set_reference != generation_summary.get("record_set_reference"):
            errors.append("selected record-set reference differs from generated authority")

        projection = context.catalog_projection or {}
        if projection.get("schema_version") != "catalog-projection-v7":
            errors.append("catalog projection is not v7")
        families = [
            value
            for value in projection.get("families", ())
            if value.get("family_reference", {}).get("family_id")
            == generator.FAMILY_ID
        ]
        if len(families) != 1:
            errors.append("Pamplist family does not resolve exactly once")
        else:
            family = families[0]
            if family.get("abstraction_level") != "instrument":
                errors.append("Pamplist family is not an instrument abstraction")
            implementations = family.get("implementations", ())
            if [item.get("implementation_id") for item in implementations] != [
                generator.IMPLEMENTATION_ID
            ]:
                errors.append("Pamplist implementation identity differs")
            elif implementations[0].get("target_availability") and any(
                row.get("provider_status") == "present"
                for row in implementations[0]["target_availability"]
            ):
                errors.append("Pamplist unexpectedly claims a canonical provider")

        graphs = [
            value
            for value in context.records.get("graphs", ())
            if value.get("graph_id") == generator.GRAPH_ID
        ]
        if len(graphs) != 1:
            errors.append("Pamplist graph does not resolve exactly once")
        else:
            graph = graphs[0]
            role_ids = {
                node["contract_reference"]["component_contract_id"]
                for node in graph["nodes"]
            }
            if role_ids != EXPECTED_ROLES or len(graph["nodes"]) != 7:
                errors.append("Pamplist graph does not expose the exact seven roles")
            expected_counts = {
                "connections": 12,
                "parameter_bindings": 178,
                "public_parameters": 178,
                "public_actions": 2,
                "public_displays": 4,
                "public_ports": 2,
            }
            for field, expected in expected_counts.items():
                if len(graph[field]) != expected:
                    errors.append(f"Pamplist graph {field} count differs")
            if {
                value.get("display_label") for value in graph["public_ports"]
            } != {"Audio Left", "Audio Right"}:
                errors.append("Pamplist graph stereo public output differs")

        instruments = [
            value
            for value in context.records.get("performance_instruments", ())
            if value.get("instrument_id") == generator.INSTRUMENT_ID
        ]
        if len(instruments) != 1:
            errors.append("Pamplist instrument does not resolve exactly once")
        else:
            instrument = instruments[0]
            if len(instrument["parameters"]) != 178:
                errors.append("Pamplist instrument parameter count differs")
            if len(instrument["graph_mappings"]) != 180:
                errors.append("Pamplist instrument graph mapping count differs")
            if graph is not None:
                expected_graph = {
                    "status": "resolved",
                    **_exact_reference(graph, "graph_id"),
                }
                if instrument.get("graph_reference") != expected_graph:
                    errors.append("Pamplist instrument graph reference differs")

        catalog = context.records.get("catalog", ())[0]
        additions = [
            value
            for value in catalog["family_additions"]
            if value["family_id"] == generator.FAMILY_ID
        ]
        if len(additions) != 1:
            errors.append("Pamplist catalog authority is absent or ambiguous")
        else:
            authority = additions[0].get("source_authority", {})
            if authority.get("kind") != "schuss-instrument-prototype":
                errors.append("Pamplist source authority kind differs")
            for name, expected_path in generator.PAMPLIST_AUTHORITIES.items():
                item = authority.get("authorities", {}).get(name, {})
                if item.get("path") != expected_path:
                    errors.append(f"Pamplist authority path differs: {name}")
                    continue
                path = root / expected_path
                if not path.is_file() or item.get("sha256") != core.sha256_file(path):
                    errors.append(f"Pamplist authority hash differs: {name}")
            releases = {
                core.canonical_json(_exact_reference(value, "source_release_id"))
                for value in context.records.get("source_releases", ())
                if value.get("source_release_id")
                in {
                    "schuss-source-release-000008",
                    "schuss-source-release-000009",
                }
            }
            actual_releases = {
                core.canonical_json(value)
                for value in authority.get("source_release_references", ())
            }
            if actual_releases != releases or len(releases) != 2:
                errors.append("Pamplist source-release authority differs")

        bound_ids = {
            value["implementation_id"] for value in context.records.get("bindings", ())
        }
        provider_ids = {
            binding["catalog_implementation_locator"]["implementation_id"]
            for provider in context.records.get("implementation_providers", ())
            for binding in provider["bindings"]
        }
        if generator.IMPLEMENTATION_ID in bound_ids | provider_ids:
            errors.append("Pamplist incorrectly claims a canonical binding or provider")

        try:
            service = InstrumentLibraryService(
                root,
                context=context,
                process_factory=lambda _path: (_ for _ in ()).throw(
                    AssertionError("validation must not spawn a process")
                ),
            )
            library = service.list_instruments()
            entries = [
                value
                for value in library["instruments"]
                if value["prototype_id"] == "pamplist"
            ]
            if (
                library.get("library_revision") != 2
                or library.get("instrument_count") != 6
                or library.get("claims")
                != {
                    "canonical_identity_count": 1,
                    "production_ready": False,
                    "runtime_authority": "prototype-build-only",
                }
                or len(entries) != 1
            ):
                errors.append("audition library v2 summary differs")
            else:
                library_entry = entries[0]
                canonical = library_entry.get("canonical_identity")
                if (
                    canonical is None
                    or canonical.get("status") != "canonical"
                    or instrument is None
                    or graph is None
                    or canonical.get("instrument_reference")
                    != _exact_reference(instrument, "instrument_id")
                    or canonical.get("graph_reference")
                    != _exact_reference(graph, "graph_id")
                    or canonical.get("record_set_reference")
                    != context.record_set_reference
                ):
                    errors.append("Pamplist library canonical identity differs")
                if not library_entry.get("launchable"):
                    errors.append("Pamplist frozen audition build is not launchable")
        except (AssertionError, KeyError, OSError, TypeError, ValueError) as exc:
            errors.append(f"audition library closure is invalid: {exc}")

        try:
            search = dispatch_operation(
                catalog_search_request("Pamplist", {}), context
            )
            results = search.get("value", {}).get("results", ())
            if (
                search.get("status") != "success"
                or len(results) != 1
                or results[0]["family_reference"]["family_id"]
                != generator.FAMILY_ID
            ):
                errors.append("Pamplist is not discoverable through catalog.search")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"Pamplist catalog search is invalid: {exc}")

    return {
        "schema_version": "task043-pamplist-canonical-validation-summary-v1",
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "record_set_reference": generation_summary.get("record_set_reference"),
        "family_reference": generation_summary.get("family_reference"),
        "graph_reference": generation_summary.get("graph_reference"),
        "instrument_reference": generation_summary.get("instrument_reference"),
        "graph_role_count": len(graph["nodes"]) if graph is not None else 0,
        "instrument_parameter_count": (
            len(instrument["parameters"]) if instrument is not None else 0
        ),
        "library_entry_count": 6 if library_entry is not None else 0,
        "canonical_library_entry_count": 1 if library_entry is not None else 0,
        "runtime_provider_claimed": False,
        "application_or_endpoint_opened": False,
        "device_or_listening_evidence_claimed": False,
        "git_or_publication_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="retained for check symmetry")
    parser.parse_args()
    result = validate()
    print(core.canonical_json(result))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
