# ADR 0012: M2 local extraction import scope

## Status

Accepted.

## Context

The unchanged canonical roadmap is `tasks/milestones.md`. Original
`M0 - Repo and contracts` and `M1 - Synthetic vertical slice` are complete. Original
`M2 - Local extraction import` is active.

The completed 5A-labelled series established local-only safety contracts, ignored private roots,
synthetic fixtures, metadata-only dry-runs, and redacted evidence helpers. It did not implement the
three original M2 completion criteria:

- import locally extracted DB;
- build line index;
- build context graph.

This ADR defines the next M2 boundary only. It does not implement an importer, parser, line index,
or context graph.

## Decision

The next M2 step is a synthetic import format contract. Before any importer reads a local export,
the project must define a synthetic fixture shape and checker for one explicit user-selected local
export.

Allowed future sources are limited to:

- committed invented synthetic fixtures;
- one explicit user-selected local export placed under
  `workspace/local-private/extraction-indexing/input/`;
- generated local/private import outputs under
  `workspace/local-private/extraction-indexing/import/`.

This contract does not permit reading real local input. A later separately approved implementation
may read only one explicit workspace-private export after a synthetic import format contract exists.
It must not infer, discover, or scan a game installation.

## Forbidden Behavior

This M2 scope gate does not approve:

- automatic Steam or game-install scanning;
- arbitrary drive scanning;
- real local-input reads;
- committed extracted text, indexes, payloads, or private paths;
- BepInEx or game-log reads;
- screenshots, OCR, save parsing, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes.

## Fixture And Checker

The canonical scope document is:

```text
docs/adr/0012-m2-local-extraction-import-scope.md
```

The machine-readable contract fixture is:

```text
tests/fixtures/m2_local_extraction_import_scope.synthetic.json
```

Validate it with:

```powershell
python scripts/check_m2_local_extraction_import_scope.py --quiet
```

The fixture records that original M2 remains active and incomplete. The only allowed next step is:

```text
m2_synthetic_import_format_contract
```

That next step is still synthetic/docs contract work. It is not local-content reading or real
extraction.

## Synthetic Import Format Contract

The next bounded contract is documented in:

```text
docs/m2-synthetic-import-format-contract.md
tests/fixtures/m2_synthetic_import_db.synthetic.json
specs/m2-synthetic-import-db.schema.json
scripts/m2_synthetic_import_validator.py
scripts/check_m2_synthetic_import_format.py
```

It defines invented fixture records and relation edges only. It does not implement import, line
indexing, context-graph construction, or local-content reads.

## Synthetic Line-Index Contract

The next metadata-only output contract is documented in:

```text
docs/m2-synthetic-line-index-contract.md
specs/m2-synthetic-line-index.schema.json
tests/fixtures/m2_synthetic_line_index.synthetic.json
scripts/check_m2_synthetic_line_index_contract.py
```

It defines a committed synthetic line-index fixture only. It does not build an index, include
source text, import a real DB, read private input, or build a context graph.

## Synthetic Line-Index Builder Dry-Run

The approved fixture-only projection helper is:

```text
scripts/run_m2_synthetic_line_index_builder_dry_run.py
```

It validates one explicit invented synthetic import JSON and produces metadata-only line-index
entries. Optional output remains ignored and private under
`workspace/local-private/extraction-indexing/import/line-index/`. It does not read a private local
export, include source text or graph edges, or complete the original M2 line-index criterion.

The next allowed step after this dry-run is:

```text
m2_synthetic_line_index_builder_review_gate
```

## Synthetic Line-Index Builder Review Gate

The approved redacted fixture-only review helper is:

```text
scripts/review_m2_synthetic_line_index_builder_dry_run.py
```

It reviews only generated metadata-only line-index dry-run output under the ignored private
workspace root. It does not read source text, real local exports, or runtime evidence. It does not
complete the original M2 line-index criterion or approve context-graph construction.

The next allowed step after the review gate is:

```text
m2_synthetic_context_graph_contract
```

## Synthetic Context-Graph Contract

The metadata-only context-graph contract is documented in:

```text
docs/m2-synthetic-context-graph-contract.md
specs/m2-synthetic-context-graph.schema.json
tests/fixtures/m2_synthetic_context_graph.synthetic.json
scripts/check_m2_synthetic_context_graph_contract.py
```

