# Wirefall Instrument Lab prototype

Wirefall is a non-production `new-design` consumer of Instrument Lab v1. The
approved authority is `research/proposals/wirefall.md` revision 0.1 with
SHA-256 `cf9b5f58e50856a9d38d754ee476ced58c52473bb9f9ff1216c75e7ca28707b8`.
Its implementation-ready contract is under `contract/`.

The proposal's retained `Status: proposed` line is the frozen pre-approval
snapshot, not the current approval state. The v2 implementation contract owns
the later approval reference and binds that exact proposal SHA-256; the
repository validator checks both facts.

The portable C++17 Core owns the instrument's oscillators, fold, filter,
oversampling, complementary scheduler, state, controls, diagnostics, and
fixed-capacity delay paths. Instrument Lab supplies only bounded host and
artifact mechanics through `SchussInstrumentLab::Core`.

This subtree is prototype-local and allocates no canonical Schuss identity. A
successful build, test, or offline render can establish source, host-structural,
or host-signal evidence only. It cannot establish real-time behavior, target or
device execution, listening quality, distribution, or production integration.

The implementation is original C++17 plus the repository-owned Instrument Lab.
Research papers and product manuals cited by the proposal are design evidence;
no third-party DSP source, protected assets, presets, samples, branding, or
panel expression are copied here.

Revision 0.1 now has a complete Core-only implementation and retained
host-signal observations. Source, focused host-structural, sanitizer,
all-partition determinism, and schedule-parity checks pass, but the frozen
host-signal acceptance does not: DC/true-void, 4x reference/alias, TENSION
energy, and Shadow rejection bounds failed. See `contract/RESULTS.md`,
`contract/GAPS.md`, and `results/wirefall-objective-summary.json`. The failed
signal bounds are stop conditions for revision 0.1, not permission to weaken
the approved contract.
