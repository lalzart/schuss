# Shared Authenticated Mutable DSP Source Package Pilot

> Status: proposed
> Proposal revision: 0.2
> Work type: source-reimplementation
> Original request: Extract Tide Pit Gills' existing audited 21-file Mutable
> Instruments dependency closure into one shared immutable Schuss source
> package, migrate Tide Pit to consume it without duplicated source bytes, and
> prove its exact source comparator remains unchanged.
> Implementation target: Schuss shared source-package support plus the Tide Pit
> Gills prototype as the first behavior-preserving consumer.
> Decision gate: documentation is approved in this chat; implementation is
> reserved for a new chat and begins only after live governance and readiness
> checks.

## 1. Port thesis and identity

### One-sentence thesis

Make one authenticated, immutable Mutable/Ksoloti source closure reusable by
multiple Schuss instruments without turning source provenance into a catalog
identity or changing Tide Pit's sound, timing, state, or host behavior.

### Identity to preserve

The pilot preserves two independent identities:

1. the exact 21-file Mutable source closure from Ksoloti commit
   `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`; and
2. the complete Tide Pit Gills portable Core and standalone behavior already
   accepted at Schuss commit
   `2b0180a47f7ac03011f56e9683c77060c8080f09`.

The source package is dependency evidence and reusable build input. It is not
an instrument, DSP graph, component contract, object collection, catalog
family, runtime factory, or implementation provider.

### Working definition and evidence level

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| `packages/dsp_sources/mutable_ksoloti_v1/` plus a Tide Pit consumer using it | host structural and host signal | One immutable 21-file copy, source-package validation, independent include/link smoke test, Tide Pit Release/sanitizer/JUCE suites, and exact `39d8...ad2b` audio equality all pass | New Mutable catalog support, provider eligibility, real-time fitness, device behavior, listening, packaging, or distribution approval |

## 2. Scope and decision rights

### Goal and why

Remove repeated vendoring and repeated source-intake work from future
Mutable-based instruments while retaining exact revision, per-file hashes,
license evidence, consumer-specific numeric profiles, and fail-closed builds.

### In scope

- Introduce one repository-owned shared source-package root for the exact
  already-audited Mutable/Ksoloti closure.
- Preserve the upstream directory layout beneath an immutable `upstream/`
  boundary.
- Add a deterministic package lock, component groupings, notices, and a
  reusable validator.
- Expose source-root and component-file discovery without creating a runtime
  ABI or compiled provider.
- Migrate Tide Pit's provider-local `tide_pit_mutable` build wrapper to the
  shared package.
- Remove Tide Pit's duplicate `third_party/ksoloti` bytes only after the shared
  copy and all references validate.
- Preserve Tide Pit's separate Gills source, port overlays, random-state
  ownership, compile flags, Core, UI, controller map, renderer, and evidence.

### Out of scope

- Adding any Mutable algorithm beyond the frozen 21-file closure.
- Importing a whole Mutable or Ksoloti repository.
- Modifying any byte below the shared `upstream/` boundary.
- Creating or changing a catalog family, implementation, source-release
  semantic record, component contract, graph node, binding, provider, runtime
  factory, target/backend eligibility, or collection.
- Activating or extending Task 033 Phase 3; that phase may only generate the
  existing seven-factory registry.
- A monolithic `libmutable`, public provider SDK, dynamic loading, JUCE DSP
  provider, plugin format, UI redesign, hardware action, or listening claim.
- Unifying consumer-specific RNG, memory, block-size, numeric, sanitizer, or
  optimization policy.

### Inputs and deliverables

Inputs are ADR 0017; Task 033's accepted source/provider separation; Schuss
commit `2b0180a`; Tide Pit's `SOURCE_LOCK.json`, notices, CMake, source validator,
golden test, render experiment, results, and gaps; and the authenticated Ksoloti
source root at revision `08d3e6e1` supplied only at validation time.

Deliverables are:

1. `packages/dsp_sources/mutable_ksoloti_v1/` with immutable upstream bytes;
2. `SOURCE_PACKAGE.json` with exact file, manifest, component, revision, and
   license facts;
