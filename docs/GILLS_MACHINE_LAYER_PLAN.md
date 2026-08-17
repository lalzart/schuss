# Gills machine layer plan

Status: Task 029 implemented in this isolated worktree. Local acceptance is
complete; the change is not staged or committed.

The active implementation contract is
[GILLS_MACHINE_IMPLEMENTATION_CONTRACT.md](GILLS_MACHINE_IMPLEMENTATION_CONTRACT.md).

This plan defines the next product layer for complete Gills instruments. A
**machine** is a completed, inspectable instrument product. It is not an
individual catalog object, a new DSP node, a generated legacy patch, or a
synonym for a project manifest.

The implementation deliberately does not change the accepted twenty-object direct
palette. Missing machine dependencies remain missing or unsupported until
their own evidence supports a later decision.

## Authority, baseline, and isolation

This inspection used the Schuss authority chain in `PROJECT_CONTEXT.md`,
`STATUS.md`, accepted ADRs, device/instrument contracts, current task records,
and the exact accepted record set before consulting archived prose.

The verified Schuss baseline was:

- worktree: this isolated worktree, detached at
  `0cddd56eb1f3c0d9e82c1661054e39c93f41facb`;
- accepted parent record set: `schuss-record-set-000021@1`;
- catalog revision: 4, with 60 families and 83 implementations;
- direct Gills palette: the exact 20 selections accepted by Task 028, with
  structural evidence levels 1-3 only;
- Task 029 successor record set: `schuss-record-set-000022@1`, parented exactly
  by `schuss-record-set-000021@1`.

The currently running desktop catalog-foundation work is a separate task. This
implementation neither reads its worktree nor assumes, modifies, merges, or
reserves any of its files, IDs, routes, components, or decisions. Its Viewer is
the isolated `apps/schuss_machine_viewer/` client and does not integrate with
or depend on `apps/schuss_desktop/`.

## Inspected instruments and exact source identity

The requested name `Pamulist` does not occur in the inspected Gills or Ksoloti
checkouts. The evidence-backed match is **Palimpsest**.

| Instrument | Exact portable location in `gills-instruments` |
|---|---|
| Tide Pit | `projects/tide-pit-gills/` |
| Palimpsest | `projects/palimpsest-gills/` |

The inspected Gills checkout was
`https://github.com/lalzart/gills-instruments.git` at working-tree HEAD
`33038b5de6315bce9bbe167062f2876823ff1adc`. The checkout contained unrelated
dirty and untracked work, which was not modified. The target project files were
tracked and unchanged relative to HEAD; their last project-affecting commit was
`53287e49e5bcc5fb0d73b546d88431f82467f969` (`Import Gills instrument
collection`). The two durable source-review records pin a portable source ID,
repository URL, this project-affecting commit, relative paths, and exact file
hashes rather than the absolute checkout path.

The inspected target bytes were:

| Project file | SHA-256 |
|---|---|
| `projects/tide-pit-gills/LICENSE.md` | `2701d4f24dfe91723d1d43103daa123e8be61e53ad09f142735c91f58a06baac` |
| `projects/tide-pit-gills/README.md` | `be3a5174d13f03fc02faff57b9afa3275faf34b3210850c7f50b219fdad7b52a` |
| `projects/tide-pit-gills/tidepit-gills.axp` | `35b8df83ffc06bacca1890d936525c75758b193bcf7ef7edd69082acdb7e963c` |
| `projects/tide-pit-gills/tidepit.axo` | `8e62fdfd1f6b101cb5b6f876d3d54538af8be9a04a46cddba2711eaabc3b9009` |
| `projects/tide-pit-gills/tidepit_dsp.h` | `3f75a3aa337109e7de270cb4a4aa7281f71ba4de443f057b4e37299e3bd7b32e` |
| `projects/tide-pit-gills/tidepit_voice.h` | `e6cd224160df87afbfda5743c5124a4600c5f3c6fe4c02df272c41916cd6566c` |
| `projects/palimpsest-gills/LICENSE.md` | `3ed2c3d7e2d88af7320354f51bcfd5748408145ecae1fabb7092ddc7f736acbc` |
| `projects/palimpsest-gills/README.md` | `5371ebc7e5e53cf0db2c92e9db90151b4c67f2581c6730178e3dde4f85a369e6` |
| `projects/palimpsest-gills/palimpsest-gills.axp` | `95f92e4634353f4629677b1430041aa4d71238acf4bfcbadf236def46d81cfed` |
| `projects/palimpsest-gills/palimpsest.axo` | `52dd0f13611620852c78afd5761f26835dbea138a498ddfa136f0a632ab3e9cd` |
| `projects/palimpsest-gills/palimpsest_dsp.h` | `28bf741f4841c98b8059574a7dcfe941b024d3f0bde9608bc2c7fec86d8ebb05` |

Neither project has an `instrument.contract.json` or project-local host harness.
Both currently rely on the documented legacy authoring exemption. That is
source evidence, not proof that either is already a Schuss machine.

