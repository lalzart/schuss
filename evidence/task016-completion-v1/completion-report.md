# Task 016 completion report

Task 016 is complete for the exact accepted
`schuss-graph-000002@1` closure under the user-selected legacy-equivalent
direct semantics. The implementation does not generalize beyond this graph.

## Delivered boundary

- successor record set `schuss-record-set-000010@1`, content hash
  `sha256:452a15b56980ba7f2aa05672635c454b4eb1d1708edb5540bf747506849aa5a7`;
- seven authenticated `direct-operation-spec-v0` records;
- seven candidate and seven promoted `native-cpp` bindings, one direct backend,
  seven exact eligibilities, and direct build request
  `schuss-build-request-000002@3`;
- normalized-DSP module v1 with eight nodes, nine authoritative connections,
  nine scheduled operations, explicit object state and three post-call latches;
- deterministic direct C++ using the authenticated Ksoloti runtime math and
  patch ABI without Java, `.axp`, legacy-object calls, hidden adapters, or
  ambient discovery;
- exact Task 014 handler `schuss-build-handler-000002@1`, registered alongside
  but never falling back to the transitional handler; and
- semantic goldens, focused tests, read-only validators, two-fresh-root build
  evidence, and retained content-addressed artifacts.

The two Sine nodes select the same promoted implementation binding and retain
independent phase state. Source mapping contains 86 origins covering every
scheduled operation, node, public contract facet/state declaration,
connection, binding, and public parameter mapping.

## Determinism and local build evidence

Two fresh local roots produced byte-identical portable operation results and
all artifact bytes. Principal artifacts are:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| normalized DSP | 10,494 | `746f4a7eaf81d9fdea5dcb6f95ecc19831a571ed6d7820bbb13a7ebc06f42d96` |
| direct C++ | 8,769 | `a29078fef3bb46ad34c9a0175dad2312d765490bbd92e2d0fdc8e5b4c77958af` |
| source map | 25,127 | `acf81cdd6564988d04dddbc23e6ba4c67475584b96c31b587ec2eef84db57f77` |
| ARM object | 8,216 | `0d5d63ab75f6e1fda79b9dcc89ee977f22dfe9d96f96824d74e40d99ba3a75bf` |
| linked ELF | 68,644 | `60bac66986b21e083fb8372ce229157c8d6a0867aff4efe3c00fa0a0396902cc` |
| link map | 143,944 | `b083d7489b36b87daf8daf159a5e4259afcd46bdf7e434298aa58eebfcc6a8cb` |
| command vector | 1,663 | `c552d74b6c89a3abc88c8a3ca1470e817f21a2eed9fb6165bb6461cf9423e4c4` |

The linked output was inspected as little-endian ARM. The link reused the
authenticated installed runtime boundary and made no change to the Ksoloti
source checkout, installed application, or firmware.

## Evidence boundary

Evidence levels 1-5 passed locally and remain separate: schema/structure,
component/graph resolution, direct lowering, generated source, and ARM
compile/link. Levels 6-8 are explicitly `not-run`. There was no connected
device execution, real-time measurement, or audible/listening validation.
No upload, flash, SD-card write, firmware mutation, UI work, stage, commit, or
push occurred.

Retained machine evidence is in `validation-summary.json`,
`portable-operation-result.json`, `semantic-goldens.json`, and
`artifacts/sha256/`. The validator also re-runs the accepted Task 015 gate; its
generated C++ remains
`a14f0733cf7e724e347e2edbafc8337bb26b18a6a16b6109aefd894cd540023d`.

## Reproduction

```bash
python3 tools/contracts/generate_task016_records.py --check
python3 -m unittest tools.contracts.tests.test_task016_direct_frontend
python3 tools/contracts/validate_task016_contract.py
python3 tools/contracts/validate_task016.py
```

`validate_task016.py` is read only. It authenticates the pinned source/tool
closure, re-plans and lowers the exact graph, performs two fresh local ARM
builds, checks retained bytes, and re-validates Task 015.

The affected Task 013-016 plus governance selection ran 60 tests successfully,
and the dedicated Task 016 module ran nine tests successfully. The ordinary
repository-wide discovery gate ran 246 tests and retained six inherited
baseline failures outside Task 016: five stale expected-hash/golden assertions
for legacy validation output (`test_task008_control_plane`,
`test_task009_prerequisite`, `test_task010_cli`, and `test_task011a_catalog`)
and one absent ignored Task 009 content-addressed artifact-store assertion
(`test_task009_prerequisite_repair`). No Task 016 test failed. Those baseline
repairs are not silently folded into this task, so repository-wide green status
remains an explicit proof gap even though the Task 016 boundary validates.
