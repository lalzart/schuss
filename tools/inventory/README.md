# Legacy inventory tools

The raw inventory implementation was migrated unchanged in behavior from the
Ksoloti working tree. It scans explicit source roots and writes only portable
source IDs and relative paths.

## Validate the retained baselines

```bash
python3 -m unittest discover -s tools/inventory/tests
python3 tools/inventory/validate_raw_inventory.py \
  catalog/snapshots/legacy-catalog-v0
python3 tools/inventory/validate_resolved_inventory.py \
  catalog/snapshots/legacy-resolved-catalog-v0
python3 tools/inventory/validate_phase3_review_packet.py \
  catalog/reviews/phase-3-inventory-review-v0
```

## Regenerate the raw inventory into a scratch directory

Resolve paths from ignored `catalog/sources.local.yml`, then pass them
explicitly. The current exporter deliberately does not read or mutate Ksoloti
preferences.

```bash
python3 tools/inventory/export_raw_inventory.py \
  --output /tmp/schuss-legacy-catalog-v0 \
  --source patcher=/absolute/path/to/ksoloti \
  --source axoloti-factory=/absolute/path/to/axoloti-factory \
  --source ksoloti-objects=/absolute/path/to/ksoloti-objects \
  --source ksoloti-contrib=/absolute/path/to/ksoloti-contrib \
  --source axoloti-contrib=/absolute/path/to/axoloti-contrib
```

Do not export directly over a retained snapshot until a task explicitly
authorizes replacement and byte-identity has been checked.

## Regenerate the resolved inventory into a scratch directory

The resolved harness verifies the live checkouts against
`catalog/sources.lock.json`, archives the pinned commits, builds the legacy Java
runtime in isolation, and compiles the bridge. It runs the behavioral fixture
twice and the production export twice in fresh JVMs, byte-compares each pair,
rejects absolute-path leaks, validates every record and cross-record reference,
and confirms that the upstream Git states did not change. The output directory
must not already contain files.

```bash
python3 tools/inventory/export_resolved_inventory.py \
  --output /tmp/schuss-legacy-resolved-catalog-v0 \
  --source axoloti-factory=/absolute/path/to/axoloti-factory \
  --source axoloti-contrib=/absolute/path/to/axoloti-contrib \
  --source ksoloti-objects=/absolute/path/to/ksoloti-objects \
  --source ksoloti-contrib=/absolute/path/to/ksoloti-contrib \
  --source patcher=/absolute/path/to/ksoloti
```

The resolved records are host-side observations of the legacy Java model.
They do not provide ARM compile/link, connected-board, or audible evidence.

## Regenerate the Phase 3 review packet

The review generator reads but never writes the frozen resolved snapshot. It
validates that input, records the hash of every snapshot file, creates the
packet twice in fresh temporary directories, byte-compares both generations,
validates all report reconciliations and deterministic samples, and confirms
that the snapshot hashes remain unchanged before materializing the packet.

```bash
python3 tools/inventory/build_phase3_review_packet.py \
  --output /tmp/schuss-phase-3-inventory-review-v0
python3 tools/inventory/validate_phase3_review_packet.py \
  /tmp/schuss-phase-3-inventory-review-v0
```

The impact report is explicitly engineering judgment for review routing. A
`material` or `blocking` compilation-readiness label is not evidence that an
ARM compile was attempted or failed.
