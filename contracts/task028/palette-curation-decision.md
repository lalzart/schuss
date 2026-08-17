# Task 028 direct-palette curation decision

This decision selects one closed fifteen-item tranche from the accepted Task
027 catalog and source review. The count is constrained by exact local
component, binding, eligibility, selection, and normalized lowering evidence;
source presence or legacy behavior alone is insufficient.

## Selected cohort

| Allocation | Source implementation | Observation | Family | Function | Decision |
| --- | --- | --- | --- | --- | --- |
| 000097 | 000053 Attack-Decay Envelope | 113 | 000033 | modulation-control | promote |
| 000098 | 000049 Clocked Logic Toggle | 229 | 000029 | timing-sequencing | promote |
| 000099 | 000050 Pseudo-Euclidean Gate Sequencer | 1208 | 000030 | timing-sequencing | promote |
| 000100 | 000057 Struck Drum Voice | 527 | 000037 | sound-sources | promote; retain Mutable provenance separately |
| 000101 | 000058 Struck Bell Voice | 526 | 000038 | sound-sources | promote; retain Mutable provenance separately |
| 000102 | 000008 Uniform Noise | 499 | 000004 | sound-sources | promote exact standard factory variant |
| 000103 | 000011 Standard ADSR | 115 | 000007 | modulation-control | promote; exclude looping sibling |
| 000104 | 000013 Standard Sine LFO | 208 | 000008 | modulation-control | promote; exclude extended sibling |
| 000105 | 000069 Decay Envelope | 123 | 000049 | modulation-control | promote |
| 000106 | 000064 Control Low-pass Filter | 199 | 000044 | filters-resonators | promote control-rate variant only |
| 000107 | 000070 Two-pole Resonant Audio Low-pass | 162 | 000050 | filters-resonators | promote exact audio variant only |
| 000108 | 000078 Saturating Gain | 318 | 000058 | shaping-dynamics | promote exact audio overload only |
| 000109 | 000077 Two-input Audio Mixer | 421 | 000057 | mixing-routing | promote exact two-input audio overload only |
| 000110 | 000034 Audio-rate Addition | 255 | 000023 | mixing-routing | promote exact audio overload only |
| 000111 | 000074 Triggered Value Latch | 224 | 000054 | data-math-logic | promote exact fractional-control overload only |

The fixed baseline is Task 025 native implementations 000090, 000091, 000092,
000093, and 000095. Those five plus the fifteen rows above are the only records
counted toward twenty. The Task 026 seven-node application profile remains a
separate supporting set.

## Selection rationale

The cohort prioritizes practical graph completeness: five added sources, five
envelope/modulation tools, two filtering/resonance tools, three gain/mix/route
tools, two timing tools, and one data-state tool, with overlaps counted by the
row's retained primary function rather than by new taxonomy. No effect is added
because the reviewed richer effects carry unresolved allocation, dependency,
resource, compile, or behavioral boundaries.

Drum and Bell are the only selected implementations tagged by Task 027 as
Mutable-derived. Their exact source attribution helps inspect provenance; it
does not establish their component, compiler, target, device, resource, or
audible support. Those claims are established or withheld independently.

## Explicit gates

- Rings-derived reverb remains failed/unsupported and native allocation 000094
  remains absent because the retained 32768-byte request conflicts with the
  target's exact 16384-byte SDRAM region.
- Extended Rings physical resonator 000096 remains catalogued-only because no
  accepted exact Schuss component/binding/dependency/lowering contract exists.
- Clouds, Elements, Warps, macro voice, topographic sequencing, Task 027's
  other tagged candidates, and all inventory-only extended entries remain
  outside the palette because source attribution is not direct support.
- Transparent compounds remain deferred rather than used to inflate the
  independently selectable implementation count.
- Every non-selected catalog implementation remains catalogued at its prior
  readiness. Absence from this small palette is not a quality judgment.

## Evidence boundary

Task 028 may pass only levels 1-3: structural identity, exact component/binding
resolution, and deterministic normalized local backend lowering. Source
artifact generation, ARM compile/link, connected-device execution,
realtime/resource measurement, and audible validation remain `not-run`.
