#!/usr/bin/env python3
"""Bounded executable backend for the exact Task 011B Gills graph."""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Iterable, Mapping, Sequence

import task009_backend as task009
import validator_core as core


GRAPH_ID = "schuss-graph-000002"
GRAPH_REVISION = 1
GRAPH_HASH = "sha256:ea98b4cbf1ecb58d70338e5aaaef02385a6ede707b9b78bbc90fac09d53c7460"
INSTRUMENT_ID = "schuss-instrument-000002"
INSTRUMENT_REVISION = 1
INSTRUMENT_HASH = "sha256:d20e0f108397987a4b102fab35afc8fb00a42acfa33d48522226de2c343e7adb"
PROCEDURE_ID = "schuss-procedure-000002"
PROCEDURE_HASH = "sha256:86954dd767c3d49e396f25313f467d843b4d168d24e317e435fd61737c111985"

FACTORY_COMMIT = "25d2615ed5233546d617017666a4ab1e60a8c506"
CONTRIB_COMMIT = "2e994478c0ab15fb1daa3bb4b86c88e22952d99c"
CONTRIB_SOURCE_PATH = "objects/drj/seq/stepseq_16_pitch.axo"
CONTRIB_SOURCE_SHA256 = "45336e472f1e15a295617b0f4fd1e31e83203acf9ae37a067125459f66022b0f"

PROBE_STAGES = task009.PROBE_STAGES
ARTIFACT_ORDER = task009.ARTIFACT_ORDER
ARTIFACT_STEM = "gills-slice"

NODE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "node_id": "graph-node-000001",
        "contract": ["schuss-component-contract-000004", "sha256:987acb05ac5334d69a87af584395d3d9728a2e566d8f932d7767176324701877"],
        "binding_id": "schuss-implementation-000039",
        "binding_r1_hash": "sha256:1ebc80f66077124dfd1c2a9fa1b59327e0f4a1603a7f795889da5666c4ba6248",
        "binding_file": "lfo.json",
        "form": "generated-legacy-object",
        "legacy_type": "lfo/square",
        "legacy_uuid": "de6909eb64db13af5b43f979a4c130024b3a4793",
        "instance": "schuss_lfo",
        "source_id": "axoloti-factory",
        "source_path": "objects/lfo/square.axo",
        "source_sha256": "d417bd0e455e28c6af9988732f6406b2d3e3c94eea9338f76ab61df926463051",
    },
    {
        "node_id": "graph-node-000002",
        "contract": ["schuss-component-contract-000005", "sha256:09e0ccff23775d0b01b8792aa92f370fb3f741d7baa541eb92123bcfcbf871e1"],
        "binding_id": "schuss-implementation-000040",
        "binding_r1_hash": "sha256:7d0a525eedd5ca8bacf61a89c67042340f9732619710da0f69ceaf165e45daf3",
        "binding_file": "counter.json",
        "form": "generated-legacy-object",
        "legacy_type": "logic/counter",
        "legacy_uuid": "7a141ba82230e54e5f5cd12da5dbe5a74ba854a5",
        "instance": "schuss_counter",
        "source_id": "axoloti-factory",
        "source_path": "objects/logic/counter.axo",
        "source_sha256": "fb61bbfeb9504cee015b093888fb8c6da237d12b760a5e6ebdb9b160447bd9e1",
    },
    {
        "node_id": "graph-node-000003",
        "contract": ["schuss-component-contract-000006", "sha256:f1aa523d117d6516a72bbb7ab70c36399abf34d2dbfe6a27bf1d14e8a6e58023"],
        "binding_id": "schuss-implementation-000041",
        "binding_r1_hash": "sha256:b7a19f4b0b87adc12fedc17346b2af99a50219ba320e191431f50a7a43b11d64",
        "binding_file": "sequencer.json",
        "form": "legacy-native-object",
        "legacy_type": "drj/seq/stepseq_4_pitch",
        "legacy_uuid": "aa0848ea71ef03f595a32f0c14bff9cab097294701",
        "instance": "schuss_seq",
        "source_id": "axoloti-contrib",
        "source_path": CONTRIB_SOURCE_PATH,
        "source_sha256": CONTRIB_SOURCE_SHA256,
    },
    {
        "node_id": "graph-node-000004",
        "contract": ["schuss-component-contract-000007", "sha256:6c3bdbe18269794e885c392b3cd40d90c445ed0b207ab4dedb79abe8c28ec410"],
        "binding_id": "schuss-implementation-000007",
        "binding_r1_hash": "sha256:3bd25ea0d236141a8d6e615b4328f9c9e7f5637ab05f762586708e7c7e1beff0",
        "binding_file": "sine.json",
        "form": "generated-legacy-object",
        "legacy_type": "osc/sine",
        "legacy_uuid": "6e094045cca76a9dbf7ebfa72e44e4700d2b3ba",
        "instance": "schuss_sine_a",
        "source_id": "axoloti-factory",
        "source_path": "objects/osc/sine.axo",
        "source_sha256": "bf865e647b2eea2ebe1ef852038994f2dea8f1e8b8e60e1133e1d580a3402a4b",
    },
    {
        "node_id": "graph-node-000005",
        "contract": ["schuss-component-contract-000007", "sha256:6c3bdbe18269794e885c392b3cd40d90c445ed0b207ab4dedb79abe8c28ec410"],
        "binding_id": "schuss-implementation-000007",
        "binding_r1_hash": "sha256:3bd25ea0d236141a8d6e615b4328f9c9e7f5637ab05f762586708e7c7e1beff0",
        "binding_file": "sine.json",
        "form": "generated-legacy-object",
        "legacy_type": "osc/sine",
        "legacy_uuid": "6e094045cca76a9dbf7ebfa72e44e4700d2b3ba",
        "instance": "schuss_sine_b",
        "source_id": "axoloti-factory",
        "source_path": "objects/osc/sine.axo",
        "source_sha256": "bf865e647b2eea2ebe1ef852038994f2dea8f1e8b8e60e1133e1d580a3402a4b",
    },
    {
        "node_id": "graph-node-000006",
        "contract": [task009.CONTRACT_ID, task009.CONTRACT_HASH],
        "binding_id": task009.BINDING_ID,
        "binding_r1_hash": task009.BINDING_R1_HASH,
        "binding_file": None,
        "form": "generated-legacy-object",
        "legacy_type": "mix/xfade",
        "legacy_uuid": task009.XFADE_UUID,
        "instance": "schuss_xfade",
        "source_id": "axoloti-factory",
        "source_path": "objects/mix/xfade.axo",
        "source_sha256": "8169f5ec39eabe8f76bf5025ab2c68df0bed531c0c8aeb8c51bba3307859e361",
    },
    {
        "node_id": "graph-node-000007",
        "contract": ["schuss-component-contract-000008", "sha256:b4a4f03947665ff8d100371427d886b7217fcc68199f3b164f8c1ca37cdd1c77"],
        "binding_id": "schuss-implementation-000015",
        "binding_r1_hash": "sha256:d52a9f134ab1ad2595d728d7fc6a3adb759fdcee3b24d5a56d5328d276a7205f",
        "binding_file": "filter.json",
        "form": "generated-legacy-object",
        "legacy_type": "filter/multimode svf m",
        "legacy_uuid": "71d5f8b2131b691d591a9a9ee28771309f8938d",
        "instance": "schuss_filter",
        "source_id": "axoloti-factory",
        "source_path": "objects/filter/multimode svf m.axo",
        "source_sha256": "e73239cd072b9dc63debd2ec95a32ec0bf79ae1be1754336a1d5928d4e8af057",
    },
    {
        "node_id": "graph-node-000008",
        "contract": ["schuss-component-contract-000009", "sha256:179c1526ed2bd6d9ad1c6fbfc9caa7abc21f479bef50cf93c8599b5817ca8718"],
        "binding_id": "schuss-implementation-000004",
        "binding_r1_hash": "sha256:e72dd177c4984b525782b0395c96cdc816907b1bf0731902acc729c1c49062bd",
        "binding_file": "output.json",
        "form": "generated-legacy-object",
        "legacy_type": "audio/out stereo",
        "legacy_uuid": "a1ca7a567f535acc21055669829101d3ee7f0189",
        "instance": "schuss_output",
        "source_id": "axoloti-factory",
        "source_path": "objects/audio/out stereo.axo",
        "source_sha256": "d8392b522b54be3bdfa5e671975a2a675ac494e9d1dc8bee2586dcd1eaecc7e3",
    },
)

