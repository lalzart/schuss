#!/usr/bin/env python3
"""Validate the Task 016 accepted decision and completed evidence boundary."""

from pathlib import Path
import hashlib
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/tasks/016-complete-gills-slice-direct-frontend.md"
BRIEF_PATH = ROOT / "docs/tasks/016-direct-semantics-decision-brief.md"
COMPLETION_PATH = ROOT / "evidence/task016-completion-v1/completion-report.md"
SUMMARY_PATH = ROOT / "evidence/task016-completion-v1/validation-summary.json"

REQUIRED_CONTRACT_SECTIONS = (
    "## Goal and why it exists",
    "## In scope",
    "## Required prerequisite specifications",
    "## Evidence audit and accepted decision",
    "## Out of scope",
    "## Inputs and deliverables",
    "## Acceptance tests",
    "## Decisions Task 016 may make",
    "## Decisions Task 016 must not make",
    "## Completion report",
)

REQUIRED_BRIEF_SECTIONS = (
    "## Why one decision remains",
    "## Exact decision requested",
    "## Authenticated evidence base",
    "## Conditional specification for the recommended route",
    "## Constraints after the accepted decision",
)

PINNED_FACTS = (
    "08d3e6e1e2b61230308c20a15ded58ffdaf4656c",
    "7877897b3112dcbb7ee1239f3187f535d6113875cacbb49c76bd30a0321bcfd3",
    "Legacy-equivalent direct semantics (recommended)",
    "Schuss-native direct semantics",
    "Decision status: accepted on 2026-08-16",
    "The user selected option 1",
)

PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
ORACLE_SHA256 = "7877897b3112dcbb7ee1239f3187f535d6113875cacbb49c76bd30a0321bcfd3"
ORACLE_LENGTH = 18_359
RUNTIME_MEMBERS = {
    "firmware/axoloti_math.c": "ba4e3146eb3e6cf436ee836d1f5c82d9b5c13606e3ab0f273ff43432ef3626c1",
    "firmware/axoloti_math.h": "95ccbdbea15078a6ef207e87749bb8defaa4662b6eebddfb40944f350b549191",
    "firmware/patch.h": "fe64781fac09b82d6f45eafbb60efcfe7b1af655af5dcccaac232e29c31dad2c",
    "firmware/xpatch.h": "85e4abc70123952e8f47217751f2b6f7299e7cb978b6c994acf7b383425379a0",
    "src/main/java/axoloti/Patch.java": "7c1cc7e644ef5d1453741e4ec40090e71c3f3697ef9c7a20761ce739f9b804b6",
}
OBJECT_MEMBERS = {
    9: ("axoloti-factory", "objects/audio/out stereo.axo", "d8392b522b54be3bdfa5e671975a2a675ac494e9d1dc8bee2586dcd1eaecc7e3"),
    159: ("axoloti-factory", "objects/filter/multimode svf m.axo", "e73239cd072b9dc63debd2ec95a32ec0bf79ae1be1754336a1d5928d4e8af057"),
    209: ("axoloti-factory", "objects/lfo/square.axo", "d417bd0e455e28c6af9988732f6406b2d3e3c94eea9338f76ab61df926463051"),
    215: ("axoloti-factory", "objects/logic/counter.axo", "fb61bbfeb9504cee015b093888fb8c6da237d12b760a5e6ebdb9b160447bd9e1"),
    549: ("axoloti-factory", "objects/osc/sine.axo", "bf865e647b2eea2ebe1ef852038994f2dea8f1e8b8e60e1133e1d580a3402a4b"),
    918: ("axoloti-contrib", "objects/drj/seq/stepseq_16_pitch.axo", "45336e472f1e15a295617b0f4fd1e31e83203acf9ae37a067125459f66022b0f"),
}


def authenticate_evidence() -> list[str]:
    errors: list[str] = []
    source_lock = json.loads((ROOT / "catalog/sources.lock.json").read_text(encoding="utf-8"))
    locked_sources = {entry["id"]: entry for entry in source_lock["sources"]}
    if locked_sources.get("patcher", {}).get("commit") != PATCHER_COMMIT:
        errors.append("patcher source lock does not match the audited commit")

    capsule = json.loads(
        (ROOT / "evidence/task-009-prerequisite-v0/source-capsule-members.json").read_text(
            encoding="utf-8"
        )
    )
    capsule_members = {member["path"]: member for member in capsule["members"]}
    for member_path, expected_sha256 in RUNTIME_MEMBERS.items():
        member = capsule_members.get(member_path)
        if member is None or member.get("byte_sha256") != expected_sha256:
            errors.append(f"runtime evidence mismatch: {member_path}")

    object_records: dict[int, dict] = {}
    object_path = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/resolved/objects.jsonl"
    for line in object_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("variant_index") in OBJECT_MEMBERS:
            object_records[record["variant_index"]] = record
    for variant_index, expected in OBJECT_MEMBERS.items():
        record = object_records.get(variant_index)
        if record is None:
            errors.append(f"resolved object evidence absent: {variant_index}")
            continue
        actual = (
            record["origin"]["source_id"],
            record["origin"]["path"],
            record["origin"]["sha256"],
        )
        if actual != expected or record.get("metadata", {}).get("license") != "BSD":
            errors.append(f"resolved object evidence mismatch: {variant_index}")

    oracle_path = ROOT / f"evidence/task-011c-v1/artifacts/sha256/{ORACLE_SHA256}"
    oracle_bytes = oracle_path.read_bytes()
    if len(oracle_bytes) != ORACLE_LENGTH:
        errors.append("Task 011C oracle length mismatch")
    if hashlib.sha256(oracle_bytes).hexdigest() != ORACLE_SHA256:
        errors.append("Task 011C oracle hash mismatch")
    return errors


def main() -> int:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    brief = BRIEF_PATH.read_text(encoding="utf-8")
    completion = COMPLETION_PATH.read_text(encoding="utf-8")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    missing_contract = [
        heading for heading in REQUIRED_CONTRACT_SECTIONS if heading not in contract
    ]
    missing_brief = [heading for heading in REQUIRED_BRIEF_SECTIONS if heading not in brief]
    numbered_specs = [f"{number}." in contract for number in range(1, 9)]
    missing_facts = [fact for fact in PINNED_FACTS if fact not in brief]
    evidence_errors = authenticate_evidence()

    invalid = (
        missing_contract
        or missing_brief
        or missing_facts
        or evidence_errors
        or not all(numbered_specs)
        or "accepted locally through evidence level 5" not in contract
        or "schuss-build-request-000002@3" not in contract
        or "Two fresh local roots" not in completion
        or [item["status"] for item in summary.get("evidence_levels", [])]
        != ["passed"] * 5 + ["not-run"] * 3
        or summary.get("device_actions_performed") is not False
    )
    if invalid:
        print(
            json.dumps(
                {
                    "missing_brief_facts": missing_facts,
                    "missing_brief_sections": missing_brief,
                    "missing_contract_sections": missing_contract,
                    "evidence_errors": evidence_errors,
                    "status": "invalid",
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "decision_status": "accepted-legacy-equivalent",
                "authenticated_evidence_members": 13,
                "evidence_characterization_status": "complete",
                "evidence_status": "levels-1-through-5-passed",
                "implementation_status": "complete",
                "prerequisite_specifications": 8,
                "required_brief_sections": len(REQUIRED_BRIEF_SECTIONS),
                "required_contract_sections": len(REQUIRED_CONTRACT_SECTIONS),
                "schema_version": "task016-contract-validator-v3",
                "status": "valid",
                "unresolved_product_decisions": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
