import copy
import hashlib
import io
import json
import locale
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core import catalog_projection
from packages.schuss_core.cli import run as run_cli
from packages.schuss_core.product_cli import (
    catalog_inspect_request,
    catalog_search_request,
    completion_script,
    resolve_locator,
)

import validator_core as core


CLI = ROOT / "bin/schuss"
RECORD_SET = ROOT / "contracts/record-sets/task011a-catalog-v1.json"
REQUEST_FIXTURE = (
    ROOT / "tools/contracts/tests/fixtures/task011a-catalog-operation-requests.json"
)
GOLDEN_FIXTURE = ROOT / "tools/contracts/tests/fixtures/task011a-cli-golden-hashes.json"
TASK023_GOLDEN_FIXTURE = (
    ROOT / "tools/contracts/tests/fixtures/task023-cli-v2-golden-hashes.json"
)
V1_FIXTURE = ROOT / "tools/contracts/tests/fixtures/task008-operation-requests.json"
OVERLAY = ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json"
CORPUS = ROOT / "contracts/catalog/task011a-corpus-v1.json"


def _digest(value):
    return {
        "byte_length": len(value),
        "byte_sha256": hashlib.sha256(value).hexdigest(),
    }


def _process(arguments, *, input_bytes=b"", cwd=ROOT, environment=None):
    env = os.environ.copy()
    if environment:
        env.update(environment)
    return subprocess.run(
        [str(CLI), *arguments],
        cwd=cwd,
        env=env,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _gui_fixture(request, context):
    return canonical_result_bytes(dispatch_operation(copy.deepcopy(request), context), context)


def _ai_fixture(request, context):
    return canonical_result_bytes(dispatch_operation(copy.deepcopy(request), context), context)


class Task011ACatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.default_context = load_repository_context(ROOT)
        cls.fixtures = core.load_json(REQUEST_FIXTURE)
        cls.projection = cls.context.catalog_projection
        cls.by_family = {
            item["family_reference"]["family_id"]: item
            for item in cls.projection["families"]
        }

    def dispatch(self, name):
        return dispatch_operation(copy.deepcopy(self.fixtures[name]), self.context)

    def test_projection_covers_exact_pilot_and_only_reviewed_additions(self):
        expected_pilot = {f"schuss-family-{index:06d}" for index in range(1, 27)}
        self.assertEqual(
            expected_pilot | {"schuss-family-000027", "schuss-family-000028"},
            set(self.by_family),
        )
        self.assertEqual(
            "497a27d295d0ccda799848ac6fcba245139ca29156f509431b7cb7522d791858",
            hashlib.sha256(OVERLAY.read_bytes()).hexdigest(),
        )
        implementation_ids = {
            value["implementation_id"]
            for family in self.by_family.values()
            for value in family["implementations"]
        }
        self.assertEqual(41, len(implementation_ids))
        self.assertEqual(
            {"schuss-implementation-000039", "schuss-implementation-000040", "schuss-implementation-000041"},
            implementation_ids - {f"schuss-implementation-{index:06d}" for index in range(1, 39)},
        )

    def test_every_phase4a_family_is_exactly_inspectable(self):
        for index in range(1, 27):
            family = self.by_family[f"schuss-family-{index:06d}"]
            result = dispatch_operation(
                catalog_inspect_request(family["family_reference"]), self.context
            )
            self.assertEqual("success", result["status"], index)
            self.assertEqual(family, result["value"]["family"], index)

    def test_slice_identity_review_preserves_four_and_sixteen_step_realizations(self):
        family = self.by_family["schuss-family-000022"]
        implementations = {
            item["implementation_id"]: item for item in family["implementations"]
        }
        self.assertEqual(
            ["legacy-resolved-catalog-v0:object:918"],
            implementations["schuss-implementation-000041"]["observation_references"],
        )
        self.assertEqual(
            ["legacy-resolved-catalog-v0:object:920"],
            implementations["schuss-implementation-000032"]["observation_references"],
        )
        corpus = core.load_json(CORPUS)
        self.assertEqual(7, len(corpus["slice_review"]["roles"]))

    def test_empty_browse_and_all_approved_query_fields(self):
        empty = dispatch_operation(catalog_search_request("", {}), self.context)
        self.assertEqual("success", empty["status"])
        self.assertEqual(28, empty["value"]["total_matches"])
        queries = {
            "schuss-family-000018": "schuss-family-000018",
            "Crossfader": "schuss-family-000018",
            "Xfade": "schuss-family-000018",
            "Interpolates": "schuss-family-000018",
            "crossfade": "schuss-family-000018",
            "crossfade-position": "schuss-family-000018",
        }
        for query, expected in queries.items():
            with self.subTest(query=query):
                result = dispatch_operation(catalog_search_request(query, {}), self.context)
                ids = [item["family_reference"]["family_id"] for item in result["value"]["results"]]
                self.assertIn(expected, ids)

    def test_filter_matrix_and_and_or_semantics(self):
        filters = {
            "function": ["mixing-routing"],
            "abstraction": ["primitive"],
            "form": ["generated-object"],
            "signal_domain": ["stream"],
            "signal_rate": ["audio"],
            "signal_role": ["audio"],
            "capability": ["audio-stream-fixed-q27"],
            "technique": ["crossfade"],
            "readiness": ["compile-proven"],
            "provenance": ["axoloti-factory"],
        }
        result = dispatch_operation(catalog_search_request("", filters), self.context)
        self.assertEqual("success", result["status"])
        self.assertEqual(
            ["schuss-family-000018"],
            [item["family_reference"]["family_id"] for item in result["value"]["results"]],
        )
        filters["function"].append("sound-sources")
        result = dispatch_operation(catalog_search_request("", filters), self.context)
        self.assertEqual("success", result["status"])
        self.assertEqual(1, result["value"]["total_matches"])

    def test_provenance_is_not_function_and_filter_values_are_closed(self):
        accepted = dispatch_operation(
            catalog_search_request("", {"provenance": ["axoloti-factory"]}),
            self.context,
        )
        self.assertEqual("success", accepted["status"])
        self.assertGreater(accepted["value"]["total_matches"], 0)
        rejected = dispatch_operation(
            catalog_search_request("", {"function": ["factory"]}), self.context
        )
        self.assertEqual("invalid", rejected["status"])
        self.assertEqual("CATALOG_FILTER_VALUE_UNSUPPORTED", rejected["diagnostics"][0]["code"])

    def test_signal_capability_and_readiness_are_derived_from_exact_records(self):
        for family in self.by_family.values():
            if family["signal_facets"]:
                self.assertTrue(family["contract_facets_available"])
            for implementation in family["implementations"]:
                states = set(implementation["readiness_states"])
                if "contracted" in states:
                    self.assertTrue(implementation["contract_references"])
                if "bound" in states:
                    self.assertTrue(implementation["binding_references"])
                if "eligible" in states:
                    self.assertTrue(implementation["eligibility_references"])
                if states & {"compile-proven", "device-tested", "real-time-tested", "audible-tested"}:
                    self.assertTrue(implementation["evidence_references"])
        for identifier in (39, 40, 41):
            implementation = next(
                item
                for family in self.by_family.values()
                for item in family["implementations"]
                if item["implementation_id"] == f"schuss-implementation-{identifier:06d}"
            )
            self.assertEqual(["catalogued-only", "unresolved"], implementation["readiness_states"])

    def test_crossfader_exposes_exact_chain_without_level_6_to_8_claims(self):
        result = self.dispatch("catalog_inspect_crossfader")
        self.assertEqual("success", result["status"])
        implementations = {
            item["implementation_id"]: item
            for item in result["value"]["family"]["implementations"]
        }
        mixed = implementations["schuss-implementation-000028"]
        for field in (
            "contract_references",
            "binding_references",
            "eligibility_references",
            "target_references",
            "backend_references",
            "result_references",
            "artifact_references",
            "evidence_references",
        ):
            self.assertTrue(mixed[field], field)
        self.assertEqual(
            ["contracted", "bound", "eligible", "compile-proven", "unresolved"],
            mixed["readiness_states"],
        )
        self.assertFalse(
            {"device-tested", "real-time-tested", "audible-tested"}
            & set(mixed["readiness_states"])
        )

    def test_projection_rejects_stale_exact_input_closure(self):
        corpus = copy.deepcopy(self.context.records["catalog"][0])
        corpus["overlay_source"]["byte_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            catalog_projection.CatalogProjectionError, "content hash mismatch|input closure is stale"
        ):
            catalog_projection.build_catalog_projection(
                corpus=corpus,
                corpus_schema=self.context.schemas["catalog_corpus"],
                projection_schema=self.context.schemas["catalog_projection"],
                overlay=copy.deepcopy(self.context.overlay),
                overlay_sha256=self.context.overlay_sha256,
                observations=copy.deepcopy(self.context.observations),
                records=self.context.records,
                record_set_reference=copy.deepcopy(self.context.record_set_reference),
                core=core,
            )

    def test_successor_schemas_and_v1_bytes_are_preserved(self):
        for path in (
            ROOT / "schemas/catalog-corpus-v1.schema.json",
            ROOT / "schemas/catalog-projection-v1.schema.json",
            ROOT / "schemas/operation-request-v2.schema.json",
            ROOT / "schemas/operation-result-v2.schema.json",
        ):
            self.assertEqual([], core.validate_schema_annotations(core.load_json(path)), path.name)
        preserved = {
            "operation-request-v1.schema.json": "975a5374c04e1e9282d963ef470284ac704e1a66e776054cd27750aacb7f4ce1",
            "operation-result-v1.schema.json": "e10f60568c26d646cd17bc167460f08a81fe4aeb104ce3ce7f31fefbb2b14c5e",
        }
        for filename, expected in preserved.items():
            self.assertEqual(expected, hashlib.sha256((ROOT / "schemas" / filename).read_bytes()).hexdigest())
        v1 = core.load_json(V1_FIXTURE)
        expected_results = {
            "records_validate": "cb0735df54a0baade54c8cc16807a94771c1e7cbbc93a6710291084fcb656543",
            "graph_inspect": "88d5a4f52f4d3bfc31ff361ebe3a8835860e7b5890e9c9791be21cd86c179ee1",
            "build_resolve": "643a063d1553ff000a4776fd2a4eb5b7d300c0ba34ccbb977f3babd78abf7de9",
            "graph_transact_noop": "6def7986739604e807b3b95e26513fe6a9a41cd1d827ea4e417809b9027c48b8",
        }
        for name, digest in expected_results.items():
            result = dispatch_operation(copy.deepcopy(v1[name]), self.default_context)
            self.assertEqual("schuss-operation-result-v1", result["schema_version"])
            self.assertEqual(digest, hashlib.sha256(canonical_result_bytes(result, self.default_context)).hexdigest())

    def test_v1_v2_mixing_and_extra_members_fail_closed(self):
        mixed = copy.deepcopy(self.fixtures["catalog_search_crossfade"])
        mixed["schema_version"] = "schuss-operation-request-v1"
        result = dispatch_operation(mixed, self.context)
        self.assertEqual("invalid", result["status"])
        extra = copy.deepcopy(self.fixtures["catalog_search_crossfade"])
        extra["payload"]["unsupported"] = True
        result = dispatch_operation(extra, self.context)
        self.assertEqual("invalid", result["status"])
        unavailable = dispatch_operation(
            copy.deepcopy(self.fixtures["catalog_search_crossfade"]),
            self.default_context,
        )
        self.assertEqual("schuss-operation-result-v1", unavailable["schema_version"])
        self.assertEqual("invalid-request", unavailable["operation"])
        self.assertEqual("invalid", unavailable["status"])

    def test_all_client_projections_are_canonical_byte_equal(self):
        request = self.fixtures["catalog_search_crossfade"]
        direct = canonical_result_bytes(dispatch_operation(copy.deepcopy(request), self.context), self.context)
        ergonomic = _process(
            [
                "catalog",
                "search",
                "crossfade",
                "--record-set",
                str(RECORD_SET),
                "--json",
            ]
        )
        raw = _process(
            ["op", "--request", "-", "--record-set", str(RECORD_SET), "--json"],
            input_bytes=core.canonical_json(request).encode("utf-8") + b"\n",
        )
        self.assertEqual(0, ergonomic.returncode)
        self.assertEqual(0, raw.returncode)
        self.assertEqual(direct + b"\n", ergonomic.stdout)
        self.assertEqual(direct + b"\n", raw.stdout)
        self.assertEqual(direct, _gui_fixture(request, self.context))
        self.assertEqual(direct, _ai_fixture(request, self.context))

    def test_each_catalog_command_dispatches_exactly_once(self):
        for arguments, operation in (
            (["catalog", "search", "crossfade", "--json"], "catalog.search"),
            (["catalog", "inspect", "schuss-family-000018@1", "--json"], "catalog.inspect"),
        ):
            arguments = [*arguments, "--record-set", str(RECORD_SET)]
            calls = []

            def counted(request, context):
                calls.append(copy.deepcopy(request))
                return dispatch_operation(request, context)

            with mock.patch("packages.schuss_core.cli.dispatch_operation", side_effect=counted):
                code = run_cli(
                    arguments,
                    io.BytesIO(),
                    io.BytesIO(),
                    io.StringIO(),
                    lambda **kwargs: self.context,
                )
            self.assertEqual(0, code)
            self.assertEqual([operation], [request["operation"] for request in calls])

    def test_process_results_ignore_cwd_locale_and_hash_seed(self):
        outputs = []
        with tempfile.TemporaryDirectory(prefix="task011a-cwd-a-") as alpha, tempfile.TemporaryDirectory(prefix="task011a-cwd-b-") as beta:
            for cwd, seed, selected_locale in (
                (Path(alpha), "1", "C"),
                (Path(beta), "987654", locale.setlocale(locale.LC_COLLATE, None) or "C"),
            ):
                process = _process(
                    ["catalog", "search", "crossfade", "--json"],
                    cwd=cwd,
                    environment={"PYTHONHASHSEED": seed, "LC_ALL": selected_locale},
                )
                self.assertEqual(0, process.returncode, process.stderr)
                outputs.append(process.stdout)
        self.assertEqual(outputs[0], outputs[1])

    def test_record_enumeration_order_does_not_change_projection(self):
        def reversed_enumerator(root, child):
            return reversed(sorted((root / child).glob("*.json")))

        context = load_repository_context(
            ROOT,
            record_set_path=RECORD_SET,
            record_enumerator=reversed_enumerator,
        )
        first = canonical_result_bytes(self.dispatch("catalog_search_crossfade"), self.context)
        second_result = dispatch_operation(copy.deepcopy(self.fixtures["catalog_search_crossfade"]), context)
        self.assertEqual(first, canonical_result_bytes(second_result, context))

    def test_cli_locator_context_output_help_and_completion_boundaries(self):
        wrong_context = _process([
            "catalog", "search", "crossfade", "--record-set",
            str(ROOT / "contracts/record-sets/task005-008-accepted-v0.json"), "--json",
        ])
        malformed = _process(["catalog", "inspect", "schuss-family-000018@latest", "--json"])
        self.assertEqual(2, wrong_context.returncode)
        self.assertIn(b"CLI_CATALOG_CONTEXT_UNAVAILABLE", wrong_context.stderr)
        self.assertEqual(2, malformed.returncode)
        self.assertIn(b"CLI_LOCATOR_MALFORMED", malformed.stderr)
        human = _process(["catalog", "search", "crossfade"])
        self.assertEqual(0, human.returncode)
        self.assertIn(b"record_set: schuss-record-set-000015@1", human.stdout)
        self.assertIn(b"readiness_states:", human.stdout)
        root_help = _process(["--help"])
        catalog_help = _process(["catalog", "search", "--help"])
        self.assertIn(b"catalog", root_help.stdout)
        self.assertIn(b"--signal-domain", catalog_help.stdout)
        for shell in ("bash", "zsh", "fish"):
            script = completion_script(shell)
            self.assertIn(b"catalog", script)
            self.assertIn(b"search", script)
            self.assertIn(b"inspect", script)

    def test_task011a_historical_and_task023_successor_goldens(self):
        historical = core.load_json(GOLDEN_FIXTURE)
        successor = core.load_json(TASK023_GOLDEN_FIXTURE)
        observed = {"help": {}, "completion": {}, "human": {}, "json": {}}
        for name, arguments in {
            "root": ["--help"],
            "catalog": ["catalog", "--help"],
            "catalog-search": ["catalog", "search", "--help"],
            "catalog-inspect": ["catalog", "inspect", "--help"],
        }.items():
            narrow = _process(arguments, environment={"COLUMNS": "20"})
            wide = _process(arguments, environment={"COLUMNS": "240"})
            self.assertEqual(narrow.stdout, wide.stdout)
            self.assertLessEqual(max(map(len, narrow.stdout.splitlines())), 80)
            observed["help"][name] = _digest(narrow.stdout)
        for shell in ("bash", "zsh", "fish"):
            observed["completion"][shell] = _digest(completion_script(shell))
        for name, arguments in {
            "catalog-search-crossfade": ["catalog", "search", "crossfade"],
            "catalog-inspect-crossfader": ["catalog", "inspect", "schuss-family-000018@1"],
        }.items():
            observed["human"][name] = _digest(_process(arguments).stdout)
            observed["json"][name] = _digest(_process([*arguments, "--json"]).stdout)
        expected = {
            section: {
                name: successor[section][name]
                for name in observed[section]
            }
            for section in observed
        }
        self.assertEqual(expected, observed)
        self.assertEqual(
            "f4530b7e13e1275df11fdb17a99abaf70758547db36d1025e666cb1aa8c94ed4",
            hashlib.sha256(GOLDEN_FIXTURE.read_bytes()).hexdigest(),
        )

        # The retained pre-Task-023 mismatch is four equal-length digest changes.
        # It is isolated to the exact Task 011A context rather than hidden by
        # rewriting the historical fixture or misreported as catalog semantic drift.
        historical_context = {"human": {}, "json": {}}
        for name, arguments in {
            "catalog-search-crossfade": ["catalog", "search", "crossfade"],
            "catalog-inspect-crossfader": [
                "catalog",
                "inspect",
                "schuss-family-000018@1",
            ],
        }.items():
            explicit = [*arguments, "--record-set", str(RECORD_SET)]
            historical_context["human"][name] = _digest(_process(explicit).stdout)
            historical_context["json"][name] = _digest(
                _process([*explicit, "--json"]).stdout
            )
        for section in ("human", "json"):
            for name, value in historical_context[section].items():
                self.assertEqual(
                    historical[section][name]["byte_length"], value["byte_length"]
                )
                self.assertNotEqual(
                    historical[section][name]["byte_sha256"], value["byte_sha256"]
                )

    def test_broken_pipe_and_interruption_remain_contained(self):
        class BrokenOutput:
            def write(self, data):
                raise BrokenPipeError("closed")

            def flush(self):
                return None

        code = run_cli(
            [
                "catalog",
                "search",
                "crossfade",
                "--record-set",
                str(RECORD_SET),
                "--json",
            ],
            io.BytesIO(),
            BrokenOutput(),
            io.StringIO(),
            lambda **kwargs: self.context,
        )
        self.assertEqual(1, code)
        with mock.patch("packages.schuss_core.cli.dispatch_operation", side_effect=KeyboardInterrupt):
            stderr = io.StringIO()
            code = run_cli(
                [
                    "catalog",
                    "search",
                    "crossfade",
                    "--record-set",
                    str(RECORD_SET),
                    "--json",
                ],
                io.BytesIO(), io.BytesIO(), stderr,
                lambda **kwargs: self.context,
            )
        self.assertEqual(1, code)
        self.assertEqual("schuss: interrupted\n", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
