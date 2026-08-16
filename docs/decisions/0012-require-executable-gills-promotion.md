# ADR 0012: Require executable Gills promotion

- Status: accepted
- Date: 2026-08-16

## Context

Task 017 added a useful reviewed core and two richer headless reference
instruments, but neither currently reaches direct lowering. The original Task
018 contract allowed both instruments to remain unsupported while still
calling the outcome a full Gills implementation. That would prove a complete
panel model and mapping contract without proving that any such mapped runtime
can build.

## Decision

Task 018 retains its authenticated panel, complete coverage, mapping, and
runtime-realization responsibilities. In addition, at least one exact mapped
Gills reference instrument must reach evidence level 5 through the accepted
direct build path. Stable unsupported diagnostics remain valid evidence but do
not satisfy this executable promotion gate.

The executable reference may reuse the accepted Task 016 eight-node graph and
legacy-equivalent semantics from ADR 0011. Task 018 may not invent new DSP
semantics merely to pass the gate.

Levels 6-8 remain separately authorized product evidence. Completing Task 018
does not automatically activate Task 019, Task 020, or UI work. The next
roadmap decision starts with the separately authorized Gills product evidence
gate and follows the evidence actually obtained.

## Consequences

“Full Gills implementation” now means a complete authenticated panel and
mapping model plus at least one locally executable mapped closure. It still
does not mean connected-device, real-time, audible, safety, or release proof.

Sampling, additional targets/devices, direct-semantic expansion, and the future
UI milestone remain independent bounded choices after Task 018.