3. `THIRD_PARTY_NOTICES.md` retaining the reviewed MIT notice;
4. a package CMake helper that exposes one header/include target and exact
   component source lists without compiling a provider;
5. a reusable source-package validator and focused negative tests;
6. a Tide Pit CMake/source-lock migration with no duplicate Mutable bytes; and
7. retained implementation results, gaps, exact commands, and fingerprints.

### Acceptance tests

Acceptance is the complete matrix in sections 9, 10, and 12. The decisive
gate is unchanged Tide Pit Q27 SHA-256
`39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b`.

### Decisions this work may make

- Exact package-internal JSON keys, deterministic encoding, component names,
  validator CLI, and CMake helper API.
- Whether the include surface is one CMake `INTERFACE` target plus component
  lists or an equivalently non-provider source-discovery seam.
- Exact negative fixtures and focused validation placement.
- Safe removal of the duplicate Tide Pit source subtree after byte identity,
  reference closure, and recovery are proven.

### Decisions this work must not make

- Any semantic ID, record-set successor, provider ABI, runtime factory, graph,
  catalog, collection, target/backend, or availability decision.
- Any source equation, lookup table, resource byte, license interpretation,
  Tide Pit control/state behavior, or reference-oracle change.
- Any claim that all Mutable Instruments source is MIT, portable, mutually
  compatible, or supported merely because this exact closure is reviewed.
- Any stage, commit, push, package install, network fetch, audio/MIDI device
  action, publication, or distribution action without separate authorization.

## 3. Source authority and lineage

| Portable source ID | Revision | Dirty-state scope | Authority | Forbidden mutations |
|---|---|---|---|---|
| `ksoloti:firmware/mutable_instruments` | `08d3e6e1e2b61230308c20a15ded58ffdaf4656c` | `firmware/mutable_instruments` was clean when rechecked | `https://github.com/lalzart/ksoloti.git`; exact local root supplied at validation time | Any upstream-byte edit, line-ending normalization, generator substitution, or unreviewed file addition |
| `schuss:tide-pit-gills-port` | Schuss `2b0180a47f7ac03011f56e9683c77060c8080f09` | clean tracked baseline before this proposal | tracked Tide Pit proposal, package, tests, and retained results | Any musical, state, control, renderer-timeline, or oracle rebaseline |

The 21-file manifest algorithm is SHA-256 lines containing digest, two spaces,
repository-relative path, and LF, sorted as complete lines before hashing. The
required manifest is
`0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f`.