The Ksoloti and installed-library checkouts were inspected read-only at:

- Ksoloti: `08d3e6e1e2b61230308c20a15ded58ffdaf4656c`;
- `axoloti-factory`: `25d2615ed5233546d617017666a4ab1e60a8c506`;
- `ksoloti-objects`: `7000fde4cf60d2d79a36d95098418c4a654dc056`.

These locations and commits authenticate the inspection. They do not authorize
Schuss to discover sources from ambient checkouts; durable import must use
`catalog/sources.lock.json` and portable source IDs.

## Product and model boundary

The smallest useful relationship is:

```text
machine-v0
  -> exact instrument-v0
       -> exact device profile
       -> exact authoritative DSP graph
  -> exact source-review evidence
  -> exact presentation references
  -> derived dependency/support inspection
```

Each layer has one job:

- the catalog describes independently browsable objects;
- the DSP graph describes the complete, transparent signal/control graph;
- the instrument record owns user-facing parameters, actions, state, and
  mappings onto a device profile;
- the machine record gives the completed instrument a stable product identity,
  summary, evidence packet, and presentation;
- the compute target and compiler backend remain independent choices.

A machine therefore does not collapse its implementation into a local `.axo`
wrapper. The wrapper and `.axp` can be source evidence and a legacy boundary
artifact, but the authoritative Schuss graph must ultimately expose the full
closure, including compound internals. Conversely, physical Gills pots,
buttons, encoder, LEDs, and OLED are device-profile slots, not DSP objects to
add to the catalog drawer.

## Actual patch shell shared by both instruments

Both legacy `.axp` files instantiate this shell:

```text
audio/outconfig
const/i (root default 60) -> Gills encoder (36..72)
10 x Gills pot p --------------------------+
4 x Gills button --------------------------+-> local instrument wrapper
encoder value + switch --------------------+       | stereo audio
                                                    | four LED values
                                                    | four charptr32 OLED lines
local wrapper -> audio/out stereo
local wrapper -> 4 x Gills LED
local wrapper -> Gills display
```

Both configure the output for stereo headphones at -24 dB. Both use display
scope off and narrow font on. This shell establishes wiring and defaults only;
it does not prove equivalent Schuss objects, a complete instrument contract, a
compiler route, or connected-device behavior.

## Tide Pit evidence model

### Tide Pit audio and control block diagram

The source supports this presentation diagram:

```text
four-stage pitch cycle + memory mutation + root/scale
  -> source selector
       -> REED: local high-resolution feedback waveguide
       -> RND: sine/triangle source
       -> FOLD: Braids-derived sine-fold source
  -> sympathetic string
  -> energy/LPG shaping
  -> eight-mode stereo body
  -> mono record feed
  -> Clouds-derived 16-bit record buffer and six-grain engine
  -> dry/wet mix
  -> Clouds diffusion reverb
  -> CLEAN | resonant filter | tone-shaped drive
  -> stmlib soft clipping
  -> stereo output
```

The diagram is an evidence-backed explanation, not a substitute for the future
authoritative graph. Every viewer block must carry a trace back to source spans
or an exact graph node before the diagram may claim graph completeness.

The source declares four SDRAM allocations:

| Use | Declared bytes |
|---|---:|
| feedback waveguide buffers | 10,240 |
| sympathetic-string buffers | 16,384 |
| granular record buffer | 192,016 |
| Clouds diffusion-reverb buffer | 32,768 |
| **Total** | **251,408** |

This is a source-derived allocation total, not measured peak memory, timing,
resource safety, or connected-device evidence.

### Tide Pit Gills mapping

| Physical control | Tide Pit meaning |
|---|---|
| Pot 1-4 | four stage values |
| Pot 5 | cycle rate |
| Pot 6 | memory/mutation amount |
| Pot 7 | timbre/material |
| Pot 8 | grain position |
| Pot 9-10 in CLEAN | grain size; depth/spread/tail behavior |
| Pot 9-10 in FILT | cutoff; resonance |
| Pot 9-10 in DRIVE | tone; amount |
| Button 1 | cycle REED / RND / FOLD source |
| Button 2 | mutate once |
| Button 3 | lock/unlock automatic mutation |
| Button 4 tap | cycle CLEAN / FILT / DRIVE |
| Button 4 hold | capture/freeze granular buffer |
| Encoder turn | root C2-C5 |
| Encoder press | cycle scale |
| Encoder hold | cycle pitch/body/grain/all wave destination |
| LEDs 1-4 | active stage |
| OLED line 1 | identity, destination, root |
| OLED line 2 | four stage digits and current step |
| OLED line 3 | memory and current effect parameters |
| OLED line 4 | scale, source, effect, evolve/lock, capture or no-grain state |

