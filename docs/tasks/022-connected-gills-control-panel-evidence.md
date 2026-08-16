# Task 022: Connected Gills control-panel diagnostic and evidence

Status: Phase A completed on 2026-08-16 through deterministic local evidence
level 5. Phase B stopped after exactly one approved diagnostic volatile-RAM
upload produced the retained `POT_EVENT_FOCUS_UNSTABLE` result. Connected
device identity, RAM readback, start, responsiveness, OLED startup/orientation,
all six LED channels, all ten pot slot identities, and approximate `0000` to
`4095` pot travel were observed, but exact per-pot telemetry could not be
retained. No level-6 promotion, Task 021 replacement upload, staging, commit,
or push occurred. Approval gate 2 is closed after the diagnostic failure.
Running the task does not by itself authorize a device write: the executor must
obtain explicit approval at each volatile-RAM upload gate below.

## Goal and why it exists

Establish connected-device evidence for the complete software-readable Gills
panel, then confirm the exact Task 021 instrument's deliberately narrow product
mapping on the same board. Preserve the Task 021 instrument, runtime, binary,
and evidence unchanged.

This task exists because Task 021 proved that one exact corrected program can
run in volatile RAM and drive the OLED upright, but it did not exercise a
physical control. The accepted Blend reference intentionally consumes only
Performance Pot 1, Button 1 Press, LED 1, and OLED text. Moving the other
controls and observing no product change would prove mapping isolation, not
that those controls are electrically readable. Task 022 therefore requires a
separate diagnostic telemetry build before returning to the immutable product
binary.

## Dependencies and exact parent boundary

Task 021 is the immutable parent. ADR 0013 remains authoritative for the
DMA-safe OLED correction and the existing level-6 observation. ADRs 0011 and
0012 continue to own the legacy-equivalent DSP semantics and executable Gills
promotion boundary.

The executor must resolve these exact parent identities from
`schuss-record-set-000013@1`, content hash
`sha256:6e2b1f63abc999ab3067541f6dc0095ed338fb4b3f5c55898a58cdd3397bc8d3`:

- instrument `schuss-instrument-000002@3`, content hash
  `sha256:6b41e740ba7c4d098733d0f8fe462166ae553894b01c86a5db579d9aff38fc85`;
- build request `schuss-build-request-000002@5`, content hash
  `sha256:0422c6873c2f49140f4e3649cf5ea0ca690ea1999aac41c94deb0c28da87b33d`;
- build handler `schuss-build-handler-000003@2`, content hash
  `sha256:ade5ba04dac074558fd3287fe8b51d1489bae6399d3527c1dab3de2007859935`;
- runtime realization `schuss-runtime-realization-000001@2`, content hash
  `sha256:3442be669cd24994c5cd8dec37fbbc724697f79dbfd7195975ec8b2a00bc1cc7`;
- target executable `schuss-artifact-000029@1`, content hash
  `sha256:722cc070aec8228a3cb15ac74805dff1663998cb26e21395ed3f14e112f5093c`;
- exact 76,136-byte ELF SHA-256
  `4f9bd68f5f71fc9d5bf70bd88988e7e20ff980fb46a886beff52f60c968874de`;
  and
- exact 6,440-byte volatile upload binary SHA-256
  `b573ea36aaa29b5e213ca0e616b13e7e2131d7cad2a0ab29a5b5fe9eaa8b13e3`.

The connected parent observation names Ksoloti Core USB serial
`003D00363532511735393330`, firmware `1.1.0.0`, and firmware CRC `5021D42A`.
Any identity, firmware, record-set, source, generated-code, ELF, or binary
mismatch must stop the device phase. No ambient discovery, display-name
selection, filesystem-order selection, implicit latest revision, or handler
fallback is permitted.

## In scope

- Preserve every Task 018 and Task 021 record, generated artifact, retained
  evidence byte, public mapping, DSP semantic, and exact selector.