It maps invented line-index nodes and invented import relations only. It keeps spoiler budget at
`none`, forbids arbitrary future-branch traversal, and does not construct a graph or complete any
original M2 criterion.

The next allowed step is:

```text
m2_synthetic_context_graph_builder_dry_run
```

## Synthetic Context-Graph Builder Dry-Run

The approved fixture-only projection helper is:

```text
scripts/run_m2_synthetic_context_graph_builder_dry_run.py
```

It validates one explicit invented synthetic import JSON and one explicit metadata-only synthetic
line index, then projects the committed synthetic context-graph shape. Optional output remains
ignored and private under
`workspace/local-private/extraction-indexing/import/context-graph/`.

The helper preserves spoiler budget `none`, keeps `graph_constructed=false`, and does not complete
the original M2 context-graph criterion.

The next allowed step is:

```text
m2_synthetic_context_graph_builder_review_gate
```

## Synthetic Context-Graph Builder Review Gate

The approved redacted fixture-only review helper is:

```text
scripts/review_m2_synthetic_context_graph_builder_dry_run.py
```

It reviews only ignored synthetic context-graph dry-run output under
`workspace/local-private/extraction-indexing/import/context-graph/`. Optional redacted JSON or
Markdown review output remains private under
`workspace/local-private/extraction-indexing/import/context-graph-review/`.

A passing review means only that a later static explicit-local-import adapter contract may be
defined. It does not approve local-export reads, private-input reads, adapter implementation, or
completion of any original M2 criterion.

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

It limits a future adapter to one explicitly supplied workspace-private export file and a
metadata-summary-first dry-run. It does not read or parse a local export, import a DB, build an
index, construct a graph, or complete any original M2 criterion.

The next allowed step is:

```text
m2_explicit_local_import_adapter_dry_run
```

## Explicit Local-Import Adapter Dry-Run

The metadata-only one-file dry-run helper is:

```text
scripts/run_m2_explicit_local_import_adapter_dry_run.py
```

It reads filesystem metadata only for one explicit file under the ignored private input root.
Directories, parsing, schema compatibility inspection, discovery, real DB import, index
construction, graph construction, and every original M2 completion flag remain blocked.

Optional redacted JSON output remains private under
`workspace/local-private/extraction-indexing/import/adapter-dry-run/`.

The next allowed step is:

```text
m2_explicit_local_import_adapter_dry_run_review_gate
```

## Explicit Local-Import Adapter Dry-Run Review Gate

The redacted summary-only review helper is:

```text
scripts/review_m2_explicit_local_import_adapter_dry_run.py
```

It reviews only ignored dry-run summary JSON under
`workspace/local-private/extraction-indexing/import/adapter-dry-run/`. Optional redacted review
output remains private under
`workspace/local-private/extraction-indexing/import/adapter-dry-run-review/`.

The review never reopens the selected export. Schema compatibility inspection, parsing, real DB
import, index construction, graph construction, and every original M2 completion flag remain
blocked.

The next allowed step is:

```text
m2_explicit_local_import_schema_compatibility_contract
```

## Explicit Local-Import Schema Compatibility Contract

The static envelope-only boundary is documented in:

```text
docs/m2-explicit-local-import-schema-compatibility-contract.md
tests/fixtures/m2_explicit_local_import_schema_compatibility_scope.synthetic.json
scripts/check_m2_explicit_local_import_schema_compatibility_contract.py
```

It defines one future UTF-8 JSON object profile. A later dry-run may check top-level field presence
and types and calculate aggregate record and edge counts only. This contract does not reopen or
decode a selected export, traverse nested values, emit private content, import a DB, build an
index, construct a graph, or complete any original M2 criterion.

The next allowed step is:

```text
m2_explicit_local_import_schema_compatibility_dry_run
```

## Explicit Local-Import Schema Compatibility Dry-Run

The bounded envelope-only helper is:

```text
scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py
```

It decodes one explicitly selected workspace-private UTF-8 JSON file, checks only the exact
top-level envelope field set and top-level types, and reports aggregate record and edge counts.
It does not traverse or emit nested values, import a DB, construct an index, construct a graph, or
complete any original M2 criterion.

Optional redacted output remains private under
`workspace/local-private/extraction-indexing/import/schema-compatibility/`. The helper intentionally
applies no decode-size cap, so a large explicitly selected JSON file may consume substantial memory.

The next allowed step is:

```text
m2_explicit_local_import_schema_compatibility_dry_run_review_gate
```

