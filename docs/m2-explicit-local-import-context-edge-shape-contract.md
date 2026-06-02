# M2 Explicit Local-Import Context-Edge Shape Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the narrowest boundary for a later context-edge shape dry-run over one explicit private export.
This slice does not reopen or decode an export, inspect real context edges, validate edge
references, import a DB, build an index, build a graph, or complete any original M2 criterion.

## Future Edge Profile

The later dry-run may accept one explicit workspace-private UTF-8 JSON export with:

```text
schema_version: "m2-local-private-export.v1"
```

After the approved envelope and record-shape checks pass, the later dry-run may inspect every
object in the top-level `context_edges` array. Inspection is limited to exact key presence and
top-level value types:

```text
from_record_id: string
to_record_id: string
relation: string
```

The later dry-run may check that `relation` uses the approved relation vocabulary:

```text
previous_visible
nearby_branch
player_option
```

It must not emit, log, hash, normalize, or compare edge id values. It must not validate that edge
ids refer to records, reject self-edges, deduplicate edges, traverse records, or construct a graph.
Those checks remain deferred to later separately approved contracts.

## Future Redacted Summary

A later context-edge shape dry-run may report only aggregate booleans, counts, and blocker
categories:

```text
input_exists
input_kind
envelope_compatible
records_shape_reviewed
context_edges_array_present
context_edges_count
context_edges_inspected_count
compatible_context_edge_count
incompatible_context_edge_count
all_context_edge_shapes_compatible
context_edge_shape_status
blocker_categories
```

Optional redacted output remains private under:

```text
workspace/local-private/extraction-indexing/import/context-edge-shape/
```

## Safety Boundary

This contract does not permit:

- reopening or decoding an export in this contract slice;
- context-edge inspection in this contract slice;
- edge id emission, logging, normalization, hashing, or reference validation;
- record traversal, tag traversal, metadata traversal, or source-text emission;
- self-edge checks, duplicate-edge checks, context-graph construction, or retrieval-bucket mapping;
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
docs/m2-explicit-local-import-context-edge-shape-contract.md
tests/fixtures/m2_explicit_local_import_context_edge_shape_scope.synthetic.json
scripts/check_m2_explicit_local_import_context_edge_shape_contract.py
```

Validate the static contract with:

```powershell
python scripts/check_m2_explicit_local_import_context_edge_shape_contract.py --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_context_edge_shape_dry_run
```
