# ADR 0017: Separate object collections from implementation providers

- Status: accepted
- Date: 2026-08-20
- Extends: ADRs 0014, 0015, and 0016 without changing graph identity or the accepted runtime ABI
- Task: 033, Phase 1

## Context

Ksoloti presents object libraries through filesystem roots and commonly speaks
about Factory, first-party, and contributed libraries. Schuss has already
moved the durable model away from that layout: users browse functional
families, provenance remains inspectable, graphs reference component
contracts, and a selected target/backend resolves implementations later.

The native desktop runtime makes the remaining ambiguity costly. Seven exact
host implementations now execute through `schuss_rt`, but their runtime
factory descriptors are backend-local details and the catalog does not yet
show those seven implementations individually. At the same time, the Mutable-
derived catalog cohort is important but largely has source/catalog evidence
only. Calling either group a factory library would merge provenance,
availability, graph semantics, and runtime construction into one unstable
concept.

JUCE adds a similar temptation. The exact pinned JUCE 8.0.15 `juce_dsp`
umbrella contains 39 public headers, but they are not 39 Schuss objects. The
surface includes implementation utilities, composition helpers, processing
candidates, an internal implementation header, and asset/background-service
behavior. The module also adds `juce_audio_formats`, carries AGPLv3/commercial
licensing, and is generally floating-point and JUCE-lifecycle oriented. The
accepted `schuss_rt` boundary is JUCE-independent fixed Q27.

## Decision

Schuss will model source releases, object collections, catalog
implementations, component contracts, implementation providers, and runtime
factory descriptors as separate owned layers.

A **source release** authenticates portable source evidence: source ID,
repository/archive identity, commit, byte hashes, declared licensing evidence,
and importer boundary. It does not create catalog membership or support.

An **object collection** is a curated, function-neutral set of exact catalog
implementation references. Collections may describe Schuss core, Ksoloti
first-party, contributed, Mutable-derived, project-owned, or other reviewed
cohorts. Collection names and source/library paths are browse and provenance
facets, never category paths, graph identity, or implementation priority.

A **catalog implementation** remains one exact realization placed under a
function-first family. A materially different algorithm or runtime
realization receives a distinct implementation identity even when it serves
the same family. Source ancestry does not make two implementations
interchangeable.

A graph node continues to reference exactly one target-independent
**component contract**. It contains no source release, collection, source
path, provider, runtime factory, JUCE class, target, backend, or display name.

An **implementation provider** is an executable delivery boundary for exact
implementation bindings on explicit target/backend pairs. Provider selection
occurs only after graph validation and target/backend selection. It resolves
by exact references and explicit priority; absence, stale identity, duplicate
factory identity, and equal priority fail closed. Providers are static and
repository-controlled for this task; no dynamic loading or public plug-in SDK
is introduced.

A **runtime factory descriptor** is derived provider metadata used only to
construct and process an already selected binding. It is not a catalog object,
graph node, source identity, or user-facing library. The existing seven
Task 032 descriptors will ultimately be generated from one reviewed provider
manifest while retaining the accepted package and runtime behavior.

A **machine-local collection profile** may describe which installed
collections are visible for discovery and which exact providers are locally
available. It is not part of canonical project or graph identity. Hiding a
collection cannot delete or rewrite nodes. Opening or building an exact
project with a missing provider reports the missing dependency and never
substitutes another implementation.

Availability is projected per exact implementation and target/backend. It
keeps catalogued, contracted, bound, eligible, compile-proven, device-tested,
real-time-tested, audible-tested, and unresolved evidence distinct. Schuss
will not show a source-level or family-union “compatible” result.

For the pinned JUCE DSP surface, Task 033 chooses three explicit lanes:

1. Simple selected semantics may become JUCE-independent Schuss native
   implementations under separately accepted contracts; the JUCE class is
   evidence and comparison material, not graph or runtime identity.
2. Richer floating-point or asset/service-dependent candidates may be studied
   by a later task as a statically linked JUCE host-only provider, behind a
   separate provider ABI and an explicit desktop-float target/backend if its
   numeric contract requires one.
3. Utilities, composition mechanisms, internal details, and unresolved
   candidates remain deferred and do not become palette objects.

Task 033 does not add or link `juce_dsp`, extend the JUCE source lock, mix Q27
and float implicitly, or put JUCE types into `schuss_rt`. Any later JUCE
provider must revisit dependency, licensing, distribution, allocation,
callback, channel, lifecycle, resource, and real-time evidence explicitly.

## Reference direction

```text
source release -> audit -> catalog implementation -> binding -> provider
                               ^                    -> derived factory descriptor
                               |
functional family -> component contract <- authoritative graph node

machine-local profile -> browse visibility and installed-provider availability
machine-local profile -X-> project identity, graph identity, or selection priority
```

## Consequences

Schuss can present multiple curated collections without reproducing Ksoloti
path/load-order semantics. Ksoloti, Schuss native, Mutable-derived, JUCE, user,
and community material can coexist under the same functional browser while
remaining inspectable as provenance and availability facets.

The catalog must gain exact companions for the seven already allocated host
implementations and a per-target availability projection. Shared CLI, GUI, and
AI operations must expose those facts before a Settings panel or redesigned
Object drawer consumes them. That semantic work was serialized behind Task
034; its exact accepted record-set successor is now the required parent for
Task 033 Phase 2.

The native registry gains a single reviewed source of identity instead of
three hand-maintained tables, but factory function wiring remains a narrow
generated/native concern. Existing Task 031/032 package, ABI, rendering, and
diagnostic evidence must remain exact.

This decision does not establish support for any of the 56 Mutable-derived
implementations, import any JUCE processor, redesign the UI, authorize
hardware work, or approve distribution. Catalog, compiler, build, device,
real-time, audible, and release evidence remain separate.