Pots 9 and 10 retain per-mode values and use soft pickup. Buttons 1-3 use raw
edge detection in the inspected source; Button 4 and the encoder switch have
local timing logic. Those facts must remain explicit rather than being upgraded
to a general debounce or responsiveness claim. OLED content is refreshed every
64 audio blocks in the instrument code; the Gills display service has its own
runtime cadence. Neither source fact is connected-device timing proof.

### Tide Pit direct code/resource closure

Tide Pit directly depends on local `tidepit_voice.h`, Clouds audio-buffer,
grain, parameter, resources, frame, and reverb headers; Braids resources;
stmlib DSP, reciprocal-square-root, units, and random helpers; standard C/C++
headers; and Ksoloti runtime buffer/SDRAM facilities. It also links resource
tables used by the embedded Braids and Clouds code.

The Clouds diffusion reverb here uses `FxEngine<16384, FORMAT_16_BIT>` with a
32,768-byte allocation. It is not the Rings reverb binding rejected in Task
025, whose legacy wrapper declares `FxEngine<32768>` but supplies only 32,768
bytes where 65,536 are required. Tide Pit is not evidence for changing that
fail-closed `COMPILER_BINDING_UNSUPPORTED` result.

## Palimpsest evidence model

### Palimpsest audio and control block diagram

The source supports this presentation diagram:

```text
four-stage pitch cycle + memory mutation + root/scale
  -> direct modal strike + three scale-aware delayed trace events
  -> fixed 16-event scheduler
  -> fixed 16-voice pool with quietest-voice stealing
  -> per-voice three-partial modal synthesis
       -> Braids sine resource table
       -> recipe ratios/gains/decays/transients/pan
  -> direct/wake stereo mix
  -> CLEAN | custom resonant filter | tone-shaped asymmetric drive
  -> rational limiter x / (1 + abs(x))
  -> stereo output
```

The implementation uses fixed event and voice pools and does not request
dynamic SDRAM. That is source structure, not a measured CPU, stack, RAM,
polyphony, or real-time-safety result.

### Palimpsest Gills mapping

| Physical control | Palimpsest meaning |
|---|---|
| Pot 1-4 | four stage pitches |
| Pot 5 | cycle rate |
| Pot 6 | memory/mutation amount |
| Pot 7 | harmonic-to-inharmonic material |
| Pot 8 | trace spacing |
| Pot 9-10 in CLEAN | decay; activity/wake |
| Pot 9-10 in FILT | cutoff; resonance |
| Pot 9-10 in DRIVE | tone; amount |
| Button 1 | cycle TRACE / KNOCK / SKIN / SHARD recipe |
| Button 2 | mutate once |
| Button 3 | lock/unlock automatic mutation |
| Button 4 tap | cycle CLEAN / FILT / DRIVE |
| Button 4 hold | clear voices and scheduled events |
| Encoder turn | root C2-C5 |
| Encoder press | cycle scale |
| Encoder hold | no mapping in the inspected source |
| LEDs 1-4 | active stage |
| OLED line 1 | identity, voice recipe, root |
| OLED line 2 | stage form and current step |
| OLED line 3 | memory, spacing, decay or effect parameters |
| OLED line 4 | scale, effect, evolve/lock state |

Pots 9 and 10 use per-mode storage and soft pickup. Button 1 and the encoder
have local debounce timing; Buttons 2 and 3 use raw edges, and Button 4 has
hold logic without a complete instrument-level debounce contract. A future
instrument record must preserve these distinctions.

### Palimpsest direct code/resource closure

Palimpsest directly includes Braids resources, stmlib DSP utilities, and
standard C/C++ headers. Its stage engine, event scheduler, voice allocator,
modal voice, panner, filter, drive, and limiter are local implementation units
inside one header. The Braids sine table is a linked code resource, not an
independently selectable object.

## Dependency and support inventory

The classifications below are exact to accepted record set
`schuss-record-set-000021@1`. A later task must recompute them against its own
accepted parent. “Similar” never means interchangeable.

### Classification vocabulary

- **selectable**: an exact accepted target/backend binding is eligible in the
  current 20-object direct palette;
- **accepted support**: an exact accepted contract/binding exists but is not a
  counted public palette selection;
- **catalogued-only**: a reviewed catalog identity exists without the exact
  accepted support needed here;
- **observed-only**: the current/frozen source corpus contains the definition,
  but Schuss has not promoted it to a reviewed public family;
- **absent**: no exact Schuss catalog identity was found;
- **private helper**: implementation detail of this machine closure;
- **non-object**: device, presentation, source-library, toolchain, or runtime
  facility rather than a browsable DSP object;
- **unsuitable for standalone promotion**: importing it as a drawer object
  would hide machine internals, confuse layers, or be justified only by this
  import.

### Shared shell

