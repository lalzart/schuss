# Mutable/Ksoloti source package v1

This package retains one byte-exact 21-file Mutable Instruments dependency
closure from the accepted Task 033 source authority. It provides a physical
build closure only. `schuss-source-release-000005@1` remains authoritative for
upstream identity, revision, provenance, license-review state, and distribution
review. This package is not a source release, catalog implementation, object
collection, component, graph, provider, runtime, compatibility claim, or
distribution approval.

The only immutable closure files are below `upstream/`. `SOURCE_PACKAGE.json`
is generated from the accepted source-release reference plus the live physical
closure. It owns only packaged paths and byte hashes, the path-sensitive
closure manifest, retained notice placement, and closed component groups.
Package documentation, validation, CMake, and the independent smoke consumer
stay outside that boundary.

Validate the repository-owned package from the Schuss root:

```text
python3 tools/source_packages/validate_source_package.py \
  packages/dsp_sources/mutable_ksoloti_v1 \
  --expected-source-release-id schuss-source-release-000005 \
  --expected-source-release-revision 1 \
  --expected-source-release-content-hash \
  sha256:51750a00f07f98c783cfc1972580c9399ac64690eaf3d40ad6e1d736698c972c
```

An optional authoritative checkout comparison is runtime-only:

```text
python3 tools/source_packages/validate_source_package.py \
  packages/dsp_sources/mutable_ksoloti_v1 \
  --source-root <authenticated-ksoloti-root> \
  --expected-source-release-id schuss-source-release-000005 \
  --expected-source-release-revision 1 \
  --expected-source-release-content-hash \
  sha256:51750a00f07f98c783cfc1972580c9399ac64690eaf3d40ad6e1d736698c972c \
  --expected-closure-manifest-sha256 \
  0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f
```

Consumers may include `cmake/MutableKsolotiSource.cmake`, link the
`MutableKsolotiV1::Headers` interface target, and resolve exact component
groups with `mutable_ksoloti_v1_resolve_components`. The helper validates the
package before exposing paths. It does not compile a library or set random,
numeric, block-size, optimization, sanitizer, allocation, or lifecycle policy.

The `smoke/` project is an independent include/link consumer. It has no Tide
Pit source or include dependency and links only the three resource/unit
translation units resolved from the manifest.
