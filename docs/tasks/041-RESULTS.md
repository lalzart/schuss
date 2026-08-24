# Task 041 results

Status: implementation and local Git closeout complete; Task 041 has stopped
with no active successor. The Schuss task/evidence commit is `a6eeaab` and the
Gills implementation commit is `9b5e4f9`. Neither repository was pushed or
published, and nothing was uploaded or sent to hardware.

## Bound repositories and activation audit

- Schuss remained on local `main` at published baseline
  `955084e581ebf21e979f039fb7bba088787b8f71`; the inherited Task 040 closeout
  work was preserved.
- Gills Instruments remained on local `main` at
  `33038b5de6315bce9bbe167062f2876823ff1adc`, even with `origin/main`; the
  larger unrelated dirty/untracked tranche was preserved.
- The read-only audit found one shared implementation declaration, exactly
  five direct instrument consumers, no transitive consumer, and no second
  reusable ownership boundary.
- The audited implementation header SHA-256 was and remains
  `79b125d08103b7383e18aefc66a40f5d3ea9a7df59420f8d855dccb45408278d`.
- The 64-file pre-change audit is retained in
  `projects/gills-engine-support/TASK041_BASELINE.json` at SHA-256
  `a32f0cec373eb94cf8b9f5f50bea6e199505a63ca277b9a59925541b81c8a844`.
  The validator binds that exact comparator hash.

## Dependency authority and exact bindings

The header remains whole and has one Gills-owned authoritative revision:

- identity: `gills-engine-support`;
- revision: `1`, with no `latest` alias or fallback;
- source: `projects/gills-engine-support/revisions/1/gills_engine_support.h`;
- canonical authority:
  `projects/gills-engine-support/revisions/1/dependency.json` at SHA-256
  `a5054040b32cba47c1ba75d13422784e7aba5986de9d51622abc3a1e476aba8a`;
- exact GPLv3 text: repository-root `license.txt` at SHA-256
  `ac9a21636e6fed3f264b52ba0eb2e96405f7a0bb9b7af080fbaf7c0cd65f2046`;
  and
- support notice SHA-256:
  `5472a9876fe92df01b689ad2fcf0df80bb5cf3790d89e6fcf27256404e2d6236`.

The authority binds only source integrity, the notice/license closure, exact
Ksoloti Core offline constraints, and its evidence ceiling. It allocates no
Schuss catalog, collection, implementation, provider, graph, binding, project,
instrument, machine, target, backend, or runtime-factory identity.

Each of the five projects contains one canonical
`gills-engine-support.binding.json`. Each binding selects the same authority
hash, source hash, and revision 1. A project-local 84-byte forwarding header
at SHA-256
`29496ee31e1dca138cc4845027426c670026ea23793c6449407cf97f5cca46c9`
selects the explicit source-tree revision. The instrument DSP headers include
only that local name, so generated release packages can replace the forwarder
with the exact authenticated implementation bytes without editing musical
source.

## Deterministic self-contained closure

The narrow Task 041 tool and the existing project release seam now:

1. validate the one authority, complete source set, exact five-consumer set,
   one binding per consumer, hashes, license material, include resolution, and
   pre-change comparator;
2. reject missing, changed, duplicate, ambiguous, stale, noncanonical, or
   incorrectly placed inputs before target compilation;
3. package every checked project file plus the exact dependency source,
   authority, notice, license text, and support documentation;
4. record sorted canonical paths, origins, modes, and SHA-256 values without
   timestamps or machine-local absolute paths; and
5. verify the complete file and directory inventory, then optionally compile
   and run the project host harness from the relocated package.

The generated package has no `projects/gills-engine-support/` sibling. Its
project-local `gills_engine_support.h` contains the exact authenticated
revision-1 source bytes; a second copy under
`dependency/gills-engine-support/revisions/1/` retains provenance beside the
authority and license material. These generated copies are package outputs,
not editable authorities.

## Preservation result

- All 60 pre-existing consumer files reproduce their activation hashes except
  for the five declared DSP-header include substitutions.
- Replacing each new local include with the old sibling include reproduces the
  exact pre-change DSP-header hash.
- The shared implementation source remains byte-identical after its mechanical
  move into `revisions/1/`.
- Checked `.kpatch`, Object SDK manifests, generated `.axo`/`.axp`, contracts,
  mirrors, render helpers, tests, controls, defaults, mappings, and startup
  state remain byte-identical.
- The only other changes inside the six project boundaries are the declared
  authority, bindings, forwarders, license closure, support documentation, and
  Task 041 validation/package artifacts.

The frozen complete Gills validation-input digest was
`f0cb0a721d1598959fb7f97725221fe3555406fa1c85ec3bc8adc2ff556cb5c6`
before the expensive gates and remained identical afterward.

## Focused and adjacent validation

- `scripts/gills-engine-support.py check-all`: passed for one authority,
  revision 1, five direct consumers, five bindings, and the frozen comparator.
