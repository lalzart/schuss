# Task 039: Desktop instrument library and bounded JUCE audition launch

Status: explicitly authorized; review-ready.

- Baseline commit: `74d87cf544e6e23423a2d4be03d07c33b1f13eb8`
- Kind: product-ui
- Activation: the user's 2026-08-22 instruction to start the approved
  Instruments-first desktop slice
- Next candidate after this task: Task 033 Phase 3 remains not activated

## Goal and why it exists

Make the Schuss desktop open into a compact library of the JUCE audition
instruments already created in Instrument Lab, while retaining the complete
patcher, authoring, build, and Ksoloti volatile-upload workflow as a separate
Workshop surface.

The product direction has shifted from opening directly into graph authoring
toward quickly selecting and auditioning complete controller-mapped JUCE
instruments. The existing application still contains valuable authoring and
Ksoloti capabilities, so this task changes the entry point without deleting or
reinterpreting those capabilities.

## In scope

- Add one repository-owned, noncanonical Instrument Lab audition-library
  manifest with exact prototype-index fingerprints, restrained presentation
  metadata, explicit JUCE standalone targets, and retained executable hashes
  where exact build evidence exists.
- Add a schema and deterministic generator/validator for that manifest, the
  additive v19 library/session operations, the v12 application capability
  description, and record set `schuss-record-set-000033@1`.
- Add a core-owned service that lists the exact library, validates prototype
  fingerprints, checks only declared repository-relative build artifacts, and
  starts or inspects bounded process-local native audition sessions.
- Require exact prototype ID/revision, a literal native-audition intent, an
  exact verified executable hash, and a repository-controlled locator before
  starting a process. Never accept a path or command from the renderer.
- Add the exact operations `instrument.library.list`,
  `instrument.session.start`, and `instrument.session.inspect` through the
  shared dispatcher and the closed Python/Rust desktop bridge.
- Make Instruments the default desktop surface and preserve the existing
  canvas as Workshop. Keep project setup inside Workshop so the library remains
  usable before a projects root is configured.
- Show truthful states such as verified local build, build required, stale
  build, research only, launch unverified, and controller unverified.
- Test process behavior with deterministic fakes only. No real JUCE application
  or audio/MIDI/device endpoint is opened during implementation or validation.

## Out of scope

- Rebuilding, fetching dependencies for, packaging, signing, installing, or
  distributing any JUCE application.
- Launching a real instrument during automated or visual verification, opening
  audio/MIDI endpoints, changing a controller Custom Mode, or making listening,
  physical-controller, deadline, or production claims.
- A dynamic plug-in ABI, VST3/AU packaging, a common multi-instrument audio
  host, in-process JUCE inside Tauri, or routing MIDI through React/Python.
- Automatic builds, arbitrary build-tree scanning, shell access, arbitrary
  process execution, user-supplied executable paths, or automatic relaunch.
- Canonical instrument, graph, collection, provider, runtime-factory, target,
  backend, or catalog promotion for any Instrument Lab prototype.
- Translating a JUCE prototype into Ksoloti firmware or changing the existing
  Ksoloti build/device workflow.
- DSP, control-map, standalone UI, source package, proposal, implementation
  bundle, or retained experiment changes inside the instruments.
- Git staging, commit, push, publication, USB access, firmware/SD mutation, or
  hardware action.

## Inputs and deliverables

Inputs:

- accepted ADRs 0014, 0016, 0017, and 0018;
- `docs/DESKTOP_UI_BOUNDARY.md` and the retained workspace/build-device tasks;
- `docs/workflows/instrument-development.md`;
- each exact `research/prototypes/*/prototype-index.json` authority;
- retained result files for exact standalone executable hashes; and
- the existing Tauri/React desktop, persistent Python adapter, shared
  dispatcher, application capability registry, and validation manifest.

Deliverables:

1. this active task and synchronized governance routing;
2. deterministic audition-library manifest/schema/generator and successor
   record set;
3. core list/start/inspect service and focused negative tests;
4. additive shared operations, capability declaration, and closed bridge
   allowlists;
5. Instruments-first React presentation plus preserved Workshop behavior;
6. updated desktop boundary and usage documentation; and
7. focused, adjacent, current-profile, and bounded visual results with the
   real-launch and device boundaries stated explicitly.

## Acceptance tests

1. The generated library is deterministic, stable-ordered, binds every entry
   to the exact prototype index bytes, rejects duplicate identities and path
   escape, and explicitly distinguishes launchable from research-only entries.
2. Listing validates the manifest and current prototype fingerprint before
   reporting an entry. It exposes no filesystem path, command, environment, or
   process handle to the renderer.
