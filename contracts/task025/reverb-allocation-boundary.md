# Task 025 reverb allocation boundary

Status: accepted fail-closed decision under the resumed Tasks 024-026 goal.
This record changes no Task 024 or Task 017 byte and does not modify either
authenticated upstream checkout.

## Authenticated observation

The selected Task 024 subject remains
`schuss-implementation-000056@2`, whose pinned factory source is
`objects/fx/rngs/reverb.axo` at axoloti-factory commit
`25d2615ed5233546d617017666a4ab1e60a8c506`. That source calls:

```c++
reverb.Init((uint16_t*) sdram_malloc(32768));
```

The same commit pins `objects/fx/rngs/rings_fx.h` with SHA-256
`3da1acbf013cd4d7c2a105c95d99e19b0b1c173addc24dc2f79af85523d0a55b`.
In that header:

- `DataType<FORMAT_16_BIT>::T` is `uint16_t`;
- `Reverb` uses `FxEngine<32768, FORMAT_16_BIT>`;
- `FxEngine::Clear` calls `std::fill(&buffer_[0], &buffer_[size], 0)`.

Initialization therefore clears 32,768 `uint16_t` elements, or 65,536
bytes. The retained ten delay reserves total 21,617 elements and the
inter-line gaps make the last `base + length` 21,626, so direct delay access
also exceeds a 32,768-byte allocation.

Patcher commit `08d3e6e1e2b61230308c20a15ded58ffdaf4656c` implements
`sdram_malloc(size_t size)` in `firmware/axoloti_memory.c` by subtracting and
advancing exactly `size` bytes. It does not multiply the argument by the
pointee width. The object call therefore reserves 32,768 bytes, not 32,768
`uint16_t` elements.

This is static source evidence of an inconsistent allocation/ownership
contract. It is not connected-device, real-time, stability, corruption, or
audible evidence. A successful ARM compile/link would not resolve it.

## Fail-closed decision

Task 025 must not create a native reverb realization, direct operation spec,
supported eligibility, executable handler, or ARM evidence for this subject.
The exact Task 024 selection packet and Task 017 source binding remain
historical inputs. The reverb path stays deterministically unsupported until
an independently authorized task establishes an exact allocation and
ownership contract.

Task 025 may promote only the five remaining reviewed source subjects: saw,
PWM, exponential smoothing, audio soft clipping, and interpolated VCA. The
accepted Task 016 crossfader and output bindings remain reusable inputs. The
ordinary compiler plan for `schuss-graph-000004@1` must resolve those seven
nodes and fail closed at the reverb node without backend lowering, source
generation, build-handler dispatch, or ARM execution.

## Choices deliberately not made

- Allocating 65,536 bytes would be a new runtime realization, not the exact
  32,768-byte legacy allocation fixed by the original Task 025 contract.
- Shrinking or altering `rings_fx.h` would modify authenticated algorithm
  bytes.
- Treating the allocator argument as an element count contradicts the pinned
  runtime implementation.
- Compiling the unsafe wrapper would prove only compiler acceptance and could
  mask the unresolved runtime boundary.
- Removing reverb from the Task 024 packet or rewriting historical catalog
  records would conceal provenance rather than resolve it.

## Consequence for sequencing

The original Task 025 all-eight-node level-5 acceptance is materially revised
to a partial level-2 promotion plus deterministic unsupported-plan evidence.
Task 026 cannot claim empty-workspace-to-ELF completion from this parent and
must remain proposed until a prerequisite supplies both an eligible reverb
realization and the separately identified project-authored graph identity
seam. Levels 3-8 remain `not-run` for the revised Task 025 completion.
