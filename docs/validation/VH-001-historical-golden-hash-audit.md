# Validation-hygiene task VH-001: Historical golden/hash audit

Status: accepted through the delegated desktop-aggregate split and completed.
This is a maintenance task, not numbered product work; Tasks 027-028 and the
UI-architecture lane retain their existing routing.

## Goal and why it exists

Audit the five historical golden/hash failures exposed by the desktop
initialization aggregate without rewriting evidence or confusing an absent
ignored local source map with a product regression. The task exists because
the five assertions look independent but all encode the same optional local
verification count.

## In scope

- Reproduce and classify each of the five failing assertions individually as
  an invocation/fixture environment problem, stale expectation, or behavioral
  regression.
- Preserve the original Task 008-011A expectations and Task 009 preservation
  evidence byte-for-byte.
- Prove the exact configured-versus-unconfigured byte identities and retain an
  explicit gate where configured provenance cannot be reproduced in this
  worktree.
- Add one always-runnable structural audit test and a deterministic decision
  artifact.

## Out of scope

- Changing `catalog/sources.local.yml`, local-source discovery, prerequisite
  skips, configured reproduction commands, or any configuration-dependent test
  behavior.
- Creating a local source map, accessing or mutating upstream checkouts,
  weakening source identity/hash assertions, or claiming configured
  provenance from a synthetic count substitution.
- Rewriting, deleting, bulk-normalizing, or re-baselining historical goldens.
- Product semantics, UI/palette work, Java or legacy `.axp` execution, ARM
  compilation, hardware, device, real-time, audible, Git staging, commit,
  push, or publication work.

## Inputs and deliverables

Inputs are the five failing assertions in the Task 008, Task 009 prerequisite,
Task 010, and Task 011A suites; the retained Task 009 pre-task preservation
packet; the Task 010 CLI golden fixture; the accepted Task 005-008 record set;
and the existing optional local-source verification behavior.

Deliverables are this bounded contract and decision log,
`evidence/validation-hygiene-v1/historical-golden-hash-audit.json`, and
`tools/contracts/tests/test_validation_hygiene.py`.

## Exact finding

All five mismatches are category **(a), invocation/fixture environment
problems**. The accepted record set contains nine unique portable source
evidence references. Historical configured validation verified all nine; an
ordinary worktree without ignored `catalog/sources.local.yml` verifies zero.
The only semantic delta is
`$.reference_resolution.source_evidence_locally_verified: 9 -> 0`.

Changing only that integer in the current unconfigured result reproduces all
three historical byte identities exactly:

| Output identity | Historical configured | Ordinary unconfigured |
| --- | --- | --- |
| Target/backend validator stdout | 1,964 bytes, `7a898b3409e5ad7ef02eab1246f87756cc2af7cbd512d72f9a5eb43b1573a3a2` | 1,964 bytes, `32e5faa060030588944a33794f743190c475aa10218a42fe01ff224963384c8a` |
| Canonical `records.validate` result | 4,324 bytes, `cb0735df54a0baade54c8cc16807a94771c1e7cbbc93a6710291084fcb656543` | 4,324 bytes, `da887e6c9ea04f3331edad63ccb88cb591fbe41f7730b38e4bb8741aab490980` |
| Human `validate` output | 5,371 bytes, `bb9171763459ac6c204afa3d1a510f09200b8f35e6003184afdfe31e0c998619` | 5,371 bytes, `f620e39201a56227eba18b74cd66ec833c6ecfcf30afbff36a32676b51a4d2a3` |

The substitution is a byte-causality proof only. It does not authenticate any
checkout and cannot replace configured provenance reproduction.

## Decision log

| ID | Failing assertion | Classification | Decision |
| --- | --- | --- | --- |
| HGM-001 | Task 008 `test_all_legacy_validator_stdout_bytes_are_preserved` | Invocation/fixture environment | Retain the `7a898b...` configured validator golden; the `32e5fa...` result is the precise absent-configuration gate. |
| HGM-002 | Task 009 prerequisite `test_accepted_view_preserves_operation_result_hashes` | Invocation/fixture environment | Retain the `cb0735...` configured canonical result; do not rebaseline to `da887e...`. |
| HGM-003 | Task 010 `test_all_task005_through_task009_inputs_and_outputs_are_preserved` | Invocation/fixture environment | Same canonical identity boundary as HGM-002; retain it as a distinct historical assertion. |
| HGM-004 | Task 010 `test_human_outputs_match_golden_hashes_and_keep_exact_statuses` | Invocation/fixture environment | Retain the `bb9171...` configured human golden; do not rewrite the fixture to `f620e3...`. |
| HGM-005 | Task 011A `test_successor_schemas_and_v1_bytes_are_preserved` | Invocation/fixture environment | Same canonical identity boundary as HGM-002; retain it as the Task 011A compatibility gate. |

No mismatch is a stale expected result or an actual behavioral regression.
No golden is updated. In an unconfigured worktree the five assertions remain
precise configured-validation gates rather than ordinary always-runnable
acceptance checks; changing that invocation split belongs to the separately
assigned local-source-prerequisite task.

## Validation cadence and acceptance tests

Focused validation is the structural audit test. Adjacent regression is the
five exact historical assertions plus the unaffected Task 008/010/011A
modules. Configured source reproduction is an out-of-scope expensive check and
must remain `not-run` here. The final aggregate is intentionally not claimed
green while its invocation still includes configured gates without their
prerequisite.

Acceptance requires:

1. Exactly five decisions are present and each is classified individually.
2. The retained configured identities remain unchanged in their original
   tests, fixture, and Task 009 preservation packet.
3. A forced empty local-source mapping deterministically produces nine
   references, zero locally verified references, and the three unconfigured
   identities above.
4. Replacing only the local-verification count with nine reproduces all three
   historical identities exactly, without claiming provenance reproduction.
5. The audit test passes with or without an ambient local source map and makes
   no repository writes.
6. No configuration behavior, golden, product/UI semantics, toolchain, device,
   Git, or publication action changes.

## Decisions VH-001 may make

- Exact mismatch IDs, classification language, audit artifact layout, and the
  smallest structural test needed to prove the shared byte delta.
- Whether an unresolved mismatch is retained as a precise configured gate.

## Decisions VH-001 must not make

- Local-source prerequisite policy, skip behavior, source-map creation, or the
  ongoing configured/ordinary command split.
- Any change to original golden bytes, source identity/provenance rules,
  historical product semantics, or evidence level.

## Completion result

All five mismatches are individually closed as documented category-(a) gates.
The originals are preserved, the single causal delta is deterministic, and no
configured provenance reproduction was performed. The five historical tests
therefore retain their exact gate status in this unconfigured worktree.
