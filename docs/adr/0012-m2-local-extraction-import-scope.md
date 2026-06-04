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

## Explicit Local-Import Context-Edge Shape Dry-Run Review Gate

The redacted summary-only reviewer is:

```text
scripts/review_m2_explicit_local_import_context_edge_shape_dry_run.py
```

It reviews only ignored context-edge shape summary JSON under
`workspace/local-private/extraction-indexing/import/context-edge-shape/`. Optional redacted JSON or
Markdown review output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-shape-review/`.

The review never reopens the selected export, emits edge ids, validates edge references, checks
self-edges, deduplicates edges, traverses records, imports a DB, constructs an index, constructs a
graph, or completes any original M2 criterion. A passing review permits only a later static
context-edge reference contract discussion.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_reference_contract
```

## Explicit Local-Import Context-Edge Reference Contract

The static context-edge reference boundary is documented in:

```text
docs/m2-explicit-local-import-context-edge-reference-contract.md
tests/fixtures/m2_explicit_local_import_context_edge_reference_scope.synthetic.json
scripts/check_m2_explicit_local_import_context_edge_reference_contract.py
```

It defines only a future membership check between `context_edges[*].from_record_id` /
`context_edges[*].to_record_id` and top-level `records[*].record_id` values. It does not implement
reference validation, emit ids, normalize ids, hash ids, check self-edges, deduplicate edges,
construct a graph, import a DB, or complete any original M2 criterion.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_reference_dry_run
```

## Explicit Local-Import Context-Edge Reference Dry-Run

The bounded membership-only helper is:

```text
scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py
```

It reopens one explicitly selected workspace-private UTF-8 JSON export, requires the approved
top-level envelope, record-shape precondition, and context-edge-shape precondition, and checks only
whether each `context_edges[*].from_record_id` and `context_edges[*].to_record_id` value is present
in the top-level `records[*].record_id` set. It emits aggregate counts and blocker categories only.

Optional redacted output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-reference/`. The helper
intentionally applies no decode-size cap, so a large explicitly selected JSON file may consume
substantial memory.

The helper does not emit ids, normalize ids, hash ids, check self-edges, deduplicate edges, map
retrieval buckets, import a DB, construct an index, construct a graph, or complete any original M2
criterion.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_reference_dry_run_review_gate
```

## Explicit Local-Import Context-Edge Reference Dry-Run Review Gate

The redacted summary-only reviewer is:

```text
scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py
```

It reviews only ignored context-edge reference dry-run summary JSON under
`workspace/local-private/extraction-indexing/import/context-edge-reference/`. Optional redacted JSON
or Markdown review output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-reference-review/`.

The review never reopens the selected export, emits ids, normalizes ids, hashes ids, checks
self-edges, deduplicates edges, maps retrieval buckets, imports a DB, constructs an index,
constructs a graph, or completes any original M2 criterion. A passing review permits only a later
static context-edge integrity contract discussion.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_integrity_contract
```

## Explicit Local-Import Context-Edge Integrity Contract

The static context-edge integrity boundary is documented in:

```text
docs/m2-explicit-local-import-context-edge-integrity-contract.md
tests/fixtures/m2_explicit_local_import_context_edge_integrity_scope.synthetic.json
scripts/check_m2_explicit_local_import_context_edge_integrity_contract.py
```

It defines only a future aggregate self-edge count and duplicate-edge count over already
reference-compatible top-level context edges. It does not reopen or decode an export, emit ids,
normalize ids, hash ids, emit relation values, map retrieval buckets, import a DB, construct an
index, construct a graph, or complete any original M2 criterion.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_integrity_dry_run
```

## Explicit Local-Import Context-Edge Integrity Dry-Run

The aggregate-only context-edge integrity dry-run is:

```text
scripts/run_m2_explicit_local_import_context_edge_integrity_dry_run.py
```