- Add a separate diagnostic-only panel telemetry path. It must not be presented
  as a musical instrument, production handler, or successor mapping.
- Keep the Task 021 DMA-safe OLED command buffer and independent page buffer in
  every diagnostic build that drives the display.
- Observe all ten performance pots at low, middle, and high positions with
  stable slot identity and raw-value telemetry.
- Observe press, release, and hold recognition for Buttons 1-4.
- Observe encoder turns in both directions and encoder-push press, release, and
  hold recognition.
- Exercise all six LED runtime channels through a deterministic diagnostic
  scan, while retaining unresolved hue facts as unresolved.
- Confirm upright, stable OLED startup and event telemetry without relying on
  audio.
- Reload the exact immutable Task 021 product binary and confirm Pot 1 soft
  pickup, Button 1 reset, LED 1 pickup feedback, OLED Blend feedback, and
  intentional no-op behavior for the other performance controls.
- Retain exact, fail-closed level-6 evidence for the device-profile diagnostic
  and the separate instrument-mapping observation.
- Keep build-time, connected-device, real-time/resource, and audible evidence
  explicitly separate.

## Out of scope

- New musical mappings, DSP behavior, graph nodes, public parameters, actions,
  state, display semantics, catalog work, sampling/assets, another target or
  device, firmware replacement, or UI work.
- Treating diagnostic telemetry as a new instrument or silently promoting it
  into the product runtime.
- Claiming that intentionally unused product controls affect the Blend
  instrument.
- Software-readability claims for the analog Input Volume, analog Output
  Volume, or Power Switch. The accepted runtime marks them hardware-only.
- Audio routing, output-level judgment, listening, analog-noise assessment,
  CPU/timing-margin measurement, underrun testing, endurance, electrical
  safety, or release qualification.
- Firmware flash, SD-card write, persistent install, automatic startup, or any
  device target other than volatile RAM at the authenticated address used by
  the approved procedure.
- Staging, committing, tagging, pushing, or publication without separate
  approval.
- Repairing the inherited Task 011A historical CLI golden mismatch.

## Inputs and deliverables

Inputs are this contract; ADRs 0011-0013; the exact Task 021 record set and
retained evidence; the complete Gills device profile and panel evidence; the
Task 021 DMA-safe frontend/runtime; the authenticated ARM toolchain/runtime;
and user observations made during the gated connected procedure.

Deliverables are:

- a deterministic diagnostic-only panel telemetry source and exact ARM
  artifacts, generated twice in fresh roots and processes;
- focused host vectors and tests for all ten pots, four buttons, encoder turn
  and push, six LED channels, OLED formatting, debounce, hold, pickup, and
  diagnostic state transitions;
- an exact diagnostic procedure identity and a canonical result table for
  every tested physical control, gesture, LED channel, and display check;
- retained build evidence under a Task 022-specific evidence root;
- one level-6 claim whose subject is the exact Gills device profile and whose
  inputs include the diagnostic artifact and procedure;
- a separate level-6 claim for the exact Task 021 instrument/product-binary
  mapping observation;
- explicit failed or unresolved results for any incomplete check rather than a
  partial `passed` promotion; and
- focused, aggregate, governance, path/hash, determinism, Task 021 regression,
  and contract validators.

Task 022 may complete without a new ADR if it makes no architectural or musical
decision. If implementation requires a new semantic authority, evidence level,
device protocol, or production mapping rule, stop and propose that decision
separately before editing those boundaries.

## Required diagnostic behavior

The diagnostic must be independently identifiable at startup and must never
reuse the Task 021 product presentation in a way that could confuse the two
binaries. Its first stable OLED frame must include `SCHUSS`, `PANEL TEST`,
`TASK022`, and `READY` across the four text lines.

The diagnostic interaction must satisfy all of the following:

1. It reports the last moved performance-pot slot and its raw `0..4095` value.
   Each pot has an independent session state for low, middle, and high zones.
