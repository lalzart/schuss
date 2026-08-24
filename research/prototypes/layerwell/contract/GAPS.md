# Layerwell Desktop Meta-Instrument implementation gap register

> Status: revision 0.1 implemented; higher evidence and product expansion remain open

Passing a lower evidence level never closes a higher one.

| ID | Gap | Severity | Owner or stage | Current decision | Proof required | Disposition |
|---|---|---|---|---|---|---|
| GAP-001 | Real audio-device callback deadline, lifecycle, and xrun behavior | high for runtime promotion | later real-time task | Deferred; Task 042 did not launch the app | Authorized device launch at 48 kHz with declared block sizes and load; endpoint lifecycle, xruns, worst-case and p99 callback timing | open |
| GAP-002 | Physical regular Launch Control 3 enumeration, receipt, encoder feel, LED/OLED feedback, reconnect, and cleanup | high for controller claim | later connected-device task | Synthetic protocol only | Explicit dedicated-DAW-port selection and observed Page, Track, mode, encoder, button, Shift, LED, OLED, reconnect, and disable behavior | open |
| GAP-003 | Musical usefulness, balance, seam audibility, source-switch feel, and replacement timing | medium | later listening round | No listening claim | Documented listening protocol and retained observations | open |
| GAP-004 | Distribution, dependency-license review, notice assembly, packaging, signing, and notarization | high for release | later distribution task | Local authenticated build only | Formal JUCE and source-package review plus assembled package and notarization evidence | open |
| GAP-005 | Canonical Schuss identity, catalog, complete graph, implementation provider, application library, and production runtime | high for production | future governance task | Explicitly excluded | Accepted task, stable IDs, graph/provider bindings, compatibility, native, reproduction, and release validation | open |
| GAP-006 | Persistence, recovery, external clock, richer sampling, arbitrary sources, additional layers, and plug-in formats | enhancement | future design review | Excluded from revision 0.1 | New approved proposal and explicit product decisions | deferred |
| GAP-007 | Two exact Mutable source closures originally exported colliding `braids` and `stmlib` symbols in one optimized process | high for composition | Task 042 parent seam | Privately prefix Tide Pit internal namespaces only in Layerwell; standalone default stays off | Combined source process gate, exact authority verification, and both standalone source suites | closed by current host evidence |
| GAP-008 | App presentation has not been launched or visually inspected | medium for audition usability | later authorized UI check | Build-only evidence retained | Fresh app launch, visual inspection, state projection, explicit audio/MIDI lifecycle, and clean shutdown | open |