| Required dependency | Current state | Machine-layer treatment |
|---|---|---|
| `audio/out stereo` | catalogued legacy output plus accepted exact native output support (`schuss-implementation-000048@2` / component contract `schuss-component-contract-000009`) | reuse the output semantic contract where exact; do not claim byte equivalence to the legacy object |
| `audio/outconfig` | observed current-Ksoloti candidate, not a reviewed/selectable family | model headphones/gain as machine, target, or runtime configuration; unsuitable palette padding |
| `const/i` root default | reviewed family `schuss-family-000052`, implementation `schuss-implementation-000072`, catalogued-only/unresolved | represent the initial root in instrument state/defaults; no promotion required for first viewer |
| Gills pots 1-10 | observed objects; physical slots are accepted by the Gills device profile, not public DSP families | device/instrument mappings; unsuitable for catalog promotion |
| Gills buttons 1-4 | observed objects; physical slots are accepted by the Gills device profile | device/instrument mappings; unsuitable for catalog promotion |
| Gills encoder and switch | observed object; physical slots are accepted by the Gills device profile | device/instrument mappings; unsuitable for catalog promotion |
| Gills LEDs 1-4 | observed objects; physical slots are accepted by the Gills device profile | displays/indicators mapped by the instrument; unsuitable for DSP palette promotion |
| Gills OLED display | family `schuss-family-000025`, implementation `schuss-implementation-000037`, catalogued-only/unresolved; Task 021 runtime evidence applies only to its exact retained closure | display facet and exact instrument mapping; no generalized support claim |
| local `./tidepit` / `./palimpsest` wrapper | absent as Schuss catalog objects | source evidence for complete machines; unsuitable as single drawer objects because that would conceal the graph |

### Tide Pit-specific closure

| Required dependency | Current state | Fail-closed conclusion |
|---|---|---|
| high-resolution REED waveguide | modified local/private helper | not equivalent to factory fluted-string candidates; keep private pending exact decomposition |
| RND oscillator and FOLD source | private source paths using local math/Braids resources | factory/tagged candidates do not prove exact semantics; no substitution |
| sympathetic string, LPG/energy, eight-mode body | absent/private helpers | keep inside transparent machine graph unless independent reuse later earns catalog work |
| Clouds-derived record/audio buffer and six-grain engine | a Clouds-like legacy implementation exists (`schuss-implementation-000010`) but no exact contract, binding, or palette eligibility proves this closure | unresolved; exact code/resource/parameter semantics required |
| Clouds diffusion tail | embedded private helper/resource | do not substitute the separately unsupported Rings reverb |
| resonant filter, tone drive, stmlib soft clip | private or source-library helpers | selectable lowpass/gain and Task 025 soft-clip implementations are only analogues; exact equivalence is unproved |
| Braids/Clouds tables and stmlib utilities | non-object linked resources | record as source/runtime dependencies with hashes and licenses, not palette entries |
| `sdram_malloc`, `BUFSIZE`, firmware services | non-object Ksoloti runtime facilities | target/backend prerequisites; source declaration is not resource proof |

### Palimpsest-specific closure

| Required dependency | Current state | Fail-closed conclusion |
|---|---|---|
| stage/mutation engine and scale handling | private machine logic; related scale/MTOF catalog entries are catalogued-only | preserve exact local semantics; no palette promotion needed for viewer |
| delayed-event scheduler and fixed voice allocator | absent/private helpers | machine coordination logic, unsuitable as DSP drawer padding |
| three-partial modal voice and recipe logic | absent/private helper | decompose transparently inside the graph; consider standalone catalog work only if independently useful |
| Braids sine table | non-object linked resource | dependency evidence, not a selectable oscillator object |
| panner and direct/wake mixer | private helpers | exact behavior must be represented; apparent mixer similarity is insufficient |
| custom resonant filter and asymmetric drive | private helpers | current selectable lowpass and saturating-gain objects are not proven equivalent |
| rational limiter | private helper | Task 025 audio soft clip has different semantics; no substitution |
| stmlib and standard C/C++ facilities | non-object source/toolchain dependencies | pin and license as required; do not create catalog objects for headers |

No dependency in these tables justifies expanding the 20-object palette. An
import may use a transparent machine-private compound closure while public
catalog promotion remains a separate evidence-governed decision.

## Smallest durable records

### `machine-source-review-v0`

This companion record can be created before an authoritative Schuss graph. It
is explicitly **inspection-only** and must never be interpreted as an imported,
buildable, supported, or playable machine.

Minimum fields:

| Field | Requirement |
|---|---|
| schema identity | exact schema ID/revision/hash |
| review identity | stable source-review ID/revision/canonical hash |
| source identity | portable source ID, repository URL, commit, relative project root, exact file hashes |
| asserted product identity | source-provided name and summary, with aliases/corrections such as `Pamulist` -> `Palimpsest` retained as review evidence rather than stable identity |
| patch shell | exact legacy object references, attributes, and connections |
| source blocks | ordered explanatory blocks/edges with exact source-span or file-hash evidence |
| observed panel mappings | physical device slot -> observed meaning/state/action/display, with evidence location and uncertainty |
| dependency assessments | exact dependency key, classification, matching Schuss reference if any, reason, evidence level, and proof gaps |
| proof boundary | explicit structural checks run/not run; compiler, device, real-time, and audible states fail closed |

