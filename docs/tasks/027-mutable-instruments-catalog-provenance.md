# Task 027: Mutable Instruments catalog provenance and extended-source review

Status: accepted and complete on 2026-08-17. ADR 0015 records the explicit
retargeting of the unstarted Task 027 assignment from ADR 0014. All fifteen
acceptance tests passed within the catalog structural/provenance boundary.

## Goal and why it exists

Integrate exact Mutable Instruments-related Ksoloti source evidence into the
current Schuss catalog without creating a provenance-led family hierarchy or
promoting source presence into executable support. This exists because Task
024 did not index the separate 19-object Ksoloti extended library, while the
factory corpus contains explicit Mutable-derived candidates whose ancestry is
not yet available as a precise catalog filter.

## Dependencies and verified baseline

The exact parent is `schuss-record-set-000019@1`. Task 024 supplies the pinned
first-party candidate corpus, sixty reviewed families, and catalog projection
v3. Those families remain arranged under the thirteen function-first categories.
Task 025 supplies the retained failed Rings-reverb allocation claim, which
Task 027 must not repair or promote. Task 026 changes no catalog identity.

The source lock pins `patcher` commit
`08d3e6e1e2b61230308c20a15ded58ffdaf4656c`. That exact tree contains nineteen
extended manifests and nineteen `.axo` wrappers. Its `LICENSE.md` supports a
Mutable-derived tag for exactly the Rings physical resonator, Grids-derived
topographic pattern data, and Plaits macro voice. The retained Task 024 factory
candidate artifact contains exactly fifty-three variants whose own exact
descriptions attribute Mutable Instruments source or DSP. Working-tree bytes
and later source metadata are not inputs.

## In scope

- Preservation of all sixty reviewed catalog families and all thirteen
  function-first categories without reassignment.
- A deterministic source-review record covering all nineteen extended objects
  and all fifty-three explicitly attributed factory candidates.
- Exact portable Git authority, manifest/object/license hashes, source-declared
  authorship and license strings, and source-metadata compatibility labels kept
  explicitly separate from Schuss evidence.
- The additive provenance tag `mutable-instruments-derived`, applied only where
  the exact source record or license evidence supports it.
- One exact new catalog implementation,
  `schuss-implementation-000096@1`, for the extended Rings physical resonator
  under existing `schuss-family-000010@1` Physical-model Resonator.
- Provenance tags on the five already catalogued factory implementations whose
  exact Task 024 source candidates carry Mutable attribution: Clouds-like
  granular processing, Elements-like physical modelling, Rings-derived stereo
  reverb, Struck Drum Voice, and Struck Bell Voice.
- Candidate-only tagged retention for every other attributed factory object,
  including both Warps wrappers, and for the extended topographic sequencer and
  macro voice.
- Catalog corpus/projection v4, exact selection successor, source-review schema
  and record, record set `schuss-record-set-000020@1`, search/inspect
  validation, deterministic generation, two fresh-root/source-map
  reproductions, and integrated governance.

## Out of scope

- Any new catalog family, Mutable Instruments category tree, renamed existing
  family, family merge, preferred implementation, or inferred equivalence.
- Catalog implementation promotion for the topographic sequencer, macro voice,
  Warps vocoder, Warps wrapper, or any other candidate without an exact
  existing-family equivalence decision.
- Treating a source manifest's `offline-verified`, tested-target, compatibility,
  resource, or build-failed fields as Schuss compiler or build evidence.
- Component contracts, bindings, eligibility, DSP equations, lowering,
  generated C++, ARM compilation/linking, Java, `.axp`, project writes,
  sessions/jobs, UI, device access, real-time measurement, or listening.
- Repairing, suppressing, or promoting the known Rings-derived stereo-reverb
  allocation contradiction.
- Mutation of upstream checkouts or historical records; ambient/latest source
  discovery; staging, commit, push, release, upload, reset, flash, SD-card
  write, or persistent installation.

## Inputs and deliverables

Inputs are ADRs 0003, 0005, 0007, 0014, and 0015; the exact Task 026 parent
record set; Task 024 catalog v3, current-source corpus, and candidate artifact;
the source lock; the exact locked Ksoloti extended tree; the Phase 4A overlay;
and the accepted catalog projection service.

Deliverables are this contract; the exact curation decision; source-review,
catalog-corpus-v4, and catalog-projection-v4 schemas; the deterministic review
record and JSONL packet; the one new implementation inside catalog v4; the
catalog selection successor; exact record set and completion summary; focused
tests and validators; fresh-root evidence; and coherent status, history,
roadmap, task, decision, and catalog-operation documentation.

## Curation and provenance rules

`mutable-instruments-derived` means the exact pinned source description or
license/attribution record explicitly states that the candidate uses or is
derived from Mutable Instruments code or data. Inspiration, folder names,
similar controls, or library-wide reputation are insufficient.

The provenance tag is implementation- and candidate-specific. Family search
shows the union only as a discovery facet; inspection must identify the exact
tagged implementations. A family remains in its ordinary function category.

