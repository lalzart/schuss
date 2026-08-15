# Task 016 direct-semantics decision brief

Decision status: required. No option is accepted by this brief.

## Why one decision remains

The accepted graph and component contracts define topology, public types, and
several control rules, but they intentionally do not say whether a new direct
frontend must preserve the pinned Task 011C sound or establish a new Schuss
sound. A source audit shows that the previously listed eight prerequisite
specifications are not eight independent product questions. The retained
sources can determine all eight for a legacy-equivalent path. The irreducible
product decision is therefore the compatibility mode.

## Exact decision requested

Choose exactly one:

1. **Legacy-equivalent direct semantics (recommended).** Remove Java and
   `.axp` from the direct generation path while preserving the exact pinned
   Task 011C integer DSP behavior, block schedule, state transitions, runtime
   tables, and Ksoloti patch ABI. Equivalence means identical public integer
   outputs and component state transitions for exact input/parameter sequences;
   it does not mean identical generated C++ or ELF bytes.
2. **Schuss-native direct semantics.** Treat the existing contracts only as
   public interfaces and design new oscillator, LFO, filter, scheduling, and
   runtime behavior before implementation. This requires a separate reviewed
   musical-DSP specification and cannot be inferred automatically.

A hybrid that silently preserves some legacy behavior and changes other parts
is not an accepted option. It would make compatibility and audible differences
impossible to state precisely.

The shortest authorization for option 1 is: **Use legacy-equivalent Task 011C
behavior for Task 016.**

## Authenticated evidence base

The source audit was read only. All upstream revisions match
`catalog/sources.lock.json`; the existing dirty Ksoloti patcher worktree was not
modified. The normative compatibility oracle is the retained 18,359-byte Task
011C generated C++ artifact with SHA-256
`7877897b3112dcbb7ee1239f3187f535d6113875cacbb49c76bd30a0321bcfd3`.

