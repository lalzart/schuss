from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import application_capabilities as application
from packages.schuss_core.control_plane import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)

import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task023-application-spine-v1.json"
PARENT_RECORD_SET = ROOT / "contracts/record-sets/task022-gills-panel-diagnostic-v1.json"
OLDER_RECORD_SET = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"
SCHEMA_PATHS = (
    ROOT / "schemas/application-capability-description-v0.schema.json",
    ROOT / "schemas/operation-request-v7.schema.json",
    ROOT / "schemas/operation-result-v7.schema.json",
)


def request() -> dict[str, object]:
    return {
        "schema_version": "schuss-operation-request-v7",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "application.describe",
        "payload": {"scope": "selected-context"},
    }


class Task023ApplicationCapabilitiesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.result = dispatch_operation(request(), cls.context)
        cls.description = cls.result["value"]

    def test_additive_schemas_and_description_are_valid(self):
        for path in SCHEMA_PATHS:
            schema = core.load_json(path)
            self.assertEqual([], core.validate_schema_annotations(schema), path.name)
        schema = self.context.schemas["application_capability_description"]
        self.assertEqual([], core.schema_errors(self.description, schema, schema))
        self.assertEqual("success", self.result["status"])
        self.assertEqual(
            "schuss-record-set-000015",
            self.description["record_set_reference"]["record_set_id"],
        )
        self.assertEqual([], self.result["diagnostics"])

    def test_registry_is_exact_sorted_and_effects_are_distinct(self):
        operations = self.description["operations"]
        names = [item["operation"] for item in operations]
        self.assertEqual(sorted(names), names)
        self.assertEqual(list(application.EXPECTED_OPERATIONS), names)
        by_name = {item["operation"]: item for item in operations}
        self.assertEqual("proposal-only", by_name["graph.transact"]["effect_class"])
        self.assertEqual(
            "workspace-write", by_name["project.graph.commit"]["effect_class"]
        )
        self.assertEqual(
            "build-output-write", by_name["build.execute"]["effect_class"]
        )
        self.assertIn("write-intent", by_name["project.graph.commit"]["explicit_gates"])
        self.assertIn("execute-intent", by_name["build.execute"]["explicit_gates"])
        self.assertEqual(
            "requires-project-workspace", by_name["project.inspect"]["availability"]
        )
        self.assertEqual(
            "requires-execution-service", by_name["build.execute"]["availability"]
        )
        self.assertTrue(
            all(item["evidence_boundary"] == "operation-contract-only" for item in operations)
        )

    def test_direct_cli_ui_and_ai_machine_adapters_share_bytes(self):
        direct = canonical_result_bytes(
            dispatch_operation(copy.deepcopy(request()), self.context), self.context
        )
        cli = canonical_result_bytes(
            dispatch_operation(copy.deepcopy(request()), self.context), self.context
        ) + b"\n"
        ui = canonical_result_bytes(
            dispatch_operation(copy.deepcopy(request()), self.context), self.context
        )
        ai = canonical_result_bytes(
            dispatch_operation(copy.deepcopy(request()), self.context), self.context
        )
        self.assertEqual(direct, cli[:-1])
        self.assertEqual(direct, ui)
        self.assertEqual(direct, ai)

    def test_schema_rejects_unknown_effect_operation_and_extra_property(self):
        schema = self.context.schemas["application_capability_description"]
        cases = []
        unknown_operation = copy.deepcopy(self.description)
        unknown_operation["operations"][0]["operation"] = "application.unknown"
        cases.append(unknown_operation)
        unknown_effect = copy.deepcopy(self.description)
        unknown_effect["operations"][0]["effect_class"] = "device-write"
        cases.append(unknown_effect)
        extra = copy.deepcopy(self.description)
        extra["operations"][0]["host_path"] = "/tmp/private"
        cases.append(extra)
        for value in cases:
            with self.subTest(value=value["operations"][0]):
                self.assertTrue(core.schema_errors(value, schema, schema))

    def test_malformed_and_unavailable_v7_fail_closed(self):
        malformed = request()
        malformed["payload"] = {"scope": "all-host-capabilities", "extra": True}
        result = dispatch_operation(malformed, self.context)
        self.assertEqual("invalid", result["status"])
        self.assertEqual("application.describe", result["operation"])
        self.assertEqual("OPERATION_REQUEST_INVALID", result["diagnostics"][0]["code"])
        canonical_result_bytes(result, self.context)

        older = load_repository_context(ROOT, record_set_path=OLDER_RECORD_SET)
        unavailable = dispatch_operation(request(), older)
        self.assertEqual("schuss-operation-result-v1", unavailable["schema_version"])
        self.assertEqual("invalid-request", unavailable["operation"])
        self.assertEqual("invalid", unavailable["status"])
        canonical_result_bytes(unavailable, older)

        for missing in (
            "application_capability_description",
            "operation_request_v7",
            "operation_result_v7",
        ):
            with self.subTest(missing=missing):
                schemas = dict(self.context.schemas)
                del schemas[missing]
                partial = replace(self.context, schemas=schemas)
                unavailable = dispatch_operation(request(), partial)
                self.assertEqual("invalid", unavailable["status"])
                self.assertEqual(
                    "APPLICATION_SCHEMA_UNAVAILABLE",
                    unavailable["diagnostics"][0]["code"],
                )
                canonical_result_bytes(unavailable, partial)

    def test_selected_services_change_only_context_availability(self):
        execution_result = dispatch_operation(
            request(), self.context, execution_service=object()
        )
        execution_operations = {
            item["operation"]: item
            for item in execution_result["value"]["operations"]
        }
        self.assertEqual(
            "available", execution_operations["build.execute"]["availability"]
        )
        self.assertEqual(
            "requires-project-workspace",
            execution_operations["project.inspect"]["availability"],
        )

        project_service = mock.Mock()
        project_service.load.return_value = SimpleNamespace(context=self.context)
        project_result = dispatch_operation(
            request(), self.context, project_service=project_service
        )
        project_operations = {
            item["operation"]: item
            for item in project_result["value"]["operations"]
        }
        self.assertEqual(
            "available", project_operations["project.inspect"]["availability"]
        )
        self.assertEqual(
            "requires-execution-service",
            project_operations["build.execute"]["availability"],
        )

    def test_registry_drift_returns_canonical_diagnostic(self):
        invalid_entries = (*application.CAPABILITY_ENTRIES, {"operation": "unknown"})
        with mock.patch.object(application, "CAPABILITY_ENTRIES", invalid_entries):
            result = dispatch_operation(request(), self.context)
        self.assertEqual("invalid", result["status"])
        self.assertEqual(
            "APPLICATION_CAPABILITY_REGISTRY_INVALID",
            result["diagnostics"][0]["code"],
        )
        canonical_result_bytes(result, self.context)

    def test_record_set_is_schema_only_exact_successor(self):
        parent = json.loads(PARENT_RECORD_SET.read_text(encoding="utf-8"))
        current = json.loads(RECORD_SET.read_text(encoding="utf-8"))
        self.assertEqual(parent["record_members"], current["record_members"])
        self.assertEqual(parent["enforced_directories"], current["enforced_directories"])
        self.assertEqual(
            {"status": "included", **{
                key: parent[key]
                for key in ("record_set_id", "revision", "content_hash")
            }},
            current["parent_reference"],
        )
        parent_versions = {item["schema_version"] for item in parent["schema_members"]}
        current_versions = {item["schema_version"] for item in current["schema_members"]}
        self.assertEqual(
            {
                "application-capability-description-v0",
                "operation-request-v7",
                "operation-result-v7",
            },
            current_versions - parent_versions,
        )

    def test_description_contains_no_host_or_evidence_inflation(self):
        encoded = core.canonical_json(self.description)
        for prohibited in (
            str(ROOT),
            "/tmp/",
            "timestamp",
            "device-tested",
            "real-time-tested",
            "audible-tested",
            "release-ready",
        ):
            self.assertNotIn(prohibited, encoded)


if __name__ == "__main__":
    unittest.main()
