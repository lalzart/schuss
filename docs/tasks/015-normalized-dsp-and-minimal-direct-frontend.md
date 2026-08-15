# Task 015: Normalized DSP representation and minimal direct frontend

Status: complete on 2026-08-16; accepted locally through evidence level 4.

## Goal and why it exists

Define the first backend-independent normalized DSP representation and lower
the accepted one-node Blend graph directly to deterministic standalone C++.
This proves the compiler can cross the graph-to-code boundary without `.axp`,
Java, or the legacy object model before Task 016 absorbs the complete
eight-node graph.

## In scope

- Consume the successful Task 013 plan for
  `schuss-build-request-000001@2` and exact graph
  `schuss-graph-000001@1`.
- A closed normalized-DSP module schema with exact graph/plan provenance,
  Q27 numeric rules, public buffers/control, one `linear-mix-q27` operation,
  explicit ordering, and source origins.
- One pure `lower_minimal_direct(...)` API returning normalized IR, generated
  C++, source map, artifact hashes, and ordered diagnostics.
- Exact arithmetic: clamp blend to `[0, 2^27]`, accumulate both products in
  signed 64-bit space, arithmetic shift by 27, and saturate to signed 32-bit.
- Deterministic standalone C++17 with no runtime, Java, `.axp`, filesystem,
  CLI, handler, or device dependency.
- Fresh-root/order/environment determinism, host C++ syntax checking, and
  executable arithmetic-vector comparison against a pure reference model.
- A parent-preserving schema-only record set and read-only validator.

## Out of scope

- Production direct backend/binding eligibility, Task 014 handler
  registration, Ksoloti runtime ABI, ARM linking, scheduling beyond one
  operation, oscillators/filter/sequencer/state, the full Task 011C graph,
  optimizer, UI, hardware, device/audio proof, commit, or push.

## Inputs and deliverables

Inputs are the exact Task 014 record set, successful Blend plan, authoritative
graph/contract, and this arithmetic contract. Deliverables are this contract;
two closed schemas; `direct_frontend.py`; record set `000009`; focused tests;
read-only validator and retained summary; normative documentation; and a
completion report.

## Acceptance tests

1. All prior tests/validators pass and parent members remain byte-identical.
2. Only the exact successful Blend plan is accepted; stale, failed, multi-node,
   wrong-contract, malformed exposure/binding, and unsupported-operation inputs
   fail closed.
3. IR ordering, identities, Q27 rules, origins, and canonical hashes are stable
   across fresh roots, cwd, locale, hash seed, and input enumeration.
4. Generated C++ is byte-identical, contains no absolute path/timestamp/Java/
   `.axp`/legacy symbol, and passes `clang++ -std=c++17 -fsyntax-only`.
5. Boundary, midpoint, saturation, negative, and deterministic randomized
   vectors match the reference evaluator exactly.
6. Source map traces every C++ input/output/control and operation to graph and
   contract facets.
7. Evidence reaches at most level 4. No ARM, device, real-time, or audible
   claim is made.
8. `git diff --check` and the ordinary full test gate pass.

## Decisions Task 015 may make

- Normalized IR/schema layout, stable derived IDs, Q27 operation spelling,
  standalone C++ API/name, source-map layout, and diagnostics.

## Decisions Task 015 must not make

- Production direct-binding/backend eligibility, Ksoloti runtime ABI,
  multi-node scheduling/state semantics, implicit conversion, graph rewrite,
  optimization, or hardware/UI behavior.

## Stop conditions

Stop if the accepted contract does not determine the four Blend facets; if
arithmetic needs an unowned rounding/overflow decision beyond this explicit
task contract; or if completion requires Task 016, Java, `.axp`, ARM/runtime,
hardware, stage, commit, or push.

## Completion report

Task 015 is complete for exact Blend request `schuss-build-request-000001@2`,
graph `schuss-graph-000001@1`, and mixed Crossfader contract
`schuss-component-contract-000003@1`. `lower_minimal_direct(...)` emits one
normalized `linear-mix-q27` operation, an explicit one-operation schedule,
complete facet origins, a direct source map, and standalone C++17 symbol
`schuss_blend_process_q27`. `evaluate_linear_mix_q27(...)` is the independent
reference evaluator.

Record set `schuss-record-set-000009@1` has content hash
`sha256:fb8e351335d623195e902ab464a3f79b30afe24391798e4792fcbc4107795b0b`
and file SHA-256
`52b7a2ae0259c7cb79c15a85d6dc3400bd05fa1e2a956bda12fd6edfd31e7436`.
It adds only `normalized-dsp-module-v0` (schema file SHA-256
`0398869cc5a46b4cdcfac71bdbf6779d986909764acf7c6d00dc29f9ae044f8b`)
and `direct-frontend-result-v0` (schema file SHA-256
`e0a1b97a520bdaa4dc38f79eb795bf87959e6d3babe8611548643199b15e0354`).

The normalized module is 1,483 canonical bytes with SHA-256
`60aa4a2dc07ba64bb65c37d36841505e361f15245f39126b37cf7e9ddf3bdfdd`.
Generated C++ is 991 bytes with SHA-256
`a14f0733cf7e724e347e2edbafc8337bb26b18a6a16b6109aefd894cd540023d`;
the 653-byte source map hashes to
`7a06c1a8c3fb6d06a26929728d4ed86b157c09a91c8d0bca6534f6766296ef0f`.
Clang C++17 syntax validation passes. Forty compiled boundary and deterministic
random arithmetic vectors equal the pure reference bit-for-bit.

Eight focused tests and the read-only Task 015 validator pass. The complete
gate passes 223 contract tests, 14 inventory tests, and 6 catalog tests, for
243 tests total. Negative cases
cover failed/stale plans, graph/contract identity, multi-node input, and public
mapping drift. Evidence levels 1-4 pass; ARM/link, device, real-time, and
audible levels 5-8 are `not-run`. No direct production backend/binding was
promoted, no legacy bridge was used, and no stage, commit, push, upload, flash,
or hardware action occurred. Task 016 owns the full eight-node direct path and
the additional scheduling/state/native-operation semantics it requires.
