# Task 043: Pamplist canonical instrument identity

Status: complete in the current working tree on 2026-08-24; not committed or
published.

## Goal and why it exists

Promote the accepted Pamplist 0.6 musical identity from Instrument Lab into
the canonical Schuss semantic model, and link that exact identity from the
desktop audition library. This closes the distinction that confused the
audition workflow: the executable remains a prototype-hosted build, while the
instrument name, complete DSP topology, public controls, and exact revision
become canonical Schuss records.

## Inputs

- `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/STATUS.md`, ADRs 0016-0018,
  Task 039, the closed Task 040 allocation, and
  `docs/workflows/instrument-development.md`.
- Parent record set `schuss-record-set-000033@1` at content hash
  `sha256:01dc913b0d637573adda283f84985e7196ee7162b6f2eaadf76b1d3a2890b786`.
- Pamplist proposal 0.6, prototype index, topology, control map, source
  dependencies, retained results, and authenticated JUCE build receipt.
- The user's current-thread hands-on acceptance: "It's good now."

## In scope

- One additive Pamplist catalog family and transparent native-C++ prototype
  implementation description.
- Seven exact component contracts and one complete DSP graph for timeline,
  lane decisions, local modulation, macro-voice bank, dry mixer, cohesion body,
  and final output.
- One controller-independent `instrument-v1` record exposing every persistent
  Pamplist 0.6 musical control plus Run/Stop and Clear Cohesion actions.
- One deterministic successor record set and additive catalog/library schemas.
- An audition-library v2 entry that resolves the canonical instrument and graph
  while retaining the exact prototype/build launch authority.
- Core and desktop presentation changes needed to show canonical versus
  prototype-only identity truthfully.
- Focused, adjacent, freshness, current-profile, and copied-root validation.

## Out of scope

- Any change to Pamplist DSP, source files, control behavior, controller map,
  presets, audio output, or accepted prototype evidence.
- A canonical native implementation binding, provider factory, build request,
  performance-control executor, Ksoloti/Gills adaptation, or machine record.
- Application launch, endpoint enumeration, controller access, callback timing,
  packaging, distribution, publication, staging, commit, or push.
- Reusing Task 040's closed Cinderwheel meanings or changing historical record
  bytes.

## Deliverables

1. `schuss-record-set-000036@1`, successor to `000033@1`.
2. Family `schuss-family-000109@1`, implementation
   `schuss-implementation-000170@1`, component contracts `000042@1` through
   `000048@1`, graph `schuss-graph-000009@1`, and instrument
   `schuss-instrument-000007@1`.
3. Catalog corpus revision 7 and selection revision 6.
4. Audition library revision 2 with one exact canonical Pamplist reference.
5. Deterministic generator, validator, tests, and updated product guidance.

The skipped numbers are intentional: Task 040 explicitly released but retains
proposed Cinderwheel allocations `family 000108`, component contracts
`000032-000041`, graphs `000007-000008`, instrument `000006`, implementation
`000169`, and record sets `000034-000035`. Task 043 does not reuse their
meaning even though they were never canonical records.

## Acceptance tests

1. Every frozen Pamplist 0.6 authority and the authenticated executable hash
   matches its declared portable file.
2. All new schemas and records are canonical, content-addressed, deterministic,
   closed to unknown fields, and resolve through the exact parent ancestry.
3. The graph contains exactly the seven promotion roles, preserves their audio,
   control, action, state, and stereo-output boundaries, and hides no role
   behind the fused implementation note.
4. The instrument maps every declared parameter and action exactly once to the
   graph. Page selection and physical CC numbers do not become instrument
   facets.
5. The library resolves Pamplist's exact instrument, graph, record set,
   prototype, results, and executable identities before reporting it canonical
   or launchable.
6. Historical library v1 behavior and tests remain valid under record set
   `000033@1`; the desktop selects successor `000036@1` and displays the mixed
   identity states without exposing launch paths.
7. Focused tests, catalog/component/graph adjacent validation, generated-file
   freshness, copied-root reproduction, and the `current` profile pass.
8. Results distinguish canonical semantic identity and user-reported audition
   acceptance from provider/runtime, real-time, device, distribution, and
   production evidence.

## Decisions this task may make

- The exact additive IDs listed above, schema v7/v2 field shapes, stable facet
  ordering, and concise desktop wording.
- The smallest normalized/exact-domain representation needed to express the
  already accepted Pamplist controls without changing them.
- A catalog source-authority form that binds exact prototype and source-release
  evidence without making the prototype or JUCE host canonical runtime truth.

## Decisions this task must not make

- New musical behavior, defaults, modulation laws, graph roles, controller
  gestures, source equivalence, or listening judgments.
- A provider, target/backend support, factory, performance configuration,
  machine, distribution license result, or production-readiness claim.
- Any mutation of Task 039 history, Task 040's retained plan, configured source
  checkouts, hardware, Git index, commit history, or remotes.

## Validation classification

- Focused: Task 043 generation, semantic validator, library service, and React
  component tests.
- Adjacent: Task 039 historical tests, catalog projection, component/graph and
  record-set validators, desktop bridge structure.
- Routine: `current` after implementation freeze.
- Reproduction: one copied-root Task 043 generation/semantic check after
  implementation freeze.
- Native: no new compilation is required; the exact retained Pamplist build
  receipt and executable are authenticated without launch.
- Full `release` is not required because no shared DSP/provider/runtime or
  distribution boundary changes.

## Evidence ceiling

Completion establishes canonical catalog, graph, and instrument identity plus
an exact link to retained host-build and user-reported audition acceptance. It
does not establish a canonical implementation provider, canonical runtime
execution, callback deadline, physical controller session, structured
listening packet, embedded target, package, distribution, or production
release.

## Results

- Generated and validated `schuss-record-set-000036@1` with catalog family
  `schuss-family-000109@1`, transparent implementation description
  `schuss-implementation-000170@1`, seven component roles, graph
  `schuss-graph-000009@1`, and instrument `schuss-instrument-000007@1`.
- The graph exposes all 178 musical parameters, two actions, four displays, and
  stereo output. The instrument maps all 178 parameters and both actions.
- Audition library v2 contains six entries and marks only Pamplist canonical.
  The desktop selects the same record set and labels canonical versus prototype
  identity without exposing executable paths.
- Focused generation, semantic, historical-library, desktop-structure, and UI
  checks passed. The desktop's 27 tests and production TypeScript/Vite build
  passed. The routine `current` profile passed 9/9 checks in 74.016 seconds.
- Fresh generation and semantic validation also passed from a relocated copied
  root using only the exact Pamplist build artifact required for hash checking;
  the temporary copy was removed afterward.
- No application, audio/MIDI endpoint, controller, USB/device, Git index,
  commit, push, package, or publication action occurred. No canonical binding
  or implementation provider was claimed.