### `machine-v0`

A real machine record is smaller because it references existing authority
instead of copying it. Its minimum fields should be:

| Field | Requirement |
|---|---|
| schema identity | exact schema ID/revision/hash |
| machine identity | stable machine ID, revision, and canonical record hash |
| display name and summary | machine-owned product presentation only |
| instrument reference | exact accepted `instrument-v0` ID/revision/hash; transitively resolves the device profile and authoritative DSP graph |
| source-review reference | exact accepted source-review ID/revision/hash |
| presentation reference | exact block-diagram and panel-presentation record ID/revision/hash |

The machine record must not duplicate the graph, mappings, target/backend,
support state, or dependency list. `machine.inspect` resolves those from exact
references and derives a current, reviewable result. Validation rejects stale
hashes, missing closure, mismatched device mappings, unsupported required
dependencies, or a presentation block that cannot trace to source/graph
evidence.

This split prevents an inspection-only source review from masquerading as an
accepted machine while still allowing the first Viewer work to use durable,
honest evidence.

## Gills panel visual and semantic assets

The visual source of truth is the editable
`assets/gills/gills-panel-v06.svg` silhouette/layout of the real Gills panel.
It was derived from trusted pinned CAD and editable layout sources, not
manufactured from memory or traced from the photograph.

Use three separate layers:

1. `assets/gills/gills-panel-v06.svg`: deterministic editable geometry and artwork for the
   physical panel, with stable SVG element IDs, normalized view box/encoding,
   no embedded mutable external references, and no machine-specific labels.
2. `panel-layout-v0`: a semantic device-profile map. Each entry binds a stable
   Gills control/display slot ID and kind to its physical label, SVG element ID,
   anchor point, and optional hit/highlight region. SVG DOM order, coordinates,
   and visible text are never identity.
3. the exact instrument mapping: machine meanings, current modes, actions,
   values, and display content. The Viewer overlays these mappings without
   editing either the physical SVG or the device profile.

Minimum semantic entry fields are:

```text
semantic_slot_id
kind
physical_label
svg_element_id
anchor { x, y }
highlight_element_id
```

The map must cover ten pots, four buttons, the encoder turn and switch actions,
four LEDs, and the OLED region. If jacks or other physical elements are shown,
they receive stable device IDs only when the accepted device profile owns them;
decorative SVG elements remain non-semantic.

### Trusted source and completed SVG

The pinned v0.6 hardware commit
`280503036aee95e6c6ef91a1f1357443f4768faa` contains both the exact metric
panel PCB and a trusted editable board-layout SVG at
`ksoloti-gills_panel/ksoloti-gills_panel-brd.svg`. Their SHA-256 values are
`348e22c25b7b54bd9db989c581408ed7429b9d7c2df65f19e8beb6a99b0368c4`
and `bd0c9b33298f5bfa91ee13939d96048882d5bd7c32ca99819781b9b8fd5ec833`.
The repository license hash is
`9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94`;
the retained asset records CC BY 4.0 attribution and adaptation notice.

The completed Schuss SVG has exact 158 x 100 mm geometry, stable element and
highlight IDs, no raster pixels or external references, and SHA-256
`575eaab71b2e742692dbdd73eedfc99ad47dc2a62ce347c558922191f68b894c`.
The separate `schuss-panel-layout-000001@1` record maps all 42 qualified device
slots and explicitly excludes only the unanchored power-switch slot.

Each source review accounts for 34 machine-meaning slots exactly once: ten
performance-pot inputs, all sixteen accepted button/encoder gestures, six
feedback channels, and both OLED capabilities. The four raw button inputs and
two raw encoder inputs are still present in the 42-region physical panel map
but are not assigned duplicate machine meanings beside their accepted gesture
slots. Input/output volume remain panel hardware rather than patch-controlled
instrument facets. Power is the one explicit panel-map exclusion.

### Supplied physical-panel photograph

The user supplied `Photo 1.jpg` in this planning task. The received attachment
is a 3840 x 2880 baseline JPEG with upper-left orientation and SHA-256
`725fc22a21d5fe78118ad865e36eb9626eb9f74aa003309144b48614c1801674`.
The temporary attachment path is not a durable source identity and the image
was not copied into the repository.

The photograph is sufficient appearance/population evidence for the depicted
physical unit and for later visual comparison. It clearly shows the full
populated front panel and upright silkscreen, OLED window, ten main pots, four
buttons, encoder, four LED windows, input/output volume pots, panel
perimeter/slots, and the top I/O legends. It also shows the light metallic panel
finish and black legend treatment.