2. Low is raw `0..512`, middle is raw `1536..2559`, and high is raw
   `3583..4095`. A clean counter-clockwise-to-center-to-clockwise sweep must
   visit the three zones in monotonic order. Reverse polarity, insufficient
   travel, discontinuity, a frozen value, or the wrong slot identity is a
   named failure; the executor must not adjust thresholds after observing the
   board merely to obtain a pass.
3. It reports press, release, and one hold event separately for each of Buttons
   1-4. The accepted four-update debounce and 1,500-debounced-update hold
   policies remain unchanged.
4. It reports at least three encoder detents in each physical direction and
   records the observed sign for each direction. Opposite directions must have
   consistent opposite signs. Physical clockwise/positive polarity is recorded
   as an observation and must not be silently added to the accepted device
   profile.
5. It reports encoder-push press, release, and one hold event separately.
6. It performs a deterministic six-channel LED scan. The OLED identifies the
   active runtime channel while the user confirms whether the corresponding
   physical indicator illuminates. LED 3/4 `Color A` hues remain observations,
   not authenticated color identities.
7. It retains a visible completion summary for ten pots, four buttons, encoder
   turn, encoder push, six LED channels, and OLED orientation. The summary may
   say `PASS` only when every required subcheck passed.
8. The observation surface must not depend on an unverified control to make
   another control observable. Automatic startup/LED sequencing and
   last-event telemetry must remain usable even if any one input fails.
9. Control processing remains at the accepted control-update rate. Host tests
   must prove the deterministic update path; the connected user observation
   may report prompt/stable response but must not be promoted to quantitative
   real-time evidence.

## Required execution order and approval gates

### Phase A: read-only and offline work

1. Verify the repository root, branch, worktree status, this task contract,
   ADRs 0011-0013, and every exact parent identity above.
2. Re-run the Task 021 generator, evidence, validator, and focused regression
   checks before changing code. A Task 021 mismatch stops the task.
3. Implement the smallest separate diagnostic path that satisfies the required
   behavior without changing the product instrument or Task 021 bytes.
4. Generate and build the diagnostic in two fresh roots and processes. Compare
   portable results and every artifact byte, retain exact hashes, and verify
   that no Java/legacy `.axp` fallback was used.
5. Run focused and aggregate offline validation. Show the user the exact
   diagnostic ELF/binary hashes, byte lengths, planned RAM address, expected
   startup text, exact board identity, and number of planned device uploads.

No device command is permitted in Phase A.

### Approval gate 1: diagnostic volatile-RAM upload

Pause and obtain explicit user approval for exactly one diagnostic binary,
one exact board, and volatile RAM only. Approval for Task 022 generally is not
approval for this upload. Do not combine this gate with firmware flash, SD-card
write, reset, a second upload, or any persistent action.

### Phase B: diagnostic connected-device procedure

1. Ask the user to disconnect or mute downstream audio and turn physical
   output level down; audio is not part of this task.
2. Resolve the connected board identity and firmware. Stop on any mismatch.
3. Upload only the approved diagnostic binary to the approved volatile-RAM
   address, read it back byte-for-byte, start it, and verify acknowledgement,
   responsiveness, and flags before asking the user to touch a control.
4. Stop immediately on lost responsiveness, nonzero fault flags, inverted or
   corrupted display output, unexpected heat/odor, repeated resets, or any
   deviation from the approved write boundary. Retain the failed observation;
   do not perform a recovery upload without new approval.
5. Guide the user through the LED scan, Pots 1-10 in physical order, Buttons
   1-4, encoder turns, and encoder push. Record each result independently.
6. Recheck device responsiveness and flags after the complete sweep.

## Observed Phase B result