3. A declared executable is `verified-local-build` only when its exact regular
   executable exists below the repository build root and its SHA-256 matches
   retained expected evidence. Missing, unresolved, mismatched, symlinked, or
   escaping artifacts fail closed as nonlaunchable states.
4. Start accepts only exact ID/revision plus
   `explicit-native-juce-audition`, revalidates the executable immediately, and
   invokes a process factory with one repository-controlled executable and no
   shell. Unknown, stale, research-only, duplicate-running, and invalid-intent
   requests start nothing.
5. Inspect accepts only a process-local opaque session ID and reports running
   or exited state without leaking paths. Unknown sessions fail closed.
6. Core and bridge tests use fake processes and prove that no real app, audio,
   MIDI, USB, or hardware path is touched.
7. The desktop opens on Instruments, renders all retained entries in stable
   order, explains unavailable states, and enables Open only for an exact
   verified local build. Open requires an explicit click and reports the
   process-local result.
8. Workshop remains reachable in one action and retains project loading,
   patcher drawers, authoring, history, build, and explicit Ksoloti device
   presentation without semantic or operation changes.
9. The renderer remains free of filesystem, shell, process, network, USB,
   semantic-record, and executable-path authority; Rust and Python reject every
   operation outside their exact allowlists.
10. Focused service/schema/generator, Python bridge, Rust, React, accessibility,
    and production-bundle checks pass. A browser-mode visual smoke uses a fake
    bridge and launches no native instrument.
11. Adjacent desktop project/workspace/build-device behavior and shared
    application-capability/control-plane tests pass, followed by one `current`
    profile. Because shared schemas and dispatcher behavior change,
    `compatibility` runs once after implementation freeze; native,
    configured-source, reproduction, and release profiles do not apply.

## Decisions

This task may decide:

- compact Instruments/Workshop navigation, list density, status wording,
  keyboard/focus behavior, and component boundaries;
- the exact noncanonical audition-library schema and presentation fields;
- bounded process-local session IDs and inspection states;
- the exact additive v19 request/result and v12 capability vocabulary required
  by the three new operations; and
- deterministic repository-relative build locators for already retained
  standalone evidence.

This task must not decide:

- canonical product identity or promotion for a prototype;
- provider, factory, collection, target/backend, or graph compatibility;
- whether any instrument sounds good, meets a callback deadline, works with a
  physical controller, is Ksoloti-compatible, or is distribution-ready;
- a general process runner, plug-in system, common host ABI, automatic build
  service, or arbitrary local application launcher;
- changes to instrument DSP, mappings, standalone windows, source lineage, or
  proposal/implementation authority; or
- permission to launch a real JUCE app, connect hardware, install, stage,
  commit, push, publish, flash, or write removable media.

## Validation cadence

1. Run generator/schema and service unit tests first, including fake-process
   and filesystem negative cases.
2. Run bridge allowlist/request tests, then React component tests/build and
   Rust tests.
3. Run affected project/workspace/build-device and application capability /
   dispatcher regressions.
4. Review the complete diff, generated freshness, path/process boundaries, and
   evidence wording before one `current` profile.
5. Run one browser-mode visual smoke through the read-only list operation. Do
   not select Open and do not invoke the native Tauri launch path.
6. After implementation freeze, run `compatibility` once. No configured source,
   native instrument build, reproduction, release, audio/MIDI, or hardware
   profile is required.

## Review-ready results

- The generated exact library contains five noncanonical prototype revisions.
  Generative Drum Machine 0.6, Tide Pit Gills 0.1, and Wirefall 0.2 match their
  retained executable hashes. Cinderwheel 0.1 is build-required because no
  current executable hash is frozen, and Wirefall 0.1 remains research-only.
- Core list/start/inspect behavior passes seven focused tests. Start and exit
  behavior use only an injected fake process; public results expose no path or
  command.
- The closed Python bridge, Rust allowlist, complete React suite, TypeScript
  production build, desktop structure validator, and affected shared
  dispatcher/capability/workspace/build-device regressions pass.
- Browser-mode inspection showed the five-entry Instruments home, disabled
  unavailable action, enabled verified action, and one-action Workshop return
  with no overlay or console warnings. Open was not selected.
- Manifest-defined `current` passed all 8 checks. The frozen `compatibility`
  rerun passed 486 tests with 23 historical skips.
- `cargo test` passed all 3 Rust tests. `cargo fmt --check` was unavailable
  because the installed Rust toolchain has no `rustfmt` component; no component
  was installed.
- No real JUCE application, audio/MIDI endpoint, USB/device path, build,
  package, commit, push, or publication action was performed.