NEW_BINDING_IDS = tuple(sorted({
    spec["binding_id"] for spec in NODE_SPECS
    if spec["binding_id"] != task009.BINDING_ID
}))


@dataclasses.dataclass(frozen=True)
class ExecutionConfig:
    repository_root: Path
    content_store: Path
    java: Path
    javac: Path
    arm_bin: Path
    contrib_checkout: Path

    def normalized(self) -> "ExecutionConfig":
        return ExecutionConfig(*(
            Path(value).resolve() for value in dataclasses.astuple(self)
        ))

    def task009_config(self) -> task009.ExecutionConfig:
        return task009.ExecutionConfig(
            self.repository_root,
            self.content_store,
            self.java,
            self.javac,
            self.arm_bin,
        )


def _reference(identifier: str, revision: int, content_hash: str, field: str) -> dict[str, Any]:
    return {field: identifier, "revision": revision, "content_hash": content_hash}


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8")


def _require_equal(actual: Any, expected: Any, code: str, subject: str) -> None:
    if actual != expected:
        raise task009.Task009BackendError(
            code, "backend-lowering", subject, "exact Task 011C closure mismatch"
        )


def verify_execution_config(config: ExecutionConfig) -> ExecutionConfig:
    config = config.normalized()
    task009.verify_execution_config(config.task009_config())
    source = config.contrib_checkout / CONTRIB_SOURCE_PATH
    if not source.is_file() or core.sha256_file(source) != CONTRIB_SOURCE_SHA256:
        raise task009.Task009BackendError(
            "TASK011C_CONTRIB_SOURCE_MISMATCH",
            "backend-lowering",
            CONTRIB_SOURCE_PATH,
            "pinned contrib source byte mismatch",
        )
    completed = subprocess.run(
        ["/usr/bin/git", "rev-parse", "HEAD^{commit}"],
        cwd=config.contrib_checkout,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode or completed.stdout.decode("ascii").strip() != CONTRIB_COMMIT:
        raise task009.Task009BackendError(
            "TASK011C_CONTRIB_COMMIT_MISMATCH",
            "backend-lowering",
            "axoloti-contrib",
            "pinned contrib checkout commit mismatch",
        )
    return config


def load_exact_inputs(config: ExecutionConfig) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    graph_path = config.repository_root / "contracts/task011b/graphs/four-step-dual-sine.json"
    graph = core.load_json(graph_path)
    _require_equal(
        _reference(graph["graph_id"], graph["revision"], graph["content_hash"], "graph_id"),
        _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "TASK011C_GRAPH_STALE",
        GRAPH_ID,
    )
    bindings: dict[str, dict[str, Any]] = {}
    for spec in NODE_SPECS:
        path = spec["binding_file"]
        if path is None:
            record_path = config.repository_root / "contracts/task009/crossfader-mixed-legacy-v0-r2.json"
            record = core.load_json(record_path)
            expected_revision = 2
            expected_hash = "sha256:7afa2bd29077c10c2f9e9313d7d803c0092c6e059aee89f7f4de2b230ed688cf"
        else:
            record_path = config.repository_root / "contracts/task011b/implementation-bindings" / path
            record = core.load_json(record_path)
            expected_revision = 1
            expected_hash = spec["binding_r1_hash"]
        _require_equal(
            _reference(record["implementation_id"], record["revision"], record["content_hash"], "implementation_id"),
            _reference(spec["binding_id"], expected_revision, expected_hash, "implementation_id"),
            "TASK011C_BINDING_STALE",
            spec["binding_id"],
        )
        bindings[spec["binding_id"]] = record
    return graph, bindings


def validate_probe_input(probe: Mapping[str, Any]) -> None:
    binding = probe.get("binding_reference", {})
    binding_id = binding.get("implementation_id")
    spec = next((item for item in NODE_SPECS if item["binding_id"] == binding_id), None)
    if spec is None or binding_id == task009.BINDING_ID:
        raise task009.Task009BackendError(
            "TASK011C_PROBE_INPUT_REJECTED",
            "backend-lowering",
            str(probe.get("conformance_probe_id", "probe")),
            "probe does not name one exact new Task 011B binding",
        )
    expected = {
        "candidate_state": "candidate-under-test",
        "binding_reference": _reference(binding_id, 1, spec["binding_r1_hash"], "implementation_id"),
        "contract_reference": _reference(spec["contract"][0], 1, spec["contract"][1], "component_contract_id"),
        "graph_reference": _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "environment_reference": _reference(
            task009.ENVIRONMENT_ID, 1, task009.ENVIRONMENT_HASH,
            "prerequisite_environment_id",
        ),
        "procedure_reference": _reference(PROCEDURE_ID, 1, PROCEDURE_HASH, "procedure_id"),
        "requested_stages": list(PROBE_STAGES),
        "execution_authorization": "task-011c-authorized",
        "production_selection_authority": False,
    }
    for key, value in expected.items():
        _require_equal(
            probe.get(key), value, "TASK011C_PROBE_INPUT_REJECTED",
            str(probe.get("conformance_probe_id", "probe")),
        )


def axp_bytes() -> bytes:
    lines = (
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<patch-1.0 appVersion="1.0.12">',
        '   <obj type="lfo/square" uuid="de6909eb64db13af5b43f979a4c130024b3a4793" name="schuss_lfo" x="14" y="28">',
        '      <params>',
        '         <frac32.s.map name="pitch" value="-48.0"/>',
        '      </params>',
        '      <attribs/>',
        '   </obj>',
        '   <obj type="logic/counter" uuid="7a141ba82230e54e5f5cd12da5dbe5a74ba854a5" name="schuss_counter" x="154" y="28">',
        '      <params>',
        '         <int32 name="maximum" value="4"/>',
        '      </params>',
        '      <attribs/>',
        '   </obj>',
        '   <obj type="drj/seq/stepseq_4_pitch" uuid="aa0848ea71ef03f595a32f0c14bff9cab097294701" name="schuss_seq" x="294" y="28">',
        '      <params>',
        '         <frac32.s.map name="p1" value="0.0"/>',
        '         <frac32.s.map name="p2" value="5.0"/>',
        '         <frac32.s.map name="p3" value="7.0"/>',
        '         <frac32.s.map name="p4" value="12.0"/>',
        '      </params>',
        '      <attribs/>',
        '   </obj>',
        '   <obj type="osc/sine" uuid="6e094045cca76a9dbf7ebfa72e44e4700d2b3ba" name="schuss_sine_a" x="448" y="14">',
        '      <params>',
        '         <frac32.s.map name="pitch" value="-24.0"/>',
        '      </params>',
        '      <attribs/>',
        '   </obj>',
        '   <obj type="osc/sine" uuid="6e094045cca76a9dbf7ebfa72e44e4700d2b3ba" name="schuss_sine_b" x="448" y="126">',
        '      <params>',
        '         <frac32.s.map name="pitch" value="-23.875"/>',
        '      </params>',
        '      <attribs/>',
        '   </obj>',
        f'   <obj type="patch/inlet f" uuid="{task009.INLET_F_UUID}" name="schuss_blend" x="448" y="238">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        f'   <obj type="mix/xfade" uuid="{task009.XFADE_UUID}" name="schuss_xfade" x="602" y="70">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        '   <obj type="filter/multimode svf m" uuid="71d5f8b2131b691d591a9a9ee28771309f8938d" name="schuss_filter" x="756" y="70">',
        '      <params>',
        '         <frac32.s.map name="pitch" value="24.0"/>',
        '         <frac32.u.map name="reso" value="0.125"/>',
        '      </params>',
        '      <attribs/>',
        '   </obj>',
        '   <obj type="audio/out stereo" uuid="a1ca7a567f535acc21055669829101d3ee7f0189" name="schuss_output" x="924" y="70">',
        '      <params/>',
        '      <attribs/>',
        '   </obj>',
        '   <nets>',
        '      <net><source obj="schuss_lfo" outlet="wave"/><dest obj="schuss_counter" inlet="trig"/></net>',
        '      <net><source obj="schuss_counter" outlet="o"/><dest obj="schuss_seq" inlet="step"/></net>',
        '      <net><source obj="schuss_seq" outlet="out"/><dest obj="schuss_sine_a" inlet="pitch"/><dest obj="schuss_sine_b" inlet="pitch"/></net>',
        '      <net><source obj="schuss_sine_a" outlet="wave"/><dest obj="schuss_xfade" inlet="i1"/></net>',
        '      <net><source obj="schuss_sine_b" outlet="wave"/><dest obj="schuss_xfade" inlet="i2"/></net>',
        '      <net><source obj="schuss_blend" outlet="inlet"/><dest obj="schuss_xfade" inlet="c"/></net>',
        '      <net><source obj="schuss_xfade" outlet="o"/><dest obj="schuss_filter" inlet="in"/></net>',
        '      <net><source obj="schuss_filter" outlet="lp"/><dest obj="schuss_output" inlet="left"/><dest obj="schuss_output" inlet="right"/></net>',
        '   </nets>',
        '   <settings>',
        '      <subpatchmode>normal</subpatchmode>',
        '   </settings>',
        '   <notes><![CDATA[]]></notes>',
        '</patch-1.0>',
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _binding_reference_for_node(
    spec: Mapping[str, Any], binding_references: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    reference = binding_references.get(str(spec["binding_id"]))
    if reference is None:
        raise task009.Task009BackendError(
            "TASK011C_BINDING_MISSING",
            "backend-lowering",
            str(spec["node_id"]),
            "exact node binding is absent",
        )
    return copy.deepcopy(dict(reference))


def resolution_plan(
    graph: Mapping[str, Any],
    binding_records: Mapping[str, Mapping[str, Any]],
    binding_references: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    graph_nodes = {item["node_id"]: item for item in graph["nodes"]}
    nodes = []
    for spec in NODE_SPECS:
        binding_record = binding_records[spec["binding_id"]]
        nodes.append({
            "node_id": spec["node_id"],
            "contract_reference": _reference(
                spec["contract"][0], 1, spec["contract"][1],
                "component_contract_id",
            ),
            "binding_reference": _binding_reference_for_node(spec, binding_references),
            "realization_form": spec["form"],
            "legacy_object": {
                "type": spec["legacy_type"],
                "uuid": spec["legacy_uuid"],
                "instance_name": spec["instance"],
                "source_id": spec["source_id"],
                "source_path": spec["source_path"],
                "source_sha256": spec["source_sha256"],
            },
            "facet_mappings": copy.deepcopy(binding_record["facet_mappings"]),
            "parameter_values": copy.deepcopy(graph_nodes[spec["node_id"]]["parameter_values"]),
        })
    return {
        "schema_version": "task011c-resolution-plan-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_request_graph_reference": _reference(
            GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"
        ),
        "nodes": nodes,
        "connections": copy.deepcopy(graph["connections"]),
        "graph_parameter_bindings": copy.deepcopy(graph["parameter_bindings"]),
        "legacy_public_boundary": [
            ["graph-facet-000001", "schuss_blend", "inlet"]
        ],
        "implicit_discovery": False,
        "unsupported_fallback": False,
    }


def source_map(
    graph: Mapping[str, Any],
    binding_records: Mapping[str, Mapping[str, Any]],
    binding_references: Mapping[str, Mapping[str, Any]],
    generated: bytes,
) -> dict[str, Any]:
    lines = generated.decode("utf-8").splitlines()
    graph_nodes = {item["node_id"]: item for item in graph["nodes"]}
    regions = []
    node_entries = []
    for spec in NODE_SPECS:
        generated_name = spec["instance"].replace("_", "__")
        matches = [index + 1 for index, line in enumerate(lines) if generated_name in line]
        if not matches:
            raise task009.Task009BackendError(
                "TASK011C_SOURCE_MAP_REGION_MISSING",
                "artifact-generation",
                spec["instance"],
                "generated source contains no stable region for emitted object",
            )
        regions.append({
            "node_id": spec["node_id"],
            "legacy_instance": spec["instance"],
            "first_line": min(matches),
            "last_line": max(matches),
        })
        binding = binding_records[spec["binding_id"]]
        node_entries.append({
            "node_id": spec["node_id"],
            "contract_reference": _reference(
                spec["contract"][0], 1, spec["contract"][1],
                "component_contract_id",
            ),
            "binding_reference": _binding_reference_for_node(spec, binding_references),
            "legacy_object_uuid": spec["legacy_uuid"],
            "axp_location": f"/patch-1.0/obj[@name='{spec['instance']}']",
            "facet_mappings": copy.deepcopy(binding["facet_mappings"]),
            "parameter_values": copy.deepcopy(
                graph_nodes[spec["node_id"]]["parameter_values"]
            ),
        })
    blend_matches = [
        index + 1 for index, line in enumerate(lines) if "schuss__blend" in line
    ]
    if not blend_matches:
        raise task009.Task009BackendError(
            "TASK011C_SOURCE_MAP_REGION_MISSING",
            "artifact-generation",
            "schuss_blend",
            "generated source contains no public blend region",
        )
    regions.append({
        "graph_facet_id": "graph-facet-000001",
        "legacy_instance": "schuss_blend",
        "first_line": min(blend_matches),
        "last_line": max(blend_matches),
    })
    return {
        "schema_version": "task011c-source-map-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "graph_reference": _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "nodes": node_entries,
        "connections": [
            {
                "connection_id": connection["connection_id"],
                "axp_net_index": (1, 2, 3, 3, 4, 5, 7, 8, 8)[index - 1],
                "source": copy.deepcopy(connection["source"]),
                "destination": copy.deepcopy(connection["destination"]),
            }
            for index, connection in enumerate(graph["connections"], 1)
        ],
        "public_parameter_binding": {
            "binding_id": "graph-binding-000001",
            "graph_facet_id": "graph-facet-000001",
            "legacy_instance": "schuss_blend",
            "axp_location": "/patch-1.0/obj[@name='schuss_blend']",
        },
        "generated_cpp_sha256": hashlib.sha256(generated).hexdigest(),
        "generated_regions": regions,
        "diagnostic_ids": [],
    }


def _compile_bridge(
    config: ExecutionConfig,
    output_root: Path,
    source_root: Path,
    classes_root: Path,
) -> tuple[str, list[dict[str, Any]]]:
    repository = config.repository_root
    bridge_classes = output_root / "work/bridge-classes"
    bridge_classes.mkdir(parents=True)
    classpath = task009._classpath(
        source_root,
        classes_root,
        repository / "evidence/task-009-prerequisite-v0/java-classpath-members.json",
    )
    sources = [
        repository / "legacy/ksoloti-bridge/src/main/java/axoloti/object/SchussObjectAccess.java",
        repository / "legacy/ksoloti-bridge/src/main/java/axoloti/SchussPatchAccess.java",
        repository / "legacy/ksoloti-bridge/src/main/java/generatedobjects/SchussExactGeneratedObjects.java",
        repository / "legacy/ksoloti-bridge/src/main/java/org/schuss/legacy/ksoloti/StableJson.java",
        repository / "legacy/ksoloti-bridge/src/main/java/org/schuss/legacy/ksoloti/GillsSliceBridge.java",
    ]
    arguments = [
        str(config.javac), "-g:none", "-encoding", "UTF-8", "-source", "21",
        "-target", "21", "-cp", classpath, "-d", str(bridge_classes),
        *(str(path) for path in sources),
    ]
    task009._run(
        arguments,
        output_root,
        task009._tool_environment(output_root, config.arm_bin),
        "artifact-generation",
        "TASK011C_BRIDGE_COMPILE_FAILED",
        "legacy/ksoloti-bridge",
    )
    portable = task009._portable_command(
        "javac",
        [
            "javac", "-g:none", "-encoding", "UTF-8", "-source", "21",
            "-target", "21", "-cp", "authenticated-java-closure",
            "-d", "work/bridge-classes",
            *(path.relative_to(repository).as_posix() for path in sources),
        ],
        ".",
    )
    return os.pathsep.join([str(bridge_classes), classpath]), [portable]


def _run_bridge(
    config: ExecutionConfig,
    output_root: Path,
    source_root: Path,
    factory_root: Path,
    contrib_root: Path,
    runtime_root: Path,
    classpath: str,
    axp: Path,
    generated: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    arguments = [
        str(config.java), "-XX:-UsePerfData", "-Djava.awt.headless=true",
        "-Dfile.encoding=UTF-8", "-Duser.language=en", "-Duser.country=US",
        "-Duser.timezone=UTC", f"-Duser.home={output_root / 'work/home'}",
        f"-Djava.io.tmpdir={output_root / 'work/tmp'}", "-cp", classpath,
        "org.schuss.legacy.ksoloti.GillsSliceBridge",
        f"--axp={axp}", f"--output={generated}",
        f"--factory-root={factory_root}", f"--contrib-root={contrib_root}",
        f"--patcher-root={source_root}", f"--runtime-root={runtime_root}",
    ]
    completed = task009._run(
        arguments,
        output_root,
        task009._tool_environment(output_root, config.arm_bin),
        "artifact-generation",
        "TASK011C_JAVA_GENERATION_FAILED",
        "gills-slice-bridge",
    )
    if completed.stderr:
        raise task009.Task009BackendError(
            "TASK011C_BRIDGE_STDERR_INVALID",
            "artifact-generation",
            "gills-slice-bridge",
            "bridge emitted unstable or ambient stderr output",
        )
    try:
        result = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise task009.Task009BackendError(
            "TASK011C_BRIDGE_OUTPUT_INVALID",
            "artifact-generation",
            "gills-slice-bridge",
            "bridge did not emit one canonical JSON value",
        ) from error
    if (
        result.get("status") != "success"
        or result.get("axp_sha256") != core.sha256_file(axp)
        or result.get("registered_object_count") != 8
        or result.get("resolved_instance_count") != 9
    ):
        raise task009.Task009BackendError(
            "TASK011C_BRIDGE_RESULT_MISMATCH",
            "artifact-generation",
            "gills-slice-bridge",
            "bridge result does not name the exact input/output closure",
        )
    portable = task009._portable_command(
        "java",
        [
            "java", "-XX:-UsePerfData", "-Djava.awt.headless=true",
            "-Dfile.encoding=UTF-8", "-Duser.language=en", "-Duser.country=US",
            "-Duser.timezone=UTC", "-Duser.home=work/home",
            "-Djava.io.tmpdir=work/tmp", "-cp", "authenticated-java-closure",
            "org.schuss.legacy.ksoloti.GillsSliceBridge",
            "--axp=proof/build/gills-slice.axp",
            "--output=proof/build/gills-slice.cpp",
            "--factory-root=factory-capsule", "--contrib-root=contrib-capsule",
            "--patcher-root=source-capsule", "--runtime-root=runtime",
        ],
        ".",
    )
    return result, portable


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise task009.Task009BackendError(
            "TASK011C_OUTPUT_ALREADY_EXISTS",
            "artifact-generation",
            path.name,
            "exact output already exists",
        )
    path.write_bytes(payload)


def execute_exact_slice(
    binding_references: Mapping[str, Mapping[str, Any]],
    config: ExecutionConfig,
    output_root: Path,
    failure_stage: str | None = None,
) -> task009.ExecutionOutcome:
    output_root = Path(output_root).resolve()
    if output_root.exists():
        raise task009.Task009BackendError(
            "TASK011C_OUTPUT_ROOT_NOT_FRESH",
            "backend-lowering",
            "output-root",
            "output root must not exist",
        )
    config = verify_execution_config(config)
    graph, binding_records = load_exact_inputs(config)
    expected_ids = {spec["binding_id"] for spec in NODE_SPECS}
    if set(binding_references) != expected_ids:
        raise task009.Task009BackendError(
            "TASK011C_BINDING_SET_INVALID",
            "backend-lowering",
            GRAPH_ID,
            "exact eight-node binding set differs",
        )
    output_root.mkdir(parents=True)
    stages = {stage: "not-run" for stage in PROBE_STAGES}
    facts: list[task009.ArtifactFact] = []
    commands: list[dict[str, Any]] = []
    bridge_result: dict[str, Any] | None = None
    resources: dict[str, Any] | None = None
    current_stage = "backend-lowering"
    try:
        if failure_stage == current_stage:
            raise task009.Task009BackendError(
                "TASK011C_INJECTED_LOWERING_FAILURE",
                current_stage,
                GRAPH_ID,
                "injected exact-slice lowering failure",
            )
        source_root = output_root / "source-capsule"
        factory_root = output_root / "factory-capsule"
        classes_root = output_root / "class-capsule"
        task009._safe_extract(
            config.content_store / "sha256" / task009.PATCHER_ARCHIVE_SHA256,
            source_root,
        )
        task009._safe_extract(
            config.content_store / "sha256" / task009.FACTORY_ARCHIVE_SHA256,
            factory_root,
        )
        task009._safe_extract(
            config.content_store / "sha256" / task009.CLASS_ARCHIVE_SHA256,
            classes_root,
        )
        contrib_root = output_root / "contrib-capsule"
        contrib_path = contrib_root / CONTRIB_SOURCE_PATH
        contrib_path.parent.mkdir(parents=True)
        shutil.copyfile(config.contrib_checkout / CONTRIB_SOURCE_PATH, contrib_path)
        if core.sha256_file(contrib_path) != CONTRIB_SOURCE_SHA256:
            raise task009.Task009BackendError(
                "TASK011C_CONTRIB_COPY_MISMATCH",
                current_stage,
                CONTRIB_SOURCE_PATH,
                "fresh-root contrib source differs",
            )
        runtime_root = output_root / "runtime"
        (runtime_root / "build").mkdir(parents=True)
        shutil.copyfile(
            config.content_store / "sha256" / task009.FIRMWARE_BIN_SHA256,
            runtime_root / "build/ksoloti.bin",
        )
        plan_path = output_root / "proof/build/resolution-plan.json"
        _write_bytes(
            plan_path,
            _canonical_bytes(
                resolution_plan(graph, binding_records, binding_references)
            ),
        )
        facts.append(task009._retain(
            output_root,
            "resolution-plan",
            plan_path,
            "application/vnd.schuss.resolution-plan+json",
            "implementation-resolution",
        ))
        stages[current_stage] = "success"

        current_stage = "artifact-generation"
        if failure_stage == current_stage:
            raise task009.Task009BackendError(
                "TASK011C_INJECTED_JAVA_FAILURE",
                current_stage,
                "gills-slice-bridge",
                "injected exact-slice Java-generation failure",
            )
        axp_path = output_root / "proof/build/gills-slice.axp"
        generated_path = output_root / "proof/build/gills-slice.cpp"
        _write_bytes(axp_path, axp_bytes())
        classpath, compile_commands = _compile_bridge(
            config, output_root, source_root, classes_root
        )
        commands.extend(compile_commands)
        bridge_result, bridge_command = _run_bridge(
            config,
            output_root,
            source_root,
            factory_root,
            contrib_root,
            runtime_root,
            classpath,
            axp_path,
            generated_path,
        )
        commands.append(bridge_command)
        generated = generated_path.read_bytes()
        if hashlib.sha256(generated).hexdigest() != bridge_result["generated_cpp_sha256"]:
            raise task009.Task009BackendError(
                "TASK011C_GENERATED_SOURCE_HASH_MISMATCH",
                current_stage,
                "gills-slice.cpp",
                "generated source differs from bridge result",
            )
        source_map_path = output_root / "proof/build/source-map.json"
        _write_bytes(
            source_map_path,
            _canonical_bytes(
                source_map(
                    graph, binding_records, binding_references, generated
                )
            ),
        )
        facts.extend([
            task009._retain(
                output_root,
                "legacy-boundary-patch",
                axp_path,
                "application/vnd.ksoloti.axp+xml",
                current_stage,
            ),
            task009._retain(
                output_root,
                "source-map",
                source_map_path,
                "application/vnd.schuss.source-map+json",
                current_stage,
            ),
            task009._retain(
                output_root,
                "generated-cpp",
                generated_path,
                "text/x-c++src",
                current_stage,
            ),
        ])
        stages[current_stage] = "success"

        current_stage = "target-compile-link"
        if failure_stage == current_stage:
            raise task009.Task009BackendError(
                "TASK011C_INJECTED_ARM_FAILURE",
                current_stage,
                "gills-slice.cpp",
                "injected exact-slice ARM compile/link failure",
            )
        object_path, elf_path, map_path, resources, arm_commands = task009._arm_build(
            config.task009_config(),
            output_root,
            source_root,
            generated_path,
            artifact_stem=ARTIFACT_STEM,
        )
        resources = copy.deepcopy(resources)
        resources["schema_version"] = "task011c-static-resource-facts-v0"
        commands.extend(arm_commands)
        facts.extend([
            task009._retain(
                output_root, "arm-object", object_path,
                "application/x-elf-object", current_stage,
            ),
            task009._retain(
                output_root, "target-executable", elf_path,
                "application/x-elf", current_stage,
            ),
            task009._retain(
                output_root, "link-map", map_path, "text/plain", current_stage,
            ),
        ])
        stages[current_stage] = "success"
        ordered = tuple(sorted(
            facts, key=lambda item: ARTIFACT_ORDER.index(item.kind)
        ))
        task009._reject_path_leaks(output_root, ordered)
        return task009.ExecutionOutcome(
            "success", ordered, tuple(stages.items()), (), bridge_result,
            tuple(commands), resources, None,
        )
    except task009.Task009BackendError as error:
        stages[current_stage] = "failed"
        terminal = False
        for stage in PROBE_STAGES:
            if stage == current_stage:
                terminal = True
            elif terminal:
                stages[stage] = "not-run"
        diagnostic = error.as_probe_diagnostic()
        diagnostic["code"] = diagnostic["code"].replace("TASK009_", "TASK011C_")
        return task009.ExecutionOutcome(
            "failed", tuple(facts), tuple(stages.items()), (diagnostic,),
            bridge_result, tuple(commands), resources, error,
        )


def validate_invocation_input(
    invocation: Mapping[str, Any],
    schema: Mapping[str, Any],
    build_request_schema: Mapping[str, Any],
    expected_binding_references: Mapping[str, Mapping[str, Any]],
    expected_build_request: Mapping[str, Any],
) -> None:
    closed_schema = task009.invocation_schema_closure(schema, build_request_schema)
    errors = core.schema_errors(dict(invocation), closed_schema, closed_schema)
    request_value = invocation.get("accepted_build_request")
    if isinstance(request_value, dict):
        errors.extend(core.schema_errors(
            request_value,
            dict(build_request_schema),
            dict(build_request_schema),
            "$.accepted_build_request",
        ))
    if errors:
        raise task009.Task009BackendError(
            "TASK011C_INVOCATION_SCHEMA_INVALID",
            "backend-lowering",
            "schuss-backend-invocation-input-v1",
            "backend invocation violates its public schema",
        )
    if invocation.get("status") != "ready-for-backend-invocation":
        raise task009.Task009BackendError(
            "TASK011C_INVOCATION_NOT_READY",
            "backend-lowering",
            "schuss-backend-invocation-input-v1",
            "backend invocation is not ready",
        )
    request = invocation["accepted_build_request"]
    _require_equal(
        request, dict(expected_build_request), "TASK011C_BUILD_REQUEST_STALE",
        str(request.get("build_request_id", "build-request")),
    )
    _require_equal(
        request["graph_reference"],
        _reference(GRAPH_ID, GRAPH_REVISION, GRAPH_HASH, "graph_id"),
        "TASK011C_GRAPH_UNSUPPORTED",
        str(request["build_request_id"]),
    )
    expected_selected = sorted(
        [
            {
                "node_id": spec["node_id"],
                "binding_reference": copy.deepcopy(
                    dict(expected_binding_references[spec["binding_id"]])
                ),
            }
            for spec in NODE_SPECS
        ],
        key=lambda item: item["node_id"],
    )
    _require_equal(
        invocation.get("selected_bindings"), expected_selected,
        "TASK011C_BINDING_NOT_SELECTED", str(request["build_request_id"]),
    )
    traces = invocation.get("resolution_traces", [])
    if len(traces) != len(NODE_SPECS):
        raise task009.Task009BackendError(
            "TASK011C_RESOLUTION_TRACE_INVALID",
            "backend-lowering",
            str(request["build_request_id"]),
            "exact Task 011C resolution trace count differs",
        )
    expected_by_node = {item["node_id"]: item["binding_reference"] for item in expected_selected}
    for trace in traces:
        node_id = trace.get("node_id")
        reference = expected_by_node.get(node_id)
        candidates = [
            candidate for candidate in trace.get("candidates", [])
            if candidate.get("binding_reference") == reference
        ]
        clean_candidates = [
            candidate for candidate in candidates
            if candidate.get("exclusion_reasons") == []
            and candidate.get("unresolved_reasons") == []
        ]
        if (
            reference is None
            or trace.get("status") != "selected"
            or trace.get("selected_binding_reference") != reference
            or len(clean_candidates) != 1
        ):
            raise task009.Task009BackendError(
                "TASK011C_RESOLUTION_TRACE_INVALID",
                "backend-lowering",
                str(node_id),
                "exact selected trace is absent or uncertain",
            )
    _require_equal(
        invocation["boundary"],
        {
            "completed_stage": "implementation-resolution",
            "next_stage": "backend-lowering",
            "next_stage_status": "not-run",
            "executable_handler_status": "absent",
        },
        "TASK011C_INVOCATION_BOUNDARY_INVALID",
        str(request["build_request_id"]),
    )


def run_backend_handler(
    invocation: Mapping[str, Any],
    invocation_schema: Mapping[str, Any],
    build_request_schema: Mapping[str, Any],
    expected_binding_references: Mapping[str, Mapping[str, Any]],
    expected_build_request: Mapping[str, Any],
    config: ExecutionConfig,
    output_root: Path,
    failure_stage: str | None = None,
) -> task009.ExecutionOutcome:
    validate_invocation_input(
        invocation,
        invocation_schema,
        build_request_schema,
        expected_binding_references,
        expected_build_request,
    )
    return execute_exact_slice(
        expected_binding_references,
        config,
        output_root,
        failure_stage=failure_stage,
    )


def compare_deterministic_outcomes(
    first: task009.ExecutionOutcome,
    second: task009.ExecutionOutcome,
) -> dict[str, Any]:
    first_hashes = {
        item.kind: [item.byte_sha256, item.byte_length] for item in first.artifacts
    }
    second_hashes = {
        item.kind: [item.byte_sha256, item.byte_length] for item in second.artifacts
    }
    if (
        first.status != "success"
        or second.status != "success"
        or first_hashes != second_hashes
    ):
        raise task009.Task009BackendError(
            "TASK011C_FRESH_ROOT_NONDETERMINISM",
            "target-compile-link",
            GRAPH_ID,
            "fresh-root artifact identities differ",
        )
    return {
        "schema_version": "task011c-fresh-root-equality-v0",
        "status": "passed",
        "artifacts": dict(sorted(first_hashes.items())),
        "command_vectors_equal": first.command_vectors == second.command_vectors,
        "bridge_results_equal": first.bridge_result == second.bridge_result,
        "resource_facts_equal": first.resource_facts == second.resource_facts,
    }