It reopens one explicit workspace-private JSON export under
`workspace/local-private/extraction-indexing/input/`, requires the prior envelope, record-shape,
context-edge-shape, and context-edge-reference compatibility gates, and reports only aggregate
self-edge and duplicate-edge counts. Optional redacted output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-integrity/`.

The helper does not emit ids, relation values, duplicate tuples, source text, paths, filenames,
hashes, logs, payloads, or runtime evidence. It does not map retrieval buckets, import a DB,
construct an index, construct a graph, or complete any original M2 criterion.

The next allowed step is:

```text
m2_explicit_local_import_context_edge_integrity_dry_run_review_gate
```

## Explicit Local-Import Context-Edge Integrity Dry-Run Review Gate

The redacted summary-only context-edge integrity reviewer is:

```text
scripts/review_m2_explicit_local_import_context_edge_integrity_dry_run.py
```

It reads only ignored context-edge integrity summary JSON under
`workspace/local-private/extraction-indexing/import/context-edge-integrity/`. Optional redacted
review output remains private under
`workspace/local-private/extraction-indexing/import/context-edge-integrity-review/`.

The review never reopens the selected export, emits ids, emits relation values, emits duplicate
tuples, maps retrieval buckets, imports a DB, constructs a line index, constructs a context graph,
or completes any original M2 criterion. A passing review permits only a final local-import approval
contract discussion before the first real M2 criterion can begin.

The next allowed step is:

```text
m2_local_import_final_approval_contract
```

## Local Import Final Approval Contract

The final static approval boundary before the first original M2 criterion is:

```text
docs/m2-local-import-final-approval-contract.md
tests/fixtures/m2_local_import_final_approval_scope.synthetic.json
scripts/check_m2_local_import_final_approval_contract.py
```

It approves only the next `m2_local_import_implementation` slice. That implementation may read one
explicit workspace-private `m2-local-private-export.v1` JSON export and write a private imported DB
artifact only under `workspace/local-private/extraction-indexing/import/db/`.

This approval does not complete original M2, build a line index, build a context graph, map
retrieval buckets, scan game installs, change companion contracts, or permit committed extracted
text, private paths, payloads, private DB artifacts, indexes, or reports.

The next allowed step is:

```text
m2_local_import_implementation
```

## Local Import Implementation

The approved first original-M2 implementation slice is:

```text
scripts/run_m2_local_import.py
```

It reads one explicit workspace-private `m2-local-private-export.v1` JSON export under
`workspace/local-private/extraction-indexing/input/` and writes one ignored private DB artifact
under `workspace/local-private/extraction-indexing/import/db/`.

The implementation requires the previously approved envelope, record-shape, context-edge-shape,
context-edge-reference, and context-edge-integrity boundaries before writing the artifact. Public
stdout and returned summaries include only aggregate redacted status. Record ids, edge ids,
relation values, source text, tags, metadata, private paths, filenames, logs, payloads, and runtime
evidence remain out of public output and tracked files.

The implementation does not build a line index, build a context graph, map retrieval buckets, scan
game installs, read runtime logs, call providers, change companion contracts, or commit generated
private artifacts.

The next allowed step is:

```text
m2_line_index_contract
```

## Local Import Review Gate

The redacted local-import summary reviewer is:

```text
scripts/review_m2_local_import.py
tests/fixtures/m2_local_import_review_decision.synthetic.json
```

It reads only ignored redacted summary JSON under
`workspace/local-private/extraction-indexing/import/db-summary/`. It never reopens the selected
export or private DB artifact. A passing review permits only the already scoped
`m2_line_index_implementation`.

The next allowed step is:

```text
m2_line_index_implementation
```

## Line Index Implementation

The approved second original-M2 implementation slice is:

```text
scripts/run_m2_line_index.py
```

It reads one explicit private imported DB artifact under
`workspace/local-private/extraction-indexing/import/db/` plus one redacted local-import review under
`workspace/local-private/extraction-indexing/import/db-review/`, then writes one ignored private
`m2-line-index.v1` artifact under
`workspace/local-private/extraction-indexing/import/line-index/`.

Public stdout and returned summaries include only aggregate redacted status. Private ids, source
text, tags, metadata, private paths, filenames, logs, payloads, and runtime evidence remain out of
public output and tracked files.

The implementation does not build a context graph, map retrieval buckets, scan game installs, read
runtime logs, call providers, change companion contracts, or commit generated private artifacts.

The next allowed step is:

```text
m2_context_graph_contract
```

## Context-Graph Contract

The static approval boundary for the third original M2 criterion is:

```text
docs/m2-context-graph-contract.md
tests/fixtures/m2_context_graph_scope.synthetic.json
scripts/check_m2_context_graph_contract.py
```

It approves only the next `m2_context_graph_implementation` slice. That implementation may read one
explicit private imported DB artifact under `workspace/local-private/extraction-indexing/import/db/`
and one explicit private line-index artifact under
`workspace/local-private/extraction-indexing/import/line-index/`, then write one ignored private
context-graph artifact under `workspace/local-private/extraction-indexing/import/context-graph/`.

The contract limits relation-to-retrieval-bucket mapping to the graph implementation boundary:
`previous_visible -> visible_history`, `nearby_branch -> nearby_tree`, and
`player_option -> player_options`. It does not permit source text duplication in graph output,
arbitrary future-branch traversal, game scanning, runtime reads, provider execution, companion
contract changes, committed extracted text, private paths, payloads, private DB artifacts, line
indexes, graphs, or reports.

The next allowed step is:

```text
m2_line_index_review_gate
```

## Line Index Review Gate

The redacted line-index summary reviewer is:

```text
scripts/review_m2_line_index.py
tests/fixtures/m2_line_index_review_decision.synthetic.json
```

It reads only ignored redacted summary JSON under
`workspace/local-private/extraction-indexing/import/line-index-summary/`. It never reopens the
private DB artifact or private line-index artifact. A passing review permits only the already scoped
`m2_context_graph_implementation`.

The next allowed step after a passing review is:

```text
m2_context_graph_implementation
```

## Line Index Contract

The static approval boundary for the second original M2 criterion is:

```text
docs/m2-line-index-contract.md
tests/fixtures/m2_line_index_scope.synthetic.json
scripts/check_m2_line_index_contract.py
```

It approves only the next `m2_line_index_implementation` slice. That implementation may read one
explicit private imported DB artifact under `workspace/local-private/extraction-indexing/import/db/`
and write one ignored private line-index artifact under
`workspace/local-private/extraction-indexing/import/line-index/`.

The contract does not build the line index, build a context graph, map retrieval buckets, scan game
installs, read runtime logs, call providers, change companion contracts, or permit committed
extracted text, private paths, payloads, private DB artifacts, line indexes, graphs, or reports.
The implementation requires a passing `scripts/review_m2_local_import.py` review first.

The next allowed step is:

```text
m2_local_import_review_gate
```
