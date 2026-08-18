from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.ai_authoring import SonicAuthoringService  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    core,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.mcp_server import (  # noqa: E402
    EXPECTED_PROJECT_TOOL_NAMES,
    EXPECTED_TOOL_NAMES,
    SchussMcpAdapter,
)
from packages.schuss_core.native_kernel import (  # noqa: E402
    NativeKernelError,
    validate_program,
)
from packages.schuss_core.project_cli import (  # noqa: E402
    project_init_request,
    project_profile_fork_request,
)
from packages.schuss_core.product_cli import build_plan_request  # noqa: E402
from packages.schuss_core.project_service import ProjectError, ProjectService  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/ai-sonic-authoring-v1.json"
RECORD_SET_LOCATOR = "contracts/record-sets/ai-sonic-authoring-v1.json"


class InjectedFailure(RuntimeError):
    pass


def _ref(record: dict, id_field: str) -> dict:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _request(operation: str, payload: dict) -> dict:
    return {
        "schema_version": "schuss-operation-request-v13",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "payload": payload,
    }


def _intent() -> dict:
    return {
        "objective": "A precise oscillator with a vivid, distinctive edge",
        "function": "sound-sources",
        "required_capabilities": [],
        "desired_character": ["distinctive", "vivid"],
        "priorities": {"accuracy": 95, "interest": 90, "quality": 100},
        "novelty_preference": "prefer-distinctive",
    }


def _native_specification(expected_project_reference: dict) -> dict:
    return {
        "expected_project_reference": copy.deepcopy(expected_project_reference),
        "display_name": "Project Sine",
        "aliases": ["Sonic Sine"],
        "intent": _intent(),
        "interface": {
            "ports": [
                {
                    "key": "trigger",
                    "display_label": "Trigger",
                    "direction": "inlet",
                    "rate": "event",
                    "semantic_role": "trigger",
                    "unit": "boolean",
                },
                {
                    "key": "wave",
                    "display_label": "Wave",
                    "direction": "outlet",
                    "rate": "audio",
                    "semantic_role": "audio",
                    "unit": "normalized",
                },
            ],
            "parameters": [
                {
                    "key": "frequency",
                    "display_label": "Frequency",
                    "unit": "hertz",
                    "minimum": "20",
                    "maximum": "20000",
                    "default": "440",
                }
            ],
        },
        "realization": {
            "form": "native-kernel",
            "instructions": [
                {
                    "instruction_id": "kernel-instruction-000001",
                    "operation": "oscillator-sine",
                    "inputs": [{"kind": "parameter", "key": "frequency"}],
                }
            ],
            "outputs": [
                {
                    "port_key": "wave",
                    "source": {
                        "kind": "instruction",
                        "instruction_id": "kernel-instruction-000001",
                    },
                }
            ],
        },
        "provenance": "ai-authored",
    }


def _compound_specification(
    expected_project_reference: dict, contract_reference: dict
) -> dict:
    return {
        "expected_project_reference": copy.deepcopy(expected_project_reference),
        "display_name": "Project Saw Wrapper",
        "aliases": [],
        "intent": _intent(),
        "interface": {
            "ports": [
                {
                    "key": "wave",
                    "display_label": "Wave",
                    "direction": "outlet",
                    "rate": "audio",
                    "semantic_role": "audio",
                    "unit": "normalized",
                }
            ],
            "parameters": [],
        },
        "realization": {
            "form": "transparent-compound",
            "nodes": [
                {
                    "node_key": "saw",
                    "contract_reference": copy.deepcopy(contract_reference),
                    "parameter_values": [
                        {"facet_id": "component-parameter-000001", "value": "-24"}
                    ],
                    "attribute_values": [],
                }
            ],
            "connections": [],
            "mappings": [
                {
                    "public_kind": "port",
                    "public_key": "wave",
                    "target": {
                        "node_key": "saw",
                        "facet_id": "component-port-000002",
                    },
                }
            ],
        },
        "provenance": "ai-authored",
    }


def _governed_hashes(workspace: Path) -> dict[str, str]:
    return {
        path.relative_to(workspace).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(workspace.rglob("*"))
        if path.is_file() and ".schuss" not in path.parts
    }


class AiSonicAuthoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(
            repository_root=ROOT,
            record_set_path=RECORD_SET,
        )
        cls.graph = next(
            item
            for item in cls.context.records["graphs"]
            if item["graph_id"] == "schuss-graph-000006" and item["revision"] == 1
        )
        cls.instrument = next(
            item
            for item in cls.context.records["instruments"]
            if item["instrument_id"] == "schuss-instrument-000005"
            and item["revision"] == 1
        )
        cls.build_request = next(
            item
            for item in cls.context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000005"
            and item["revision"] == 1
        )
        cls.saw_contract = next(
            item
            for item in cls.context.records["contracts"]
            if item["component_contract_id"] == "schuss-component-contract-000012"
            and item["revision"] == 1
        )

    def _initialize(
        self, workspace: Path, **service_options: object
    ) -> tuple[ProjectService, dict]:
        service = ProjectService(
            workspace,
            repository_root=ROOT,
            initial_context=self.context,
            **service_options,
        )
        initialized = dispatch_operation(
            project_init_request(
                "schuss-project-910026",
                {
                    "reference": copy.deepcopy(self.context.record_set_reference),
                    "portable_locator": RECORD_SET_LOCATOR,
                },
                _ref(self.graph, "graph_id"),
                [_ref(self.instrument, "instrument_id")],
                [_ref(self.build_request, "build_request_id")],
            ),
            service.context,
            project_service=service,
        )
        self.assertEqual("success", initialized["status"], initialized["diagnostics"])
        return service, initialized["value"]["project"]

    def _initialize_and_fork(
        self, workspace: Path
    ) -> tuple[ProjectService, dict]:
        service, project = self._initialize(workspace)
        forked = dispatch_operation(
            project_profile_fork_request(
                _ref(project, "project_id"),
                _ref(self.graph, "graph_id"),
                _ref(self.instrument, "instrument_id"),
                _ref(self.build_request, "build_request_id"),
            ),
            service.context,
            project_service=service,
        )
        self.assertEqual("success", forked["status"], forked["diagnostics"])
        return service, forked["value"]

    def test_generated_contracts_capabilities_and_sonic_policy_are_closed(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "tools/contracts/generate_ai_sonic_authoring_records.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        description = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v7",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "application.describe",
                "payload": {"scope": "selected-context"},
            },
            self.context,
        )
        self.assertEqual("success", description["status"])
        self.assertEqual("application-capability-description-v6", description["value"]["schema_version"])
        self.assertEqual(35, len(description["value"]["operations"]))

        planned = dispatch_operation(
            _request(
                "sonic.intent.plan",
                {"intent": _intent(), "maximum_existing_candidates": 8},
            ),
            self.context,
        )
        self.assertEqual("success", planned["status"], planned["diagnostics"])
        policy = planned["value"]["optimization_policy"]
        self.assertEqual("hard-gate", policy["validity"])
        self.assertEqual("absent", policy["cost_objective"])
        self.assertEqual("prohibited", policy["existing-object-shortcut"])
        self.assertEqual(
            ["existing-object", "transparent-compound", "native-kernel"],
            [item["lane"] for item in planned["value"]["lanes"]],
        )
        for candidate in planned["value"]["lanes"][0]["candidates"]:
            self.assertEqual("not-evaluated", candidate["sonic_fidelity"])
            self.assertEqual("not-evaluated", candidate["sonic_interest"])
            self.assertEqual("not-evaluated", candidate["sonic_quality"])
        invalid_function = dispatch_operation(
            _request(
                "sonic.intent.plan",
                {
                    "intent": {**_intent(), "function": "model-invented-category"},
                    "maximum_existing_candidates": 8,
                },
            ),
            self.context,
        )
        self.assertEqual("invalid", invalid_function["status"])
        self.assertEqual(
            "OPERATION_REQUEST_INVALID",
            invalid_function["diagnostics"][0]["code"],
        )

    def test_native_draft_audition_preview_accept_and_reload(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schuss-ai-native-") as temporary:
            workspace = Path(temporary) / "project"
            service, forked = self._initialize_and_fork(workspace)
            authoring = SonicAuthoringService(service)
            project_reference = _ref(forked["project"], "project_id")
            before = _governed_hashes(workspace)

            created = dispatch_operation(
                _request(
                    "authoring.draft.create",
                    _native_specification(project_reference),
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", created["status"], created["diagnostics"])
            self.assertEqual("not-written", created["value"]["persistence_status"])
            draft_id = created["value"]["draft_id"]
            inspected = dispatch_operation(
                _request("authoring.draft.inspect", {"draft_id": draft_id}),
                self.context,
                authoring_service=authoring,
            )
            definition = inspected["value"]["object_definition"]
            trigger = next(
                item
                for item in definition["component_contract"]["ports"]
                if item["semantic_key"] == "trigger"
            )
            frequency = definition["component_contract"]["parameters"][0]
            self.assertEqual(
                {
                    "status": "optional",
                    "absence_behavior": "no-event",
                    "default_value": "0",
                },
                trigger["port_type"]["optionality"],
            )
            self.assertEqual("float", frequency["representation"]["kind"])
            noncanonical = copy.deepcopy(definition)
            noncanonical["component_contract"]["ports"].reverse()
            object_schema = self.context.schemas["project_object_definition"]
            noncanonical["content_hash"] = core.record_content_hash(
                noncanonical, object_schema
            )
            with self.assertRaises(ProjectError) as canonical_error:
                service.preview_object_change(noncanonical, None)
            self.assertEqual(
                "PROJECT_OBJECT_CONTRACT_INVALID", canonical_error.exception.code
            )
            invalid_kernel = copy.deepcopy(definition)
            kernel = invalid_kernel["realization"]["kernel"]
            kernel["instructions"][0]["inputs"] = [
                {
                    "kind": "instruction",
                    "instruction_id": "kernel-instruction-000001",
                }
            ]
            kernel_schema = self.context.schemas["native_kernel"]
            kernel["content_hash"] = core.record_content_hash(kernel, kernel_schema)
            binding = invalid_kernel["implementation_binding"]
            binding["realization"]["kernel_reference"]["content_hash"] = kernel[
                "content_hash"
            ]
            binding_schema = self.context.schemas["binding_versions"][
                "implementation-binding-v3"
            ]
            binding["content_hash"] = core.record_content_hash(
                binding, binding_schema
            )
            invalid_kernel["content_hash"] = core.record_content_hash(
                invalid_kernel, object_schema
            )
            with self.assertRaises(ProjectError) as kernel_error:
                service.preview_object_change(invalid_kernel, None)
            self.assertEqual(
                "PROJECT_OBJECT_KERNEL_INVALID", kernel_error.exception.code
            )

            audition = {
                "sample_rate": 48000,
                "frame_count": 4800,
                "stimuli": [],
            }
            first_evaluation = dispatch_operation(
                _request(
                    "authoring.draft.evaluate",
                    {"draft_id": draft_id, "audition": audition},
                ),
                self.context,
                authoring_service=authoring,
            )
            second_evaluation = dispatch_operation(
                _request(
                    "authoring.draft.evaluate",
                    {"draft_id": draft_id, "audition": audition},
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", first_evaluation["status"])
            self.assertEqual(first_evaluation["value"], second_evaluation["value"])
            artifact = first_evaluation["value"]["artifact"]
            artifact_path = workspace / artifact["portable_cache_locator"]
            self.assertTrue(artifact_path.is_file())
            self.assertEqual(
                artifact["content_hash"],
                "sha256:" + hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            )
            changed_evaluation = dispatch_operation(
                _request(
                    "authoring.draft.evaluate",
                    {
                        "draft_id": draft_id,
                        "audition": {**audition, "sample_rate": 44100},
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertNotEqual(
                artifact["content_hash"],
                changed_evaluation["value"]["artifact"]["content_hash"],
            )

            previewed = dispatch_operation(
                _request(
                    "authoring.change.preview",
                    {
                        "draft_id": draft_id,
                        "expected_project_reference": project_reference,
                        "placement": {
                            "kind": "add-node",
                            "parameter_values": [
                                {"parameter_key": "frequency", "value": "220"}
                            ],
                        },
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", previewed["status"], previewed["diagnostics"])
            self.assertEqual("not-written", previewed["value"]["persistence_status"])
            self.assertEqual(before, _governed_hashes(workspace))

            preview = previewed["value"]
            mismatch = dispatch_operation(
                _request(
                    "authoring.change.accept",
                    {
                        "preview_id": preview["preview_id"],
                        "expected_project_reference": project_reference,
                        "confirmation_fingerprint": "sha256:" + "0" * 64,
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("conflict", mismatch["status"])
            self.assertEqual(before, _governed_hashes(workspace))

            accepted = dispatch_operation(
                _request(
                    "authoring.change.accept",
                    {
                        "preview_id": preview["preview_id"],
                        "expected_project_reference": project_reference,
                        "confirmation_fingerprint": preview[
                            "confirmation_fingerprint"
                        ],
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", accepted["status"], accepted["diagnostics"])
            self.assertEqual("project-v1", accepted["value"]["project"]["schema_version"])
            self.assertEqual("written", accepted["value"]["persistence_status"])
            self.assertEqual("not-run", accepted["value"]["object_definition"]["evidence"]["target_lowering"])
            retained_host_evidence = accepted["value"]["object_definition"][
                "evidence"
            ]["host_evaluation"]
            self.assertEqual("passed", retained_host_evidence["status"])
            self.assertEqual(
                changed_evaluation["value"]["artifact"]["content_hash"],
                retained_host_evidence["artifact"]["content_hash"],
            )
            self.assertNotEqual(before, _governed_hashes(workspace))

            plan = dispatch_operation(
                build_plan_request(
                    _ref(accepted["value"]["build_request"], "build_request_id")
                ),
                self.context,
                project_service=service,
            )
            self.assertNotEqual("success", plan["status"])
            self.assertTrue(
                any(
                    diagnostic["code"]
                    in {
                        "COMPILER_IMPLEMENTATION_UNRESOLVED",
                        "COMPILER_BINDING_UNSUPPORTED",
                        "IMPLEMENTATION_SELECTION_UNRESOLVED",
                        "TARGET_IMPLEMENTATION_UNRESOLVED",
                    }
                    for diagnostic in plan["diagnostics"]
                ),
                plan["diagnostics"],
            )

            replay = dispatch_operation(
                _request(
                    "authoring.change.accept",
                    {
                        "preview_id": preview["preview_id"],
                        "expected_project_reference": project_reference,
                        "confirmation_fingerprint": preview[
                            "confirmation_fingerprint"
                        ],
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("conflict", replay["status"])
            self.assertEqual("AUTHORING_PREVIEW_CONSUMED", replay["diagnostics"][0]["code"])

            reloaded_service = ProjectService(workspace, repository_root=ROOT)
            reloaded_authoring = SonicAuthoringService(reloaded_service)
            listed = reloaded_authoring.list_objects()
            self.assertEqual(1, listed["object_count"])
            self.assertEqual("Project Sine", listed["objects"][0]["display_name"])
            inspected_object = reloaded_authoring.inspect_object(
                listed["objects"][0]["object_reference"]
            )
            self.assertEqual(
                "native-kernel",
                inspected_object["object_definition"]["realization"]["form"],
            )

            read_only_adapter = SchussMcpAdapter(self.context)
            project_adapter = SchussMcpAdapter(
                self.context,
                project_service=reloaded_service,
                authoring_service=reloaded_authoring,
            )
            self.assertEqual(
                EXPECTED_TOOL_NAMES,
                tuple(item["name"] for item in read_only_adapter.tools),
            )
            self.assertEqual(
                EXPECTED_PROJECT_TOOL_NAMES,
                tuple(item["name"] for item in project_adapter.tools),
            )
            annotations = {
                item["name"]: item["annotations"] for item in project_adapter.tools
            }
            self.assertFalse(
                annotations["schuss.authoring.change.accept"]["readOnlyHint"]
            )
            self.assertFalse(
                annotations["schuss.authoring.change.accept"]["idempotentHint"]
            )
            self.assertTrue(
                annotations["schuss.project.objects.list"]["readOnlyHint"]
            )
            tool_result = project_adapter.call_tool(
                "schuss.project.objects.list", {}
            )
            self.assertFalse(tool_result["isError"])
            self.assertEqual(
                1,
                tool_result["structuredContent"]["value"]["object_count"],
            )
            planned_tool = project_adapter.call_tool(
                "schuss.sonic.intent.plan",
                {
                    "intent": {**_intent(), "objective": "Project Sine"},
                    "maximum_existing_candidates": 20,
                },
            )
            existing_lane = planned_tool["structuredContent"]["value"]["lanes"][0]
            project_candidates = [
                item
                for item in existing_lane["candidates"]
                if item["origin"] == "project-local"
            ]
            self.assertEqual(1, len(project_candidates))
            self.assertEqual("Project Sine", project_candidates[0]["display_name"])

    def test_transparent_compound_accepts_and_stale_preview_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schuss-ai-compound-") as temporary:
            workspace = Path(temporary) / "project"
            service, project = self._initialize(workspace)
            now = [0.0]
            authoring = SonicAuthoringService(
                service, clock=lambda: now[0], draft_ttl_seconds=1.0
            )
            project_reference = _ref(project, "project_id")
            invalid_compound = _compound_specification(
                project_reference,
                _ref(self.saw_contract, "component_contract_id"),
            )
            invalid_compound["realization"]["connections"] = [
                {
                    "source": {
                        "node_key": "absent",
                        "facet_id": "component-port-000002",
                    },
                    "destination": {
                        "node_key": "saw",
                        "facet_id": "component-port-000001",
                    },
                }
            ]
            rejected_topology = dispatch_operation(
                _request("authoring.draft.create", invalid_compound),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("invalid", rejected_topology["status"])
            self.assertEqual(
                "AUTHORING_COMPOUND_CONNECTION_NODE_UNRESOLVED",
                rejected_topology["diagnostics"][0]["code"],
            )
            compound = dispatch_operation(
                _request(
                    "authoring.draft.create",
                    _compound_specification(
                        project_reference,
                        _ref(self.saw_contract, "component_contract_id"),
                    ),
                ),
                self.context,
                authoring_service=authoring,
            )
            native = dispatch_operation(
                _request(
                    "authoring.draft.create",
                    _native_specification(project_reference),
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", compound["status"], compound["diagnostics"])
            self.assertEqual("success", native["status"], native["diagnostics"])
            foreign_reference = copy.deepcopy(project_reference)
            foreign_reference["project_id"] = "schuss-project-999999"
            foreign = dispatch_operation(
                _request(
                    "authoring.draft.create",
                    _native_specification(foreign_reference),
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("conflict", foreign["status"])
            self.assertEqual(
                "AUTHORING_PROJECT_STALE", foreign["diagnostics"][0]["code"]
            )
            compound_preview = dispatch_operation(
                _request(
                    "authoring.change.preview",
                    {
                        "draft_id": compound["value"]["draft_id"],
                        "expected_project_reference": project_reference,
                        "placement": {"kind": "library-only"},
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            native_preview = dispatch_operation(
                _request(
                    "authoring.change.preview",
                    {
                        "draft_id": native["value"]["draft_id"],
                        "expected_project_reference": project_reference,
                        "placement": {"kind": "library-only"},
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", compound_preview["status"])
            self.assertEqual("success", native_preview["status"])

            first = compound_preview["value"]
            accepted = dispatch_operation(
                _request(
                    "authoring.change.accept",
                    {
                        "preview_id": first["preview_id"],
                        "expected_project_reference": project_reference,
                        "confirmation_fingerprint": first[
                            "confirmation_fingerprint"
                        ],
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", accepted["status"], accepted["diagnostics"])
            definition = accepted["value"]["object_definition"]
            self.assertEqual("transparent-compound", definition["realization"]["form"])
            self.assertEqual(
                "depends-on-exact-internal-bindings",
                compound["value"]["validation"]["target_eligibility"],
            )

            stale = native_preview["value"]
            rejected = dispatch_operation(
                _request(
                    "authoring.change.accept",
                    {
                        "preview_id": stale["preview_id"],
                        "expected_project_reference": project_reference,
                        "confirmation_fingerprint": stale[
                            "confirmation_fingerprint"
                        ],
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("conflict", rejected["status"])
            self.assertEqual("PROJECT_REVISION_STALE", rejected["diagnostics"][0]["code"])
            self.assertEqual(1, authoring.list_objects()["object_count"])
            now[0] = 2.0
            expired_preview = dispatch_operation(
                _request(
                    "authoring.change.accept",
                    {
                        "preview_id": stale["preview_id"],
                        "expected_project_reference": project_reference,
                        "confirmation_fingerprint": stale[
                            "confirmation_fingerprint"
                        ],
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("unresolved", expired_preview["status"])
            self.assertEqual(
                "AUTHORING_PREVIEW_EXPIRED",
                expired_preview["diagnostics"][0]["code"],
            )
            expired = dispatch_operation(
                _request(
                    "authoring.draft.inspect",
                    {"draft_id": native["value"]["draft_id"]},
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("unresolved", expired["status"])
            self.assertEqual(
                "AUTHORING_DRAFT_EXPIRED", expired["diagnostics"][0]["code"]
            )

    def test_native_kernel_rejects_forward_edges_and_wrong_arity(self) -> None:
        interface = {
            "ports": [
                {
                    "key": "wave",
                    "display_label": "Wave",
                    "direction": "outlet",
                    "rate": "audio",
                    "semantic_role": "audio",
                    "unit": "normalized",
                }
            ],
            "parameters": [],
        }
        forward = {
            "input_keys": [],
            "parameter_keys": [],
            "instructions": [
                {
                    "instruction_id": "kernel-instruction-000001",
                    "operation": "abs",
                    "inputs": [
                        {
                            "kind": "instruction",
                            "instruction_id": "kernel-instruction-000002",
                        }
                    ],
                },
                {
                    "instruction_id": "kernel-instruction-000002",
                    "operation": "noise",
                    "inputs": [],
                },
            ],
            "outputs": [
                {
                    "port_key": "wave",
                    "source": {
                        "kind": "instruction",
                        "instruction_id": "kernel-instruction-000001",
                    },
                }
            ],
        }
        with self.assertRaises(NativeKernelError) as forward_error:
            validate_program(forward, interface)
        self.assertEqual("NATIVE_KERNEL_DATAFLOW_INVALID", forward_error.exception.code)

        wrong_arity = copy.deepcopy(forward)
        wrong_arity["instructions"] = [
            {
                "instruction_id": "kernel-instruction-000001",
                "operation": "abs",
                "inputs": [],
            }
        ]
        with self.assertRaises(NativeKernelError) as arity_error:
            validate_program(wrong_arity, interface)
        self.assertEqual("NATIVE_KERNEL_ARITY_INVALID", arity_error.exception.code)

        excessive = copy.deepcopy(forward)
        excessive["instructions"] = [
            {
                "instruction_id": "kernel-instruction-000001",
                "operation": "abs",
                "inputs": [{"kind": "literal", "value": "1000000001"}],
            }
        ]
        with self.assertRaises(NativeKernelError) as numeric_error:
            validate_program(excessive, interface)
        self.assertEqual(
            "NATIVE_KERNEL_NUMERIC_LIMIT_EXCEEDED", numeric_error.exception.code
        )

    def test_interrupted_object_accept_recovers_the_complete_prior_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schuss-ai-recovery-") as temporary:
            workspace = Path(temporary) / "project"
            armed = False
            fired: list[str] = []

            def interrupt(label: str) -> None:
                if armed and label == "after:immutable-1.publish" and not fired:
                    fired.append(label)
                    raise InjectedFailure(label)

            service, project = self._initialize(
                workspace,
                failure_injector=interrupt,
                pid_provider=lambda: 424242,
                process_alive=lambda pid: False,
            )
            authoring = SonicAuthoringService(service)
            project_reference = _ref(project, "project_id")
            created = dispatch_operation(
                _request(
                    "authoring.draft.create",
                    _native_specification(project_reference),
                ),
                self.context,
                authoring_service=authoring,
            )
            previewed = dispatch_operation(
                _request(
                    "authoring.change.preview",
                    {
                        "draft_id": created["value"]["draft_id"],
                        "expected_project_reference": project_reference,
                        "placement": {"kind": "library-only"},
                    },
                ),
                self.context,
                authoring_service=authoring,
            )
            self.assertEqual("success", previewed["status"])
            baseline = _governed_hashes(workspace)
            preview = previewed["value"]
            armed = True
            with self.assertRaises(InjectedFailure):
                dispatch_operation(
                    _request(
                        "authoring.change.accept",
                        {
                            "preview_id": preview["preview_id"],
                            "expected_project_reference": project_reference,
                            "confirmation_fingerprint": preview[
                                "confirmation_fingerprint"
                            ],
                            "write_intent": "explicit",
                        },
                    ),
                    self.context,
                    authoring_service=authoring,
                )
            self.assertEqual(["after:immutable-1.publish"], fired)
            recovered = ProjectService(
                workspace,
                repository_root=ROOT,
                process_alive=lambda pid: False,
            ).load()
            self.assertEqual(project, recovered.manifest)
            self.assertEqual("recovered-prior", recovered.recovery_status)
            self.assertEqual(baseline, _governed_hashes(workspace))


if __name__ == "__main__":
    unittest.main()
