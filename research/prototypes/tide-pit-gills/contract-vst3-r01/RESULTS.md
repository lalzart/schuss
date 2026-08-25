# Tide Pit Local VST3 Host Migration implementation results

> Status: implemented and validated through target-build and offline host-signal
> evidence; the bundle remains uninstalled and Ableton was not launched

## Proposal and authority fingerprints

- Proposal: `research/proposals/tide-pit-vst3-local.md`
- Proposal SHA-256:
  `841f77bdf4a0e2cc9b8301178a95ced9f18641629cf58aff560eaa40b4be0fd5`
- State schema: `schuss-tide-pit-vst3-state-v1`
- Parameter-model fingerprint: `14672542899034963389`
- JUCE authority: authenticated 8.0.15 source manifest SHA-256
  `db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5`
- Original Tide Pit Q27 oracle SHA-256:
  `39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b`
- Tide Pit source-lock SHA-256:
  `52a13c11dbd81df05a3590d2aaa5cf1efc95bdddcc874d69cf6961c18de61a02`

Task 046 lives under `research/prototypes/tide-pit-gills/vst3/`. That isolated
child consumes the existing portable targets without changing the original
Tide Pit standalone source, source lock, Q27 oracle, or retained evidence.

## Implemented boundary

- One private macOS arm64 JUCE VST3 instrument, zero audio inputs, stereo
  output, MIDI input, exact 48 kHz operation, and no copy-after-build install.
- Sixteen stable parameters: eleven continuous source controls plus desired
  Source, Lock, FX Mode, Target, and Scale. Mutate and Freeze remain
  non-persistent one-shots.
- Transactional bounded XML state with complete schema, fingerprint, ID,
  cardinality, finite-value, range, duplicate, truncation, and size validation.
  Recall creates a fresh Core and never claims captured-audio, mutation, random,
  timeline, tail, gesture, diagnostic, MIDI-edge, or scope restoration.
- Arbitrary positive host blocks pass through the existing 16-frame
  `Q27HostBridge`; sample-offset channel-16 CCs use the existing controller
  adapter, and unsupported rates/layouts render exact silence.
- A 1,080 by 650 accepted-state editor exposes the original eleven controls,
  seven buttons, display, scope, accepted modes, and bounded diagnostics without
  owning an audio or MIDI endpoint.
- Per-instance Core, random sequence, capture state, bridge, MIDI adapter,
  parameters, state, scratch events, UI mailbox, and scope mailbox.

JUCE additionally publishes one bypass parameter and 2,080 non-automatable
VST3 MIDI-controller service parameters. The first sixteen parameters are the
complete stable Tide Pit surface; the 2,081 additional entries are wrapper
protocol, not Tide Pit controls or canonical Schuss parameters.

## Validation results

| Check | Result | Observation |
|---|---|---|
| Ready bundle and source authority | passed | Proposal, contracts, original six Gills files, Tide Pit source lock, shared Mutable package, and authenticated 4,425-file JUCE tree matched |
| VST model, processor, allocation, and module suites | 4/4 passed in Release | The real bundle scanned as exactly one instrument, instantiated twice as 0-in/2-out, round-tripped state, emitted nonzero finite PCM, and created/destroyed its editor |
| Parameter model | passed | Sixteen unique ordered IDs, source domains/defaults/quantization, complete mappings, and frozen fingerprint |
| Direct Core parity | passed | Exact float PCM parity for host blocks 1, 16, 64, 128, 511, 512, 513, 2,048, and 4,096 at 48 kHz |
| MIDI, modes, and one-shots | passed | Timestamped channel-16 CCs matched the direct path; desired modes settled through original gestures; Mutate and Freeze resolved once |
| State and negatives | passed | Fresh-Core twin matched; malformed, truncated, incomplete, duplicate, nonfinite, off-grid, out-of-range, and over-1-MiB inputs were rejected transactionally |
| Layout and instance boundary | passed | 44.1/96 kHz and mono runtime shapes produced exact silence; identical instances matched and remained independent |
| Allocation probe | passed | Zero observed C++ heap allocations across 256 calls of 4,096 frames with two timestamped CC events per call |
| Sanitizers | 2/2 passed | Model and processor passed Apple arm64 AddressSanitizer and UndefinedBehaviorSanitizer |
| Existing Tide Pit regression | 8/8 passed | Fresh authenticated Release build passed source, Core, control, UI, MIDI, render, and byte-exact Q27 oracle checks |
| Schuss current | passed | Routine current closure passed after documentation freeze |
| Relocated reproduction | passed | Copied-root Release rebuild and all four VST suites passed without source-tree mutation; the runner emitted the exact pre-build consumer-tree hash |

## Release artifact

- Bundle:
  `build/tide-pit-vst3-task046-release/tide-pit-vst3_artefacts/Release/VST3/Tide Pit.vst3`
- Architecture/kind: Mach-O 64-bit bundle, arm64
- Plug-in binary SHA-256:
  `11d3c9086007816d1b9f263c4f775b1528ff8b45e155635c9a9f2785b41bb59e`
- Bundle-tree SHA-256:
  `4ce4957704b1dace71f6b224935b89bf6bf3e17c7071a2c6608f9f6f189a2ef4`
- Receipt: `vst3-build.json`, status `passed`
- Signature evidence: valid local ad-hoc seal only; no identity signing or
  notarization claim

The separate JUCE module host loaded the exact retained bundle and exercised
its bus, MIDI, parameter, state, editor, multi-instance, and signal seams. No
plug-in folder, application, audio/MIDI endpoint, or physical device was
touched.

## Corrections made during validation

1. Added an explicit `std::string_view` to JUCE UTF-8 conversion seam after the
   first editor compilation exposed that JUCE does not accept `string_view`
   directly.
2. Froze the observed parameter-contract digest in the model test after the
   descriptor table passed its exhaustive first run.
3. Re-applied the local ad-hoc seal after JUCE's post-link module-info write so
   strict bundle verification covers the final bytes.
4. Rebuilt the adjacent standalone in a fresh authenticated directory after
   its old retained build cache pointed at a deleted temporary JUCE path; the
   old binaries still passed 8/8, and the fresh build independently passed 8/8.

Each correction reran its affected focused or target check.

## Evidence ladder

| Level | Result | Remaining limitation |
|---|---|---|
| Research | passed | Private-use licensing is bounded; redistribution remains unreviewed |
| Proposal | approved | The request did not authorize installation, app launch, device, Git, or publication actions |
| Source | passed | Source identity and byte equivalence do not prove host execution |
| Host structural | passed | Offline structure is not callback-deadline evidence |
| Host signal | passed | Exact PCM parity is not a listening judgment |
| Target build | passed | The arm64 bundle is uninstalled and untested in Live |
| Real-time | not run | No callback, xrun, CPU, memory, or useful multi-instance measurements |
| Connected device | not run | No Live MIDI route or physical controller session |
| Listening | not run | No single or layered creative audition |
| Production integration | not run | No canonical provider, host matrix, release signing, notarization, packaging, or distribution review |
