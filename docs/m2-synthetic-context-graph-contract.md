# M2 Synthetic Context-Graph Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the metadata-only shape of a future synthetic context graph. It does not construct a graph, import
a real database, read private input, or complete any original M2 criterion.

## Synthetic Context-Graph Envelope

Committed graph fixtures use:

```text
schema_version: "m2-synthetic-context-graph.v1"
source_import_schema_version: "m2-synthetic-import-db.v1"
source_line_index_schema_version: "m2-synthetic-line-index.v1"
source_kind: "synthetic_fixture"
default_spoiler_budget: "none"
```

Nodes are metadata-only entries sorted by `line_id`. Each node contains stable synthetic ids and
placeholders already approved by the line-index contract:

- `line_id`;
- `record_id`;
- `conversation_id`;
- `speaker_id`;
- `context_placeholder`;
- sorted synthetic `context_tags`.

Edges are sorted deterministically and contain:

- `from_line_id`;
- `to_line_id`;
- `relation`;
- `retrieval_bucket`.

The relation vocabulary is intentionally small and matches existing synthetic event retrieval:

| Relation | Retrieval bucket |
| --- | --- |
| `previous_visible` | `visible_history` |
| `nearby_branch` | `nearby_tree` |
| `player_option` | `player_options` |

Default spoiler budget remains `none`. Arbitrary future-branch traversal is forbidden.

## Safety Boundary

The graph contract does not permit:

- source text, extracted content, or arbitrary free text in graph fixtures;
- real DB import or private-input reads;
- graph construction from local exports;
- arbitrary future branches or hidden consequences;
- automatic Steam, game-install, or drive scanning;
- BepInEx or game-log reads;
- filenames, paths, hashes, payloads, logs, or runtime evidence;
- screenshots, OCR, saves, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes.

## Fixture And Checker

The portable schema and invented metadata-only fixture are:

```text
docs/m2-synthetic-context-graph-contract.md
specs/m2-synthetic-context-graph.schema.json
tests/fixtures/m2_synthetic_context_graph.synthetic.json
scripts/check_m2_synthetic_context_graph_contract.py
```

Validate the contract with:

```powershell
python scripts/check_m2_synthetic_context_graph_contract.py --quiet
```

The fixture maps nodes to the committed synthetic line index and edges to invented import
relations. It is contract evidence only.

## Synthetic Builder Dry-Run

The approved fixture-only projection helper is:

```text
scripts/run_m2_synthetic_context_graph_builder_dry_run.py
```

It validates one explicit invented synthetic import JSON and one explicit metadata-only synthetic
line index. It projects only sorted synthetic nodes and invented relation edges. Optional generated
output remains ignored and private under
`workspace/local-private/extraction-indexing/import/context-graph/`.

The helper preserves spoiler budget `none`, keeps `graph_constructed=false`, and does not complete
the original M2 context-graph criterion. Validate the deterministic fixture projection with:

```powershell
python scripts/run_m2_synthetic_context_graph_builder_dry_run.py --check-fixture --quiet
```

The next allowed step is:

```text
m2_synthetic_context_graph_builder_review_gate
```

## Synthetic Builder Review Gate

The approved redacted fixture-only review helper is:

```text
scripts/review_m2_synthetic_context_graph_builder_dry_run.py
```

It reviews only generated synthetic context-graph dry-run output under the ignored private graph
root. Optional JSON or Markdown review output remains private under
`workspace/local-private/extraction-indexing/import/context-graph-review/`.

The helper emits only counts, safety booleans, blocker categories, and decision readiness. It does
not copy nodes, edges, ids, placeholders, source text, paths, or runtime evidence. A passing review
permits only a later static contract discussion. It does not approve local-export reads or adapter
implementation.

Validate the review gate without real or private input with:

```powershell
python scripts/review_m2_synthetic_context_graph_builder_dry_run.py --self-test --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_adapter_contract
```

## Explicit Local-Import Adapter Contract

The next contract-only boundary is documented in:

```text
docs/m2-explicit-local-import-adapter-contract.md
tests/fixtures/m2_explicit_local_import_adapter_scope.synthetic.json
scripts/check_m2_explicit_local_import_adapter_contract.py
```

It permits only a later metadata-summary dry-run for one explicit workspace-private export file.
It does not approve local-export reads, parsing, DB import, indexing, or graph construction.