| Relative path below Ksoloti root | SHA-256 | Role | License and notice |
|---|---|---|---|
| `firmware/mutable_instruments/braids/braids_resources.cpp` | `b28a075193e7568e53621361ba95e3c9ff952b350eafe02e47dfb070b76f6b53` | normative resource TU | reviewed MIT header; Emilie Gillet notice retained |
| `firmware/mutable_instruments/braids/resources.h` | `b718316c76f53a5c6f7235c163dab7814c14eb566316ef27d316bc03d344c85d` | normative resource declarations | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/clouds_resources.cpp` | `ff5aad218cb381d1a1e34bfb67361493a7a922202bb973abe7dfa5aa210c37f2` | normative resource TU | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/resources.h` | `02d89753235e62fcb8b1a180c333518159bfa222999214f7a28c07e3f54d2f60` | normative resource declarations | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/dsp/audio_buffer.h` | `110c63276ec84cbb211f98a5897d075307471da25ae1845da82dac504d052657` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/dsp/frame.h` | `203a758cd626f7d5ca0d3bd70457ba15b36d2ddc9fea5a2c56eab3cdd15ec3b4` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/dsp/grain.h` | `08feb5ac5408e2cb30eb037a844f6ee187d8dedd53fee913d1b5ab2c74ebfac3` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/dsp/mu_law.h` | `b35c5c89c66632efeb86c94411dbe6fdbb618a9ddbfbfd741168728fd1a7d0a9` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/dsp/parameters.h` | `1d41ec7d86063204ef8f2301ee62170df0cf5933a955545be37e9ab400c46e64` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/dsp/fx/fx_engine.h` | `8bd367622b97247a371f70871446971b63191df51b7d2a4e06163c86f3408641` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/clouds/dsp/fx/reverb.h` | `721226338def6f28adc60215073ce97ef1a3f6ef0c4d8fc889b5056d7717e174` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/stmlib.h` | `aa98ad93fe5862bb2e8f7153f886439c6b95783ae08168ac6d32bd7edb91d8e3` | normative support | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/dsp/cosine_oscillator.h` | `32aabaf95eec930ead9e02b88d8ddaf4d52262cfb9039bd1eb07ad26230de5c8` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/dsp/dsp.h` | `756219ce25649d28e03faddcf2f5d6a072d8a72e774b39374a82d80f644ac3f6` | normative platform DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/dsp/filter.h` | `bc647a8ab7441c381a0c72d56ae84c7dbeeecf55763941835c8438a6aab131e0` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/dsp/rsqrt.h` | `a827501522f85d7045783619404366eb0fb338ede3cb1480650cf5f038d68c91` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/dsp/units.cpp` | `0acbe230ffaa2d181ba285fce54f2fd0b2339b3ec163a1dd00c946e6bf82ea4a` | normative linked TU | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/dsp/units.h` | `be38219743728af8e081373371153eab8a3461d8d01128f81b0dfee2be7bff2d` | normative DSP | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/utils/dsp.h` | `c0fad7f6b5b20f053d184614a35baf595e41f1394db53f80ac742d7467dbbe1b` | normative support | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/utils/random.cpp` | `145c4d7a30e373d001fd664ce6f97a475458f7dc8286252d24ca6f592e0cdb93` | authoritative but not linked by Tide Pit | reviewed MIT header; notice retained |
| `firmware/mutable_instruments/stmlib/utils/random.h` | `423f01e905fa279864878f34e42136ad1eb37a33dad58739affaaab06b793e5d` | normative random API | reviewed MIT header; notice retained |

## 4. Dependency and license closure

| Dependency | Exact revision/files | License | Authentication | Distribution disposition |
|---|---|---|---|---|
| Ksoloti Mutable closure | commit `08d3e6e1`; exact 21 files above | reviewed per-file MIT headers and retained Emilie Gillet notice | per-file hashes, sorted manifest, optional external source-root comparison | private development reviewed for this closure; broader distribution remains separate |
| Tide Pit Gills source | import `53287e49e5bcc5fb0d73b546d88431f82467f969`; six-file manifest `6cbb9842...aaa85` | MIT project with attributed Mutable DSP | existing Tide Pit source lock and golden | unchanged; local standalone trial |
| CMake | minimum 3.22; observed 4.4.2 | tool dependency | executable version plus deterministic focused builds | development tool only |
| JUCE consumer build | 8.0.15 commit `91ad83ae34a81e0833b1a2b0866f54846370ae53`, archive SHA `04f8d505...3e70` | JUCE boundary | existing authenticated Tide Pit build | unchanged and outside source package |

No network fetch is required for the pilot. No absolute source path is stored
in a durable artifact.

## 5. Source behavior contract

### Signal flow

The shared package performs no processing. It supplies exact source bytes to a
consumer-owned build wrapper. Tide Pit's signal flow remains:

```text
shared immutable Mutable bytes
  -> Tide Pit provider-local compile profile and overlays
  -> Tide Pit 48-kHz / 16-frame Q27 Core
  -> renderer or JUCE host
```

### Parameters, defaults, and curves

The package owns none. Tide Pit's existing parameters, audition preset,
quantizers, soft pickup, modes, and defaults remain instrument-owned and
byte-for-byte unchanged.

### State, timing, randomness, and buffers

The package owns no runtime instance. Tide Pit retains its explicitly zeroed
source object, exact five-allocation/251,408-byte arena, 48-kHz/16-frame
schedule, per-instance compatible stmlib random state, mutation RNG, recorder,
grains, reverb, waveguides, and host bridge.

### Gestures, modes, display, and feedback

The package owns none. Tide Pit's complete state machine, synthetic source
gestures, display strings, controller map, UI snapshots, and diagnostic
semantics remain unchanged.

### Platform and numeric assumptions

