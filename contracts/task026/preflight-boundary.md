# Task 026 activation boundary

Status: accepted decision; the recommended reverb-free route is authorized.

## Observed parent result

Task 025 completed exact record set `schuss-record-set-000017@1` as a
fail-closed semantic tranche. Five new native-operation subjects and the two
accepted Task 016 routing subjects are eligible for backend
`schuss-backend-000002@3`. The ordinary compiler plan selects those seven
nodes, then rejects `graph-node-000004`, the selected Rings-derived reverb.
The plan emits only a resolution-plan artifact; complete-graph evidence level
2 fails and levels 3 through 8 remain `not-run`.

The Task 025 result deliberately contains no reverb operation, native binding,
build handler, normalized module, generated C++, ARM object, or ELF. Its build
request also names exact historical graph `schuss-graph-000004@1` and omits an
instrument.

## Why Task 026 cannot activate

ADR 0014 and `docs/APPLICATION_SPINE_PLAN.md` require Task 026 to create and
persist a new project-owned graph, instrument, and build request, then build
that authored result to a deterministic ELF using the Task 025 executable
tranche. Building historical graph `schuss-graph-000004@1` would not prove the
authored closure. Reusing an exact-graph handler for a new graph identity would
also fail closed unless an independently specified semantic-profile seam
proves the authored topology, contracts, public mappings, and parameters.

The accepted Task 025 parent supplies neither an executable complete graph nor
that identity-independent frontend/handler seam. Task 026 therefore cannot
satisfy its required empty-workspace-to-ELF acceptance without first changing
a material product decision or adding a bounded executable prerequisite.

## Recommended safe route

Revise the first application acceptance profile to a new project-owned
seven-node graph that uses the five safe Task 025 operations plus the two
accepted Task 016 routing operations and deliberately omits reverb. A bounded
executable-profile prerequisite should then:

1. identify support by exact topology, contract references, public mappings,
   parameters, backend, and target rather than by one historical graph ID;
2. normalize and lower only that exact seven-node profile;
3. accept an exact included authored instrument and authored build request;
4. generate deterministic source maps, C++, ARM/link evidence, and a handler
   only for the accepted profile; and
5. leave the Task 024 packet, failed reverb claim, and Task 025 unsupported
   plan unchanged.

This route advances the authoring application without guessing a reverb memory
contract. It does not remove reverb from catalog/history or imply later reverb
support.

## Alternative route requiring separate authority

Keep reverb in the first end-to-end profile and authorize a separate resource
ownership task. That task must decide whether a corrected realization may
reserve 65,536 bytes, prove target budgets and lifetime/ownership, retain the
exact algorithmic math/state/schedule, and then establish fresh frontend,
ARM/link, device-resource, real-time, and audible evidence independently as
applicable. A compile alone cannot close the allocation contradiction.

## Authorized decision

The user delegated the overnight sequence and explicitly authorized the
recommended safe route without another routine approval pause. Task 026 will
therefore use a seven-node profile containing the five Task 025 supported
subjects plus the carried Task 016 crossfade and audio-output subjects. The
Rings-derived reverb stays catalogued and historically selected, but remains
deterministically unsupported and absent from this executable profile.

The prerequisite is child work package 026A. It must complete before the
authoring workflow in 026B may claim an executable result. This decision does
not revise Task 024's selection packet, Task 025's failed reverb evidence, or
the historical eight-node graph/request.

No build, ARM toolchain, project write, Git publication, or hardware action was
performed to create the original preflight observation. Later 026A/026B local
builds are governed by their own accepted contracts and remain limited to
evidence level 5.
