# Wirefall v0 frozen DSP specification

> Status: ready for implementation
> Proposal authority: `research/proposals/wirefall.md` revision 0.1
> Proposal SHA-256: `cf9b5f58e50856a9d38d754ee476ced58c52473bb9f9ff1216c75e7ca28707b8`

This file resolves the two implementation details that the approved proposal
requires the bundle to freeze before DSP edits. It does not change the musical
architecture, extend the evidence ceiling, or contain an implementation.

## Numeric and timing profile

- Core sample type: IEEE-754 binary32; intermediate coefficient generation may
  use IEEE-754 binary64, then stores binary32 values.
- Base sample rate: exactly 48,000 Hz; Wire oversampling factor: exactly 4.
- Events are ordered by `(sample_index, ingress_sequence)` and applied before
  the named sample. At most 128 events are accepted per host block; additional
  newest events are dropped and counted.
- Continuous targets are clamped before smoothing. Non-finite targets are
  ignored and counted. The smoothing recurrence is
  `z = a*z + (1-a)*target`, where `a=exp(-1/(tau*48000))`.
- Derived Wire frequency, fold drive, SVF frequency/Q, saturation drive, and
  compensation are recomputed from smoothed controls at base samples whose
  absolute index is divisible by 16. The resulting coefficient set is held for
  the following 16 base samples and their 64 oversamples. This phase is based
  on the absolute sample index and therefore cannot restart at a host block.

## Exact TPT state-variable filter

The Wire branch uses one trapezoidal-integrator state-variable filter at
192,000 Hz. For each oversample, compute:

```text
fc = min(0.42 * 48000, fW * (1.35 + 1.15 * BITE))
Q  = 0.8 + 14 * TENSION^2 * (0.25 + 0.75 * BITE)
g  = tan(pi * fc / 192000)
k  = 1 / Q
a1 = 1 / (1 + g * (g + k))
a2 = g * a1
a3 = g * a2

v3 = input - ic2eq
v1 = a1 * ic1eq + a2 * v3
v2 = ic2eq + a2 * ic1eq + a3 * v3

ic1eq = 2 * v1 - ic1eq
ic2eq = 2 * v2 - ic2eq

low  = v2
band = v1
high = input - k * v1 - v2
```

Only `band` enters the approved Wire mixture. `low` and `high` are retained as
test observations, not extra voices. `fc` is clamped to `(0, 20160]` Hz and
`Q` to `[0.8, 14.8]` before coefficient calculation. Any non-finite input,
coefficient, integrator, or output zeros the band contribution for that sample,
starts the proposal's 5 ms branch mute/reset, and increments the containment
counter. There is no alternative filter fallback.

The exact Wire sample after the filter is:

```text
d = 1 + 6 * TENSION^2
c = 1 / sqrt(1 + 0.9*TENSION + 1.1*TENSION^2)
w = c * tanh(d * (0.68*fold + 0.32*band/sqrt(Q))) / tanh(d)
```

## Frozen oversampling kernel

`wirefall-fir-63.json` is authoritative. Its 63 words are the little-endian
IEEE-754 binary32 encodings obtained by evaluating the approved normalized
Blackman-windowed sinc in binary64, dividing every tap by the binary64 tap
sum, and rounding each result once to binary32. Concatenating the 63 four-byte
little-endian words in index order has SHA-256
`a99f4e674be713a0b0f2405711cff20b6a0676a13f4af63380165c4984e70b1a`.

The Wire oscillator and nonlinear path are evaluated directly at 192 kHz, so
their decimation filter uses the stored kernel at unity DC gain and emits each
fourth phase-aligned result after continuous FIR state has advanced. If a
base-rate test signal is zero-stuffed into the 4x reference path, and only in
that case, the interpolation kernel is multiplied by 4 as specified in the
proposal. FIR state is Core state; its phase cannot restart at block edges.

The 31-oversample linear-phase group delay is retained and reported as
`31/4 = 7.75` base frames. Comparisons align the 4x and 8x references by their
declared fractional delays before measuring the residual; render files are not
silently trimmed.

## Complement, scheduler, and output invariants

- The scheduler denominator is 8, `k=round(1+5*HOLES)`, and the accumulator
  transition is exactly `err += k; cut = err >= 8; if cut then err -= 8`.
- `CUT` and `HOLES` targets become pending immediately and commit together on
  the next beat boundary. A HOLES commit resets `err` to zero. CUT `OPEN`
  emits no opportunities and no cuts.
- A raised-cosine edge always begins from the current complementary coordinate
  `q`; `gW=cos(pi*q/2)` and `gS=sqrt(SHADOW)*sin(pi*q/2)`. The Wire and Shadow
  wet/dry space paths are complete before these gains.
- Output processing is DC block followed by
  `0.8912*tanh(dc/0.8912)`. A non-finite output writes zero and starts the
  latched Panic transition defined by `state-matrix.md`.
- Processing uses only fixed-capacity state and performs no allocation, file,
  network, device, lock, or exception-producing work.

## Implementation stop rule

Any implementation that cannot reproduce these coefficient bytes, event
timing, state semantics, or five-condition experiment must stop and revise the
approved bundle. It may not silently substitute an approximate filter,
different oversampling phase, looser determinism relation, or new evidence
claim.
