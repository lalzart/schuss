# Pamplist prototype dependency notices

Pamplist compiles the configured Ksoloti Extended Macro Voice wrapper and its
vendored Mutable Instruments Plaits DSP closure read-only. No upstream source
bytes are copied into this prototype.

- Ksoloti Extended Macro Voice wrapper: GPL-3.0-or-later; locked `patcher`
  revision `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`.
- Mutable Instruments Plaits DSP: MIT; upstream revision
  `08460a69a7e1f7a81c5a2abcc7189c9a6b7208d4`.
- Mutable Instruments stmlib: MIT; upstream revision
  `e3bd7c9cc00e4364166f9905c0509b6ffd0535ec`.
- JUCE 8.0.15 is used only for the optional private-development standalone and
  local VST3 targets under the repository's authenticated local-source policy.
  JUCE is available under its commercial terms or AGPLv3; its authenticated
  source tree includes the Steinberg VST3 SDK under the notices and terms in
  that tree. Task 045 makes no redistribution determination.

Original notices remain in the configured source tree. This file records local
prototype provenance. The VST3's final local ad-hoc macOS seal is only a
structural local-build step; it is not identity signing, notarization,
distribution, or licensing approval.
