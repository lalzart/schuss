# Task 044: Layerwell 0.2 embedded-source sampler

Status: complete locally in the current uncommitted working tree for the user's
2026-08-24 request to replace the minimal Layerwell source shell with an
embedded instrument workspace using exactly Tide Pit and Pamplist, and to add
corrective loop-boundary trimming. Completion is bounded to source,
host-structural, objective host-signal, and authenticated target-build evidence;
the app was not launched.

## Goal and why it exists

Build Layerwell 0.2 as one desktop instrument in which selecting Tide Pit or
Pamplist reveals that source's complete playable control surface inside the
sampler. A permanent lower sampler strip owns capture, three synchronized
layers, mixing, and non-destructive start/end trim. The task exists because
Layerwell 0.1 proved source composition and capture mechanics but did not give
the performer enough visual or direct control over the selected instrument.

The literal working artifact is a built but unlaunched authenticated
`Layerwell.app`, plus deterministic Core, control, trim, render, and embedded-
panel model evidence. The maximum evidence level is target build and objective
host signal. It does not imply application launch, visual approval, live
callback timing, physical controller operation, listening approval, packaging,
or production integration.

## In scope

- A frozen Layerwell 0.2 new-design proposal and ready Sonic Research Lab
  implementation bundle before DSP or JUCE implementation edits.
- Exactly two resident sources: Tide Pit Gills 0.1 and the frozen accepted
  Pamplist 0.6 Core. Generative Drums is removed from Layerwell only and remains
  unchanged as an independent instrument.
- Read-only reuse of both source Cores, control reducers, UI/presentation
  models, exact source/dependency authorities, and retained license notices.
- One Layerwell-owned audio/MIDI host. Embedded panels must not instantiate a
  second source Core, audio device, MIDI endpoint, application, or process.
- A source-faithful Tide Pit panel with all sixteen encoder positions, eight
  button positions, four display lines, accepted mode state, and a bounded
  source scope.
- A source-faithful Pamplist panel with eight pages, Voice/Motion context,
  sixteen contextual controls, Run/Stop, Global/Clear behavior, dependency
  help, and bounded seven-lane impact history.
- Panel controls dispatch through Layerwell's source adapters and existing
  source reducers. Every displayed value comes from the accepted Layerwell
  snapshot; raw GUI or MIDI input is never presentation authority.
- Three source-only synchronized stereo layers plus one staging store, with
  the existing provisional capture/replace/cancel semantics and fixed maximum
  32-second storage at exactly 48 kHz.
- One shared non-destructive playback window `[trim_start, trim_end)` for the
  session. Trim is available only while capture is idle and exactly one layer
  is occupied, so later layers cannot be desynchronized silently.
- Start and end trim may move only inside the occupied layer's recorded sample
  extent, must preserve at least 24,000 frames, never copy or rewrite committed
  samples, and immediately reset shared playback phase to zero after acceptance.
- Later captures record exactly the current trimmed cycle from the selected
  source into offset-zero staging storage. After a second layer commits, the
  trim controls become read-only until only one layer remains.
- A regular Launch Control 3 DAW-mode mapping: Page selects Tide Pit/Pamplist;
  Control owns the selected source surface; Mixer retains layer/capture/mix and
  adds start/end trim on previously unused encoders with accepted feedback.
- A restrained JUCE layout with one global audio/MIDI header, one replaceable
  embedded source panel, and one permanent sampler strip.

## Out of scope

- More than Tide Pit and Pamplist; any change to Generative Drums itself; an
  arbitrary source browser, plug-in host, separate-process embedding, or audio
  routing between standalone applications.
- Changes to Tide Pit or Pamplist DSP equations, defaults, musical mappings,
  source authority, accepted identity, standalone UI evidence, or canonical
  records. Layerwell-owned presentation adapters may reproduce those exact
  public semantics without rewriting either frozen standalone source.
- Per-layer independent loop periods, timestretch, resampling, reverse,
  slicing, transient detection, automatic zero-crossing search, destructive
  cropping, undo history, waveform editing, overdub, composite resampling,
  sample import/export, persistence, presets, or external/MIDI clock.
- Canonical Layerwell family, graph, provider, runtime, project, machine,
  audition-library entry, distribution, signing, notarization, or publication.
- Application launch, endpoint enumeration/opening, physical controller or USB
  access, listening claims, staging, commit, push, upload, or hardware action.

## Inputs and deliverables

### Inputs

