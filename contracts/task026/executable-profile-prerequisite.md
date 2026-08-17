# Task 026A: Reverb-free executable-profile prerequisite

Status: complete. The focused validator, adjacent regression suite, and
two-fresh-root local ARM compile/link reproduction passed. Evidence is bounded
to levels 1-5; levels 6-8 remain `not-run`.

## Goal and reason

Establish one bounded, identity-independent direct frontend and local build
handler for the first safe application profile. This closes the exact gap
between Task 025's partial semantic tranche and Task 026B's requirement to
build a newly authored closure, without guessing a reverb memory contract.

## Exact parent and profile

The parent is `schuss-record-set-000017@1`. The profile contains exactly one
instance of each of these reviewed operation contracts:

- `blep-saw-q27` / `schuss-component-contract-000012@1`;
- `blep-pwm-q27` / `schuss-component-contract-000013@1`;
- `soft-clip-q27` / `schuss-component-contract-000016@1`;
- `exponential-smooth-q27` / `schuss-component-contract-000015@1`;
- `linear-mix-q27` / `schuss-component-contract-000003@1`;
- `interpolated-vca-q27` / `schuss-component-contract-000020@1`; and
- `stereo-audio-output-q27` / `schuss-component-contract-000009@1`.

The saw feeds soft clip. PWM and soft clip feed the two crossfade audio inputs.
The public Blend parameter feeds the crossfade control. The public Motion
parameter feeds the exponential smoother, whose output controls the VCA. The
crossfade output feeds the VCA audio input, and the VCA output feeds both audio
output channels. Saw pitch is `-24`, PWM pitch is `-12`, smoother time is the
contract default, and every other value/mapping is fixed by the graph record.
Reverb is not a profile member.

## In scope

- A new exact profile graph, included instrument, build request, direct-backend
  successor, seven backend-eligibility successors, and successor record set.
- A semantic-profile signature that ignores stable graph identity but validates
  exact contracts, node parameters/attributes, topology, public parameters,
  public bindings, backend, target, and included instrument mapping.
- Normalized DSP, origin/source map, generated C++, exact local ARM compile/link
  handler, deterministic artifact publication to a fresh caller-selected root,
  and two-root reproduction evidence through level 5.
- Focused contract, frontend, handler, drift, determinism, and regression tests.

## Out of scope

- Any reverb operation spec, native binding, eligibility promotion, allocation
  fix, resource-ownership decision, source modification, or evidence upgrade.
- General graph compilation, arbitrary operation scheduling, Java, `.axp`,
  hidden fallback, connected-device execution, real-time/resource suitability,
  audible proof, release, staging, commit, push, publication, or hardware action.

## Inputs and deliverables

Inputs are the exact Task 025 record set and evidence, Task 016 crossfade/output
semantics and local ARM boundary, authenticated Ksoloti runtime/source bytes,
the Task 026 preflight decision, and accepted ADRs 0011 and 0014.

Deliverables are the durable records named above; one frontend and one bounded
handler implementation; a deterministic run tool; focused tests and validators;
two fresh-root evidence packets; and documentation/governance updates needed to
activate 026B.

## Acceptance tests

1. This contract validates before implementation and names goal, scope, inputs,
   deliverables, decisions, tests, cadence, and prohibited actions.
2. The successor record set has the exact Task 025 parent and does not mutate or
   replace any Task 024/025 record or reverb evidence.
3. Planning the exact seven-node fixture selects exactly the seven accepted
   bindings and includes the exact instrument and target/backend references.
4. An equivalent graph with a different stable graph identity produces the same
   semantic profile signature and can enter the frontend through an exact
   included request; identity alone is not the support test.
5. Any topology, contract, facet, parameter, attribute, public mapping,
   instrument mapping, backend, target, or operation-spec drift fails before
   generated source or output-root creation with a stable diagnostic.
6. The generated schedule and origin map cover every node, contract facet,
   connection, public parameter, and parameter binding exactly once as required.
7. Generated C++ preserves the accepted Task 025 and carried Task 016 integer,
   state, control-latch, block-order, and audio-output semantics, and contains no
   reverb, Java, `.axp`, or legacy bridge dispatch.
8. The exact handler accepts an included instrument/request, compiles and links
   with the authenticated local ARM boundary, and emits an ARM ELF at level 5.
9. Two fresh output roots reproduce byte-identical normalized DSP, source map,
   generated C++, command vector, ARM object, stripped ELF, and evidence bytes.
10. Levels 6-8 remain `not-run`; resource/real-time and audible safety are not
    inferred from local compile/link.
11. Focused and adjacent tests pass before 026B activates; one later final
    aggregate may cover the same stable checks without redundant rebuilds.

## Validation cadence

Run the contract validator first. During implementation run focused pure
profile/frontend tests, then one local compile smoke after source generation is
stable. Run the two-root reproduction once after the diff freezes. Adjacent
compiler/build/CLI tests follow. The repository-wide aggregate is deferred to
the end of 026B so the same expensive closure is not repeated.

## Decisions 026A may make

- New stable IDs after the accepted allocation frontier, exact profile node and
  connection IDs, internal normalized operation IDs, handler ID, artifact
  layout, and the smallest reusable frontend/backend API needed by 026B.
- Deterministic schedule ordering where the exact data dependencies permit one
  order and Task 025 has already fixed each operation's block semantics.

## Decisions 026A must not make

- Reverb allocation, ownership, compatibility, promotion, or resource safety.
- New DSP math/state/timing, different component contracts, implicit fallback,
  arbitrary graph support, target/device/instrument collapse, or evidence above
  what local execution reproduces.
- Git staging/commit/push, release/publication, upload, reset, flash, SD-card
  writes, or any connected hardware action.