- Task 041 focused tests: 9/9 passed. They cover the positive closure, a
  one-byte source mutation, stale revision, missing source, duplicate
  authority, notice/license mismatch, baseline mutation, ambiguous include,
  non-include consumer drift, successor-revision coexistence, deterministic
  packaging, sibling removal, and relocated verification.
- Complete Gills Python unit discovery: 23/23 passed.
- All five existing project-local portable contract/XML/object/render/host
  gates passed. The retained stress results were 30,000 blocks for Coupled
  Resonator and Scanned, and 20,000 blocks for Feedback PM, Pulsar FOF, and
  Wave Terrain.

## Frozen release evidence

Each `scripts/validate-project.sh --release` gate ran once after freeze. Every
gate produced and verified two identical 20-file closure inventories, passed
its existing deterministic renderer and host harness, and produced matching
source-tree/fresh-installed-process input, generated C++, and Cortex-M4 binary
identity from two fresh compiler processes.

| Consumer | Closure inventory SHA-256 | Generated C++ SHA-256 | ARM binary SHA-256 | CCMSRAM / SRAM1 |
| --- | --- | --- | --- | ---: |
| Coupled Resonator | `8d30cbb9b4d61bcddf80895114a41e0de312403be119a30b0d89ba8f30b3931a` | `845c7f114ac9657633f29d41865df3dc236977a7a8e04d918abb07e224bdd0d6` | `51f552388db572c7dadf333d7f557a302854e9dd27b23c5fb864f32af3fbb4c2` | 34,912 B / 13,092 B |
| Feedback PM | `9f55b5fb3d85ceebe50c1701490f683812fa9c8df3a270aedf7e01ba2942b669` | `aaf0fb7fd550e664ad2ee511fb00abbf57a202162a87d4a95c2c764eb4f89f64` | `28f6544fc62c16166d8b5ea2895b12df484ca27111a9353a9db4205480f2103b` | 2,136 B / 12,056 B |
| Pulsar FOF | `7086dd9ada8cc9f051471341e08f34e31007ada23e46708a4aeaab393bcf8e7f` | `ad2aee024998e56a7a61af4aa2eab1dee3bfdfa2098b0f606fd07f1781c73889` | `16492471b6c88d66c722154448fed01327d9055d7362342858c96b85558381d3` | 2,936 B / 16,100 B |
| Scanned | `2acbd5f17d2b3c2a334abc030ec0fe1397b1e3cb683a4082a75bfcf37891253e` | `c1fa41bbf9ef7c2b00620a6afc09898e8b4969062c684f2f6baa35f687bc9e90` | `b82ae176025c806192633062f6fedaa24d709bcf23257796901153453f0414f6` | 3,112 B / 12,672 B |
| Wave Terrain | `b7c1696b804852dbfd92f9d10f10c0c8032c28f9624dc5bd0fb186911d384fa4` | `c4e6a636ab54c976ab37d2c2213681195a24d345dacb2f93d4c58e32179dae75` | `a2cf6480ed9e7d86f28a26bd3da517a50b49c0483a517bfd352f1502cf8c3c7a` | 18,472 B / 15,900 B |

The single post-freeze relocated reproduction packaged each consumer twice,
compared its canonical manifests, removed any dependency on the original
sibling layout, and compiled/ran all five host harnesses from packaged bytes.
The resulting `RELEASE_CLOSURE.json` file SHA-256 values were:

- Coupled Resonator:
  `ee20d11a3f60d84714d98dd442e3e193ab33695780c2882de29c43b6b5f1e18b`;
- Feedback PM:
  `659377ccb19b100bca42a6e4fb8bcb77c92be94c842eca557878c6ba264b0b25`;
- Pulsar FOF:
  `dcfd23827a0eac32c9b84cee6d0b2ae8c8b2bccf44f142c010f8084bca7651a3`;
- Scanned:
  `b40f8bbca56e5a0f073978ed832deead6c60da26d92c685f8fb48974977abb5c`;
  and
- Wave Terrain:
  `aedfb4f8cf2b11ab97c2448af415f7202206c177c2620fae3e4ac7df91a9ae8f`.

The Schuss `current` profile passed after the final documentation and
review-ready governance update. No compatibility, configured-source, native,
reproduction, or release profile was applicable to the Schuss documentation-
only boundary.

## Evidence boundary

Task 041 establishes dependency ownership/integrity, preserved portable host
behavior, deterministic self-contained packaging, and offline Cortex-M4
compile/link identity. It did not connect to a board or audio/MIDI endpoint,
upload or flash firmware, mutate an SD card, measure callback deadlines, view a
physical OLED, assess analog output, perform listening, review a distributable
artifact, publish, or push. Staging and local commits occurred only during the
later explicitly authorized Git closeout.

The first Schuss `current` attempt used an intermediate review-ready routing
state and correctly failed because the retained Task 040 closeout requires no
active successor. Task 041's own stop condition provided the narrow correction:
final routing now has no active task, while this result remains recoverable.
No Task 040 validator or other shared Schuss executable was changed.

The later Git authorization supplied the required local commits, so governance
now records Task 041 in `recent_completed_milestones` and `HISTORY.md` while
keeping publication and all higher evidence gates open.
