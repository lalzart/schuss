# Ksoloti compatibility bridge

This boundary contains the code that interacts directly with the legacy
Ksoloti Java object model, patch resolver, XML format, and generated-object
providers. New Schuss code must not depend directly on those classes.

The Phase 3 implementation is a synchronous, device-free exporter for ordered
catalog objects and compound graphs. Its behavioral source matrix lives under
`fixtures/resolved-inventory/`; the record and evidence contract is documented
in `docs/inventory/resolved-catalog-spec.md`.

The bridge may perform the named in-memory subpatch-interface projection needed
to observe runtime ports. It does not generate target artifacts, compile or
link ARM code, access a device, write preferences, or mutate the upstream
checkouts. The production harness builds and reads Git archives of the pinned
commits, runs two fresh JVMs, and requires byte-identical output.

Code outside this directory must consume versioned Schuss records rather than
legacy Java or Swing objects.

The Task 009 prerequisite adds
`ExplicitCompileEnvironmentSmoke` as a bounded no-patch proof that a later
bridge entrypoint can receive content-addressed source, registry, target,
firmware, locale, and encoding values explicitly. It does not load the Blend
graph, generate source, read preferences, present GUI, access a device, upload,
or flash. Its compiled class and output are authenticated by the prerequisite
environment capture; it is not an executable backend handler.

The separately authorized prerequisite repair adds
`ExplicitLegacyIsolationProbe`. It installs a fresh in-memory `Preferences`
singleton with one explicit pinned factory root, invokes the real
`generatedobjects.Mixer` provider through `SchussGeneratedCapture`, and checks
the exact mixed-rate Crossfader emission without serializing factory objects.
The repair harness runs it in isolated user, preference, temporary, and working
roots, checks those roots and the factory tree for writes, rejects additional
authority arguments, and audits its direct bytecode references. This remains a
no-Schuss-graph prerequisite probe: it does not load or lower Blend, emit
`.axp`/patch source, compile a patch, access a device, upload, or flash.

Task 009 adds `ExactSliceBridge`, a headless entry point for only the exact
Blend/mixed-Crossfader proof. It receives explicit `.axp`, output, pinned
factory, pinned patcher, and runtime roots; installs fresh in-memory
preferences; registers only the required inlet, outlet, and mixed-rate
Crossfader types; compares the factory definition with the real Mixer provider;
and emits one canonical JSON result plus generated C++. It cannot discover an
ambient registry or call USB, upload, flash, or GUI presentation paths.

The Python adapter in `tools/contracts/task009_backend.py` compiles and invokes
this bridge from authenticated retained inputs. The bridge remains a bounded
compatibility adapter, not the Schuss graph model or a general `.axp` compiler.

Task 011C adds `GillsSliceBridge` for only graph `schuss-graph-000002`. It
registers the exact Square LFO, Cyclic Counter, four-step Pitch Sequencer, Sine,
mixed Crossfader, multimode filter, stereo output, and public fractional inlet
definitions; the two Sine instances share one definition. Generated factory
objects pass through the same legacy post-processing step and are compared to
the pinned factory records. The sequencer is loaded only from the pinned
contrib file and exact definition index/UUID. No ambient library scan, GUI,
controller, device, upload, flash, or firmware action is reachable.

`tools/contracts/task011c_backend.py` emits the exact Task 011B plan, boundary
`.axp`, source map, and generated C++, then reuses the authenticated Task 009
ARM/runtime closure with a task-specific artifact stem. This is still an exact
slice adapter, not arbitrary graph, object, `.axp`, or backend support.