The extended Rings object is an honest implementation variant of the existing
Physical-model Resonator family because both exact reviewed descriptions own
excitation plus configurable physical resonation. The topographic rhythm map
is not a pseudo-Euclidean or pitch-step sequencer, and the 24-engine macro
voice is not a sine, saw, PWM, drum, or bell family. They therefore remain
candidate-only. The macro voice also retains the source-manifest
`build-failed` fact without creating a Schuss build claim.

The factory Warps vocoder remains an uncurated candidate. The broader Warps
wrapper additionally retains its exact source statement that it does not
currently link. Neither source fact establishes a component contract, binding,
eligibility, compiler result, or executable support.

## Validation cadence

Focused checks cover the task contract, exact source census/hashes, attribution
policy, dispositions, schemas, new implementation, provenance projection, and
negative mutations. Adjacent regression covers Task 024 catalog loading,
search/inspect, record-set closure, and the retained Rings-reverb failure.

After implementation freeze, one expensive reproduction copies the repository
twice, maps both copies to the same exact external Git source, and requires
byte-identical generated Task 027 outputs under varied process settings. The
final aggregate contract/inventory/catalog suite covers the ordinary full-suite
check; it is not repeatedly run during iteration. Any correction after an
aggregate failure returns to focused and adjacent checks before one final
aggregate rerun.

## Acceptance tests

1. The contract validator confirms the goal, exact parent/source authority,
   scope, deliverables, IDs, decisions, evidence boundary, validation classes,
   and prohibited actions.
2. Generation reads only `patcher@08d3e6e...` Git bytes and the accepted Task
   024 factory candidate artifact; a missing/mismatched source root, commit,
   tree, decision hash, manifest, object, or license fails closed.
3. The extended census is exactly nineteen manifests and nineteen `.axo`
   wrappers with unique stable IDs and UUIDs; every entry has portable paths,
   hashes, exact declared author/license, one functional category, and one
   disposition.
4. Exactly three extended entries and fifty-three factory entries receive the
   Mutable-derived tag. The other sixteen extended entries are inventory-only
   and are not tagged by inspiration or adjacency.
5. Exactly seventy-two source-review entries are emitted in canonical order;
   no absolute path, host, timestamp, user name, or working-tree byte enters a
   durable artifact.
6. Catalog v4 retains all sixty v3 families and all prior implementations
   byte-for-byte and adds only `schuss-implementation-000096@1` under exact
   family `schuss-family-000010@1`.
7. The new implementation records exact pinned manifest, `.axo`, and license
   authority; it is `catalogued-only` and `unresolved` with no contract,
   binding, eligibility, result, artifact, or evidence reference.
8. Exactly six catalogued implementations are tagged and exactly five ordinary
   families are returned by a provenance-only Mutable-derived search. Inspect
   identifies tags per implementation without implying sibling ancestry.
9. The topographic sequencer, macro voice, and forty-eight attributed but
   uncatalogued factory objects remain tagged candidates. Warps vocoder remains
   uncurated; Warps `wrps` retains its explicit link-failure source fact.
10. The macro voice retains exact `h7-recommended` and `build-failed` source
    metadata labelled non-Schuss evidence; no support, ARM, hardware, real-time,
    or audible promotion follows.
11. The exact Task 025 Rings-reverb failed claim, unsupported eligibility,
    record bytes, and diagnostics remain unchanged and continue to validate.
12. Missing tag evidence, extra tags, changed dispositions, ambiguous family
    mapping, stale exact references, duplicate source identities, unsupported
    provenance filters, and source working-tree substitution fail closed with
    deterministic diagnostics.
13. Two independent in-process generations and two copied fresh roots produce
    byte-identical schemas, records, review packet, manifest, projection, and
    completion summary.
14. Task 027 reports catalog structural/provenance levels 1-2 only; levels 3-8
    are `not-run`, and compiler/build, Java, project, hardware, audible, and
    publication actions remain false.
15. Focused and adjacent suites pass, generated files are fresh, the complete
    diff and acceptance matrix are reviewed, and one final aggregate suite
    passes after freeze.

## Decisions Task 027 may make

- The source-review schema and artifact layout, canonical ordering, exact
  provenance tag spelling, portable Git evidence representation, and negative
  diagnostics.
- Whether an exact sourced object is candidate-only or an implementation of an
  already reviewed family, but only under the equivalence rules fixed above.
- The smallest catalog/projection successor required to expose per-object
  provenance tags through the existing shared search and inspect operations.

## Decisions Task 027 must not make

- A new family or category, family identity from source ancestry or path, an
  implementation preference, a component interface, compiler/backend/target
  semantic, or any evidence claim above the reproduced catalog boundary.
- A repair or alternate allocation for Rings reverb, a reduced Plaits engine
  set, a Warps support claim, or a promotion from source metadata.
- Mutation of accepted parent bytes, upstream checkouts, or source locks;
  ambient discovery; fallback; sessions/jobs; UI implementation; hardware or
  publication action.

## Activation state

The user's explicit Task 027 request and ADR 0015 activate this complete
contract. Completion does not activate Task 028, assign a number to the
deferred sessions/jobs lane, authorize UI implementation, or authorize Git or
hardware action.
