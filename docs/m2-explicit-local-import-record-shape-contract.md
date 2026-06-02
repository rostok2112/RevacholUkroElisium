# M2 Explicit Local-Import Record-Shape Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the narrowest boundary for a later record-shape dry-run over one explicit private export. This
slice does not reopen or decode an export, inspect real records, traverse context edges, import a
DB, build an index, build a graph, or complete any original M2 criterion.

## Future Record Profile

The later dry-run may accept one explicit workspace-private UTF-8 JSON export with:

```text
schema_version: "m2-local-private-export.v1"
```

After the approved envelope check passes, the later dry-run may inspect every object in the
top-level `records` array. Inspection is limited to exact key presence and top-level value types:

```text
record_id: string
line_id: string
conversation_id: string
speaker_id: string
speaker_label: string
context_placeholder: string
source_text: string
context_tags: array
redacted_metadata: object
```

The later dry-run may confirm that `context_tags` is an array and `redacted_metadata` is an object.
It must not traverse either container or inspect, compare, normalize, hash, log, or emit any record
value.

## Future Redacted Summary

A later record-shape dry-run may report only aggregate booleans, counts, and blocker categories:

```text
input_exists
input_kind
envelope_compatible
records_array_present
records_count
records_inspected_count
compatible_record_count
incompatible_record_count
all_record_shapes_compatible
record_shape_status
blocker_categories
```

Optional redacted output remains private under:

```text
workspace/local-private/extraction-indexing/import/record-shape/
```

## Safety Boundary

This contract does not permit:

- reopening or decoding an export in this contract slice;
- record inspection, record-value emission, logging, comparison, normalization, or hashing;
- traversal of `context_tags`, `redacted_metadata`, `context_edges`, or metadata contents;
- source-text emission or committed extracted text;
- real DB import, line-index construction, or context-graph construction;
- automatic discovery, Steam scanning, game-install scanning, or drive traversal;
- BepInEx or game-log reads;
- screenshots, OCR, saves, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes;
- committed payloads, indexes, reports, or private paths.

## Fixture And Checker

The machine-readable scope fixture is:

```text
docs/m2-explicit-local-import-record-shape-contract.md
tests/fixtures/m2_explicit_local_import_record_shape_scope.synthetic.json
scripts/check_m2_explicit_local_import_record_shape_contract.py
```

Validate the static contract with:

```powershell
python scripts/check_m2_explicit_local_import_record_shape_contract.py --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_record_shape_dry_run
```

## Record-Shape Dry-Run

The bounded record-only helper is:

```text
scripts/run_m2_explicit_local_import_record_shape_dry_run.py
```

It reopens one explicitly selected workspace-private UTF-8 JSON file, requires the approved
top-level envelope, and inspects every item in `records` for exact top-level keys and immediate
value types only. It does not emit, log, hash, compare, or normalize record values. It does not
traverse `context_tags`, redacted metadata contents, context edges, or envelope metadata contents.

Optional redacted JSON output remains private under:

```text
workspace/local-private/extraction-indexing/import/record-shape/
```

The helper intentionally applies no decode-size cap. It decodes the selected JSON export and
checks all record objects in memory, so a large selected file may consume substantial memory.

Validate the synthetic temp-workspace smoke with:

```powershell
python scripts/run_m2_explicit_local_import_record_shape_dry_run.py --self-test --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_record_shape_dry_run_review_gate
```
