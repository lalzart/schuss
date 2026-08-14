# Device and instrument contract tools

Validate the Task 005 production schemas, canonical content hashes, exact
device reference, deferred graph boundary, and mappings:

```bash
python3 tools/contracts/validate_device_instrument_contracts.py
python3 -m unittest discover -s tools/contracts/tests
```

The validator is read only and emits a deterministic one-line JSON summary. It
does not access hardware, invoke Java, generate a legacy patch, compile, or
write caches. The test fixture matrix under `tests/fixtures/` covers the
cross-layer prohibitions and fail-closed diagnostics.