It is not a metric geometry source by itself. The image has mild perspective
and possible lens distortion, uneven light/glare, shadows, and knob occlusion;
no trusted panel dimension or matching hardware revision accompanies it. The
OLED is off and the LEDs are unlit, so display appearance and populated LED
colors cannot be inferred. File creation metadata is attachment-processing
metadata and is not treated as the capture date.

### Photo-to-CAD qualification result

The bounded qualification test fetched only the pinned public hardware commit
into a temporary checkout. The checkout resolved exactly to
`280503036aee95e6c6ef91a1f1357443f4768faa`; its panel PCB SHA-256 was the
retained Task 018 value
`348e22c25b7b54bd9db989c581408ed7429b9d7c2df65f19e8beb6a99b0368c4`.
The repository identifies the hardware and enclosure panels as v0.6 and
licenses the hardware design under CC BY 4.0.

The photograph matches the pinned **white v0.6** top-panel topology: outer
silhouette, three top and three bottom horizontal slots, four side slots, four
corner mounting holes, OLED opening, three upper controls, two upper and two
lower buttons, two rows of five main pots, four LED windows, and the visible
silkscreen/I/O legends all correspond. A heuristic neutral-panel boundary fit
gave a mean photographic width/height ratio of about 1.590 versus the CAD's
exact 1.580; the opposite top/bottom edge errors are consistent with the
visible perspective and are not treated as dimensional evidence.

The CAD supplies the missing metric authority:

- top-panel outer size: exactly 158.000 x 100.000 mm;
- OLED opening: exactly 31.200 x 17.200 mm;
- top-panel coordinate origin: upper-left outer-corner bounding box, with `x`
  increasing right and `y` increasing down.

The first semantic control/display anchor set is therefore recoverable without
tracing photo pixels:

| Stable device slot(s) | Physical reference | Region kind | Anchor x (mm) | Anchor y (mm) |
|---|---|---|---:|---:|
| `device-input-000001` | RV1 / pot 1 | rotary control | 29.002 | 58.242 |
| `device-input-000002` | RV2 / pot 2 | rotary control | 54.002 | 58.242 |
| `device-input-000003` | RV3 / pot 3 | rotary control | 79.002 | 58.242 |
| `device-input-000004` | RV4 / pot 4 | rotary control | 104.002 | 58.242 |
| `device-input-000005` | RV5 / pot 5 | rotary control | 129.002 | 58.242 |
| `device-input-000006` | RV6 / pot 6 | rotary control | 29.002 | 83.242 |
| `device-input-000007` | RV7 / pot 7 | rotary control | 54.002 | 83.242 |
| `device-input-000008` | RV8 / pot 8 | rotary control | 79.002 | 83.242 |
| `device-input-000009` | RV9 / pot 9 | rotary control | 104.002 | 83.242 |
| `device-input-000010` | RV10 / pot 10 | rotary control | 129.002 | 83.242 |
| `device-input-000011` | SW1 / button 1 | momentary button | 54.002 | 42.242 |
| `device-input-000012` | SW2 / button 2 | momentary button | 79.002 | 42.242 |
| `device-input-000013` | SW3 / button 3 | momentary button | 66.502 | 70.742 |
| `device-input-000014` | SW4 / button 4 | momentary button | 91.502 | 70.742 |
| `device-input-000015`, `device-input-000016` | ENC1 turn and push | encoder region | 94.002 | 34.142 |
| `device-input-000017` | RV11 / input volume | hardware-only rotary control | 29.002 | 33.242 |
| `device-input-000018` | RV12 / output volume | hardware-only rotary control | 129.002 | 33.242 |
| `device-feedback-000001` | LED1 | indicator region | 113.460 | 21.192 |
| `device-feedback-000002` | LED2 | indicator region | 113.460 | 29.192 |
| `device-feedback-000003`, `device-feedback-000004` | LED3 dual channels | shared indicator region | 63.382 | 54.422 |
| `device-feedback-000005`, `device-feedback-000006` | LED4 dual channels | shared indicator region | 88.410 | 54.422 |
| `device-display-000001`, `device-display-000002` | OLED1 text and graphics | shared display region | 66.500 | 19.890 |

The LED result corrects a potential modeling trap: four physical LED windows
represent six accepted feedback slots because LED3 and LED4 each expose two
channels. Multiple stable semantic slots may therefore reference one SVG
highlight region; the region must not collapse their runtime identities.

KiCad 10.0.5 exported the complete panel drawing to SVG twice. The raw files
had different SHA-256 values solely because the generated `<title>` embeds the
wall-clock export time. Replacing that title time with a fixed normalized value
made the exports byte-identical at SHA-256
`508c8a6a871bdeed7e73c378d3708d93bf6002b9f986e5ffbf1ed3b54ecd630b`.
The retained Schuss asset is therefore a reviewed clean technical adaptation,
not the timestamp-bearing raw export.