## Explicit Local-Import Schema Compatibility Dry-Run Review Gate

The redacted summary-only reviewer is:

```text
scripts/review_m2_explicit_local_import_schema_compatibility_dry_run.py
```

It reviews only ignored compatibility-summary JSON under
`workspace/local-private/extraction-indexing/import/schema-compatibility/`. Optional redacted JSON
or Markdown output remains private under
`workspace/local-private/extraction-indexing/import/schema-compatibility-review/`.

The review never reopens the selected export or traverses nested values. A passing review permits
only a later static record-shape contract discussion; record-shape inspection, real DB import,
index construction, graph construction, and every original M2 completion flag remain blocked.

The next allowed step is:

```text
m2_explicit_local_import_record_shape_contract
```

## Explicit Local-Import Record-Shape Contract

The static record-only boundary is documented in:

```text
docs/m2-explicit-local-import-record-shape-contract.md
tests/fixtures/m2_explicit_local_import_record_shape_scope.synthetic.json
scripts/check_m2_explicit_local_import_record_shape_contract.py
```

It defines a later all-record top-level shape check using the established synthetic record
vocabulary. The contract does not reopen or decode an export, inspect record values, traverse
`context_tags`, traverse redacted metadata contents, traverse context edges, import a DB, construct
an index, construct a graph, or complete any original M2 criterion.

The next allowed step is:

```text
m2_explicit_local_import_record_shape_dry_run
```

## Explicit Local-Import Record-Shape Dry-Run

The bounded record-only helper is:

```text
scripts/run_m2_explicit_local_import_record_shape_dry_run.py
```

It reopens one explicitly selected workspace-private UTF-8 JSON export, requires the approved
top-level envelope, and checks every object in `records` for exact top-level keys and immediate
value types only. It does not emit, log, hash, compare, normalize, or traverse private record
values. It does not inspect context-edge contents or complete any original M2 criterion.

Optional redacted output remains private under
`workspace/local-private/extraction-indexing/import/record-shape/`. The helper intentionally
applies no decode-size cap, so a large explicitly selected JSON file may consume substantial
memory.

The next allowed step is:

```text
m2_explicit_local_import_record_shape_dry_run_review_gate
```

## Explicit Local-Import Record-Shape Dry-Run Review Gate

The redacted summary-only reviewer is:

```text
scripts/review_m2_explicit_local_import_record_shape_dry_run.py
```

It reviews only ignored record-shape summary JSON under
`workspace/local-private/extraction-indexing/import/record-shape/`. Optional redacted JSON or
Markdown review output remains private under
`workspace/local-private/extraction-indexing/import/record-shape-review/`.

The review never reopens the selected export, traverses record values, traverses tags, traverses
metadata, or inspects context-edge contents. A passing review permits only a later static
context-edge shape contract discussion; context-edge inspection, real DB import, index
construction, graph construction, and every original M2 completion flag remain blocked.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_shape_contract
```

## Explicit Local-Import Context-Edge Shape Contract

The static context-edge-only boundary is documented in:

```text
docs/m2-explicit-local-import-context-edge-shape-contract.md
tests/fixtures/m2_explicit_local_import_context_edge_shape_scope.synthetic.json
scripts/check_m2_explicit_local_import_context_edge_shape_contract.py
```

It defines a later all-context-edge top-level shape check using the existing relation vocabulary.
The contract does not reopen or decode an export, inspect edge values, validate edge references,
check self-edges, deduplicate edges, traverse records, import a DB, construct an index, construct a
graph, or complete any original M2 criterion.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_shape_dry_run
```

## Explicit Local-Import Context-Edge Shape Dry-Run

The bounded context-edge-only helper is:

```text
scripts/run_m2_explicit_local_import_context_edge_shape_dry_run.py
```

It reopens one explicitly selected workspace-private UTF-8 JSON export, requires the approved
top-level envelope and record-shape precondition, and checks every object in `context_edges` for
exact top-level keys, immediate string types, and the approved relation vocabulary only. It does
not emit, log, hash, normalize, or compare edge id values. It does not validate edge references,
reject self-edges, deduplicate edges, traverse records, import a DB, construct an index, construct
a graph, or complete any original M2 criterion.

Optional redacted output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-shape/`. The helper intentionally
applies no decode-size cap, so a large explicitly selected JSON file may consume substantial
memory.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_shape_dry_run_review_gate
```