| Evidence | Exact identity | What it can establish |
| --- | --- | --- |
| Ksoloti patcher | commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c` | Existing runtime ABI, scheduler generation, math tables and intrinsics |
| `firmware/axoloti_math.h` | SHA-256 `95ccbdbea15078a6ef207e87749bb8defaa4662b6eebddfb40944f350b549191` | `mtof48k_ext_q31`, `sin_q31`, Q31 interpolation and ARM multiply rules |
| `firmware/axoloti_math.c` | SHA-256 `ba4e3146eb3e6cf436ee836d1f5c82d9b5c13606e3ab0f273ff43432ef3626c1` | Exact 4,097-entry sine and 257-entry pitch-table initialization |
| `firmware/patch.h` | SHA-256 `fe64781fac09b82d6f45eafbb60efcfe7b1af655af5dcccaac232e29c31dad2c` | Patch metadata and process-function ABI |
| `firmware/xpatch.h` | SHA-256 `85e4abc70123952e8f47217751f2b6f7299e7cb978b6c994acf7b383425379a0` | Existing patch compilation/runtime include boundary |
| `src/main/java/axoloti/Patch.java` | SHA-256 `7c1cc7e644ef5d1453741e4ec40090e71c3f3697ef9c7a20761ce739f9b804b6` | Retained object ordering, latches, initialization, disposal and exported entry points |

The exact object sources are:

| Role | Portable source and file SHA-256 | Source declaration |
| --- | --- | --- |
| Square LFO | `axoloti-factory:objects/lfo/square.axo`, `d417bd0e455e28c6af9988732f6406b2d3e3c94eea9338f76ab61df926463051` | `<license>BSD</license>` |
| Cyclic Counter | `axoloti-factory:objects/logic/counter.axo`, `fb61bbfeb9504cee015b093888fb8c6da237d12b760a5e6ebdb9b160447bd9e1` | `<license>BSD</license>` |
| Four-step Sequencer | definition 0 in `axoloti-contrib:objects/drj/seq/stepseq_16_pitch.axo`, `45336e472f1e15a295617b0f4fd1e31e83203acf9ae37a067125459f66022b0f` | `<license>BSD</license>` |
| Sine Oscillator | `axoloti-factory:objects/osc/sine.axo`, `bf865e647b2eea2ebe1ef852038994f2dea8f1e8b8e60e1133e1d580a3402a4b` | `<license>BSD</license>` |
| State-variable Filter | `axoloti-factory:objects/filter/multimode svf m.axo`, `e73239cd072b9dc63debd2ec95a32ec0bf79ae1be1754336a1d5928d4e8af057` | `<license>BSD</license>` |
| Stereo Audio Output | `axoloti-factory:objects/audio/out stereo.axo`, `d8392b522b54be3bdfa5e671975a2a675ac494e9d1dc8bee2586dcd1eaecc7e3` | `<license>BSD</license>` |

The runtime math, patch ABI, and generator files carry GPL-3.0-or-later text in
their own file headers. The table records above report those declarations; they
are not a legal compatibility conclusion. Option 1 should call the retained
runtime boundary rather than copy runtime tables or GPL implementation into a
Schuss core module. Any redistribution or copying policy remains a separate
license-review responsibility.

## Conditional specification for the recommended route

If option 1 is selected, the eight Task 016 prerequisites resolve as follows:

1. **Pitch conversion.** Use signed Q21 parameter-plus-inlet values and the
   pinned runtime's 48 kHz `mtof48k_ext_q31` path. It saturates to 29 signed
   bits, indexes and linearly interpolates the exact `pitcht[257]` table, and
   returns a Q31 phase increment. The table is initialized from A4 = 440 Hz by
   the retained runtime; the direct frontend calls that runtime behavior rather
   than regenerating a new table.
2. **Square LFO.** State is signed 32-bit `Phase = 0` plus reset arm `r = 1`.
   A rising reset sets phase to zero and disarms until reset falls. Otherwise
   the control-cycle update is `Phase += frequency >> 2`; the Boolean output is
   `Phase > 0`. Signed 32-bit wrap, reset timing, and the resulting half-cycle
   polarity are part of compatibility.
3. **Sine oscillator.** State is unsigned 32-bit `Phase = 0`. Each of 16 audio
   samples adds the control-cycle frequency plus audio-rate frequency input,
   adds phase modulation shifted left four bits, linearly interpolates the
   pinned 4,097-entry Q31 sine table, and emits the result shifted right four
   bits into Q27.
4. **State-variable filter.** State is signed 32-bit `low = 0` and `band = 0`.
   The exact retained `__USAT`, `__SSAT`, `___SMMUL`, pitch-to-frequency,
   sine-interpolation, damp-square, and per-sample notch/low/high/band update
   sequence is normative. No alternative SVF topology, drive term, smoothing,
   or saturation is introduced.
5. **Block schedule.** One control cycle owns one 16-sample audio block. The
   retained Task 011C order is Sine A, LFO, Counter, Sequencer, Crossfader,
   Filter, Audio Output, Sine B, then the exposed Blend control. Sine A reads
   the previous block's sequencer output; Crossfader reads the previous block's
   Sine B buffer and Blend value. Those three latches update only after all
   object calls. This behavior is intentionally preserved even though a new
   topological scheduler could sound different.
6. **Runtime ABI.** Emit the existing `xpatch_init(uint32_t)` boot entry,
   `PatchProcess(int32_t*, int32_t*)`, disposal, preset/MIDI stubs, `patchMeta`
   assignments, 16-frame interleaved stereo conversion, and the authenticated
   Task 011C linker boundary. Reuse existing firmware headers and runtime
   tables; do not introduce a replacement firmware ABI.
7. **Compatibility claim.** Claim only exact integer behavioral equivalence
   demonstrated by operation and graph transition vectors plus separate ARM
   compile/link evidence. Generated-source identity, device execution,
   real-time safety, and audible identity are different claims and remain
   unproved unless their own evidence levels run.
8. **Source authority.** Bind every operation to the portable object source,
   exact file hash, pinned patcher/runtime commit and retained Task 011C oracle
   above. Record the source's own license declaration. Do not infer a license
   from a repository or directory name and do not copy runtime code into core.

Counter and four-step selection behavior already have exact component rules;
the retained source provides their initialization and within-cycle ordering.
Task 015 remains the normative direct Crossfader arithmetic contract.

## What remains prohibited before a decision

- No direct binding, backend, eligibility, or compatibility promotion.
- No Task 016 normalized IR, generated C++, ARM object, ELF, or evidence claim.
- No assumption that compile/link evidence proves device, real-time, audible,
  or release behavior.
- No Java or `.axp` fallback disguised as the direct backend.
- No UI, hardware action, stage, commit, push, or external publication.
