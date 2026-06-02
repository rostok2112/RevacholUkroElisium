# M2 Explicit Local-Import Schema Compatibility Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the narrowest boundary for a later compatibility dry-run over one explicit private export. This
slice does not reopen or decode a selected export, inspect private content, import a DB, build a
line index, build a context graph, or complete any original M2 criterion.

## Future Input Profile

A later compatibility dry-run may accept exactly one user-selected UTF-8 JSON object file under:

```text
workspace/local-private/extraction-indexing/input/
```

The private export profile uses:

```text
schema_version: "m2-local-private-export.v1"
```

The only future inspectable top-level envelope fields are:

```text
schema_version
source_kind
records
context_edges
metadata
```

The later dry-run may decode one JSON object, check the presence and top-level types of those
fields, and calculate aggregate `records` and `context_edges` counts. It must not traverse nested
record objects, graph edges, or metadata contents.

## Future Redacted Summary

A later compatibility dry-run may report only:

```text
input_exists
input_kind
json_object_decoded
profile_schema_version_matches
required_envelope_fields_present
required_envelope_types_match
records_count
context_edges_count
schema_status
blocker_categories
```

Optional private output remains under:

```text
workspace/local-private/extraction-indexing/import/schema-compatibility/
```

Tracked output must not contain private paths, filenames, nested values, source text, extracted
text, hashes, logs, payloads, screenshots, OCR output, save data, decompiled details, or runtime
evidence.

## Safety Boundary

This contract does not permit:

- reopening or decoding a selected export in this contract slice;
- nested traversal, nested-value emission, source-text emission, or metadata-content inspection;
- content, path-string, or filename hashing;
- real DB import, line-index construction, or context-graph construction;
- automatic discovery, Steam scanning, game-install scanning, or drive traversal;
- BepInEx or game-log reads;
- screenshots, OCR, saves, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes;
- committed extracted text, payloads, indexes, reports, or private paths.

## Fixture And Checker

The machine-readable scope fixture is:

```text
docs/m2-explicit-local-import-schema-compatibility-contract.md
tests/fixtures/m2_explicit_local_import_schema_compatibility_scope.synthetic.json
scripts/check_m2_explicit_local_import_schema_compatibility_contract.py
```

Validate the contract with:

```powershell
python scripts/check_m2_explicit_local_import_schema_compatibility_contract.py --quiet
```

## Envelope-Only Dry-Run

The bounded implementation is:

```text
scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py
```

It accepts one explicit private UTF-8 JSON file under the ignored input root, decodes one JSON
value, requires a top-level object, checks the exact envelope field set and top-level types, and
calculates only aggregate `records` and `context_edges` counts. It does not traverse or emit nested
record values, graph-edge values, or metadata contents.

Optional redacted JSON output remains private under:

```text
workspace/local-private/extraction-indexing/import/schema-compatibility/
```

The dry-run intentionally applies no decode-size cap. That keeps the envelope-only helper simple
but means a large explicitly selected JSON file may consume substantial memory during decoding.

Validate the synthetic temp-workspace smoke with:

```powershell
python scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py --self-test --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_schema_compatibility_dry_run_review_gate
```
