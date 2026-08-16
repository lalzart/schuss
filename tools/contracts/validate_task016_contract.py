#!/usr/bin/env python3
"""Validate the Task 016 accepted decision and completed evidence boundary."""

from pathlib import Path
import hashlib
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
DECISION_PATH = ROOT / "docs/decisions/0011-preserve-legacy-equivalent-direct-semantics.md"
COMPLETION_PATH = ROOT / "evidence/task016-completion-v1/completion-report.md"
SUMMARY_PATH = ROOT / "evidence/task016-completion-v1/validation-summary.json"

REQUIRED_DECISION_SECTIONS = (
    "## Context",
    "## Decision",
    "## Consequences",
)

PINNED_FACTS = (
    "legacy-equivalent semantics",
    "may not silently substitute Schuss-native behavior",
    "may never fall back invisibly to the Java bridge",
    "levels 6-8 are independent and remain `not-run`",
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
    decision = DECISION_PATH.read_text(encoding="utf-8")
    completion = COMPLETION_PATH.read_text(encoding="utf-8")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    missing_sections = [
        heading for heading in REQUIRED_DECISION_SECTIONS if heading not in decision
    ]
    missing_facts = [fact for fact in PINNED_FACTS if fact not in decision]
    evidence_errors = authenticate_evidence()

    invalid = (
        missing_sections
        or missing_facts
        or evidence_errors
        or "- Status: accepted" not in decision
        or "Two fresh local roots" not in completion
        or [item["status"] for item in summary.get("evidence_levels", [])]
        != ["passed"] * 5 + ["not-run"] * 3
        or summary.get("device_actions_performed") is not False
        or summary.get("status") != "valid"
        or summary.get("record_set_reference", {}).get("record_set_id")
        != "schuss-record-set-000010"
    )
    if invalid:
        print(
            json.dumps(
                {
                    "missing_decision_facts": missing_facts,
                    "missing_decision_sections": missing_sections,
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
                "decision_document": "ADR 0011",
                "decision_status": "accepted-legacy-equivalent",
                "authenticated_evidence_members": 13,
                "evidence_status": "levels-1-through-5-passed",
                "implementation_status": "complete",
                "record_set": "schuss-record-set-000010@1",
                "required_decision_sections": len(REQUIRED_DECISION_SECTIONS),
                "schema_version": "task016-contract-validator-v4",
                "status": "valid",
                "unresolved_product_decisions": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
