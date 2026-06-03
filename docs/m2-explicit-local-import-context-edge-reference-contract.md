# M2 Explicit Local-Import Context-Edge Reference Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the narrowest boundary for a later context-edge reference dry-run over one explicit private export.
This slice does not reopen or decode an export, inspect real edge ids, validate references, import
a DB, build an index, build a graph, or complete any original M2 criterion.

## Future Reference Profile

A later dry-run may run only after the approved envelope, record-shape, context-edge-shape, and
context-edge-shape review gates. It may accept one explicit workspace-private UTF-8 JSON export
with:

```text
schema_version: "m2-local-private-export.v1"
```

The later dry-run may compare each top-level `context_edges` reference against the set of top-level
`records[*].record_id` values already decoded from that same explicit export:

```text
context_edges[*].from_record_id -> records[*].record_id
context_edges[*].to_record_id -> records[*].record_id
```

The comparison is membership-only. It must not emit, log, normalize, hash, or compare edge id or
record id values outside the in-memory membership check. It must not reject self-edges, deduplicate
edges, traverse record values, construct retrieval buckets, or construct a graph. Those checks
remain deferred to later separately approved contracts.

## Future Redacted Summary

A later context-edge reference dry-run may report only aggregate booleans, counts, and blocker
categories:

```text
input_exists
input_kind
envelope_compatible
records_shape_reviewed
context_edges_shape_reviewed
record_id_set_built
context_edges_count
context_edges_references_checked_count
context_edges_with_resolved_from_count
context_edges_with_resolved_to_count
context_edges_with_unresolved_reference_count
all_context_edge_references_resolved
context_edge_reference_status
blocker_categories
```

Optional redacted output remains private under:

```text
workspace/local-private/extraction-indexing/import/context-edge-reference/
```

## Safety Boundary

This contract does not permit:

- reopening or decoding an export in this contract slice;
- context-edge reference validation in this contract slice;
- edge id or record id emission, logging, normalization, hashing, or committed output;
- self-edge checks, duplicate-edge checks, graph construction, or retrieval-bucket mapping;
- record value traversal, tag traversal, metadata traversal, or source-text emission;
- real DB import, line-index construction, or context-graph construction;
- automatic discovery, Steam scanning, game-install scanning, or drive traversal;
- BepInEx or game-log reads;
- screenshots, OCR, saves, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes;
- committed payloads, indexes, reports, private paths, or extracted text.

## Fixture And Checker

The machine-readable scope fixture is:

```text
docs/m2-explicit-local-import-context-edge-reference-contract.md
tests/fixtures/m2_explicit_local_import_context_edge_reference_scope.synthetic.json
scripts/check_m2_explicit_local_import_context_edge_reference_contract.py
```

Validate the static contract with:

```powershell
python scripts/check_m2_explicit_local_import_context_edge_reference_contract.py --quiet
```

## Context-Edge Reference Dry-Run

The bounded membership-only helper is:

```text
scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py
```

It reopens one explicitly selected workspace-private UTF-8 JSON export, requires the approved
top-level envelope, record-shape precondition, and context-edge-shape precondition, and compares
edge references against an in-memory set of top-level record ids. It emits only aggregate counts,
booleans, and blocker categories.

Optional redacted output remains private under:

```text
workspace/local-private/extraction-indexing/import/context-edge-reference/
```

The helper intentionally applies no decode-size cap, so a large explicitly selected JSON file may
consume substantial memory. It does not emit ids, normalize ids, hash ids, check self-edges,
deduplicate edges, map retrieval buckets, import a DB, construct an index, construct a graph, or
complete any original M2 criterion.

Validate the dry-run smoke with:

```powershell
python scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py --self-test --quiet
```

## Context-Edge Reference Dry-Run Review Gate

The redacted summary-only reviewer is:

```text
scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py
```

It reviews only ignored context-edge reference summary JSON under
`workspace/local-private/extraction-indexing/import/context-edge-reference/`. Optional redacted JSON
or Markdown review output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-reference-review/`.

The review never reopens the selected export, emits ids, normalizes ids, hashes ids, checks
self-edges, deduplicates edges, maps retrieval buckets, imports a DB, constructs an index,
constructs a graph, or completes any original M2 criterion. A passing review permits only a later
static context-edge integrity contract discussion.

Validate the review gate without real or private input with:

```powershell
python scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py --self-test --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_context_edge_integrity_contract
```
