# Task 024 current-Ksoloti curation decision

Status: accepted implementation authority for the Task 024 revision.

## Observed Ksoloti model

The current pinned Ksoloti application defines four enabled library roots:
`axoloti-factory`, `axoloti-contrib`, `ksoloti-objects`, and
`ksoloti-contrib`. The roots are source and provenance scopes. The application
builds its visible object tree by recursively loading each enabled library's
`objects/` directory, using the configured library ID at the root and folder
names below it. Normal `.axo` definitions and `.axs` subpatches are distinct
loaded forms. Folder placement and library load order are discoverability
inputs, not reviewed musical semantics.

The pinned deterministic Ksoloti catalog supplies the stronger import identity
model for normal definitions: `library:canonical/path/id` is a base reference,
and exact UUID or hash identities are variants beneath it. Each variant keeps
its source bytes, interface facts, declared includes, and declared dependency
names. Includes and dependencies are implementation-closure facts, not catalog
families. Source presence and parsing establish neither behavior nor target
support.

At the commits in `catalog/sources.lock.json`, the two first-party libraries
contain 668 `.axo` files, 835 normal definitions, 666 canonical base
references, and 19 `.axs` compounds. The frozen legacy inventory is not an
exact census of this current source population: its generic `dist` and `out`
directory exclusions omit legitimate object paths. The frozen report therefore
remains valid for its exact 3,602 observations, but it is not a safe product
backlog or current-library completeness authority.

## Chosen Schuss model

1. `axoloti-factory` and `ksoloti-objects` are the primary current first-party
   candidate corpus. `axoloti-contrib` and `ksoloti-contrib` remain pinned,
   independently reviewable provenance cohorts; they do not become primary
   taxonomy roots.
2. Library ID, source path, import form, exact variant identity, declared
   include/dependency closure, and optional cohort membership remain separate
   facets.
3. A current Ksoloti base reference is the starting cohort for implementation
   review. It is not automatically a Schuss family. Object-level review may
   split or combine cohorts when exact semantic evidence supports the result.
4. Schuss retains the thirteen function-first category slugs in
   `docs/TAXONOMY.md`. Ksoloti paths are candidate crosswalk evidence only.
5. The 3,602 frozen observations and their Task 024 dispositions remain
   immutable provenance, lineage, and gap evidence. Graph frequency remains
   prioritization evidence only. The former queued residue is not described or
   managed as the presumed product-review backlog.
6. Product review proceeds in independent cohorts: first-party functional
   objects, Ksoloti/Gills hardware and services, exact compiler-consumer
   selections, and later contrib/community candidates. One serialized
   integration authority owns taxonomy vocabulary, family grouping, stable
   IDs, schemas, record sets, shared catalog behavior, and status.

## Existing Task 024 additions

All twenty selected source observations still match exact current
`axoloti-factory@25d2615ed5233546d617017666a4ab1e60a8c506` bytes. No source
lineage is deleted. Their product-facing treatment changes as follows.

| Family | Treatment | Decision |
| --- | --- | --- |
| `schuss-family-000041` Constant String | retain | Keep the exact one-variant data/string utility family. |
| `schuss-family-000042` Analog Voltage Input | reconsider as a separate family | Review with existing Smoothed Analog GPIO Input and current Ksoloti raw/smoothed/bipolar variants. Preserve both lineages; do not silently merge identities. |
| `schuss-family-000043` Monophonic MIDI Note Input | revise | Rename to Selected MIDI Note Gate/Input: the exact object filters one configured note and exposes gate, velocity, and release velocity, not a note/pitch output. |
| `schuss-family-000044` Control Low-pass Filter | retain | Keep the exact first-order control-rate filter family. |
| `schuss-family-000045` Unipolar to Bipolar Converter | revise | Review the complete current control-rate and audio-rate variant cohort; rate is a form/contract distinction. |
| `schuss-family-000046` Constant Multiplier | revise | Review the complete current control-rate and audio-rate variant cohort. |
| `schuss-family-000047` Eight-input Multiplexer | revise | Review all current fractional, integer, audio-buffer, Boolean, and string variants; data type is a form/contract distinction. |
| `schuss-family-000048` Boolean Inverter | retain | Keep the exact one-variant Boolean NOT family. |
| `schuss-family-000049` Decay Envelope | retain | Keep the exact trigger-to-decay envelope family. |
| `schuss-family-000050` Control-rate Resonant Low-pass | revise | Rename to Two-pole Resonant Audio Low-pass; audio is processed at sample rate while coefficients update at control rate. |
| `schuss-family-000051` Triggered Uniform Random | retain | Keep the exact triggered control-random family without runtime-quality claims. |
| `schuss-family-000052` Integer Constant | retain | Keep the exact typed graph utility family. |
| `schuss-family-000053` Pitched Table Player | retain | Keep the exact table-reference player family without asset/runtime claims. |
| `schuss-family-000054` Clocked Value Latch | revise | Rename to Triggered Value Latch and review both current fractional and integer variants. |
| `schuss-family-000055` Two-input Boolean OR | retain | Keep the exact Boolean OR family. |
| `schuss-family-000056` All-pass Reverb Section | retain | Keep as an inspectable diffusion/reverb-building primitive, not a complete-reverb or audible claim. |
| `schuss-family-000057` Two-input Audio Mixer | reconsider as a separate family | Review with the existing Four-input Mixer; decide centrally whether arity is a family or form/contract distinction. Preserve both lineages. |
| `schuss-family-000058` Saturating Gain | revise | Review the complete current control-rate and audio-rate variant cohort. |
| `schuss-family-000059` Interpolated Delay Reader | retain | Keep the exact named-delay tap while leaving dependency resolution unproved. |
| `schuss-family-000060` SDRAM Delay Writer | retain | Keep the exact named-delay owner/writer while leaving memory and execution support unproved. |

The two reconsidered identities remain reserved and visible in the review
record until serialized family integration resolves them. They are not
reassigned to unrelated subjects. The revised Task 024 catalog therefore may
retain all sixty reviewed family records while marking review disposition and
visibility explicitly; catalog membership is not default-drawer endorsement.

## Evidence boundary

This decision establishes source-library parity, deterministic import
identity, candidate-cohort structure, reviewed taxonomy routing, and lineage
only. It does not establish a component contract, implementation binding,
compiler eligibility, DSP equivalence, target compatibility, ARM build,
connected-device behavior, electrical safety, real-time/resource behavior, or
audible quality. Every stronger claim still requires its own exact record and
evidence level.

## Implementation consequence

Task 024 must add a deterministic current-Ksoloti first-party candidate corpus
and crosswalk while retaining the frozen coverage packet as historical lineage
evidence. Catalog additions must record their current base reference, complete
variant-cohort status, review treatment, and default-versus-advanced visibility.
Task 025 may continue to consume only its exact eight-contract graph packet;
this catalog reset does not expand compiler scope.