Raw source bytes do not imply a numeric profile. The Tide Pit consumer keeps
`TEST=1`, `BUFSIZE=16`, C++17, Q27, Apple clang 16 `-O2` golden profile, its
defined-C++ voice overlay, and its sanitizer instrumentation. Another consumer
must freeze its own profile.

### Known source quirks

- Mutable's global random API is not safe as shared cross-instance ownership;
  Tide Pit continues to override it locally.
- Source code contains embedded/ARM assumptions; source availability does not
  imply desktop portability.
- Clouds reverb initialization relies on storage history outside `Init`; Tide
  Pit's zero-storage construction remains required.
- The shared package includes `random.cpp` as authenticated source evidence but
  Tide Pit deliberately does not link it.

## 6. Fidelity matrix

| Behavior or subsystem | Classification | Equivalence rule | Evidence |
|---|---|---|---|
| 21 upstream files | preserve | each byte and sorted manifest identical | package validator plus external source-root check |
| Upstream relative layout | preserve below `upstream/` | every include resolves without source edits | include/link smoke test and Tide Pit build |
| Repository location | allowed change | one shared copy replaces Tide Pit-local duplicate | duplicate/path audit |
| Component group metadata | allowed change | metadata names exact existing files and carries no support claim | schema/negative validator tests |
| Tide Pit compile wrapper | allowed path-only change | same sources, definitions, flags, overlays, link result, and diagnostics | CMake diff review and native tests |
| Tide Pit audio/state/control | preserve | exact golden, render matrix, snapshots, and adapter parity unchanged | existing Release, sanitizer, JUCE, and render suites |
| Executable byte hash | exclude | path/debug/archive metadata may differ; output and behavior are authoritative | record new executable hashes without equality claim |
| Other Mutable projects or revisions | exclude | no copied file, component, or compatibility claim | package extras check |
| Canonical Schuss provider/catalog integration | exclude | no semantic record or runtime change | record/diff audit |

## 7. Port seams and architecture

| Source seam | Portable adaptation | Fixed capacity or timing | Failure behavior | Test |
|---|---|---|---|---|
| Repository path | relocate exact files beneath shared `upstream/` | exactly 21 files | missing, extra, duplicate, or hash drift fails | source-package validator negatives |
| Include root | package CMake helper exports one portable root | no absolute durable path | missing package or wrong revision fails configure | copied-root configure/build |
| Component selection | manifest names exact file sets; helper resolves paths | finite closed sets only | unknown component or file fails | helper/validator tests |
| Consumer compilation | Tide Pit retains local static wrapper and flags | existing three linked TUs | compile/link/golden failure blocks migration | Tide Pit native suite |
| Port overlays | remain Tide Pit-owned outside shared upstream | existing exact generated hashes | source or generated drift fails | Tide Pit source lock and golden |

### Portable Core boundary

The package has no Core API. Consumer Cores include exact headers and own all
runtime state. No Mutable type enters Schuss graph identity or the public
`schuss_rt` ABI.

### Renderer and reference boundary

The existing Tide Pit renderer and golden test are unchanged consumers. They
are the regression oracle for the path extraction, not deliverables of the
source package itself.

### Host, MIDI, controller, and UI boundary

No host, MIDI, controller, or UI code moves into the source package. All such
files must remain byte-identical unless a mechanical include/CMake path update
is unavoidable and independently reviewed.

## 8. Controller and UI reuse

| Reused artifact | Fingerprint | Reused mechanism | Instrument-specific replacement |
|---|---|---|---|
| Tide Pit control map | `a91f4ee46b3339f455d5d277f4b8f25d378c652eb946d6c017076e44fd356f60` | existing semantic bindings and generated descriptors | none |
| Launch Control 3 topology | `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b` | existing surface profile | none |
| Tide Pit JUCE UI | tracked at Schuss `2b0180a` | authoritative Core snapshot reflection | none |

Controller and UI behavior are adjacent regression inputs only. This task does
not modify them.

## 9. Reference oracle

