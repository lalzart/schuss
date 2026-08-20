# Tide Pit Gills portable JUCE port implementation results

> Status: host-validated standalone prototype, frozen 2026-08-20

## Bound inputs

- Proposal revision 0.2: SHA-256
  `3c2157eaa26ceed61afe87b256a395dccc5fbbd0dab889189926ffb72b5c2157`.
- Implementation contract: SHA-256
  `81071c9cac8b76770eb4184d9afd07dda5bc47a1b0bfcdd6075d56a42e01b8c2`.
- Source-equivalence contract: SHA-256
  `2c661c07068d552a696cb222f78c37aea27c468939f386b3a793eac82b7cf747`.
- Gills target import `53287e49e5bcc5fb0d73b546d88431f82467f969`,
  observed at repository HEAD
  `33038b5de6315bce9bbe167062f2876823ff1adc`; the target directory remained
  clean after intake and validation.
- Six-file Tide Pit source manifest:
  `6cbb9842a785c90f54de28e122487194c79868b4b5505f0ab26506836abaaa85`.
- Ksoloti Mutable closure revision
  `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`, 21-file manifest
  `0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f`.
- Experiment SHA-256:
  `f8baac381d1e83f2e5db6ee4b56988299d5ae7b3e5b1b2ff4bcdfd1a0459c9fd`.
- Control map SHA-256:
  `a91f4ee46b3339f455d5d277f4b8f25d378c652eb946d6c017076e44fd356f60`;
  generated C++ descriptor SHA-256
  `f32eae062294c49c5f01c4e571865b8ecd64b5766635746882280b8ca434c51e`.
- Reused regular Launch Control 3 topology SHA-256:
  `d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b`.

## Toolchain and dependency authentication

- Apple clang 16.0.0 (`clang-1600.0.26.6`), arm64 Darwin 24.6.0.
- CMake 4.4.2, C++17, canonical oracle built at `-O2` with the compiler's
  default floating-point contraction.
- JUCE 8.0.15 commit `91ad83ae34a81e0833b1a2b0866f54846370ae53`.
  The local source tree used for this build came from a retained archive whose
  SHA-256 was independently rechecked as
  `04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70`.
  Generic local-source CMake mode checks only the JUCE version and still
  requires this separate operator authentication.

## Commands and results

| Check | Exact command or command family | Result |
|---|---|---|
| Ready bundle | `validate_implementation_bundle.py ... --phase ready` with the authenticated Gills source root | passed |
| Source lock | `validate_source_lock.py --source-root /Users/lanceship/Projects/gills-instruments --mutable-root /Users/lanceship/Projects/ksoloti` | passed; vendored and authoritative bytes match |
| Release Core | configure and build `build/tide-pit-core`, then `ctest --test-dir build/tide-pit-core --output-on-failure` | 5/5 passed |
| Fail-fast sanitizers | configure and build `build/tide-pit-sanitize`, then `ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 ctest ...` | 5/5 passed; Mutable, Core, and tests instrumented; no retained sanitizer diagnostic |
| Pinned JUCE build | configure `build/tide-pit-juce` with the authenticated JUCE tree, build all targets, then CTest | 7/7 passed; renderer, adapter test, and standalone linked |
| Render matrix | `validate_render_matrix.py build/tide-pit-juce/tide-pit-render` | 16/64/128/512 byte-equal; fresh repeat passed; overwrite and experiment-drift negatives passed |
| Sonic Research Lab 0.3 | proposal tests, implementation-bundle tests, skill validation, and plugin validation | 3/3, 5/5, skill valid, plugin valid |
| Schuss current profile | `python3 tools/validation/run.py --profile current` | 4/4 checks passed; no failure or incomplete check |

The source-lock check now regenerates the ported voice in a temporary directory,
checks the frozen output hash, and independently verifies exactly two
`<< 1` to `* 2` replacements. The build generator enforces the same source and
output hashes.

## Canonical source comparator

The permanent reference test renders 12,000 source quanta using explicit
zero-BSS-equivalent instance storage, stmlib seed `0x21`, the recovered source
fixture, and planar little-endian Q27 output.

- Frames: 192,000 stereo frames at 48 kHz.
- Bytes: 1,536,000.
- SHA-256:
  `39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b`.
- Peak: 39,182,832 Q27, normalized `0.29193484783172607`.
- RMS: `14011444.589680206` Q27.
- Raw DC mean: left `0.075637019891175439`, right
  `0.075236455696751359`.
- Source arena: exactly five allocations and 251,408 bytes, with maximum
  alignment valid.

The generated defined-C++ voice has SHA-256
`d076fa8df10eab0fdbac0ce1cd846e54fd1fa3896bba8ad7608a0ca5202b59ea`.
Its two changed expressions have a proven int32 result range of
`[-65536, 65534]`; the canonical audio remains byte-identical.

