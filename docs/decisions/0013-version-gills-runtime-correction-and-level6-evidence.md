# ADR 0013: Version the Gills runtime correction and level-6 evidence

- Status: accepted
- Date: 2026-08-16

## Context

Task 018 completed one mapped Gills closure through deterministic local ARM
compile/link evidence level 5. A separately authorized connected-device probe
then showed that its OLED command payload was allocated inside a thread working
area in CCM, which is not accessible to the STM32 DMA path used by I2C. The
exact Task 018 binary therefore failed at OLED initialization on the connected
board.

A diagnostic probe that reused the page buffer for command bytes executed, but
corrupted the page buffer control byte and inverted the existing display. A
second probe used a dedicated two-byte `.sram2` command buffer. Its RAM image
matched the uploaded bytes, started successfully, remained responsive, and was
visually confirmed upright with all four expected words.

Task 018 records, generated artifacts, and retained evidence are immutable.
Correcting its generator in place would make the retained level-5 proof stale.
Tasks 019 and 020 remain deferred and do not describe this corrective work.

## Decision

Task 021 is a separately authorized corrective successor. It preserves every
Task 018 v1 byte and adds exact versioned successors for the mapped handler,
runtime realization, build request, and the mechanical instrument/coverage
identities needed to keep instrument inspection unambiguous. The instrument
and coverage successors do not change musical behavior, mappings, or DSP
semantics.

The Task 021 OLED transport uses a dedicated two-byte command buffer in
`.sram2`. The 129-byte page buffer remains independent and retains its `0x40`
data-control byte. No implicit fallback from the Task 021 handler to Task 018
or any legacy handler is permitted.

Build execution continues to report levels 1-5 and leaves levels 6-8
`not-run`. A separate exact evidence claim records the already-performed
volatile-RAM connected-device observation as level 6. It does not upgrade the
build handler itself and does not imply level 7 real-time/resource or level 8
audible/listening evidence.

Task 021 does not activate Task 019, Task 020, or UI work. It authorizes no
firmware flash, SD-card write, persistent install, Git publication, or further
hardware action.

## Consequences

The corrected executable can coexist with and be selected independently from
the retained Task 018 executable by exact request and handler revisions. Both
old and new instrument revisions remain exactly inspectable.

The connected observation is deliberately narrow: one exact Ksoloti Core,
one exact ELF/binary pair, volatile RAM execution, responsiveness probes, and
upright four-word OLED output. Control behavior, audio, timing margin,
endurance, electrical safety, persistence, and release readiness remain open.