The user explicitly approved exactly one diagnostic volatile-RAM upload. The
executor authenticated Ksoloti Core USB serial `003D00363532511735393330`,
firmware `1.1.0.0`, and firmware CRC `5021D42A`; uploaded only the exact
5,552-byte diagnostic binary SHA-256
`7c843acb42b17c13d0c535834d12ab620d312b451fd4ee435733e4acf7321113`
to `0x20011000`; read the bytes back exactly; received the start
acknowledgement; and observed three successful responsiveness probes over six
seconds with flags zero.

The user confirmed upright, stable OLED startup text `SCHUSS`, `PANEL TEST`,
`TASK022`, and `READY`. All six runtime LED channels illuminated; observed hues
were green, red, blue, red, blue, and red for channels 1-6 respectively, with
hue identities remaining unauthenticated observations. All ten pot slot
identities were correct and each pot moved smoothly and non-frozen through an
aggregate range of approximately `0000`, `2000` to `2010`, and `4093` to
`4095`.

Stationary ADC values varied by approximately 5 to 15 raw counts. That exceeded
the diagnostic's fixed four-count last-moved threshold, causing OLED line 2 to
cycle among inactive pot slots. The diagnostic therefore could not retain the
required exact per-pot low/middle/high telemetry. The retained failure is
`POT_EVENT_FOCUS_UNSTABLE`; it is an observation-surface failure and does not
claim a hardware fault. The sweep stopped before buttons, encoder, completion
summary, final responsiveness/flags, or level-6 promotion. Approval gate 2 is
closed, the exact Task 021 product binary was not uploaded, and no second
upload, reset, firmware flash, SD-card write, or persistent install occurred.

### Approval gate 2: immutable Task 021 product-binary upload

After presenting the diagnostic results, pause and obtain separate explicit
approval to replace the diagnostic in volatile RAM with the exact Task 021
6,440-byte binary named above. No rebuilt or merely equivalent binary may be
substituted.

### Phase C: exact product-mapping confirmation

1. Before starting the product binary, ask the user to place Pot 1 fully
   counter-clockwise and leave it there. Then read back the exact Task 021
   bytes, start them, and verify acknowledgement, responsiveness, flags zero,
   upright OLED output, and startup lines `SCHUSS`, `BLEND 050%`,
   `PICKUP ARM`, and `TASK018`.
2. Confirm LED 1 is illuminated while pickup is armed.
3. Move Pot 1 while remaining on one side of the current 50% Blend value. Blend
   must remain at 50% and `PICKUP ARM` must remain visible.
4. Move Pot 1 across the current Blend position. Pickup must become set, LED 1
   must turn off, and the displayed Blend value must then follow Pot 1
   monotonically through low, middle, and high regions.
5. Press Button 1. Blend must return to 50%, pickup must re-arm, and LED 1 must
   illuminate again. Release and hold introduce no additional mapped product
   action.
6. Exercise Pots 2-10, Buttons 2-4, encoder turns in both directions, and
   encoder-push press/release/hold one at a time. They must not change Blend,
   pickup state, LED 1, or the four product display roles. This proves exact
   mapping isolation; it does not replace the diagnostic control-read proof.
7. Recheck responsiveness and flags after the product-mapping procedure.

At completion, do not reset, power-cycle, upload again, flash, or write an SD
card automatically. Tell the user which volatile binary remains active and
that reset or power loss removes it.

## Acceptance tests

1. Every Task 018 and Task 021 generated record, artifact, selector, retained
   evidence file, and hash remains byte-exact.
2. The diagnostic path is explicitly non-product, exactly selected, and cannot
   be reached through Task 021's build request or handler by fallback.
3. Two fresh roots and processes produce identical diagnostic portable results
   and artifact bytes, with the DMA-safe OLED command/page-buffer separation
   retained.
4. Host vectors cover all ten pots at low/middle/high, all button and
   encoder-push press/release/hold events, both encoder directions, all six LED
   channels, OLED formatting, and the accepted debounce/hold policies.
5. The exact connected board passes diagnostic binary readback, start,
   responsiveness, and fault-flag checks before and after the panel sweep.
