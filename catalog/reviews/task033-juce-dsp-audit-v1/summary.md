# Task 033 pinned JUCE DSP audit

This packet authenticates the JUCE 8.0.15 archive already pinned by Task 031
at commit `91ad83ae34a81e0833b1a2b0866f54846370ae53` and accounts for every
public header included by the pinned `juce_dsp` umbrella. It does not add the
module to Schuss's source lock, build, catalog, provider registry, or runtime.

## Exact result

The umbrella contains exactly 39 reviewed headers:

- 20 musical node candidates;
- 12 implementation utilities;
- 5 composition helpers;
- 1 asset-dependent processor; and
- 1 internal/deferred implementation subject.

`Convolution` additionally carries a host-service trait because impulse
loading, partition storage, latency, and an optional background message queue
cross the simple audio-node boundary. No header becomes a standalone Schuss
host service or graph node by that observation.

The module declaration is version 8.0.15, C++17, AGPLv3/commercial, with an
additional `juce_audio_formats` dependency. `juce_dsp` is absent from the
current Schuss JUCE source-lock module list. The reviewed APIs are generally
templated/floating-point and use JUCE blocks, process specifications, and
prepare/reset/process lifecycles; none proves equivalence to the accepted
fixed-Q27 `schuss_rt` profile.

## Architecture recommendation

- Twelve simple algorithm subjects are candidates for separately specified,
  JUCE-independent Schuss native semantics. This is not permission to copy or
  import a JUCE class.
- Eight richer or service-sensitive subjects—Convolution, Reverb, Ladder
  Filter, Compressor, Noise Gate, Limiter, Phaser, and Chorus—belong, if ever
  pursued, in a later statically linked JUCE host provider with an explicit
  desktop-float target/backend and a fresh license/dependency/real-time review.
- Nineteen utilities, helpers, internal details, or unresolved candidates are
  deferred as palette objects.

Task 033 therefore keeps `juce_dsp` unlinked and preserves JUCE outside the
portable runtime ABI. The canonical `headers.jsonl` records each exact source
hash/span, classification, numeric/channel/lifecycle constraints, callback
concerns, required Schuss work, and recommendation. `manifest.json` binds the
archive, source lock, module files, entry bytes, counts, and evidence boundary.
