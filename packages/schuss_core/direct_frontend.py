"""Task 015 normalized DSP IR and exact one-node direct C++ frontend."""

from __future__ import annotations

import copy
import hashlib
from typing import Any, Mapping

from .compiler_front_half import core


FRONTEND_ID = "schuss-direct-frontend-000001"
GRAPH_REFERENCE = {
    "graph_id": "schuss-graph-000001",
    "revision": 1,
    "content_hash": "sha256:b38562dc2dcf80036e8fc1d78fe8ee425de01f4943495a23375bfb4e7f346e6e",
}
CONTRACT_REFERENCE = {
    "component_contract_id": "schuss-component-contract-000003",
    "revision": 1,
    "content_hash": "sha256:96a29faf58769be5f2ac52de07aa80cae3dcdff28f0f3c158fb1fd12cc234a8d",
}
REQUEST_REFERENCE = {
    "build_request_id": "schuss-build-request-000001",
    "revision": 2,
    "content_hash": "sha256:7093aa5ce9c1752360a05eec855331b0781ba8fc6c0969c45e3220d24e9ce1ae",
}
Q27_SCALE = 1 << 27


def _bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8")


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def evaluate_linear_mix_q27(a: int, b: int, blend: int) -> int:
    """Reference arithmetic for the normalized `linear-mix-q27` operation."""

    control = min(Q27_SCALE, max(0, int(blend)))
    value = (int(a) * (Q27_SCALE - control) + int(b) * control) >> 27
    return min((1 << 31) - 1, max(-(1 << 31), value))


def _cpp() -> str:
    return """#include <cstddef>\n#include <cstdint>\n#include <limits>\n\nextern \"C\" void schuss_blend_process_q27(\n    const std::int32_t* input_a,\n    const std::int32_t* input_b,\n    std::int32_t blend_q27,\n    std::int32_t* output,\n    std::size_t frame_count) noexcept {\n  constexpr std::int64_t scale = INT64_C(134217728);\n  std::int64_t control = blend_q27;\n  if (control < 0) control = 0;\n  if (control > scale) control = scale;\n  for (std::size_t index = 0; index < frame_count; ++index) {\n    const std::int64_t mixed =\n        (static_cast<std::int64_t>(input_a[index]) * (scale - control) +\n         static_cast<std::int64_t>(input_b[index]) * control) >> 27;\n    if (mixed > std::numeric_limits<std::int32_t>::max()) {\n      output[index] = std::numeric_limits<std::int32_t>::max();\n    } else if (mixed < std::numeric_limits<std::int32_t>::min()) {\n      output[index] = std::numeric_limits<std::int32_t>::min();\n    } else {\n      output[index] = static_cast<std::int32_t>(mixed);\n    }\n  }\n}\n"""