## Objective render observations

| Condition | Q27 SHA-256 | Peak normalized | RMS Q27 | Raw DC L / R | Events |
|---|---|---:|---:|---:|---:|
| Source-bound clean reference | `39d8c2a6...ad2b` | 0.29193485 | 14,011,444.5897 | 0.0756370 / 0.0752365 | 0 |
| Performance state trace | `2c6b7e22...347a` | 0.45518962 | 15,001,402.8337 | 0.0154193 / 0.0155030 | 13 |
| Parameter extremes | `8953a4b9...cb6f` | 0.55414110 | 26,280,583.0220 | 0.0537895 / 0.0546574 | 5 |

All samples were finite. No events were dropped, no gesture queue overflowed,
and no invalid or unsupported process call occurred. The performance condition
ends in FOLD / MIN5 / BODY / CLEAN with capture off, lock on, and both
contextual pickup flags inactive. Full final `Snapshot` state is retained and
compared across host partitions.

Retained artifact hashes from the final 128-frame render:

- Manifest:
  `b82392a96f61970ec906ac179f07a6eb734636d8b001207631a3f2f5da3e4e86`.
- Performance WAV:
  `81e6f7a5d36bc5f646b6beb30a133c66cbe83879b420543b08ad49afeccc9d36`.
- Extremes WAV:
  `494691e8ba3d39e2c6902bff2f336033efdbeae5b9538d061efead0b65756863`.

Raw DC is reported as a characteristic of the exact source stream, not used as
a generic pass/fail threshold. Removing it would create a different DSP
variant and invalidate source equivalence.

## Built application

- Standalone bundle:
  `build/tide-pit-juce/tide-pit-gills-instrument_artefacts/Release/Tide Pit Gills.app`
  (7.8 MiB on disk).
- Standalone executable SHA-256:
  `031a2778dc8d0c057848cf9c4632cfada87d6564091c2d9765aa855093cc2198`.
- Renderer executable SHA-256:
  `531fb2dad76be5c68c32eaaaab4d78dfc3f04dadf9e25358b64d37423ba7ff96`.
- JUCE adapter test SHA-256:
  `6b12ae45e7d2cc95bf2b3cbb48374d2bbfa985c73e9925ec2756ed8f9230dba1`.

The app was compiled and linked only. It was not launched and no audio or MIDI
device was opened by automated validation.

## Corrections made during validation

1. The historical `9e47...ab00` result was rejected as a fidelity oracle
   because automatic storage left two Clouds reverb histories uninitialized.
   Explicit zero-BSS-equivalent storage established the reproducible
   `39d8...ad2b` comparator.
2. A recovering UBSan run initially printed signed-left-shift undefined
   behavior while CTest still returned success. Validation was changed to
   fail-fast, and the exact two-expression source-hash-checked overlay removed
   the undefined operation without changing audio.
3. A generic `0.0001` raw-DC threshold contradicted the exact source. The
   experiment now measures and reports DC while preserving the source stream.
4. The performance experiment was lengthened and its event schedule corrected
   so the final held gesture completes and an initialized effect is revisited,
   genuinely exercising soft pickup.
5. The source's partial-allocation `NO GRAIN` state was removed from the
   preservation claim. The portable fixed-arena Core follows the proposal's
   fail-closed policy: incomplete preparation remains silent.
6. Generator, validator, vendored, and generated inputs were added to the
   machine-readable freshness sets so retained evidence cannot survive a tool
   change unnoticed.

## Evidence ladder

| Level | Result | Artifact or observation | Remaining limitation |
|---|---|---|---|
| Research | passed | exact Gills and Ksoloti authorities identified; legacy oracle limits documented | no new cultural or product claim |
| Proposal | passed | approved revision 0.2 fingerprint bound to the implementation contract | proposal is not production approval |
| Source | passed | authoritative/vendored locks, notices, closure, generated overlay, and clean target verified | cross-platform byte identity excluded |
| Host structural | passed | Release 5/5, fail-fast sanitizer 5/5, state/gesture/bounds/partition/multi-instance tests | fixed-arena exhaustion is not failure-injected |
| Host signal | passed | exact oracle and deterministic three-condition render matrix | raw DC retained; no subjective judgment |
| Target build | passed | authenticated JUCE 8.0.15 renderer and standalone compiled and linked | app not launched; local standalone only |
| Real-time | deferred | no claim | callback deadlines and restart lifecycle unmeasured |
| Connected device | deferred | Cinderwheel previously confirmed the reused controller topology | Tide Pit mapping, pickup, holds, reconnect, and feedback not physically exercised |
| Listening | deferred | no claim | no Tide Pit Gills A/B or user listening note yet |
| Production integration | deferred | isolated prototype only | no Schuss graph/provider records, plugin format, packaging, or release gate |
