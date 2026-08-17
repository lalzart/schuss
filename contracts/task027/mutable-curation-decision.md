# Task 027 Mutable-related curation decision

This decision applies only to exact source bytes in `patcher` commit
`08d3e6e1e2b61230308c20a15ded58ffdaf4656c` and the exact accepted Task 024
factory candidate artifact. `mutable-instruments-derived` requires explicit
source or license attribution to Mutable Instruments code or data.
The exact extended review covers nineteen extended objects.

## Extended library

| Stable source ID suffix | Functional category | Decision | Mutable evidence |
| --- | --- | --- | --- |
| `analysis.pitch-amdf` | `spectral-analysis` | inventory-only | none in exact library license |
| `control.keyframes-4` | `modulation-control` | inventory-only | none in exact library license |
| `effects.comb-network` | `filters-resonators` | inventory-only | none in exact library license |
| `effects.talkbox-lpc` | `spectral-analysis` | inventory-only | none in exact library license |
| `effects.waveset-repeat` | `sampling-buffers` | inventory-only | none in exact library license |
| `grain.clocked-delay` | `delay-reverb` | inventory-only | none in exact library license |
| `grain.seeded-scatter` | `sampling-buffers` | inventory-only | none in exact library license |
| `modulation.bounce` | `modulation-control` | inventory-only | none in exact library license |
| `modulation.poly-slope` | `modulation-control` | inventory-only | none in exact library license |
| `modulation.segment-6` | `modulation-control` | inventory-only | none in exact library license |
| `physical.drip-water` | `sound-sources` | inventory-only | none in exact library license |
| `physical.resonator` | `filters-resonators` | add implementation `schuss-implementation-000096@1` to `schuss-family-000010@1` | GPL wrapper around MIT Rings DSP by Emilie Gillet |
| `random.loop-mutate` | `modulation-control` | inventory-only | none in exact library license |
| `random.probability-router` | `timing-sequencing` | inventory-only | none in exact library license |
| `random.pulse-randomizer` | `timing-sequencing` | inventory-only | none in exact library license |
| `random.smooth` | `modulation-control` | inventory-only | none in exact library license |
| `sequencing.topographic-3` | `timing-sequencing` | tagged-candidate | pattern data derived from GPL Grids by Emilie Gillet; no reviewed family equivalence |
| `synthesis.macro-voice` | `sound-sources` | tagged-candidate | GPL wrapper around vendored MIT Plaits DSP by Emilie Gillet; no reviewed family equivalence; exact source manifest says `build-failed` |
| `timing.adaptive-clock` | `timing-sequencing` | inventory-only | none in exact library license |

The sixteen inventory-only entries remain exact sourced candidates for later
review. Their exclusion from the Mutable tag is not a quality, compatibility,
or future-catalog decision.

## Factory corpus

Every exact Task 024 factory candidate variant whose own description explicitly
attributes Mutable Instruments source or DSP receives the provenance tag. The
expected closed cohort is fifty-three variants. No path-only match qualifies.

Five of those variants already back reviewed implementations and receive exact
implementation tags:

- `schuss-implementation-000010` — Clouds-like granular object;
- `schuss-implementation-000016` — Elements-like physical model;
- `schuss-implementation-000056` — Rings-derived Stereo Reverb;
- `schuss-implementation-000057` — Struck Drum Voice; and
- `schuss-implementation-000058` — Struck Bell Voice.

The other forty-eight remain tagged candidates. In particular,
`axoloti-factory:fx/wrps/vocoder` remains uncurated, and
`axoloti-factory:fx/wrps/wrps` retains its exact statement that it does not
currently link. Neither becomes a catalog implementation or support claim.

## Evidence boundary

Source descriptions, manifests, and compatibility fields are recorded as
source metadata. Task 027 reproduces only catalog structural/provenance levels
1-2. Compiler, ARM, connected-device, real-time, audible, release, and
publication evidence remain `not-run`.
