# Layerwell 0.2: Embedded Tide Pit and Pamplist Sampler implementation gap register

> Status: revision 0.2 implementation complete; named higher-evidence and
> source-correction gaps remain deferred

Passing a lower evidence level must not rewrite deferred real-time, device,
visual, listening, license/distribution, or production work as success.

| ID | Gap | Severity | Owner/stage | Current decision | Proof required | Disposition |
|---|---|---|---|---|---|---|
| GAP-001 | Embedded desktop layout and interaction have not been launched or visually inspected | medium | future visual review | Build but do not launch in Task 044 | Authorized app launch, screenshots, control traversal, resizing, readability, and human visual approval | deferred |
| GAP-002 | Audio callback timing and xrun behavior are unmeasured | high | future real-time validation | Target build is the evidence ceiling | Authorized runtime measurement with declared worst-case and p99 budget on the intended host | deferred |
| GAP-003 | Regular Launch Control 3 endpoint discovery, physical receipt, encoder feel, LEDs, OLED, and reconnect are untested | high | future connected-device validation | Pure synthetic protocol only | Authorized endpoint selection and physical bidirectional test on the exact regular model | deferred |
| GAP-004 | Trim increments, seam audibility, source identity, and layered musical result have not been auditioned | medium | future listening review | Objective signal checks only | Documented matched-level audition including late-start, early-stop, repeated seam, and two-source layering cases | deferred |
| GAP-005 | Pamplist configured source and inherited licenses are authenticated for local use but distribution is not approved | high | future distribution review | Retain notices; no package/publication | License and notice review for the exact artifact and intended distribution channel | deferred |
| GAP-006 | Layerwell 0.2 has no canonical graph/provider/runtime/catalog identity or persistence format | medium | future product/governance work | Remain noncanonical prototype | Separate accepted architecture task and production-integration gates | deferred |
| GAP-007 | A generic embedded-source panel ABI has not been demonstrated beyond this two-source consumer | low | future reuse review | Keep revision 0.2 adapters local and explicit | Another distinct consumer plus maintenance evidence showing a shared ABI pays for itself | deferred |
| GAP-008 | The exact configured Macro Voice wrapper shifts signed negative Q15 samples left by 12, which Clang shift-base UBSan reports even though the intended two's-complement Q27 conversion is established source behavior | high | Pamplist source owner / future accepted source revision | Preserve authenticated bytes; Layerwell disables only `shift-base` instrumentation for `pamplist_macro_voice` while retaining ASan and all other UBSan instrumentation | Upstream-defined unsigned or multiplication conversion, new exact source authority, standalone Pamplist regression, then removal of the parent-only exception | deferred |
