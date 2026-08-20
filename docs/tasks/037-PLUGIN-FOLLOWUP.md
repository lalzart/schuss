# Task 037 Sonic Research Lab follow-up packet

Status: future external-plugin work only. Task 037 does not edit the installed
Sonic Research Lab plugin.

## Smallest routing change

After the repository interfaces are reviewed and committed separately, a
future plugin revision may add one post-readiness route:

1. detect a repository-owned Instrument Lab by the exact workflow and validator
   paths below;
2. require the existing proposal and implementation-bundle readiness gate;
3. select `new-design` or `source-reimplementation` from the approved bundle,
   never from a model guess;
4. invoke the repository generator/validator as bounded mechanics; and
5. return to the normal evidence ladder for implementation judgment,
   experiments, corrections, and gaps.

Exact repository entry points:

- `docs/workflows/instrument-development.md`
- `research/prototype_support/instrument_lab/README.md`
- `tools/instrument_lab/new_prototype.py`
- `tools/instrument_lab/validate_prototype.py`
- `tools/instrument_lab/validate_repository.py`
- `tools/instrument_lab/reproduce.py`

## Build-skill boundary

A future build-oriented skill may execute the generated Core-only CMake/CTest
surface and, when the operator supplies authenticated JUCE 8.0.15 source, the
optional target build. It must not fetch by default, launch an application,
open audio or MIDI devices, configure a controller, promote evidence, or alter
the instrument proposal, source authority, experiment, comparator, controls,
or DSP topology.

Lower-cost routing is suitable only for deterministic generation, closed-schema
validation, freshness checks, and already-declared build commands. Musical DSP
implementation, source-equivalence corrections, topology interpretation, test
failure diagnosis, and any evidence promotion remain high-judgment work.

## Required plugin tests

- Refuse routing before implementation-bundle readiness.
- Preserve both lanes and require source authority only for the source lane.
- Reject absolute paths, mutable/latest references, stale hashes, and copied
  shared implementation.
- Treat `dsp-topology.json` as noncanonical and nonexecutable.
- Keep host build, launch, real-time, device, listening, and distribution
  evidence separate.
- Make no provider, runtime-factory, target/backend, catalog, project, or stable
  ID allocation.

No plugin version, Task 038 identity, model choice, installation, or external
state mutation is authorized by this packet.