This qualification clears the geometry and appearance prerequisites for a
CAD-derived v0.6 Viewer asset. The physical unit is a strong visual match to
that revision, not serial/rear-marking proof of its electronics. Another photo
is needed only if later visual review finds an unresolved detail. Photo
retention/derivative permission is required only if the JPEG itself is copied,
embedded, or pixel-derived; a CAD-derived CC BY 4.0 vector can use the photo as
non-retained visual QA while preserving Ksoloti attribution and an adaptation
notice. The unlit photograph still does not prove the populated unit's LED
colors or OLED appearance.

The oblique/context photograph is useful for appearance but is not the
geometry authority. Task 029 revalidated the qualified CAD and editable-source
hashes, visually compared the derived rendering with the supplied reference,
and retained only the photograph hash and limitations. The JPEG was not copied,
embedded, or traced.

## Read-only Machine Viewer first slice

The first Viewer is an inspection surface, not an authoring shortcut. It
consumes a client-neutral `machine.inspect` result through the same operation
boundary used by CLI and future AI clients; it must not read raw catalog,
record, source checkout, or legacy patch files directly.

Its four required sections are:

1. **Identity and summary**: exact machine/source-review identity, revision,
   provenance, import state, and honest proof badge.
2. **Machine block diagram**: presentation blocks and edges, each traceable to
   source-review evidence and, for a completed machine, exact graph nodes.
3. **Gills panel**: the authenticated shared SVG with semantic map; selecting a
   block, parameter, action, or display highlights all mapped controls, and
   selecting a physical control reveals its mode-dependent mappings.
4. **Dependencies and support evidence**: required dependency, classification,
   exact matching record when present, accepted/selectable state, evidence
   level, reason, and first proof gap. Unsupported remains visibly fail closed.

An inspection-only source-review fixture must be labelled as such on every
entry path. It cannot show build, deploy, play, or “supported” affordances.

### Viewer/Editor versus Machine Builder

- The **Viewer** presents completed machines and inspection-only source reviews.
- A later **Editor** may change machine-owned summary/presentation metadata via
  shared operations. It still presents an already completed instrument and
  must not rewrite its DSP graph or device mappings implicitly.
- A separate later **Machine Builder** assembles and maps objects through shared
  catalog, graph, project, and instrument operations. It owns graph editing,
  mapping, validation, and promotion workflow. It is not part of the Viewer
  first slice.

This boundary prevents a product-detail screen from becoming a second,
UI-specific graph model.

## Recommended import order

**Palimpsest should be the first inspection-only Viewer candidate.** It has one
local DSP header, fixed event/voice pools, no dynamic SDRAM allocation, and a
smaller direct resource closure (Braids sine table plus stmlib) than Tide Pit.
That makes its source review and transparent decomposition more bounded. It is
not yet an accepted machine: exact graph semantics, a modern instrument
contract, dependency records, host vectors, ARM evidence, and device evidence
are absent.

Tide Pit should follow after its exact Clouds/Braids resources, private
waveguide/string/body/grain closure, declared 251,408-byte SDRAM allocation,
and correct Clouds diffusion-reverb semantics are represented and validated.
The unrelated unsupported Rings reverb must remain unsupported.

The bounded sequence and current state are:

1. **Complete:** re-read authority, allocate Task 029 IDs, and pin exact parent
   record set `schuss-record-set-000021@1` without consuming the desktop catalog
   task's outputs.
2. **Complete:** authenticate portable Gills source records and add deterministic
   `machine-source-review-v0` schema/validation for Palimpsest and Tide Pit.
3. **Complete:** qualify the user's photo against authenticated panel CAD and
   editable source, then create/verify the shared SVG and `panel-layout-v0` map.
4. **Complete:** define `machine-v0`, exact-reference closure validation, and
   derived `machine.inspect` independently of any UI client.
5. **Next machine prerequisite:** decompose Palimpsest into an authoritative transparent graph, explicitly
   deciding which units remain machine-private and completing all instrument
   parameter/action/state/display mappings;
6. **Separate catalog prerequisite:** add exact component contracts/bindings only where implementation evidence
   requires them; keep public catalog promotion a separate decision and do not
   expand the 20-object palette for import convenience;
7. **Later acceptance gate:** accept Palimpsest as `machine-v0` only after its graph and instrument closure
   pass the contract; otherwise retain it as inspection-only;
8. **Viewer complete; machine closure later:** the read-only Viewer consumes
   only `machine.inspect`; repeat the graph/instrument process for Tide Pit in a
   separate bounded tranche.
9. **Separately authorized evidence:** schedule compiler lowering, resource measurement, connected-device, and
   audible work as separately authorized tasks with separate evidence.

## Task 029 implementation validation

The implementation freeze uses read-only/local checks only. The retained
focused commands are:

- `python3 -m unittest tools.contracts.tests.test_task029_gills_machines`:
  13 tests passed;
- `npm test --prefix apps/schuss_machine_viewer`: five tests passed;
- `python3 tools/contracts/generate_task029_records.py --check` and
  `python3 tools/contracts/generate_task029_viewer_fixtures.py --check`:
  deterministic records, record set, operation requests, and Viewer fixtures
  are fresh;
