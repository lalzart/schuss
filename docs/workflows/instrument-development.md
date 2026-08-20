# Instrument development with Instrument Lab v1

Instrument Lab is the non-production mechanical path from an approved,
implementation-ready DSP bundle to a portable Core, bounded host shell,
objective renderer, graph-promotion requirements, and level-specific evidence.
It does not design the instrument and it does not promote a prototype into the
Schuss catalog, graph runtime, provider architecture, target/backend system, or
product surface.

## Choose the evidence lane first

### New design

Start with an approved musical proposal and an implementation bundle whose
state, controls, experiment, stop conditions, and unresolved choices are
explicit. The Core and all musical decisions remain instrument-owned. Use
Cinderwheel as the regression example, not as a superclass or sonic template.

### Observed-behavior reimplementation

Start with lawful observations, separately labelled evidence and inference,
and an experiment that can falsify the proposed behavior. Do not turn observed
similarity into a source-fidelity claim. The implementation bundle must say
which behavior is measured, approximated, or unresolved.

### Authorized source port

Start with exact source identity, authorization, revision, hashes, provenance,
licensing evidence, and a source-equivalence contract. Reuse an existing
source-release or physical source-package authority; never create a parallel
source catalog in a prototype. Tide Pit is the regression example. Its Task
036 handoff and exact Q27 comparator remain prerequisites, not lab-owned data.

## Common flow

1. Read the active task, approved proposal, implementation bundle, state
   matrix, control map, experiment, validation plan, results, and gaps.
2. Create a repository-relative `prototype-index.json`. Bind every authority by
   SHA-256 and declare the numeric host profile rather than accepting a default.
3. Write a noncanonical, nonexecutable `dsp-topology.json`. Expose the complete
   internals of any fused Core using local roles. Keep physical selectors, host
   framework classes, source paths, providers, runtime factories, targets, and
   backends outside this DSP topology.
4. Generate or supply an exhaustive instrument-owned control descriptor
   adapter. Reuse the regular Launch Control 3 topology only for physical
   layout/protocol facts; labels, curves, defaults, gestures, feedback, and
   semantic actions belong to the instrument.
5. Implement the portable Core and thin composition adapter. Link
   `SchussInstrumentLab::Core`; do not copy the lab headers, source, CMake
   helper, or host implementation into the prototype.
6. Prove Core-only behavior first. Add authenticated JUCE targets only after
   portable tests and freshness checks pass. Fetching remains opt-in and exact.
7. Drive interactive presentation from accepted Core snapshot state. Raw MIDI
   is diagnostic input, not authoritative UI state. Keep any unproved restart
   mailbox instrument-local and record the gap.
8. Keep experiment conditions, event timelines, comparators, tolerances,
   interpretations, and source oracles instrument-owned. Shared renderer code
   may encode, hash, measure, enumerate, and reject overwrites only.
9. Generate `PROMOTION_NEEDS.json` and `IMPLEMENTATION_HANDOFF.md`; then run the
   focused, affected native, and fresh-root reproduction checks.
10. Stop at the evidence ceiling. A passing target build is not an application
    launch, callback deadline, device lifecycle, listening pass, distribution
    approval, or production graph/provider integration.

## Generator and validator entry points

The smoke specification demonstrates deterministic generation without making
a musical claim:

```sh
python3 tools/instrument_lab/new_prototype.py \
  --spec research/prototype_support/instrument_lab/fixtures/smoke-spec.json \
  --template-root research/prototype_support/instrument_lab/templates \
  --output OUTPUT \
  --write
```

Validate an existing consumer and its generated handoff/promotion report:

```sh
python3 tools/instrument_lab/validate_prototype.py \
  --repo-root . \
  --consumer-root CONSUMER \
  --check
```

Run the cheap complete repository contract gate:

```sh
python3 tools/instrument_lab/validate_repository.py --repo-root .
```

Fresh work is explicit:

```sh
python3 tools/instrument_lab/reproduce.py --repo-root . --reproduce
```

The generator refuses a non-empty output directory. The validator rejects
unknown fields, canonical-looking identities, nonportable or mutable paths,
hash drift, missing authorities, stale derived output, and DSP-topology layer
leakage. Generated consumers link the single lab source through
`SCHUSS_INSTRUMENT_LAB_ROOT`; they contain no copied shared implementation.

## Evidence ladder

Record each rung independently:

1. proposal and bundle readiness;
2. schema, descriptor, topology, and freshness validation;
3. portable Core and sanitizer tests;
4. objective host-signal renderer/comparator evidence;
5. authenticated JUCE target build;
6. callback deadline and lifecycle evidence;
7. application launch and physical device/controller evidence;
8. listening evidence;
9. distribution and production integration.

Instrument Lab v1 closes only rungs 1-5 where each consumer explicitly proves
them. Later rungs require separate authority and retained evidence.
