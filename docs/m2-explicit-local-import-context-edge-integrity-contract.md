# M2 Explicit Local-Import Context-Edge Integrity Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the narrowest boundary for a later context-edge integrity dry-run over one explicit private export.
This slice does not reopen or decode an export, inspect real edge ids, check real edges, import a
DB, build an index, build a graph, or complete any original M2 criterion.

## Future Integrity Profile

A later dry-run may run only after the approved envelope, record-shape, context-edge-shape,
context-edge-reference, and context-edge-reference review gates. It may accept one explicit
workspace-private UTF-8 JSON export with:

```text
schema_version: "m2-local-private-export.v1"
```

The later dry-run may perform aggregate-only integrity checks over already decoded and already
reference-compatible top-level `context_edges`:

```text
self-edge: from_record_id == to_record_id
duplicate edge: exact duplicate tuple of from_record_id, to_record_id, relation
```

The checks must not emit, log, normalize, hash, or persist record ids, edge ids, relation values, or
duplicate tuples. They must not map retrieval buckets, traverse record values, construct a graph,
construct an index, or import a DB. Retrieval-bucket mapping remains deferred to a later separately
approved context-graph or relation-mapping contract.

## Future Redacted Summary

A later context-edge integrity dry-run may report only aggregate booleans, counts, and blocker
categories:

```text
input_exists
input_kind
envelope_compatible
records_shape_reviewed
context_edges_shape_reviewed
context_edge_references_reviewed
context_edges_count
self_edge_count
duplicate_edge_count
all_context_edges_integrity_compatible
context_edge_integrity_status
blocker_categories
```

Optional redacted output remains private under:

```text
workspace/local-private/extraction-indexing/import/context-edge-integrity/
```

## Safety Boundary

This contract does not permit:

- reopening or decoding an export in this contract slice;
- context-edge integrity validation in this contract slice;
- edge id, record id, relation value, or duplicate tuple emission;
- id normalization, id hashing, relation normalization, or committed id output;
- retrieval-bucket mapping, graph construction, line-index construction, or DB import;
- record value traversal, tag traversal, metadata traversal, or source-text emission;
- automatic discovery, Steam scanning, game-install scanning, or drive traversal;
- BepInEx or game-log reads;
- screenshots, OCR, saves, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes;
- committed payloads, indexes, reports, private paths, or extracted text.

## Fixture And Checker

The machine-readable scope fixture is:

```text
docs/m2-explicit-local-import-context-edge-integrity-contract.md
tests/fixtures/m2_explicit_local_import_context_edge_integrity_scope.synthetic.json
scripts/check_m2_explicit_local_import_context_edge_integrity_contract.py
```

Validate the static contract with:

```powershell
python scripts/check_m2_explicit_local_import_context_edge_integrity_contract.py --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_context_edge_integrity_dry_run
```

## Context-Edge Integrity Dry-Run

The aggregate-only dry-run helper is:

```text
scripts/run_m2_explicit_local_import_context_edge_integrity_dry_run.py
```

It reopens only one explicit workspace-private JSON export under
`workspace/local-private/extraction-indexing/input/`, verifies the approved envelope,
record-shape, context-edge-shape, and context-edge-reference preconditions, and reports only
aggregate self-edge and duplicate-edge counts. Optional redacted JSON output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-integrity/`.

The dry-run does not emit ids, relation values, duplicate tuples, source text, paths, filenames,
hashes, logs, payloads, or runtime evidence. It does not normalize ids, hash ids, map retrieval
buckets, import a DB, construct a line index, construct a context graph, or complete any original
M2 criterion. It intentionally applies no decode-size cap, matching the earlier explicit private
JSON dry-runs.

Validate the dry-run smoke with:

```powershell
python scripts/run_m2_explicit_local_import_context_edge_integrity_dry_run.py --self-test --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_context_edge_integrity_dry_run_review_gate
```
