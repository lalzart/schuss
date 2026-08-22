# Task 038 results

Status: complete. The source-migration removal gate passed before the duplicate
consumer subtree was removed, and the final current/native/reproduction gates
passed after implementation freeze.

## Source authority and reuse gate

- The immutable Task 033 Phase 2 parent remains
  `schuss-record-set-000031@1` at
  `sha256:09ef78ec79d72736add893045973070fa0b2c43e06fc124d05392213d73fc789`.
- The source-only successor is `schuss-record-set-000032@1` at
  `sha256:661394529dd5ba12ff9ffad35283f47b224276dda07a4f9a5345d9943d85641f`.
  It adds only source releases 000008 and 000009. It changes no catalog,
  collection, implementation, provider, or runtime record.
- `mutable-eurorack-braids-v1` validates as an exact 12-file physical closure;
  `mutable-stmlib-v1` validates as an exact 5-file physical closure. Their
  package manifests reference, and do not duplicate, source-release identity,
  revision, provenance, hashes, or licensing authority.
- `SchussMutableBraidsV1::Core` owns only reusable construction, model
  selection, render-call, and deterministic RNG-seeding mechanics. Musical
  recipes, allocation, envelopes, decimation, mixing, and controls remain in
  the drum machine.
- The generated consumer dependency handoff validates the two packages,
  adapter, source-release references, and accepted JUCE source-release/tree
  references without creating a source catalog.

## Removal gate evidence

Before removal, the shared package trees were byte-identical to the drum
machine's 12 Braids and 5 stmlib source files. The migrated build then passed
all eight focused CTests, including the adapter's frozen deterministic
reference hash. The unchanged frozen objective render manifest passed across
outer block sizes 1, 16, 64, 128, 511, and 512. No expected render was updated.

This establishes source, host-structural, and preserved host-signal evidence
for the migration. It does not establish live real-time, device, listening,
distribution, provider, or production evidence.

The removed `research/prototypes/generative-drum-machine/third_party/` tree was
moved intact to
`/Users/lanceship/.Trash/schuss-gdm-third-party-task038-20260822`; the working
prototype now contains zero files below the former source path.

## Instrument Lab workflow gate

- Repository validation discovers all five current musical consumers from
  `research/prototypes/*/prototype-index.json`, plus the non-musical smoke
  fixture, in stable order. No manually maintained consumer catalog exists.
- The duplicate-shared-implementation scan covers every discovered musical
  consumer and a test proves a future consumer cannot bypass it.
- Sonic Research Lab v2 consumers must bind a ready contract, nonempty
  approval reference, exact proposal path/SHA-256, and matching work lane.
  Wirefall's proposal retains its frozen pre-approval `proposed` header; the v2
  contract remains the authoritative post-proposal approval record.
- The reusable relocated-consumer command copied no build tree, enabled no
  JUCE target, fetched nothing, and passed for the drum machine at relocated
  tree SHA-256
  `b5d63782479fba0f5b9b5216edc4e0f5752f0bcb86d6cae5063c149dc64aef7f`
  and Wirefall at
  `e3d2ddc390f4d064e2dc4c4fb04118d13e1f8ad97d049153c85e0f02c4719d21`.
  Wirefall's retained failed host-signal disposition was not changed.

## JUCE authority gate

`schuss-source-release-000007@1` remains the sole upstream JUCE authority.
Instrument Lab now derives its fetch URL and archive hash from that record.
The retained archive hash passed, and the exact extracted tree authenticated as
4,425 files at manifest SHA-256
`ee764637fc4d1358d74f2797f8f059cbd8ff8878d663a28632de9737a11b2db7`.
The authenticated drum-machine JUCE target compiled, linked, and passed all
eight CTests without being launched.

An APFS clone with only `README.md` changed retained the same JUCE version
macros but failed closed at
`f06584b956d7c776b4f5f02a5979dc6ada5a93a7e6b8b7c077fb6426cf754d30`.
That disposable negative clone was moved to
`/Users/lanceship/.Trash/schuss-task038-juce-negative.tELXVr`.

## Freeze validation

- `current`: 8/8 registered checks passed in 26.817 seconds. This profile did
  not compile, render, fetch, access hardware, or require a configured source.
- `native.instrument-lab-task038-core`: passed in 10.848 seconds; drum-machine
  8/8 CTests and Wirefall 2/2 focused CTests passed.
- `native.instrument-lab-task038-juce`: passed in 57.312 seconds using the
  declared authenticated-tree prerequisite; build and 8/8 CTests passed.
- `reproduction.instrument-lab-generative-drums`: passed in 5.542 seconds.
- `reproduction.instrument-lab-wirefall`: passed in 3.171 seconds.
- The preserved historical `catalog/sources.lock.json` remains byte-identical
  at SHA-256
  `77af227973e89ade0f7410e3dc4588c1fb9f63b249cda4e45710d71fe745eb27`.
- The frozen drum-machine render manifest remains byte-identical at SHA-256
  `c173d54bce78d4d4110a8de7d3adcb891df1fa5ae896ae2dcc5d198730adf5fe`.