6. The OLED remains upright and stable and shows the required Task 022 startup,
   per-event telemetry, LED-channel labels, and completion summary.
7. Pots 1-10 each pass exact slot identity, low/middle/high zone, monotonic
   direction, travel, and non-frozen response checks independently.
8. Buttons 1-4 each produce distinct press, release, and hold observations;
   encoder push does the same; encoder rotation produces consistent opposite
   signs in both physical directions.
9. All six LED runtime channels illuminate under the diagnostic scan, with
   unresolved hue identity kept separate from channel-function evidence.
10. The exact immutable Task 021 binary separately passes readback, start,
    responsiveness, flags, upright startup display, and LED 1 armed-state
    checks.
11. Pot 1 separately passes soft-pickup hold, crossing, monotonic Blend update,
    OLED feedback, and Button 1 reset/re-arm behavior on the product binary.
12. Pots 2-10, Buttons 2-4, encoder rotation, and encoder-push gestures produce
    no product-state, Blend, LED 1, or display-role change under the exact Task
    021 mapping.
13. The retained result contains a complete per-control matrix and exact board,
    firmware, record-set, procedure, source, ELF, binary, RAM-address,
    readback, acknowledgement, responsiveness, flags, and user-observation
    identities. Missing subchecks cannot be omitted or counted as passed.
14. Device-profile diagnostic evidence and instrument-mapping evidence remain
    separate exact level-6 claims. Build execution continues to report only
    levels 1-5; levels 7 and 8 remain `not-run`.
15. Task 022 contract, focused, aggregate, determinism, governance, path/hash,
    CLI, Task 021 regression, and `git diff --check` validation passes. The
    repository-wide suite is run, but the inherited Task 011A historical
    golden is reported rather than rewritten under this task.

## Decisions Task 022 may make

- The smallest diagnostic-only source seam and exact non-product identities
  required to build and retain the panel telemetry artifact without changing
  the instrument.
- The deterministic four-line telemetry layout, automatic LED-test cadence,
  last-event presentation, and completion-summary encoding within the required
  behavior above.
- The canonical per-control observation/result schema and exact evidence and
  procedure IDs.
- The exact bounded USB/RAM procedure reused from the authenticated Task 021
  device path, provided every target, address, byte count, and hash is shown at
  the approval gate.
- Fail-closed diagnostics and validators needed to prevent product/diagnostic
  selector ambiguity or evidence inflation.

## Decisions Task 022 must not make

- Any change to Task 018 or Task 021 records, bytes, mappings, DSP semantics,
  build selection, evidence claims, or historical goldens.
- New musical uses for Pots 2-10, Buttons 2-4, encoder rotation/push, LEDs 2-4,
  or OLED graphics.
- A claim that the analog volume knobs, power switch, optional connectors, or
  physical I/O were software-tested.
- A claim of quantitative latency, CPU margin, underrun safety, endurance,
  audio behavior, sound quality, persistence, electrical safety, or release
  readiness.
- Implicit latest revision selection, ambient discovery, display-name
  resolution, fallback, or mutation of an accepted record to make the
  diagnostic selectable.
- Firmware flash, SD-card write, persistent install, automatic startup,
  unapproved reset, additional upload, staging, commit, or push.
- Activation of Task 019, Task 020, or the unnumbered UI milestone.

## Completion and failure states

Task 022 is complete only if all fifteen acceptance tests pass and both exact
level-6 claims can be retained without modifying their parent authorities. The
completion statement must say that complete software-readable panel operation
and the existing Blend mapping were observed on one exact board; it must not
say that every panel control is musically mapped.

If any control, gesture, LED channel, display behavior, device check, or exact
identity fails, retain a failed or observed diagnostic result naming the exact
step and stop promotion. A partial panel sweep is not complete level-6 panel
evidence. Levels 7 and 8 remain `not-run` regardless of Task 022's level-6
outcome.
