from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "tools/instrument_lab"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from common import ContractError, canonical_json, load_json  # noqa: E402
from new_prototype import render_tree, validate_spec  # noqa: E402
from validate_prototype import validate_consumer, validate_topology  # noqa: E402
from validate_repository import validate_repository  # noqa: E402

CINDER = ROOT / "research/prototypes/cinderwheel"
SMOKE_SPEC = ROOT / "research/prototype_support/instrument_lab/fixtures/smoke-spec.json"
TEMPLATES = ROOT / "research/prototype_support/instrument_lab/templates"
NEGATIVE = ROOT / "research/prototype_support/instrument_lab/fixtures/contracts/negative-cases.json"


class InstrumentLabContractTest(unittest.TestCase):
    def test_live_repository_and_derived_artifacts_are_current(self) -> None:
        validate_repository(ROOT)

    def test_generation_is_byte_deterministic(self) -> None:
        spec = validate_spec(load_json(SMOKE_SPEC))
        self.assertEqual(render_tree(TEMPLATES, spec), render_tree(TEMPLATES, copy.deepcopy(spec)))

    def test_declared_negative_contract_cases_fail_closed(self) -> None:
        fixture = load_json(NEGATIVE)
        self.assertEqual(fixture["schema_version"], "instrument-lab-negative-contract-fixtures-v1")
        observed: dict[str, str] = {}
        for case in fixture["cases"]:
            mutation = case["mutation"]
            try:
                if mutation.startswith("forbidden-topology") or mutation == "duplicate-topology-role":
                    self._mutated_topology(mutation)
                else:
                    self._mutated_index(mutation)
            except ContractError as exc:
                observed[case["id"]] = exc.code
            else:
                self.fail(f"negative case passed: {case['id']}")
            self.assertEqual(observed[case["id"]], case["expected_code"])
        self.assertEqual(len(observed), len(fixture["cases"]))

    def _mutated_index(self, mutation: str) -> None:
        document = load_json(CINDER / "prototype-index.json")
        if mutation == "add-index-field":
            document["unexpected"] = True
        elif mutation == "canonical-prototype-id":
            document["prototype_id"] = "schuss-instrument-000001"
        elif mutation == "absolute-authority":
            document["authorities"]["control_map"]["path"] = "/tmp/control-map.json"
        elif mutation == "latest-authority":
            document["authorities"]["control_map"]["path"] = "research/latest/control-map.json"
        elif mutation == "invalid-hash":
            document["authorities"]["control_map"]["sha256"] = "bad"
        elif mutation == "missing-authority":
            del document["authorities"]["proposal"]
        else:
            self.fail(f"unknown mutation {mutation}")
        with tempfile.TemporaryDirectory() as temporary:
            consumer = Path(temporary)
            (consumer / "prototype-index.json").write_text(canonical_json(document), encoding="utf-8")
            validate_consumer(ROOT, consumer, write=False, check_derived=False)

    def _mutated_topology(self, mutation: str) -> None:
        document = load_json(CINDER / "dsp-topology.json")
        if mutation == "forbidden-topology-host":
            document["nodes"][0]["responsibility"] = "instantiate a JUCE class"
        elif mutation == "forbidden-topology-provider":
            document["nodes"][0]["responsibility"] = "select provider identity"
        elif mutation == "duplicate-topology-role":
            document["nodes"][1]["local_role"] = document["nodes"][0]["local_role"]
        else:
            self.fail(f"unknown mutation {mutation}")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dsp-topology.json"
            path.write_text(canonical_json(document), encoding="utf-8")
            validate_topology(path, "cinderwheel")


if __name__ == "__main__":
    unittest.main()