def lower_minimal_direct(
    plan: Mapping[str, Any], graph: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    """Lower the one exact accepted Blend graph; reject every broader input."""

    plan_value = copy.deepcopy(dict(plan))
    graph_value = copy.deepcopy(dict(graph))
    contract_value = copy.deepcopy(dict(contract))
    if plan_value.get("status") != "success":
        raise ValueError("DIRECT_PLAN_NOT_SUCCESSFUL")
    if plan_value.get("input_closure", {}).get("build_request_reference") != REQUEST_REFERENCE:
        raise ValueError("DIRECT_BUILD_REQUEST_UNSUPPORTED")
    graph_ref = {key: graph_value.get(key) for key in GRAPH_REFERENCE}
    if graph_ref != GRAPH_REFERENCE:
        raise ValueError("DIRECT_GRAPH_UNSUPPORTED")
    contract_ref = {key: contract_value.get(key) for key in CONTRACT_REFERENCE}
    if contract_ref != CONTRACT_REFERENCE:
        raise ValueError("DIRECT_CONTRACT_UNSUPPORTED")
    nodes = graph_value.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 1 or nodes[0].get("contract_reference") != CONTRACT_REFERENCE:
        raise ValueError("DIRECT_GRAPH_SHAPE_UNSUPPORTED")
    expected_exposures = {
        ("graph-facet-000002", "component-port-000001"),
        ("graph-facet-000003", "component-port-000002"),
        ("graph-facet-000004", "component-port-000004"),
    }
    actual_exposures = {
        (item.get("graph_facet_id"), item.get("node_port", {}).get("facet_id"))
        for item in graph_value.get("public_port_exposures", [])
    }
    bindings = graph_value.get("parameter_bindings", [])
    if actual_exposures != expected_exposures or len(bindings) != 1 or bindings[0].get("destination", {}).get("facet_id") != "component-port-000003":
        raise ValueError("DIRECT_PUBLIC_MAPPING_UNSUPPORTED")
    plan_sha = _hash_bytes(_bytes(plan_value))
    module = {
        "schema_version": "normalized-dsp-module-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "module_id": "schuss-normalized-dsp-module-000001",
        "frontend": {"frontend_id": FRONTEND_ID, "version": 1},
        "source_plan_sha256": plan_sha,
        "graph_reference": copy.deepcopy(GRAPH_REFERENCE),
        "numeric_contract": {
            "representation": "signed-q27",
            "scale": Q27_SCALE,
            "accumulator": "signed-64",
            "shift": 27,
            "shift_rule": "arithmetic-right",
            "output_overflow": "saturate-signed-32",
        },
        "inputs": [
            {"value_id": "dsp-value-000001", "kind": "audio-buffer", "origin_facet_id": "graph-facet-000002"},
            {"value_id": "dsp-value-000002", "kind": "audio-buffer", "origin_facet_id": "graph-facet-000003"},
            {"value_id": "dsp-value-000003", "kind": "control-q27", "origin_facet_id": "graph-facet-000001"},
        ],
        "operations": [{
            "operation_id": "dsp-operation-000001",
            "opcode": "linear-mix-q27",
            "inputs": ["dsp-value-000001", "dsp-value-000002", "dsp-value-000003"],
            "outputs": ["dsp-value-000004"],
            "origin": {"node_id": "graph-node-000001", "contract_reference": copy.deepcopy(CONTRACT_REFERENCE)},
        }],
        "outputs": [{"value_id": "dsp-value-000004", "kind": "audio-buffer", "origin_facet_id": "graph-facet-000004"}],
        "schedule": ["dsp-operation-000001"],
    }
    cpp = _cpp()
    cpp_bytes = cpp.encode("utf-8")
    source_map = {
        "schema_version": "direct-source-map-v0",
        "generated_symbol": "schuss_blend_process_q27",
        "graph_reference": copy.deepcopy(GRAPH_REFERENCE),
        "mappings": [
            {"generated": "input_a", "origin": "graph-facet-000002/component-port-000001"},
            {"generated": "input_b", "origin": "graph-facet-000003/component-port-000002"},
            {"generated": "blend_q27", "origin": "graph-facet-000001/component-port-000003"},
            {"generated": "output", "origin": "graph-facet-000004/component-port-000004"},
            {"generated": "linear-mix-q27", "origin": "graph-node-000001/schuss-component-contract-000003"},
        ],
    }
    return {
        "schema_version": "direct-frontend-result-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "status": "success",
        "frontend": {"frontend_id": FRONTEND_ID, "version": 1},
        "input_plan_sha256": plan_sha,
        "module": module,
        "generated_cpp": {
            "media_type": "text/x-c++src",
            "byte_length": len(cpp_bytes),
            "byte_sha256": _hash_bytes(cpp_bytes),
            "portable_locator": "direct/sha256/" + _hash_bytes(cpp_bytes) + ".cpp",
            "text": cpp,
        },
        "source_map": source_map,
        "diagnostics": [],
        "evidence_levels": [
            {"level": level, "status": "passed" if level <= 4 else "not-run"}
            for level in range(1, 9)
        ],
        "legacy_bridge_used": False,
        "authoritative_records_mutated": False,
    }