1. `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, ADRs 0016-0018,
   `docs/workflows/instrument-development.md`, and the completed Task 042
   Layerwell 0.1 authority.
2. Completed but uncommitted Task 043 Pamplist 0.6 canonical/prototype/source
   authority. Task 044 preserves those inherited bytes and does not adopt its
   unrelated desktop/catalog changes.
3. Tide Pit's exact Task 036 source-reimplementation handoff, public Core,
   control map, UI model, scope pattern, and notices.
4. Pamplist 0.6's exact proposal, ready bundle, public Core, contextual surface
   model, activity reducer, configured macro-voice source authority, and notices.
5. Layerwell 0.1 Core, controller adapter, source-only capture storage, render
   evidence, authenticated JUCE seam, and source-composition lessons.
6. The regular Novation Launch Control 3 repository topology and official DAW-
   mode protocol authority; synthetic messages remain distinct from a physical
   device result.

### Deliverables

1. `research/proposals/layerwell-r02.md` and a ready revision 0.2 bundle under
   `research/prototypes/layerwell/contract-r02/`.
2. Revised portable Layerwell Core and Tide Pit/Pamplist source adapter with
   exact control termination, rich accepted source presentation, and no source
   project byte mutation.
3. Shared-window trim state, events, diagnostics, deterministic tests, and
   retained objective render evidence.
4. Source-faithful embedded Tide Pit and Pamplist JUCE panels hosted by the one
   Layerwell engine, plus a permanent three-layer sampler strip.
5. Updated regular Launch Control 3 semantic mapping and synthetic feedback
   tests for the two-source surface and trim controls.
6. Updated prototype topology, dependency closure, notices, index, handoff,
   results, gaps, and authenticated unlaunched target-build receipt.

## Acceptance tests

1. The exact proposal and implementation-ready bundle validate before the
   first Layerwell Core, source-adapter, controller, or JUCE implementation edit.
2. Task 043, Pamplist prototype/source authority, Tide Pit Task 036 authority,
   and both source projects' applicable focused suites remain valid and their
   frozen source bytes are unchanged.
3. One parent build links Tide Pit and Pamplist with one Instrument Lab
   authority and no duplicate source, target, or global symbol ambiguity.
4. Source selection retains source state, advances only the selected Core, and
   projects every embedded control from accepted source state.
5. Exhaustive panel-model tests cover every Tide Pit encoder/button/display and
   every Pamplist page/context/control/action/help/activity field. UI actions
   terminate at the existing source reducer or an exact existing public action.
6. The first capture retains the revision 0.1 immediate-start/stop-exclusive
   contract, 24,000-to-1,536,000-frame bounds, provisional owner swap, and
   source-only storage.
7. Start/end trim accepts only a valid window within the sole occupied layer,
   preserves all committed sample bytes and owner pointers, resets phase to
   zero, and produces exact playback of the selected subrange with the existing
   deterministic seam treatment.
8. Trim rejects busy capture, zero or multiple occupied layers, non-finite or
   out-of-range values, and windows shorter than 24,000 frames without changing
   accepted trim, phase, storage, or layer state.
9. Later captures wait for phase zero, record exactly the trimmed length into
   offset-zero storage, align through repeated playback, and lock trim after a
   second layer commits. Clearing back to one layer restores bounded inward
   trim only for that remaining layer's recorded extent.
10. Frozen 16/64/128/512-frame timelines produce exact accepted events, trim
    windows, source progression, layer state, PCM, protocol traces, and metrics;
    an intentionally untrimmed comparator must diverge in the trim condition.
11. Repeated `process()` performs no allocation, lock, file, endpoint, JSON,
    paint, or unbounded work; all samples remain finite and within `[-1, 1]`.
12. The authenticated JUCE 8.0.15 target builds with the embedded panels and
    one host engine without launching or opening endpoints. Focused, affected
    source, prototype, current, and one configured relocated reproduction gate
    pass after implementation freeze.

## Decisions

### Task 044 may make

- Layerwell-owned panel classes, neutral fixed-capacity presentation structs,
  GUI-to-Core mailbox mechanics, layout dimensions, colours inherited from the
  source presentations, scope/activity display reduction, and sampler-strip
  organization.
- The exact trim UI units and relative-encoder step sizes, provided the Core
  state remains integer frames and sample-window semantics remain exact.
- The smallest parent-only CMake composition and private namespace isolation
  that preserves both source project bytes and standalone defaults.
- Additional focused fixtures, comparators, diagnostics, and build-receipt
  inputs needed to make the revision deterministic and auditable.

### Task 044 must not make

- A new Tide Pit or Pamplist musical control, default, equation, source
  revision, canonical record, or standalone evidence claim.
- A third source, generic embedded-panel ABI, arbitrary executable/plugin host,
  per-layer asynchronous looping, automatic editing policy, persistence, or
  external transport authority.
- Physical Launch Control behavior not stated by its authority, or device,
  visual, real-time, audible, distribution, and production success inferred
  from synthetic, structural, render, or target-build evidence.
- Mutation, staging, committing, pushing, publishing, or deleting inherited
  Task 043 work or any unrelated worktree content.

## Validation classification

- Focused: Layerwell Core/source/panel-model/controller/snapshot/allocation
  tests plus retained render checks while behavior is changing.
- Adjacent: Tide Pit focused authority/regression and Pamplist 0.6 source,
  focused, retained-evidence, and prototype freshness checks.
- Configured/native: one final exact configured Pamplist source build,
  Release plus ASan/UBSan Layerwell tests, and authenticated JUCE target build.
- Reproduction: one relocated Layerwell Core/test reproduction with the exact
  configured Pamplist source supplied as a runtime prerequisite.
- Routine: Schuss `current` once after implementation and documentation freeze.
- Full compatibility/release is not required because this noncanonical
  prototype does not change shared schema, runtime/provider, or distribution
  boundaries; a broad failure is diagnosed with its affected focused check.

## Stop condition

Stop when the frozen two-source Layerwell 0.2 contract, portable Core, embedded
panel models, trim behavior, controller protocol, retained evidence, metadata,
and authenticated unlaunched app build pass their applicable gates. Do not
launch the app, select an endpoint, access hardware, claim visual/listening
quality, alter canonical records, or perform a Git/publication action without
separate explicit authorization.