| Field | Bound value |
|---|---|
| Oracle kind | bit-exact Tide Pit source-bound comparator |
| Source fixtures and commands | existing `tide_pit_reference_golden`; 12,000 source quanta |
| Sample rate and block sizes | internal 48 kHz/16 frames; outer 16/64/128/512 matrix |
| Seed and convention | stmlib `0x21`; existing planar little-endian Q27 fixture |
| Metrics and tolerances | exactly 1,536,000 bytes; SHA-256 `39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b`; peak 39,182,832; RMS 14,011,444.589680206 |
| Retained outputs and hashes | existing Tide Pit `RESULTS.md` and render manifest |
| Explicit proof limits | proves Tide Pit consumer equivalence on the frozen macOS profile, not arbitrary consumers, cross-platform byte identity, real-time, device, listening, or distribution behavior |

## 10. Minimal experiment

### Primary bounded equivalence claim

Relocating the exact 21 files into one shared source package and changing only
Tide Pit's dependency paths does not change its source-bound audio, state,
adapter, render, or target-build results.

### Conditions and comparator

1. Validate the shared package alone with no Tide Pit path available.
2. Compile a minimal package-consumer fixture that resolves declared component
   groups and links the three Tide Pit resource/unit translation units.
3. Configure and build Tide Pit Core from the shared package.
4. Run Release and fail-fast sanitizer suites.
5. Build the authenticated JUCE standalone and run the full seven-test suite.
6. Run the four-partition render matrix and compare the canonical Q27 stream.
7. Repeat package validation from a copied root or equivalent path-relocation
   fixture where the location itself is the tested fact.

### Signals, gestures, and extremes

Use the existing source-bound clean reference, performance state trace, and
parameter-extremes conditions without editing their JSON or expected hashes.

### Objective measurements

Per-file and manifest hashes, component closure, compile/link success, golden
bytes/hash/peak/RMS, complete snapshots, MIDI adapter parity, finite samples,
event/drop diagnostics, sanitizer output, and duplicate-source count.

### Listening protocol

Not required for a byte-exact dependency relocation. No new audible claim is
made. Any audio difference is a failure, not a listening decision.

### Stop or pivot conditions

Stop if source or license identity drifts, a source byte must be edited, the
golden differs, the duplicate copy cannot be removed, another consumer needs a
different revision under the same identity, package metadata implies runtime
support, or the change requires Task 033 semantic/provider allocation.

## 11. State-operation summary

The source package has no initialization, Reset, Panic, Freeze, mode, recall,
disconnect, or recovery state. Tide Pit owns all of those operations and must
produce the same complete snapshots and diagnostics before and after the
migration. Package validation is pure, deterministic, read-only, and has no
process-global cache.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Expected result | Artifact |
|---|---|---|---|---|
| One exact shared source copy exists | package file/extras/hash/manifest validator | source | 21/21 exact, no extras | `SOURCE_PACKAGE.json` plus validator output |
| Package can be consumed independently | compile/link fixture outside Tide Pit source root | host structural | pass | focused CTest or equivalent |
| Tide Pit has no duplicate Mutable subtree | scoped filesystem/reference audit | source | only shared package owns the 21 upstream bytes | retained audit |
| Tide Pit behavior is unchanged | Release Core and golden suite | host structural/signal | 5/5 and exact `39d8...ad2b` | CTest/golden output |
| Portability seam is defined C++ | fail-fast ASan/UBSan with all Mutable TUs instrumented | host structural | 5/5, no sanitizer diagnostic | sanitizer log |
| Host adapter and renderer remain exact | authenticated JUCE suite and render matrix | target build/host signal | 7/7, byte-equal 16/64/128/512 | CTest/render manifest |
| No product/provider semantics changed | schema/record/provider/native-registry diff audit | governance | zero changes | review output |
| Routine workspace remains valid | `python3 tools/validation/run.py --profile current` | integration | all selected checks pass | validation report |

## 13. Implementation plan

### Implementation-ready contract

- Proposal path: this file.
- Task contract: `docs/tasks/036-shared-authenticated-mutable-dsp-source-package-pilot.md`.
- Source root is runtime-only and never stored in durable files.
- The new chat must verify both fingerprints, live HEAD/remote/routing, and the
  authenticated Ksoloti root before moving source bytes.

### Expected files and stages

1. Create and validate the shared package lock and exact upstream copy.
2. Add package component metadata, CMake source-discovery seam, validator, and
   focused negative tests.
