# Semantic catalog tools

Validate the Phase 4A overlay against its schema and the frozen Phase 3 object,
graph, provenance, and overload evidence:

```bash
python3 tools/catalog/validate_semantic_catalog.py \
  catalog/overlays/phase-4a-semantic-catalog-v0
python3 -m unittest discover -s tools/catalog/tests
```

The validator is read only. Its one-line JSON summary is deterministic and
separately reports family/implementation counts, category coverage, provenance,
difficult cases, dense-facet examples, compounds, overloads, and unresolved
membership/classification cases. It does not infer target compatibility.