- `python3 tools/contracts/validate_task029.py`: `schuss-record-set-000022@1`
  is valid with two source reviews, two inspection-only presentations, one
  42-region panel map, zero completed machines, zero palette mutations, and
  evidence level 1 passed / levels 2-8 not run;
- `python3 tools/contracts/validate_task029_sources.py` with explicit source,
  panel, and photo paths: eleven Gills source blobs, three panel source blobs,
  and the non-retained photo hash matched their pinned identities;
- `python3 tools/contracts/run_task029_fresh_process.py`: both exact
  `machine.inspect` requests matched the retained canonical fixtures in four
  fresh CLI processes across two CWDs;
- rendered local Chrome checks showed both Viewer fixtures with the four
  required sections and no unsafe affordances. The prescribed
  `agent-browser` helper was unavailable locally, so this is a Chrome-headless
  fallback rather than evidence from that helper.

The earlier planning freeze also established:

- `shasum -a 256` over the eleven Tide Pit and Palimpsest files listed in the
  source table matched all eleven documented digests;
- `xmllint --noout` passed for both `.axp` and both `.axo` files;
- a focused documentation check passed for unique headings, relative links,
  trailing whitespace, portable paths, and the exact source-hash table;
- `python3 tools/contracts/validate_device_instrument_contracts.py` passed as
  `valid-with-deferred-graph`, with structural schema passed and backend,
  artifact, ARM, device, real-time/resource, and audible levels not run;
- `python3 tools/contracts/validate_task028.py` passed, including 11 tests and
  its retained fresh-root reproduction: the safe selectable total remains 20,
  levels 1-3 passed, and levels 4-8 were not run;
- `python3 tools/contracts/validate_backbone_governance.py` reported one
  inherited `TASK_ARCHIVE_POLICY_VIOLATION`: the pre-existing
  `docs/tasks/ui-desktop-initialization.md` is unexpected. The machine contract
  is intentionally outside `docs/tasks/` and adds no second diagnostic. This
  task did not modify, index, or otherwise depend on that concurrent desktop
  file;
- a temporary exact-commit fetch matched the retained v0.6 README, license,
  main-PCB, and panel-PCB hashes; KiCad 10.0.5 and read-only source parsing
  recovered the 158 x 100 mm panel, 31.2 x 17.2 mm OLED opening, and the
  documented semantic anchors;
- two complete-panel `kicad-cli pcb export svg` runs differed only in the
  generated title timestamp. Replacing that timestamp with one normalized
  value made the bytes identical at SHA-256
  `508c8a6a871bdeed7e73c378d3708d93bf6002b9f986e5ffbf1ed3b54ecd630b`;
- a heuristic photo-boundary check supported the expected 1.58 panel aspect
  ratio while retaining perspective as a non-metric limitation.

The `machine-v0` schema and closure validator are implemented, but the exact
reference source closures do not yet justify a completed `machine-v0` record.
That zero count is a successful fail-closed result, not missing UI data. No
hardware-dependent check is appropriate for this layer. The full repository
aggregate remains not run because it contains expressly prohibited build
paths.

During adjacent-check classification, `validate_task018.py` was invoked once
before its internal behavior was confirmed. It ran the historical Task 018
two-root ARM reproduction in disposable temporary directories, retained no
artifacts, performed no hardware/device action, and then failed because the
current local source-evidence verification count differs from its retained
golden (0 versus 12). That invocation was outside Task 029's no-build boundary;
no further build-bearing check was run and Task 029 claims no build evidence.

## Current proof limits

This implementation proves deterministic schemas, records, exact pinned source
identity, source-level control/audio organization, a client-neutral inspection
operation, panel/presentation consistency, CLI determinism, and read-only
Viewer rendering. It does not prove:

- that either instrument has a complete Schuss graph or `instrument-v0`;
- exact equivalence between any private algorithm and a current palette object;
- compiler lowering, ARM compile/link, generated-patch equivalence, or firmware
  compatibility;
- peak RAM/stack/CPU, scheduling, resource safety, or real-time behavior;
- connected Gills control/OLED/LED behavior;
- audible output or musical equivalence;
- serial/rear-marking or electrical identity of the photographed unit beyond
  its strong visual match to the pinned white v0.6 panel;
- populated LED colors or lit OLED appearance in the photographed unit;
- permission to retain or derive pixels from the photo itself. The pinned CAD
  design's CC BY 4.0 license and attribution conditions are separately
  evidenced.

No runtime bridge, catalog promotion, DSP change, Task 029 compiler lowering,
device, hardware, staging, commit, or push action was performed. The one
accidental adjacent Task 018 reproduction is disclosed above and creates no
Task 029 evidence. The only frontend is the isolated read-only Machine Viewer;
it neither integrates with nor depends on the separately owned desktop
foundation.