3. Migrate Tide Pit's source validator and CMake to the package.
4. Remove the duplicate Tide Pit `third_party/ksoloti` subtree after recovery
   and reference checks.
5. Run focused package/Tide Pit tests, freeze review, affected native checks,
   render matrix, and one `current` profile.
6. Record results/gaps without activating production provider semantics.

### Focused and adjacent tests

- Package manifest determinism and per-file/extras/path validation.
- Tampered byte, missing file, extra file, duplicate path, unknown component,
  path escape, wrong revision, and missing-notice negatives.
- Independent include/link smoke test.
- Tide Pit source-lock, Core, golden, control map, JUCE adapter, render, and
  standalone build checks.

### Expensive, device, and listening gates

Run only affected Tide Pit native/sanitizer/render checks once after freeze.
No device, real-time, listening, compatibility, release, or configured-source
profile is required unless implementation expands beyond this contract.

### Deferred production work

A later explicitly activated task may decide whether a second real consumer
justifies compiled shared targets, a native provider, canonical source-release
evidence anchors, catalog availability, or distribution packaging.

## 14. Intentional deviations

| Deviation | Why required | Musical/technical effect | Approval | Test |
|---|---|---|---|---|
| Move exact Mutable bytes from Tide Pit-local `third_party/ksoloti` to one shared package path | eliminate repeated source copies and audits | none expected | user requested documentation now and implementation in a new chat | byte hashes, duplicate audit, exact Tide Pit golden |
| Replace Tide Pit-local dependency paths with package component discovery | make source reusable while keeping compile policy local | none expected | same approval | CMake review, suites, render matrix |

## 15. Claim-to-source ledger

| ID | State | Claim | Source | Proof gap |
|---|---|---|---|---|
| SP-001 | EVIDENCE | Tide Pit currently vendors an exact 21-file Mutable closure | Tide Pit `third_party/SOURCE_LOCK.json` at Schuss `2b0180a` | none for current bytes |
| SP-002 | EVIDENCE | The closure originates at Ksoloti commit `08d3e6e1` and its source subtree was clean when checked | local authenticated Ksoloti Git state and source lock | machine-local root must be resupplied in new chat |
| SP-003 | EVIDENCE | ADR 0017 separates source releases from providers, graph identity, and collections | accepted ADR 0017 | no implementation-provider authorization follows |
| SP-004 | INFERENCE | One shared immutable copy will reduce repeated intake and drift for future Mutable consumers | Cinderwheel/Tide Pit workflow comparison | second real consumer not yet built |
| SP-005 | HYPOTHESIS | Package-level component metadata is reusable without freezing a compiled provider API | proposed compile-only consumer fixture | must be falsified by implementation and later consumer |
| SP-006 | UNRESOLVED | Whether two real consumers can share compiled Mutable targets under one numeric/profile contract | only Tide Pit is an authenticated desktop consumer | defer until a second instrument exists |

## 16. Open questions and decision gate

### Open questions

- A second real instrument may require a different source revision or compile
  profile; this pilot must permit parallel versioned packages rather than
  mutating `v1`.
- Compiled source targets may become reusable later, but Tide Pit alone is not
  enough evidence to freeze their ABI, flags, or symbol-ownership policy.
- Distribution beyond private development still needs an exact package-level
  license review even though the current 21 files carry reviewed MIT headers.

### Recommended architecture

Create an immutable raw-source package with exact component metadata and a
non-provider CMake discovery seam. Keep the compiled `tide_pit_mutable` target,
numeric profile, random override, storage, and portability overlay inside Tide
Pit. Require a second real consumer before extracting a shared compiled
provider.

### Approval reference

On 2026-08-20 the user explicitly requested this task documentation and asked
for implementation in a new chat. This proposal does not activate work in the
current chat or alter `docs/governance/current-state.json`. The new chat must
name Task 036 and recheck live routing before implementation.

## 17. Implementation record

Reserved for the new implementation chat.

### Source and proposal fingerprints implemented

Not yet implemented.

### Commands and results

Not run; documentation-only validation belongs to the current chat.

### Deviations

None implemented.

### Remaining proof gaps

All acceptance checks remain pending until Task 036 is explicitly activated.
