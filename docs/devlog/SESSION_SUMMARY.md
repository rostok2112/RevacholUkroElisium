# Session Summary

Original M2 context-graph review gate is implemented.

Decision:
- `m2_context_graph_review_gate` is needed before M2 closeout.
- Reason: the context-graph implementation writes a private graph artifact containing private ids.
  The review gate validates only redacted context-graph summary evidence and never reopens the
  private graph, DB, line index, or selected export.

Completed in the latest session:
- Added optional `--summary-output` support to `scripts/run_m2_context_graph.py` for redacted
  summary JSON under `workspace/local-private/extraction-indexing/import/context-graph-summary/`.
- Added `scripts/review_m2_context_graph.py` and
  `tests/fixtures/m2_context_graph_review_decision.synthetic.json`.
- The reviewer reads only redacted summary JSON and optional review outputs stay under
  `workspace/local-private/extraction-indexing/import/context-graph-review/`.
- Updated the context-graph contract so `m2_closeout_review_gate` requires a passing
  `m2_context_graph_review_gate`.
- Generated graphs, line indexes, private DB artifacts, extracted text, private paths, payloads,
  reports, game scanning, runtime reads, companion changes, providers, and committed private
  artifacts remain blocked.
- The next safe step is `m2_closeout_review_gate`.

---

Original M2 context-graph implementation is added.

Completed in the latest session:
- Added `scripts/run_m2_context_graph.py` and `tests/test_m2_context_graph.py`.
- The helper requires one explicit private DB artifact, one explicit private line-index artifact,
  and one redacted line-index review under ignored workspace roots.
- It writes one ignored private `m2-context-graph.v1` artifact under
  `workspace/local-private/extraction-indexing/import/context-graph/`.
- Graph nodes do not duplicate `source_text`; source text remains in the private line index.
- Relation-to-retrieval-bucket mapping is limited to the approved context graph mappings.
- Public stdout and summaries remain aggregate/redacted; private ids are preserved only inside the
  ignored private context-graph artifact.
- Wired `python scripts/run_m2_context_graph.py --self-test --quiet` into `scripts/check_all.py`.
- Original M2 now has implementation paths for import, line index, and context graph, but generated
  private artifacts remain local/ignored and uncommitted.
- The next safe step is `m2_context_graph_review_gate`.

---

Original M2 line-index review gate is implemented.

Decision:
- `m2_line_index_review_gate` is needed before context-graph implementation.
- Reason: the graph implementation will consume a private line-index artifact that can contain
  private ids and source text. The review gate validates only the redacted line-index summary and
  never reopens the private DB or line-index artifact.

Completed in the latest session:
- Added optional `--summary-output` support to `scripts/run_m2_line_index.py` for redacted summary
  JSON under `workspace/local-private/extraction-indexing/import/line-index-summary/`.
- Added `scripts/review_m2_line_index.py` and
  `tests/fixtures/m2_line_index_review_decision.synthetic.json`.
- The reviewer reads only redacted summary JSON and optional review outputs stay under
  `workspace/local-private/extraction-indexing/import/line-index-review/`.
- Updated the context-graph contract so `m2_context_graph_implementation` requires a passing
  `m2_line_index_review_gate`.
- Context-graph construction, retrieval-bucket mapping outside the graph implementation, game
  scanning, runtime reads, companion changes, providers, committed private DB artifacts, line
  indexes, graphs, reports, private paths, and extracted text remain blocked.
- The only approved next step is `m2_line_index_review_gate`; after it passes, the next step is
  `m2_context_graph_implementation`.

---

Original M2 context-graph contract is defined.

Completed in the latest session:
- Added `docs/m2-context-graph-contract.md`,
  `tests/fixtures/m2_context_graph_scope.synthetic.json`, and
  `scripts/check_m2_context_graph_contract.py`.
- The contract requires `m2_line_index_review_gate` evidence before the next
  `m2_context_graph_implementation` slice consumes one explicit private DB artifact and one explicit
  private line-index artifact.
- Future private context-graph output is restricted to
  `workspace/local-private/extraction-indexing/import/context-graph/`.
- Relation-to-retrieval-bucket mapping is limited to the context graph mappings
  `previous_visible -> visible_history`, `nearby_branch -> nearby_tree`, and
  `player_option -> player_options`.
- Source text duplication in graph output, arbitrary future-branch traversal, game scanning,
  runtime reads, companion changes, provider execution, committed extracted text, private paths,
  payloads, private DB artifacts, line indexes, graphs, and reports remain blocked.
- Original M2 still needs the context-graph implementation before all three original criteria are
  implemented.
- The only approved next step is `m2_line_index_review_gate`.

---

Original M2 line-index implementation is added.

Completed in the latest session:
- Added `scripts/run_m2_line_index.py` and `tests/test_m2_line_index.py`.
- The helper requires one explicit private imported DB artifact and one redacted local-import review
  under ignored workspace roots.
- It writes one ignored private `m2-line-index.v1` artifact under
  `workspace/local-private/extraction-indexing/import/line-index/`.
- Public stdout and summaries remain aggregate/redacted; private ids and source text are preserved
  only inside the ignored private line-index artifact.
- Wired `python scripts/run_m2_line_index.py --self-test --quiet` into `scripts/check_all.py`.
- Original M2 still needs context-graph work.
- The only approved next step is `m2_context_graph_contract`.

---

Original M2 local import review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_local_import.py` and
  `tests/fixtures/m2_local_import_review_decision.synthetic.json`.
- Added optional `--summary-output` support to `scripts/run_m2_local_import.py` for redacted
  summary JSON under `workspace/local-private/extraction-indexing/import/db-summary/`.
- The reviewer reads only the redacted summary and never reopens the selected export or private DB
  artifact.
- A passing review permits only `m2_line_index_implementation`.
- Context-graph construction, retrieval-bucket mapping, game scanning, runtime reads, companion
  changes, providers, committed private DB artifacts, line indexes, graphs, reports, private paths,
  and extracted text remain blocked.
- The only approved next step is `m2_line_index_implementation`.

---

Original M2 line-index contract is defined.

Completed in the latest session:
- Added `docs/m2-line-index-contract.md`,
  `tests/fixtures/m2_line_index_scope.synthetic.json`, and
  `scripts/check_m2_line_index_contract.py`.
- The contract approves only the next `m2_line_index_implementation` slice for one explicit
  private imported DB artifact.
- Future private line-index output is restricted to
  `workspace/local-private/extraction-indexing/import/line-index/`.
- Context-graph construction, retrieval-bucket mapping, game scanning, runtime reads, companion
  changes, provider execution, committed extracted text, private paths, payloads, private DB
  artifacts, line indexes, graphs, and reports remain blocked.
- Original M2 remains active until line-index implementation and context-graph work are completed.
- The next implementation now requires `m2_local_import_review_gate` evidence first.

---

Original M2 local import implementation is added.

Completed in the latest session:
- Added `scripts/run_m2_local_import.py` and `tests/test_m2_local_import.py`.
- The helper reads one explicit workspace-private `m2-local-private-export.v1` JSON export and
  writes one ignored private DB artifact under
  `workspace/local-private/extraction-indexing/import/db/`.
- Public stdout and summaries remain aggregate/redacted; private values are preserved only in the
  ignored private DB artifact.
- Wired `python scripts/run_m2_local_import.py --self-test --quiet` into `scripts/check_all.py`.
- The first original M2 criterion now has an implementation path, but original M2 remains active
  until line-index and context-graph work are completed.
- The only approved next step is `m2_line_index_contract`.

---

Original M2 local import final approval contract is defined.

Completed in the latest session:
- Added `docs/m2-local-import-final-approval-contract.md`,
  `tests/fixtures/m2_local_import_final_approval_scope.synthetic.json`, and
  `scripts/check_m2_local_import_final_approval_contract.py`.
- The contract approves only the next `m2_local_import_implementation` slice for one explicit
  workspace-private `m2-local-private-export.v1` JSON export.
- Future private DB output is restricted to
  `workspace/local-private/extraction-indexing/import/db/`.
- Line-index construction, context-graph construction, retrieval-bucket mapping, game scanning,
  runtime reads, companion changes, provider execution, committed extracted text, private paths,
  payloads, private DB artifacts, indexes, and reports remain blocked.
- Original M2 remains active and incomplete until the import implementation actually runs and is
  reviewed.
- The only approved next step is `m2_local_import_implementation`.

---

Original M2 explicit local-import context-edge integrity dry-run review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_explicit_local_import_context_edge_integrity_dry_run.py` and
  `tests/fixtures/m2_explicit_local_import_context_edge_integrity_dry_run_review_decision.synthetic.json`.
- The reviewer reads only ignored redacted context-edge integrity summary JSON and never reopens
  the selected export.
- Optional redacted JSON or Markdown review output is restricted to
  `workspace/local-private/extraction-indexing/import/context-edge-integrity-review/`.
- The review output contains aggregate counts and blocker categories only; record ids, edge ids,
  relation values, duplicate tuples, source text, paths, filenames, hashes, logs, payloads, and
  runtime evidence remain sealed.
- A passing review permits only `m2_local_import_final_approval_contract`.
- Retrieval-bucket mapping, DB import, line-index construction, context-graph construction, and
  every original M2 completion flag remain blocked.
- The only approved next step is `m2_local_import_final_approval_contract`.

---

Original M2 explicit local-import context-edge integrity dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_explicit_local_import_context_edge_integrity_dry_run.py` and
  `tests/test_m2_explicit_local_import_context_edge_integrity_dry_run.py`.
- The helper reopens only one explicit workspace-private JSON export and requires the approved
  envelope, record-shape, context-edge-shape, and context-edge-reference preconditions.
- The dry-run reports only aggregate `self_edge_count` and `duplicate_edge_count`; record ids,
  edge ids, relation values, duplicate tuples, source text, paths, filenames, hashes, logs,
  payloads, and runtime evidence remain sealed.
- Optional redacted JSON output is restricted to
  `workspace/local-private/extraction-indexing/import/context-edge-integrity/`.
- Wired the temp-workspace self-test into `scripts/check_all.py`.
- Retrieval-bucket mapping, DB import, line-index construction, context-graph construction, and
  every original M2 completion flag remain blocked.
- The only approved next step is
  `m2_explicit_local_import_context_edge_integrity_dry_run_review_gate`.

---

Original M2 explicit local-import context-edge integrity contract is defined.

Completed in the latest session:
- Added `docs/m2-explicit-local-import-context-edge-integrity-contract.md`,
  `tests/fixtures/m2_explicit_local_import_context_edge_integrity_scope.synthetic.json`, and
  `scripts/check_m2_explicit_local_import_context_edge_integrity_contract.py`.
- The static contract defines a later aggregate-only self-edge count and duplicate-edge count over
  already reference-compatible context edges.
- Duplicate edges are scoped as exact duplicate tuples of `from_record_id`, `to_record_id`, and
  `relation`, but tuple values remain sealed.
- Id emission, id normalization, id hashing, relation emission, retrieval-bucket mapping, DB
  import, line-index construction, context-graph construction, and every original M2 completion
  flag remain blocked.
- Wired the fixture-only checker into `scripts/check_all.py`.
- The only approved next step is `m2_explicit_local_import_context_edge_integrity_dry_run`.

Original M2 explicit local-import context-edge reference dry-run review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py` and
  `tests/fixtures/m2_explicit_local_import_context_edge_reference_dry_run_review_decision.synthetic.json`.
- The reviewer reads only ignored redacted context-edge reference summary JSON and never reopens
  the selected export.
- Optional redacted JSON or Markdown review output is restricted to
  `workspace/local-private/extraction-indexing/import/context-edge-reference-review/`.
- The review output contains aggregate counts and blocker categories only; record ids, edge ids,
  relation values, source text, paths, filenames, hashes, logs, payloads, and runtime evidence
  remain sealed.
- A passing review permits only a static context-edge integrity contract discussion.
- Wired a synthetic temp-workspace review self-test into `scripts/check_all.py`.
- Self-edge checks, duplicate-edge checks, retrieval-bucket mapping, DB import, index
  construction, graph construction, and every original M2 completion flag remain blocked.
- The only approved next step is `m2_explicit_local_import_context_edge_integrity_contract`.

Original M2 explicit local-import context-edge reference dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py`.
- The helper reopens one explicitly selected workspace-private UTF-8 JSON export, requires the
  approved envelope, record-shape precondition, and context-edge-shape precondition, and performs
  membership-only checks from `context_edges[*].from_record_id` and
  `context_edges[*].to_record_id` to top-level `records[*].record_id` values.
- The summary emits only aggregate counts, booleans, and blocker categories; record ids, edge ids,
  relation values, source text, labels, tags, metadata, paths, filenames, hashes, logs, payloads,
  and runtime evidence remain sealed.
- Optional redacted JSON output is restricted to
  `workspace/local-private/extraction-indexing/import/context-edge-reference/`.
- The helper intentionally applies no decode-size cap; a large selected JSON file may consume
  substantial memory while reference membership is checked.
- Self-edge checks, duplicate-edge checks, retrieval-bucket mapping, DB import, line-index
  construction, context-graph construction, and every original M2 completion flag remain blocked.
- Wired a synthetic temp-workspace self-test into `scripts/check_all.py`.
- The only approved next step is
  `m2_explicit_local_import_context_edge_reference_dry_run_review_gate`.

Original M2 explicit local-import context-edge reference contract is defined.

Completed in the latest session:
- Added `docs/m2-explicit-local-import-context-edge-reference-contract.md`,
  `tests/fixtures/m2_explicit_local_import_context_edge_reference_scope.synthetic.json`, and
  `scripts/check_m2_explicit_local_import_context_edge_reference_contract.py`.
- The static contract defines a later membership-check boundary for comparing
  `context_edges[*].from_record_id` and `context_edges[*].to_record_id` against top-level
  `records[*].record_id` values.
- Edge ids, record ids, source text, relation values, paths, filenames, hashes, logs, payloads,
  and runtime evidence remain sealed.
- This contract does not reopen or decode a selected export, validate real references, check
  self-edges, deduplicate edges, import a DB, construct an index, construct a graph, or complete any
  original M2 criterion.
- Wired the fixture-only checker into `scripts/check_all.py`.
- The only approved next step is `m2_explicit_local_import_context_edge_reference_dry_run`.

Original M2 explicit local-import context-edge shape dry-run review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_explicit_local_import_context_edge_shape_dry_run.py` and
  `tests/fixtures/m2_explicit_local_import_context_edge_shape_dry_run_review_decision.synthetic.json`.
- The reviewer reads only ignored redacted context-edge shape summary JSON and never reopens the
  selected export.
- Optional redacted JSON or Markdown review output is restricted to
  `workspace/local-private/extraction-indexing/import/context-edge-shape-review/`.
- The review output contains aggregate counts and blocker categories only; edge ids, record ids,
  relation values, source text, paths, filenames, hashes, logs, payloads, and runtime evidence
  remain sealed.
- A passing review permits only a static context-edge reference contract discussion.
- Wired a synthetic temp-workspace review self-test into `scripts/check_all.py`.
- Edge reference validation, self-edge checks, duplicate-edge checks, DB import, index
  construction, graph construction, and every original M2 completion flag remain blocked.
- The only approved next step is `m2_explicit_local_import_context_edge_reference_contract`.

Original M2 explicit local-import context-edge shape dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_explicit_local_import_context_edge_shape_dry_run.py`.
- The helper reopens one explicitly selected workspace-private UTF-8 JSON export, requires the
  approved envelope and record-shape precondition, and checks every `context_edges` object for exact
  top-level keys, immediate string types, and approved relation vocabulary only.
- Edge id values, record values, tag contents, metadata contents, edge reference validation,
  self-edge checks, duplicate-edge checks, paths, filenames, hashes, logs, and payloads are never
  emitted.
- Optional redacted JSON output is restricted to
  `workspace/local-private/extraction-indexing/import/context-edge-shape/`.
- The helper intentionally applies no decode-size cap; a large selected JSON file may consume
  substantial memory while envelope, record, and context-edge shapes are checked.
- Wired a synthetic temp-workspace self-test into `scripts/check_all.py`.
- No DB is imported, no index or graph is constructed, and no original M2 completion flag advances.
- The only approved next step is `m2_explicit_local_import_context_edge_shape_dry_run_review_gate`.

Original M2 explicit local-import context-edge shape contract is defined.

Completed in the latest session:
- Added `docs/m2-explicit-local-import-context-edge-shape-contract.md`,
  `tests/fixtures/m2_explicit_local_import_context_edge_shape_scope.synthetic.json`, and
  `scripts/check_m2_explicit_local_import_context_edge_shape_contract.py`.
- The static contract reuses the existing synthetic relation vocabulary and defines a later
  all-context-edge top-level shape check only.
- Edge id values, record values, tag contents, metadata contents, reference validation, self-edge
  checks, duplicate-edge checks, paths, filenames, hashes, logs, and payloads remain sealed.
- This contract does not reopen or decode a selected export, inspect real context edges, import a
  DB, construct an index, construct a graph, or complete any original M2 criterion.
- Wired the fixture-only checker into `scripts/check_all.py`.
- The only approved next step is `m2_explicit_local_import_context_edge_shape_dry_run`.

Original M2 explicit local-import record-shape dry-run review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_explicit_local_import_record_shape_dry_run.py` and
  `tests/fixtures/m2_explicit_local_import_record_shape_dry_run_review_decision.synthetic.json`.
- The reviewer reads only ignored redacted record-shape summary JSON and never reopens the
  selected export or traverses record values, tag contents, metadata contents, or context edges.
- Optional redacted JSON or Markdown review output is restricted to
  `workspace/local-private/extraction-indexing/import/record-shape-review/`.
- Compatible evidence permits only a static context-edge shape contract discussion.
- Wired a synthetic temp-workspace review self-test into `scripts/check_all.py`.
- Context-edge inspection, DB import, index construction, graph construction, and every original
  M2 completion flag remain blocked.
- The only approved next step is `m2_explicit_local_import_context_edge_shape_contract`.

Original M2 explicit local-import record-shape dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_explicit_local_import_record_shape_dry_run.py`.
- The helper reopens one explicitly selected workspace-private UTF-8 JSON export, requires the
  approved envelope, and checks every record object for exact top-level keys and immediate value
  types only.
- Record values, source text, ids, labels, tag contents, metadata contents, context edges, paths,
  filenames, hashes, logs, and payloads are never emitted.
- Optional redacted JSON output is restricted to
  `workspace/local-private/extraction-indexing/import/record-shape/`.
- The helper intentionally applies no decode-size cap; a large selected JSON file may consume
  substantial memory while all record shapes are checked.
- Wired a synthetic temp-workspace self-test into `scripts/check_all.py`.
- No DB is imported, no index or graph is constructed, and no original M2 completion flag advances.
- The only approved next step is `m2_explicit_local_import_record_shape_dry_run_review_gate`.

Original M2 explicit local-import record-shape contract is defined.

Completed in the latest session:
- Added `docs/m2-explicit-local-import-record-shape-contract.md`,
  `tests/fixtures/m2_explicit_local_import_record_shape_scope.synthetic.json`, and
  `scripts/check_m2_explicit_local_import_record_shape_contract.py`.
- The static contract reuses the established synthetic record vocabulary and defines a later
  all-record top-level shape check only.
- Source-text values, ids, labels, tag contents, metadata contents, context edges, paths,
  filenames, hashes, logs, and payloads remain sealed.
- This contract does not reopen or decode a selected export, inspect real records, import a DB,
  construct an index, construct a graph, or complete any original M2 criterion.
- Wired the fixture-only checker into `scripts/check_all.py`.
- The only approved next step is `m2_explicit_local_import_record_shape_dry_run`.

Original M2 explicit local-import schema-compatibility dry-run review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_explicit_local_import_schema_compatibility_dry_run.py` and
  `tests/fixtures/m2_explicit_local_import_schema_compatibility_dry_run_review_decision.synthetic.json`.
- The reviewer reads only ignored redacted compatibility-summary JSON and never reopens the
  selected export or traverses nested record, edge, or metadata values.
- Optional redacted JSON or Markdown review output is restricted to
  `workspace/local-private/extraction-indexing/import/schema-compatibility-review/`.
- Compatible evidence permits only a static record-shape contract discussion.
- Wired a synthetic temp-workspace review self-test into `scripts/check_all.py`.
- Record-shape inspection, DB import, index construction, graph construction, and every original
  M2 completion flag remain blocked.
- The only approved next step is `m2_explicit_local_import_record_shape_contract`.

Original M2 explicit local-import schema-compatibility dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py`.
- The helper decodes one explicitly selected workspace-private UTF-8 JSON file and inspects only
  the exact top-level envelope field set, top-level types, and aggregate record and edge counts.
- Nested record values, graph-edge values, and metadata contents are never traversed or emitted.
- Optional redacted JSON output is restricted to
  `workspace/local-private/extraction-indexing/import/schema-compatibility/`.
- The helper intentionally applies no decode-size cap; a large explicitly selected JSON file may
  consume substantial memory.
- Wired a synthetic temp-workspace self-test into `scripts/check_all.py`.
- No DB is imported, no index or graph is constructed, and no original M2 completion flag advances.
- The only approved next step is
  `m2_explicit_local_import_schema_compatibility_dry_run_review_gate`.

Original M2 explicit local-import schema-compatibility contract is defined.

Completed in the latest session:
- Added `docs/m2-explicit-local-import-schema-compatibility-contract.md`,
  `tests/fixtures/m2_explicit_local_import_schema_compatibility_scope.synthetic.json`, and
  `scripts/check_m2_explicit_local_import_schema_compatibility_contract.py`.
- The static contract defines one future UTF-8 JSON object profile under the ignored private input
  root.
- A later dry-run may check top-level envelope presence and types and calculate aggregate record
  and edge counts only.
- This contract does not reopen or decode a selected export, traverse nested values, emit private
  content, import a DB, construct an index, construct a graph, or complete any original M2
  criterion.
- Wired the fixture-only checker into `scripts/check_all.py`.
- The only approved next step is `m2_explicit_local_import_schema_compatibility_dry_run`.

Original M2 explicit local-import adapter dry-run review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_explicit_local_import_adapter_dry_run.py` and
  `tests/fixtures/m2_explicit_local_import_adapter_dry_run_review_decision.synthetic.json`.
- The review helper reads only ignored redacted adapter dry-run summary JSON and never reopens the
  selected private export.
- Optional redacted JSON or Markdown review output is restricted to
  `workspace/local-private/extraction-indexing/import/adapter-dry-run-review/`.
- Wired a temp-workspace review self-test into `scripts/check_all.py`.
- Schema inspection, parsing, real DB import, index construction, graph construction, and every
  original M2 completion flag remain blocked.
- The only approved next step is `m2_explicit_local_import_schema_compatibility_contract`.

Original M2 explicit local-import adapter dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_explicit_local_import_adapter_dry_run.py`.
- The helper accepts one explicit workspace-private export file and reads filesystem metadata only.
- Directory inputs are rejected with a redacted blocker; schema compatibility remains deferred.
- Optional redacted JSON output is restricted to
  `workspace/local-private/extraction-indexing/import/adapter-dry-run/`.
- Wired a temp-workspace self-test into `scripts/check_all.py`.
- No file contents are read, no DB is imported, and no original M2 completion flag is advanced.
- The only approved next step is `m2_explicit_local_import_adapter_dry_run_review_gate`.

Original M2 explicit local-import adapter contract is implemented.

Completed in the latest session:
- Added `docs/m2-explicit-local-import-adapter-contract.md`,
  `tests/fixtures/m2_explicit_local_import_adapter_scope.synthetic.json`, and
  `scripts/check_m2_explicit_local_import_adapter_contract.py`.
- The contract limits a future adapter dry-run to one explicitly supplied workspace-private export
  file under `workspace/local-private/extraction-indexing/input/`.
- The contract keeps implementation, local-export reads, parsing, real DB import, index
  construction, graph construction, and every original M2 completion flag blocked.
- Wired the fixture-only checker into `scripts/check_all.py`.
- The only approved next step is `m2_explicit_local_import_adapter_dry_run`.

Original M2 synthetic context-graph builder review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_synthetic_context_graph_builder_dry_run.py` and
  `tests/fixtures/m2_synthetic_context_graph_builder_review_decision.synthetic.json`.
- The review helper reads only generated synthetic context-graph dry-run output under the ignored
  private workspace root and emits redacted evidence.
- Wired a temp-workspace review self-test into `scripts/check_all.py`.
- The review preserves spoiler budget `none`, keeps local-import adapter implementation blocked,
  and does not mark any original M2 criterion complete.
- The only approved next step is `m2_explicit_local_import_adapter_contract`.

Original M2 synthetic context-graph builder dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_synthetic_context_graph_builder_dry_run.py`.
- The helper validates one explicit invented import JSON and one explicit metadata-only synthetic
  line index, then deterministically projects the committed synthetic context graph.
- Optional output is restricted to the ignored private root
  `workspace/local-private/extraction-indexing/import/context-graph/`.
- Wired a quiet fixture-match smoke into `scripts/check_all.py`.
- The helper preserves spoiler budget `none`, keeps `graph_constructed=false`, and does not mark
  any original M2 criterion complete.
- The only approved next step is `m2_synthetic_context_graph_builder_review_gate`.

Original M2 synthetic context-graph contract is implemented.

Completed in the latest session:
- Added `docs/m2-synthetic-context-graph-contract.md`,
  `specs/m2-synthetic-context-graph.schema.json`, and
  `tests/fixtures/m2_synthetic_context_graph.synthetic.json`.
- Added `scripts/check_m2_synthetic_context_graph_contract.py` and wired it into
  `scripts/check_all.py`.
- The fixture maps metadata-only nodes to the synthetic line index and invented edges to
  `visible_history`, `nearby_tree`, and `player_options` retrieval buckets.
- Default spoiler budget remains `none`; arbitrary future-branch traversal remains blocked.
- The only approved next step is `m2_synthetic_context_graph_builder_dry_run`.
- Did not construct a graph, read private input, import a real DB, or mark any original M2
  criterion complete.

Original M2 synthetic line-index builder review gate is implemented.

Completed in the latest session:
- Added `scripts/review_m2_synthetic_line_index_builder_dry_run.py` and
  `tests/fixtures/m2_synthetic_line_index_builder_review_decision.synthetic.json`.
- The review helper reads only generated metadata-only synthetic line-index output under the
  ignored private workspace root and emits redacted evidence.
- Wired a temp-workspace review self-test into `scripts/check_all.py`.
- The review keeps context-graph construction blocked and original M2 criteria incomplete.
- The only approved next step is `m2_synthetic_context_graph_contract`.
- Did not read private input, import a real DB, include source text or graph edges, or build a
  context graph.

Original M2 synthetic line-index builder dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_m2_synthetic_line_index_builder_dry_run.py`.
- The helper validates one explicit invented synthetic import JSON and deterministically projects
  metadata-only entries matching `tests/fixtures/m2_synthetic_line_index.synthetic.json`.
- Optional output is restricted to the ignored private root
  `workspace/local-private/extraction-indexing/import/line-index/`.
- Wired a quiet fixture-match smoke into `scripts/check_all.py`.
- The only approved next step is `m2_synthetic_line_index_builder_review_gate`.
- Did not import a real DB, read private input, include source text or graph edges, or build a
  context graph.

Original M2 synthetic line-index contract is implemented.

Completed in the latest session:
- Added `docs/m2-synthetic-line-index-contract.md`,
  `specs/m2-synthetic-line-index.schema.json`, and
  `tests/fixtures/m2_synthetic_line_index.synthetic.json`.
- Added `scripts/check_m2_synthetic_line_index_contract.py` and wired it into
  `scripts/check_all.py`.
- The static fixture maps every invented synthetic import record exactly once using metadata-only
  entries sorted by `line_id`.
- The fixture excludes source text, graph edges, filenames, paths, hashes, payloads, logs, and
  runtime evidence.
- The only approved next step is `m2_synthetic_line_index_builder_dry_run`.
- Did not add a line-index builder, import a real DB, read private input, or build a context graph.

Original M2 reusable synthetic import validator is implemented.

Completed in the latest session:
- Added `specs/m2-synthetic-import-db.schema.json` and
  `scripts/m2_synthetic_import_validator.py`.
- The reusable validator exposes payload collection, assertion, and explicit-file loading helpers
  for invented synthetic fixtures only.
- Refactored `scripts/check_m2_synthetic_import_format.py` to reuse the validator while keeping the
  canonical fixture and documentation gate.
- Did not add real DB import, local-content reads, directory discovery, line-index construction,
  context-graph construction, or runtime behavior.

Original M2 synthetic import format contract is implemented.

Completed in the latest session:
- Added `docs/m2-synthetic-import-format-contract.md`, defining
  `m2-synthetic-import-db.v1` as an invented-fixture-only envelope for later M2 contract work.
- Added `tests/fixtures/m2_synthetic_import_db.synthetic.json` with three invented records,
  synthetic placeholder fields, and synthetic context edges using `previous_visible`,
  `nearby_branch`, and `player_option`.
- Added `scripts/check_m2_synthetic_import_format.py` and wired it into `scripts/check_all.py`.
- The fixture checker validates stable synthetic ids, edge references, relation values, explicit
  incomplete-M2 metadata, false safety flags, and redaction markers.
- The only approved next step is `m2_synthetic_import_validator_or_line_index_contract`.
- Did not implement an importer, read local content, import a real DB, build a line index, build a
  context graph, scan a game install, add capture behavior, call providers, or commit extracted
  text.

Original M2 local extraction import scope contract is implemented.

Completed in the latest session:
- Added `docs/adr/0012-m2-local-extraction-import-scope.md`, defining the next bounded step inside
  original `M2 - Local extraction import`.
- Added `tests/fixtures/m2_local_extraction_import_scope.synthetic.json`, recording that original
  M2 remains active and incomplete while all real-input, scanning, capture, provider, and committed
  extracted-content permissions remain false.
- Added `scripts/check_m2_local_extraction_import_scope.py` and wired it into
  `scripts/check_all.py`.
- The only approved next step is `m2_synthetic_import_format_contract`.
- Did not implement an importer, parser, line index, context graph, local-content read, game scan,
  capture path, provider execution, companion HTTP change, or committed private artifact.

Roadmap hierarchy recovery:

- `tasks/milestones.md` remains the unchanged canonical roadmap from the initial scaffold.
- Original `M0 - Repo and contracts` and `M1 - Synthetic vertical slice` are complete.
- Original `M2 - Local extraction import` is active.
- The completed 5A-labelled series is an internal M2 safety-preparation workstream, not original
  `M5 - Maximum quality pipeline`. Original M5 has not started.
- The undefined `milestone_5b_planning` placeholder is retired. The next safe decision is
  `m2_local_extraction_import_scope_contract`.

Milestone 5A.11 closes the internal 5A safety-preparation workstream at the local-only, redacted
evidence level.

Completed in the latest session:
- Added `docs/extraction-indexing-milestone-5a-closeout.md`, summarizing the safe Milestone 5A path
  from scope contract through private index builder dry-run.
- Added `tests/fixtures/extraction_indexing_5a_closeout.synthetic.json`, which records completed
  safe steps while keeping real extraction, real game-file reads, automatic game-install scanning,
  BepInEx log reads, capture, UI reads, Unity scanning, hooks, OCR, provider execution, companion
  contract changes, and committed extracted text false.
- Added `scripts/check_extraction_indexing_5a_closeout.py` and wired it into
  `scripts/check_all.py`.
- Added focused tests for fixture shape, missing safe evidence, forbidden capabilities, unsafe
  markers, docs links, and check-all registration.
- The internal 5A workstream closes without claiming real extraction. Original
  `M2 - Local extraction import` remains active, and the next safe decision is
  `m2_local_extraction_import_scope_contract`.
- Did not add extraction/indexing behavior, read private file contents, read game files, scan
  Steam/game installs, read BepInEx logs, add current-line capture, read UI text, scan Unity
  objects, add hooks/Harmony, run OCR, use decompiled code, change companion HTTP contracts, call
  providers, create generated real indexes, or commit real extracted text.

Milestone 5A.10 private index builder dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_private_index_builder_dry_run.py`, a stdlib-only helper that builds a
  `private-index-dry-run.v1` preview from a redacted private input dry-run summary and redacted
  dry-run summary hash output.
- The helper requires summaries under `workspace/local-private/extraction-indexing/`, hash outputs
  under `workspace/local-private/extraction-indexing/hash/`, and optional dry-run index output under
  `workspace/local-private/extraction-indexing/index/`.
- Added `tests/fixtures/private_index_dry_run.synthetic.json` and focused fake-workspace tests for
  deterministic output, invalid summary/hash rejection, path bounds, unsafe marker rejection,
  redacted output, quiet CLI, self-test mode, and `check_all` registration.
- Wired `python scripts/run_private_index_builder_dry_run.py --self-test --quiet` into
  `scripts/check_all.py`.
- Updated the 5A.9 construction contract and private index contract to document the 5A.10 helper.
- Did not read original private inputs, read file contents, include paths or filenames, include the
  digest value, copy raw summaries, build real text indexes, scan game installs, read BepInEx logs,
  parse saves, read screenshots, run OCR, add current-line capture, read UI text, scan Unity
  objects, add hooks/Harmony, use decompiled game code, change companion HTTP contracts, call
  providers, or commit real extracted text.

Milestone 5A.9 private index construction contract is implemented.

Completed in the latest session:
- Added `docs/extraction-indexing-private-index-construction-contract.md`, defining the future
  private index construction boundary.
- Added `tests/fixtures/private_index_construction_contract.synthetic.json`, recording that builder
  implementation remains blocked and future private index output is limited to
  `workspace/local-private/extraction-indexing/index/`.
- Added `scripts/check_private_index_construction_contract.py` and wired it into
  `scripts/check_all.py`.
- Added focused tests for fixture shape, false dangerous permissions, unsafe output roots, unsafe
  marker rejection, docs links, and check-all registration.
- Updated ADR 0011, the private index contract, the private input adapter contract, and the dry-run
  summary hash contract to point to the 5A.9 gate.
- Did not implement private index construction, read private file contents, hash file contents,
  hash paths, hash filenames, scan game installs, read BepInEx logs, parse saves, read screenshots,
  run OCR, add current-line capture, read UI text, scan Unity objects, add hooks/Harmony, use
  decompiled game code, change companion HTTP contracts, call providers, or commit real extracted
  text.

Milestone 5A.8 dry-run summary hash evidence gate is implemented.

Completed in the latest session:
- Added `scripts/review_dry_run_summary_hash.py`, a stdlib-only helper that reviews only
  `dry-run-summary-hash.v1` JSON under `workspace/local-private/extraction-indexing/hash/`.
- Added `tests/fixtures/dry_run_summary_hash_decision.synthetic.json`, recording that private index
  construction remains blocked and only a later private index construction contract may be
  discussed.
- Added focused tests for valid and malformed hash outputs, path bounds, unsafe markers, false
  safety flags, redacted JSON/Markdown review output, decision fixture safety, quiet CLI, and
  self-test mode.
- Wired `python scripts/review_dry_run_summary_hash.py --self-test --quiet` into
  `scripts/check_all.py`.
- Updated the dry-run summary hash contract and private index contract to document the 5A.8
  evidence/review gate.
- Did not read original private inputs, read file contents, read original dry-run summaries, hash
  file contents, hash paths, hash filenames, build private indexes, scan game installs, read BepInEx
  logs, parse saves, read screenshots, run OCR, add current-line capture, read UI text, scan Unity
  objects, add hooks/Harmony, use decompiled game code, change companion HTTP contracts, call
  providers, or commit real extracted text.

Milestone 5A.7 dry-run summary hash dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_dry_run_summary_hash.py`, a stdlib-only helper that hashes only canonical
  redacted dry-run summary metadata.
- Added `tests/fixtures/dry_run_summary_hash.synthetic.json`, a synthetic expected hash output
  fixture with no private paths, filenames, raw payloads, logs, game text, or extracted text.
- Added focused tests for deterministic hashing, field-order independence, blocker sorting,
  source-summary validation, `hashes_computed=true` rejection, excluded/unknown field rejection,
  unsafe marker rejection, path bounds, redacted output, no file-content reads, fixture matching,
  quiet CLI, and self-test mode.
- Wired `python scripts/run_dry_run_summary_hash.py --self-test --quiet` into
  `scripts/check_all.py`.
- Updated the dry-run summary hash contract and private input hash contract to document the helper
  and private hash output root.
- Did not read original private inputs, read file contents, hash file contents, hash paths, hash
  filenames, build private indexes, scan game installs, read BepInEx logs, parse saves, read
  screenshots, run OCR, add current-line capture, read UI text, scan Unity objects, add
  hooks/Harmony, use decompiled game code, change companion HTTP contracts, call providers, or
  commit real extracted text.

Milestone 5A.6 dry-run summary hash contract is implemented.

Completed in the latest session:
- Added `docs/extraction-indexing-dry-run-summary-hash-contract.md`, defining the future hash input
  boundary for canonical redacted dry-run summaries.
- Added `tests/fixtures/dry_run_summary_hash_contract.synthetic.json`, a synthetic contract fixture
  that keeps hash implementation, file content hashing, path string hashing, filename hashing, raw
  payload/log hashing, private index construction, real extraction, capture paths, provider
  execution, and companion contract changes closed.
- Added `scripts/check_dry_run_summary_hash_contract.py` and wired it into `scripts/check_all.py`.
- Added focused tests for fixture shape, stable allowed/excluded field lists, false dangerous
  permissions, unsafe marker rejection, docs links, and check-all registration.
- Updated ADR 0011, the private input adapter contract, the private input hash contract, and the
  private index contract to point to the 5A.6 gate.
- The next safe step is a dry-run summary hash dry-run. It is still not file content hashing, path
  hashing, filename hashing, private index construction, real extraction, or committed real text.
- Did not compute hashes, read file contents, build private indexes, scan game installs, read
  BepInEx logs, parse saves, read screenshots, run OCR, add current-line capture, read UI text, scan
  Unity objects, add hooks/Harmony, use decompiled game code, change companion HTTP contracts, call
  providers, or commit real extracted text.

Milestone 5A.5 private input hash decision contract is implemented.

Completed in the latest session:
- Added `docs/extraction-indexing-private-input-hash-contract.md`, recording that hash
  implementation is still blocked after the 5A.4 dry-run review gate.
- Added `tests/fixtures/private_input_hash_decision.synthetic.json`, a synthetic decision fixture
  that keeps file content hashing, path string hashing, private index construction, real
  extraction, capture paths, provider execution, and companion contract changes closed.
- Added `scripts/check_private_input_hash_decision_contract.py` and wired it into
  `scripts/check_all.py`.
- Added tests for fixture shape, false dangerous permissions, hash/private-index approval rejection,
  unsafe marker rejection, docs links, and check-all registration.
- Updated ADR 0011, the private input adapter contract, and the private index contract to point to
  the 5A.5 decision gate.
- The next safe step is a dry-run summary hash contract. It is not hash implementation and does not
  approve file content hashing, path string hashing, real extraction, or private index construction.
- Did not compute hashes, read file contents, build private indexes, scan game installs, read
  BepInEx logs, parse saves, read screenshots, run OCR, add current-line capture, read UI text, scan
  Unity objects, add hooks/Harmony, use decompiled game code, change companion HTTP contracts, call
  providers, or commit real extracted text.

Milestone 5A.4 private input dry-run evidence and hash/index decision gate is implemented.

Completed in the latest session:
- Added `scripts/review_private_input_adapter_dry_run.py`, a stdlib-only helper that reviews only
  redacted dry-run summary JSON under `workspace/local-private/extraction-indexing/`.
- Added `tests/fixtures/private_input_dry_run_decision.synthetic.json`, recording that hash work is
  still decision-pending and private index construction remains blocked.
- Added fake-workspace tests for valid and malformed summaries, unsafe paths, redaction, raw marker
  rejection, `hashes_computed=true` rejection, decision fixture safety, and `check_all` registration.
- Wired `python scripts/review_private_input_adapter_dry_run.py --self-test --quiet` into
  `scripts/check_all.py`.
- Updated the private input and private index contracts to document the 5A.4 review workflow.
- Did not read original private inputs, read file contents, compute hashes, build private indexes,
  scan game installs, read BepInEx logs, parse saves, read screenshots, run OCR, add current-line
  capture, read UI text, scan Unity objects, add hooks/Harmony, use decompiled game code, change
  companion HTTP contracts, call providers, or commit real extracted text.

Milestone 5A.3 private input adapter dry-run is implemented.

Completed in the latest session:
- Added `scripts/run_private_input_adapter_dry_run.py`, a stdlib-only helper that accepts one
  explicit input under `workspace/local-private/extraction-indexing/input/` and emits only a
  redacted metadata summary.
- The dry-run summary reports existence, input kind, file count, directory count, total size, allowed
  roots, redacted blockers, and explicit false safety flags.
- The helper does not read file contents, compute hashes, build indexes from private input, scan game
  installs, read BepInEx logs, parse saves, read screenshots, run OCR, add current-line capture, read
  UI text, scan Unity objects, add hooks/Harmony, use decompiled game code, change companion HTTP
  contracts, call providers, or commit real extracted text.
- Added `tests/test_private_input_adapter_dry_run.py` with fake temp workspaces only.
- Wired `python scripts/run_private_input_adapter_dry_run.py --self-test --quiet` into
  `scripts/check_all.py` so normal validation does not require real private inputs.
- Updated the private input and private index contracts to document the 5A.3 no-content/no-hash
  boundary.

Milestone 5A.2 private input adapter contract is implemented.

Completed in the latest session:
- Added `docs/extraction-indexing-private-input-adapter-contract.md`, defining the future
  user-selected private input boundary before any real input reads.
- Added `tests/fixtures/extraction_private_input_adapter_scope.synthetic.json`, a synthetic
  machine-readable contract for the 5A.2 no-scan/no-capture/no-real-text boundary.
- Added `scripts/check_extraction_private_input_adapter_contract.py` and wired it into
  `scripts/check_all.py`.
- Added focused tests for fixture shape, false dangerous permissions, unsafe private roots, unsafe
  marker values, docs links, and check-all registration.
- The future input model is limited to one explicit user-selected file or directory under
  `workspace/local-private/extraction-indexing/input/`, with future output under
  `workspace/local-private/extraction-indexing/`.
- Implementation remains blocked. The next safe step is a separately approved dry-run private input
  adapter that reports only redacted metadata summaries.
- Did not read private inputs, read game files, scan installs, read BepInEx logs, parse saves, read
  screenshots, run OCR, add current-line capture, read UI text, scan Unity objects, add
  hooks/Harmony, use decompiled game code, change companion HTTP contracts, call providers, create
  real indexes, or commit real extracted text.

Milestone 5A.1 synthetic indexer and private index contract is implemented.

Completed in the latest session:
- Added `docs/extraction-indexing-private-index-contract.md`, defining the synthetic source-record
  shape, `schema_version: "extraction-index.v1"` private index shape, redaction rules, and the
  ignored private output root.
- Added synthetic-only fixtures:
  `tests/fixtures/extraction_index_source_records.synthetic.json` and
  `tests/fixtures/extraction_index.synthetic.json`.
- Added `scripts/run_synthetic_extraction_indexer.py`, a stdlib-only deterministic helper that
  reads synthetic source records, builds a term index, prints a redacted summary, and may write only
  under `workspace/local-private/extraction-indexing/`.
- Added `scripts/check_extraction_index_contract.py` and wired it into `scripts/check_all.py`.
- Added focused tests for fixture validation, deterministic output, unsafe output rejection,
  marker rejection, quiet CLI behavior, and private workspace output handling.
- Updated ADR 0011 to point to the 5A.1 contract, fixtures, indexer, and checker.
- Real extraction from game files remains unimplemented and blocked. The next safe step is a
  user-selected private input adapter contract before any real local input reads.
- Did not read real game files, scan installs, read BepInEx logs, read screenshots, run OCR, add
  current-line capture, read UI text, scan Unity objects, add hooks/Harmony, use decompiled game
  code, change companion HTTP contracts, call providers, or commit real extracted text.

Milestone 5A extraction/indexing scope contract is implemented.

Completed in the latest session:
- Added `docs/adr/0011-real-extraction-indexing-scope.md`, the canonical true Milestone 5A
  scope/safety record.
- Added `tests/fixtures/extraction_indexing_scope.synthetic.json`, a synthetic machine-readable
  contract that keeps implementation blocked while allowing only local-only, user-selected,
  ignored/private future extraction/indexing inputs and indexes.
- Added `scripts/check_extraction_indexing_scope.py` and wired it into `scripts/check_all.py`.
- Added focused tests for fixture shape, false dangerous permissions, unsafe private output roots,
  unsafe marker values, docs links, and check-all registration.
- The allowed future private index root is `workspace/local-private/extraction-indexing/`, which is
  under ignored `workspace/`.
- Real extraction/indexing implementation has not started. The next step is a separate synthetic
  indexer and private index contract.
- Did not read game files, scan installs, create indexes, add C#/bridge behavior, change companion
  HTTP contracts, call providers, add current-line capture, read UI text, scan Unity objects, add
  hooks/Harmony, run OCR, or commit real game/runtime artifacts.

Milestone 4 closeout local bridge workflow smoke is recorded.

Completed in the latest session:
- Recorded a wrapper-based local bridge workflow smoke using only redacted observations in
  `docs/local-workflow.md`.
- The redacted result says plugin load, metadata snapshot, companion health, synthetic send,
  provider context/annotation presence, overlay state-source readiness, view-model validation, HTML
  validation, and accessibility validation all passed.
- Forbidden markers were not detected, the workspace-only report was written, and
  `MetadataProbeEnabled`, `MetadataProbeLogOnStart`, and `SendSyntheticEventOnStart` were restored
  to false.
- This closes the expanded Milestone 4 bridge/workflow validation. The BepInEx bridge skeleton is
  completed and over-validated by redacted runtime smoke and synthetic bridge-to-overlay workflow
  evidence.
- True Milestone 5A has not started yet. Milestone 5A remains: real extraction/indexing adapter,
  local-only.
- This does not prove or approve current-line capture, real text capture, UI text reading, Unity
  scanning, hooks/Harmony, OCR, extraction, real provider execution, production overlay shell
  behavior, or companion HTTP contract changes.
- Did not read raw logs, read raw provider payloads, commit workspace reports, commit generated
  HTML, change C# behavior, add companion endpoints, add hooks/OCR/scanning/capture, or commit
  runtime artifacts.

Local bridge workflow polish is implemented.

Completed in the latest session:
- Recorded this work as Milestone 4 closeout / bridge workflow polish, not top-level Milestone 5A.
- The BepInEx bridge skeleton is completed and over-validated by redacted runtime smoke evidence.
- True Milestone 5A has not started yet; the next top-level milestone remains real
  extraction/indexing adapter, local-only.
- Added `scripts/run_local_bridge_workflow.py`, a stdlib-only wrapper that coordinates existing
  metadata-smoke, companion-smoke, bridge-to-overlay smoke, cleanup, and doctor checks.
- The `doctor` phase reports redacted booleans for git cleanliness, staged runtime artifacts,
  BepInEx reference discovery, Steam/game discovery, `BepInEx/plugins` presence, companion health,
  bridge build helper availability, and bridge DLL presence.
- The prepare/post/cleanup phases delegate to existing redacted helpers instead of duplicating
  bridge, companion, provider-state, or overlay logic.
- Added `docs/local-workflow.md` and linked it from the bridge and manual-smoke docs.
- Added fake-only tests for doctor summaries, config prep, bridge-to-overlay delegation, cleanup,
  artifact staging detection, and redaction.
- Did not change C#, companion HTTP contracts, provider behavior, overlay runtime behavior,
  production shell behavior, or capture behavior.
- Did not launch the game, print raw logs, dump provider payloads, scan Unity objects, add hooks,
  run OCR, perform extraction, call real providers, or commit runtime artifacts.

Metadata-only overlay refresh readiness helper is implemented.

Completed in the latest session:
- Added `scripts/run_overlay_refresh_readiness.py`, a stdlib-only helper that summarizes companion
  health, latest provider-state presence, overlay state-source status, view-model validation,
  in-memory HTML review readiness, and accessibility-check status as redacted booleans/status.
- Added a `--self-test` path backed by committed synthetic fixtures so `check_all` can validate the
  helper without a real companion server, Steam install, game launch, BepInEx runtime, logs, or
  provider calls.
- Added `tests/test_overlay_refresh_readiness_helper.py` for ready, no-companion, no-provider,
  partial/invalid provider-state, unsafe output, redaction, quiet CLI, and workspace-only report
  behavior.
- Wired the helper self-test into `scripts/check_all.py`.
- Updated overlay, bridge, and refresh-readiness docs to document the helper and its workspace-only
  redacted output policy.
- Did not change C#, companion HTTP contracts, provider behavior, overlay renderer behavior, polling
  loops, timers, background workers, production shell behavior, or runtime capture behavior.

Metadata-only overlay refresh/readiness contract is implemented.

Completed in the latest session:
- Added `docs/overlay-refresh-readiness-contract.md`, a static contract for future overlay refresh
  readiness after the successful bridge-to-overlay synthetic smoke.
- Added `tests/fixtures/overlay_refresh_readiness_contract.synthetic.json`, a metadata-only fixture
  that records stable readiness states and keeps current-line capture, real text capture, UI text
  reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider execution, companion
  contract changes, production shell behavior, polling loops, timers, and background workers closed.
- Added `scripts/check_overlay_refresh_readiness_contract.py` and wired it into `scripts/check_all.py`.
- Added focused tests for fixture shape, readiness state stability, dangerous permission flags, unsafe
  marker rejection, and docs links.
- Updated bridge and overlay docs to link the contract and checker.
- Did not change C#, companion server/client code, provider behavior, overlay renderer behavior,
  smoke helpers, runtime capture behavior, or companion HTTP contracts.

Post bridge-to-overlay next-step decision gate is implemented.

Completed in the latest session:
- Added `docs/adr/0010-post-bridge-to-overlay-next-step.md`, an accepted ADR recording the next
  safe step after the successful redacted bridge-to-overlay synthetic smoke.
- Added `tests/fixtures/post_bridge_to_overlay_next_step.synthetic.json`, a machine-readable gate
  fixture that records the synthetic smoke passed while keeping runtime implementation, current-line
  capture, real text capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, real
  provider execution, production overlay shell behavior, and companion HTTP contract changes closed.
- Extended the bridge safety checker and tests so the ADR and fixture are required and validated.
- Updated bridge, overlay, and devlog handoff notes to point to the metadata-only overlay
  refresh/readiness contract as the next safe planning step.
- Did not change C# behavior, companion HTTP contracts, overlay runtime behavior, provider
  execution, helper behavior, or committed runtime artifacts.

Redacted bridge-to-overlay synthetic smoke evidence is recorded.

Completed in the latest session:
- Recorded a tracked redacted evidence note in `docs/manual-smoke/bepinex-metadata-probe-smoke.md`.
- The redacted result says the bridge plugin loaded, metadata snapshot was observed, localhost
  companion health was observed, synthetic send was observed, latest provider context and annotation
  existed, overlay state-source was ready, overlay view model was valid, overlay HTML was valid, and
  the accessibility check passed.
- The report was written only under ignored workspace paths, forbidden markers were not detected,
  and `MetadataProbeEnabled`, `MetadataProbeLogOnStart`, and `SendSyntheticEventOnStart` were
  restored to false.
- The note intentionally excludes raw `LogOutput.log` lines, provider payload contents, report
  contents, screenshots, private paths, game text, generated HTML, logs, and runtime artifacts.
- This evidence proves only the synthetic/manual path from game/BepInEx/bridge synthetic event to
  companion mock provider state to overlay state/view/review.
- It does not prove or approve current-line capture, real text capture, UI text reading, Unity
  scanning, hooks/Harmony, OCR, extraction, real provider execution, production overlay behavior, or
  companion HTTP contract changes.
- Did not read raw logs, read raw provider payloads, change C# behavior, add hooks/OCR/scanning,
  add current-line capture, change companion HTTP contracts, or commit runtime artifacts.

Bridge-to-overlay synthetic smoke preparation is implemented.

Completed in the latest session:
- Added `scripts/run_bridge_to_overlay_synthetic_smoke.py`, a stdlib-only wrapper for the next
  synthetic/manual bridge-to-overlay smoke.
- The wrapper has `prepare`, `post`, and `cleanup` phases. It reuses the existing BepInEx metadata
  probe helper for bridge install/config/log/report handling, uses the existing companion client for
  latest provider state, and uses the existing overlay state-source, view-model, renderer, and
  accessibility checks.
- The wrapper prints only redacted booleans/status and can write optional redacted summaries under
  `workspace/synthetic-slice/bepinex-bridge/bridge-to-overlay-smoke/`.
- Optional generated overlay HTML is restricted to
  `workspace/synthetic-slice/overlay-prototype/bridge-to-overlay-smoke/`.
- Added fake-only tests for prepare/post/cleanup, redaction, unsafe output paths, missing provider
  state, invalid overlay state, and no dependency on a real Steam install, game launch, BepInEx
  runtime, or long-running companion server.
- Updated bridge/manual-smoke/overlay docs, bridge safety registration, and devlog notes.
- Did not change C# behavior, companion HTTP contracts, provider behavior, or overlay shell
  behavior.
- Did not launch the game, print raw logs, dump provider payloads, add current-line capture, read UI
  text, scan Unity objects, add hooks, run OCR, perform extraction, call real providers, or commit
  runtime artifacts.

Redacted companion-connected synthetic bridge smoke evidence is recorded.

Completed in the latest session:
- Recorded a tracked redacted evidence note in `docs/manual-smoke/bepinex-metadata-probe-smoke.md`.
- The redacted result says the bridge plugin loaded, the metadata snapshot was observed, localhost
  companion health was observed, the invented synthetic send was observed, latest synthetic/provider
  state existed, all three 4M counter observations were present, and all capture/probe expansion
  false flags were observed.
- The report checker passed, the reviewer returned ready, forbidden markers were not detected, and
  `MetadataProbeEnabled`, `MetadataProbeLogOnStart`, and `SendSyntheticEventOnStart` were restored
  to false.
- The note intentionally excludes raw `LogOutput.log` lines, report contents, companion payloads,
  screenshots, private paths, game text, logs, and runtime artifacts.
- This evidence proves only the synthetic/manual bridge-to-companion flow. It does not prove or
  approve current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR,
  extraction, real provider execution, or companion HTTP contract changes.
- Did not read raw logs or report contents, change C# behavior, add hooks/OCR/scanning/capture,
  change companion HTTP contracts, or commit runtime artifacts.

Companion-connected synthetic bridge smoke preparation is implemented.

Completed in the latest session:
- Extended `scripts/run_bepinex_metadata_probe_local_smoke.py` with config-only
  `--enable-synthetic-send` and `--disable-synthetic-send` flags for the existing
  `SendSyntheticEventOnStart` key.
- Extended the helper's redacted log summary to detect bridge-owned companion health and synthetic
  provider send markers without printing or storing raw log lines.
- Generated metadata probe reports can now set safe existing fields such as `companion_available`,
  `synthetic_event_send_configured`, and `synthetic_event_sent` from allowlisted markers only.
- Updated manual smoke docs, bridge docs, package README/DESIGN, bridge safety checks, and fake-temp
  helper tests for the companion-connected synthetic flow.
- Reused the existing companion server/client commands; no companion HTTP contract changes or C#
  behavior changes were added.
- Did not launch the game, parse dialogue, read arbitrary game files, print raw logs, add hooks,
  add OCR, scan Unity objects, call providers, or commit runtime artifacts.

Redacted local metadata-probe smoke evidence is recorded.

Completed in the latest session:
- Recorded a tracked redacted evidence note in `docs/manual-smoke/bepinex-metadata-probe-smoke.md`.
- The redacted result says the bridge plugin loaded, the metadata snapshot was observed, all three
  4M counter observations were present, all capture/probe expansion false flags were observed,
  forbidden markers were not detected, the report checker passed, the reviewer returned ready, and
  both metadata probe config flags were restored to false.
- The note intentionally excludes raw `LogOutput.log` lines, report contents, screenshots, private
  paths, game text, logs, and runtime artifacts.
- This evidence proves only metadata-probe startup and safe counter observation. It does not prove or
  approve current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR,
  extraction, provider execution, or companion HTTP contract changes.
- Did not read raw logs or report contents, change C# behavior, add hooks/OCR/scanning/capture, or
  change companion HTTP contracts.

Local in-game metadata probe smoke preparation helper is implemented.

Completed in the latest session:
- Added `scripts/run_bepinex_metadata_probe_local_smoke.py`, a stdlib-only helper for bounded Steam
  autodiscovery, optional bridge build/install, metadata probe config enable/disable, redacted log
  checks, and workspace-only metadata probe report writing.
- The helper operates on the user-owned local Steam install only when run manually. Automated tests
  use fake temporary Steam/BepInEx structures and do not require the real game install.
- The helper may copy only the built bridge DLL to `BepInEx/plugins/`, edit only the bridge config
  under `BepInEx/config/`, and read only `BepInEx/LogOutput.log` for allowlisted metadata markers.
- Added `tests/test_bepinex_metadata_probe_local_smoke.py` for fake Steam discovery, reference DLL
  discovery, install path safety, config enable/disable, safe/unsafe log checks, redacted report
  generation, and quiet/verbose CLI behavior.
- Updated bridge safety checks/tests so the local helper is registered without making `check_all`
  require a real Steam install or a real runtime report.
- Updated manual smoke docs, bridge docs, package README/DESIGN, and devlog handoff notes.
- Validation passed: `python scripts/check_all.py`, `python scripts/validate_schemas.py`,
  `python -m unittest discover -s tests -p "test_*.py"`, `npm run check`,
  `python scripts/check_bepinex_bridge_safety.py --quiet`,
  `python scripts/check_bepinex_metadata_probe_report.py --quiet`,
  `python scripts/build_bepinex_bridge.py --quiet`, and a redacted local discovery smoke with
  `python scripts/run_bepinex_metadata_probe_local_smoke.py --print-discovery --quiet`.
- Did not change C# behavior, companion HTTP contracts, provider behavior, shell behavior, or
  metadata probe runtime behavior.
- Did not launch the game, recursively scan drives, parse dialogue, read arbitrary game files, store
  or print raw logs, commit runtime reports, add hooks, add OCR/extraction, call providers, or add
  dependencies.

Milestone 4N inert metadata implementation manual verification workflow is implemented.

Completed in the latest session:
- Updated `docs/manual-smoke/bepinex-metadata-probe-smoke.md` with explicit 4M counter
  verification steps for local manual runs.
- Documented the expected safe counter fields:
  `metadata_snapshot_created_count`, `health_check_observed_count`, and
  `synthetic_send_configured_count`.
- Tightened `scripts/check_bepinex_metadata_probe_report.py` so metadata probe reports must include
  the 4M counters as non-negative integers.
- Extended bridge safety and metadata report/review tests so the manual smoke doc, report template,
  committed fixture, and review summary all cover the 4M counters.
- Updated bridge docs, metadata probe gate docs, package README/DESIGN, and devlog handoff notes.
- Did not change C# behavior, companion HTTP contracts, provider behavior, shell behavior, or
  metadata probe runtime behavior.
- Did not add current-line capture, real text capture, UI text reading, Unity scanning, game hooks,
  Harmony patches, OCR, extraction, decompiled game-code work, frontend/shell work, keyboard hooks,
  clipboard writes, downloads, web calls, or new dependencies.

Milestone 4M minimal inert metadata-only C# extension is implemented.

Completed in the latest session:
- Extended `packages/bepinex-plugin/src/MetadataProbe.cs` with inert local metadata counters:
  `metadata_snapshot_created_count`, `health_check_observed_count`, and
  `synthetic_send_configured_count`.
- Kept the existing metadata probe config defaults disabled:
  `MetadataProbeEnabled=false` and `MetadataProbeLogOnStart=false`.
- Kept all capture/probe expansion flags explicit false values:
  `real_text_captured=false`, `current_line_capture_enabled=false`, `ui_probe_attempted=false`,
  and `scene_probe_attempted=false`.
- Updated the metadata probe report template/fixture and 4L scope fixture so the new counters are
  part of the synthetic metadata-only contract.
- Hardened bridge safety checks/tests to require the new counter markers and to keep
  `MetadataProbe.cs` free of companion calls, payload builders, file/log reads, hooks, OCR,
  extraction, and runtime inspection.
- Updated bridge docs, metadata probe gate docs, package README/DESIGN, and devlog handoff notes.
- Did not change companion HTTP contracts, provider behavior, shell behavior, or default runtime
  enablement.
- Did not add current-line capture, real text capture, UI text reading, Unity scanning, game hooks,
  Harmony patches, OCR, extraction, decompiled game-code work, frontend/shell work, keyboard hooks,
  clipboard writes, downloads, web calls, or new dependencies.

Milestone 4L metadata-only extension scope contract is implemented.

Completed in the latest session:
- Added `docs/bepinex-metadata-only-extension-scope.md`, a docs/static-contract scope for a possible
  Milestone 4M metadata-only extension.
- Added `tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json`, a synthetic
  fixture that permits only a later inert metadata step and keeps text capture, current-line capture,
  UI text reading, Unity scanning, hooks, OCR, extraction, provider calls, and companion contract
  changes false.
- Recorded the 4L decision that a reviewed local metadata report is not required for the minimal 4M
  scope because it is inert, disabled by default, no-capture, and limited to counters/booleans.
- Extended `scripts/check_bepinex_bridge_safety.py` and bridge safety tests so the scope doc and
  fixture are required and validated.
- Updated metadata probe gate docs, bridge docs, ADR 0009, package design notes, and devlog handoff
  notes.
- Did not change C# runtime behavior, companion HTTP contracts, provider behavior, or metadata probe
  runtime behavior.
- Did not add current-line capture, real text capture, UI text reading, Unity scanning, game hooks,
  Harmony patches, OCR, extraction, decompiled game-code work, frontend/shell work, keyboard hooks,
  clipboard writes, downloads, web calls, or new dependencies.

Milestone 4K metadata-only extension decision gate is implemented.

Completed in the latest session:
- Added `docs/adr/0009-metadata-only-extension-gate.md`, an accepted ADR that records the project is
  ready for metadata-only extension discussion only.
- Defined readiness states: `not_ready`, `ready_for_metadata_only_extension_discussion`, and
  `ready_for_metadata_only_extension_implementation`.
- Added `tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json`, a tiny synthetic
  gate fixture with implementation, text capture, current-line capture, and companion contract
  change permissions all closed.
- Extended `scripts/check_bepinex_bridge_safety.py` and bridge safety tests so ADR 0009 and the
  gate fixture are required and validated.
- Updated metadata probe gate docs, bridge docs, ADR 0008, package design notes, and devlog handoff
  notes.
- Did not change C# runtime behavior, companion HTTP contracts, provider behavior, or metadata probe
  runtime behavior.
- Did not add current-line capture, real text capture, UI text reading, Unity scanning, game hooks,
  Harmony patches, OCR, extraction, decompiled game-code work, frontend/shell work, keyboard hooks,
  clipboard writes, downloads, web calls, or new dependencies.

Milestone 4J metadata probe report review/readiness helper is implemented.

Completed in the latest session:
- Added `scripts/review_bepinex_metadata_probe_report.py`, a stdlib-only reviewer for redacted
  user-local metadata probe reports under
  `workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.
- Review summaries use `schema_version: "bepinex-bridge-metadata-probe-review.v1"` and include
  report status, metadata/capture flags, probe completion flags, counters, deterministic blockers,
  readiness status, recommendation, redaction marker, and no-side-effect flags.
- Review outputs can be written only under
  `workspace/synthetic-slice/bepinex-bridge/metadata-probe/review/`.
- The reviewer validates reports through `scripts/check_bepinex_metadata_probe_report.py` before
  producing any summary and never copies `redacted_notes` or other free-text evidence into output.
- Added optional template/checker fields for `blockers`, `next_step_notes`, `not_run_reason`, and
  `evidence_summary_redacted`.
- Extended bridge safety checks/tests so the metadata probe reviewer is required, documented, and
  kept out of mandatory `check_all` real-report requirements.
- Updated metadata probe docs, bridge docs, ADR 0008, package README/DESIGN, and devlog handoff
  notes.
- Did not change C# runtime behavior, companion HTTP contracts, provider behavior, or report fixture
  safety boundaries.
- Did not add current-line capture, real text capture, UI text reading, Unity object scanning, game
  hooks, Harmony patches, OCR, extraction, decompiled game-code work, frontend/shell work, keyboard
  hooks, clipboard writes, downloads, web calls, or new dependencies.

Milestone 4I metadata probe manual verification workflow is implemented.

Completed in the latest session:
- Added `docs/manual-smoke/bepinex-metadata-probe-smoke.md`, a synthetic/manual checklist for
  enabling the disabled metadata probe locally and observing only a redacted startup summary.
- Added `scripts/write_bepinex_metadata_probe_report.py`, a stdlib-only template writer that creates
  blank metadata probe reports only under
  `workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.
- Added a shared `default_metadata_probe_report_template()` helper to the metadata probe report
  checker so the committed fixture, writer, and tests stay aligned.
- Extended bridge safety checks/tests so the manual metadata probe smoke doc and template writer are
  required, while `check_all` still does not require a real local report or runtime probe execution.
- Updated bridge docs, metadata probe gate docs, package README/DESIGN, and devlog handoff notes.
- Did not change C# runtime behavior. The metadata probe remains disabled by default with
  `MetadataProbeEnabled=false` and `MetadataProbeLogOnStart=false`.
- Did not add current-line capture, dialogue detection, Unity object scanning, UI text reading, game
  hooks, Harmony patches, OCR, extraction, decompiled game-code work, provider execution,
  frontend/shell work, keyboard hooks, clipboard writes, companion HTTP changes, downloads, web
  calls, or new dependencies.

Milestone 4H disabled metadata-only BepInEx probe skeleton is implemented.

Completed in the latest session:
- Added `packages/bepinex-plugin/src/MetadataProbe.cs`, a C# snapshot helper that reports only safe
  booleans and zero/default counters.
- Added false-by-default bridge config values:
  - `MetadataProbeEnabled = false`
  - `MetadataProbeLogOnStart = false`
- When both values are manually enabled, the bridge may log one startup metadata snapshot after
  companion health handling.
- The snapshot always keeps `real_text_captured=false`, `current_line_capture_enabled=false`,
  `ui_probe_attempted=false`, and `scene_probe_attempted=false`.
- Updated the committed metadata probe report fixture and checker to include probe-enabled,
  attempted/completed, and synthetic-send-configured fields.
- Hardened bridge safety checks/tests so the C# source must keep metadata probe defaults false, safe
  false capture markers present, no raw payload logging, and no hook/scanning/OCR/extraction
  behavior.
- Updated bridge docs, metadata gate docs, package README/DESIGN, and devlog handoff notes.
- Did not add current-line capture, dialogue detection, Unity object scanning, game hooks, Harmony
  patches, OCR, extraction, decompiled game-code work, provider execution, frontend/shell work,
  keyboard hooks, clipboard writes, companion HTTP changes, downloads, web calls, or new
  dependencies.

Milestone 4G metadata-only probe gate is implemented.

Completed in the latest session:
- Added `docs/bepinex-metadata-probe-gate.md`, a static safety gate for a future metadata-only
  bridge probe.
- The gate allows only redacted metadata such as booleans, safe counters, synthetic ids, safe
  status/error codes, and explicit `current_line_capture_enabled = false` /
  `real_text_captured = false` markers.
- Added `tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json`, a committed
  synthetic `not_run` metadata probe report fixture with no user-local runtime evidence.
- Added `scripts/check_bepinex_metadata_probe_report.py`, a stdlib-only checker for the committed
  fixture and optional local reports under
  `workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.
- The checker rejects real text, screenshots, OCR markers, private paths, stack traces, raw logs,
  payload dumps, decompiled-code markers, hook/capture claims, external URLs, and secret-looking
  values.
- Extended the bridge safety checker and tests so the metadata gate doc, checker, and fixture are
  required without making `check_all` depend on a real metadata probe report.
- Updated bridge docs, ADR 0008, package design notes, and manual smoke report docs to clarify that
  the metadata gate does not approve text capture.
- Did not add C# behavior, current-line capture, game hooks, Harmony patches, Unity object
  scanning, OCR, extraction, decompiled game-code work, provider execution, frontend/shell work,
  keyboard hooks, clipboard writes, companion HTTP changes, downloads, web calls, or new
  dependencies.

Milestone 4F runtime smoke evidence review workflow is implemented.

Completed in the latest session:
- Added `scripts/review_bepinex_runtime_smoke_report.py`, a stdlib-only helper for reviewing
  user-local redacted runtime smoke reports.
- The reviewer accepts only reports under `workspace/synthetic-slice/bepinex-bridge/runtime-smoke/`
  and can write redacted JSON/Markdown summaries only under
  `workspace/synthetic-slice/bepinex-bridge/runtime-smoke/review/`.
- Review summaries use `schema_version: "bepinex-bridge-runtime-smoke-review.v1"` and include report
  status, observed smoke booleans, warning counts, redaction/no-side-effect flags, deterministic
  blockers, and a recommended next step.
- Readiness is deterministic: `pass` report status, plugin load, health check, companion availability
  path, unavailable-case observation or explanation, and synthetic-send observation or safe not-run
  reason are required.
- Review output never copies report `notes_redacted` or `evidence_summary` text, and the helper does
  not read logs, game files, screenshots, companion state, or provider outputs.
- Extended the report template/checker and committed synthetic report fixture with optional review
  fields: `blockers`, `next_step_notes`, `synthetic_send_not_run_reason`,
  `unavailable_case_not_run_reason`, and `evidence_summary_redacted`.
- Added `tests/test_bepinex_runtime_smoke_review.py` and extended bridge safety registration so the
  review helper is required without making `check_all` depend on a real runtime report.
- Updated manual-smoke docs, bridge docs, and ADR 0008 to document the review command and clarify
  that readiness does not approve current-line capture.
- Did not add C# behavior, game hooks, dialogue detection, Unity object scanning, OCR, extraction,
  decompiled game-code work, provider execution, frontend/shell work, keyboard hooks, clipboard
  writes, companion HTTP changes, downloads, web calls, or new dependencies.

Milestone 4E current-line capture research ADR and safety boundaries are implemented.

Completed in the latest session:
- Added `docs/adr/0008-current-line-capture-research.md`, an accepted ADR comparing future
  current-line capture strategies before any implementation exists.
- Compared manual/synthetic triggers, user-assisted manual input, Unity UI text observation, method
  patching, save/state/event observation, OCR fallback, and external screen/accessibility APIs.
- Accepted the conservative recommendation: remain manual/synthetic until redacted runtime smoke
  evidence is reviewed; defer OCR, broad Unity scanning, game method patches, extraction, decompiled
  integration, and real text capture.
- Documented future capture boundaries: no committed real dialogue, screenshots, audio, extracted
  localization, save files, OCR output, decompiled code or risky decompiled names, private paths,
  runtime logs containing game text, or raw companion payloads with real game text.
- Documented allowed future local experiment outputs as redacted metadata, booleans, safe counters,
  synthetic event ids, bridge-generated line ids, and redacted runtime smoke reports.
- Added a Milestone 4F readiness checklist for runtime smoke execution guide and local evidence
  review before any metadata-only current-line probe is scoped.
- Updated `docs/bepinex-bridge.md` and `packages/bepinex-plugin/DESIGN.md` to point at ADR 0008 and
  restate that current-line capture is not implemented.
- Extended `scripts/check_bepinex_bridge_safety.py` and bridge safety tests so ADR 0008 is required
  without treating the ADR as runtime source.
- Did not add C# behavior, game hooks, dialogue detection, Unity object scanning, OCR, extraction,
  decompiled game-code work, provider execution, frontend/shell work, keyboard hooks, clipboard
  writes, companion HTTP changes, downloads, web calls, or new dependencies.

Milestone 4D redacted manual runtime smoke report workflow is implemented.

Completed in the latest session:
- Added `docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md`, a safe report contract for
  summarizing user-local bridge runtime smoke results without committing raw logs, stack traces,
  payload dumps, screenshots, private paths, or real game content.
- Added `tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json`, a tiny committed
  synthetic `not_run` report fixture using only metadata booleans, warning counts, redacted notes,
  and `created_by_user_manually: true`.
- Added `scripts/check_bepinex_runtime_smoke_report.py`, a stdlib-only validator for the committed
  fixture and optional user-local reports under
  `workspace/synthetic-slice/bepinex-bridge/runtime-smoke/`.
- Added `scripts/write_bepinex_runtime_smoke_report.py`, a local template writer that creates a
  blank redacted report template under the ignored workspace report root without reading logs,
  private files, game data, or companion responses.
- Extended `scripts/check_bepinex_bridge_safety.py` so it requires the report docs, fixture, checker,
  and writer, validates the committed report fixture, and confirms report output remains under the
  ignored `workspace/` root.
- Added `tests/test_bepinex_runtime_smoke_report.py` and extended bridge safety tests for report
  shape, workspace-only paths, raw log markers, payload markers, stack traces, private paths,
  non-localhost URLs, hook/OCR/extraction/decompiled markers, and no real runtime report requirement.
- Updated `docs/manual-smoke/bepinex-bridge-runtime-smoke.md`, `docs/bepinex-bridge.md`,
  `packages/bepinex-plugin/README.md`, and `packages/bepinex-plugin/DESIGN.md` to link the redacted
  report workflow.
- The C# bridge source did not need changes; 4D does not alter runtime behavior or the companion HTTP
  contract.
- Did not add game hooks, dialogue detection, Unity object scanning, OCR, extraction, decompiled game
  code, provider execution, frontend/shell work, keyboard hooks, clipboard writes, companion HTTP
  changes, downloads, web calls, or new dependencies.

Milestone 4C BepInEx bridge manual runtime smoke and log contract is implemented.

Completed in the latest session:
- Added `docs/manual-smoke/bepinex-bridge-runtime-smoke.md`, a synthetic/manual checklist for local
  runtime verification.
- Added `docs/manual-smoke/bepinex-bridge-log-contract.md`, documenting allowed log metadata and
  forbidden log content.
- Added `tests/fixtures/bepinex_bridge.log_contract.synthetic.json`, a tiny machine-readable log
  contract fixture.
- Extended `scripts/check_bepinex_bridge_safety.py` so it requires the new manual smoke docs and log
  contract fixture, validates expected safe snippets against the C# bridge source, and keeps runtime
  report policy false for committed logs/reports.
- Extended `tests/test_bepinex_bridge_safety.py` for log contract shape, docs linkage, expected safe
  snippets, unavailable-companion non-fatal logging, no stack trace logging, no response body logging,
  and existing synthetic/manual safety posture.
- Updated `docs/bepinex-bridge.md`, `packages/bepinex-plugin/README.md`, and
  `packages/bepinex-plugin/DESIGN.md` to point to the manual smoke checklist and log contract.
- The C# bridge source did not need changes; current logs already match the metadata-only contract.
- Did not add game hooks, dialogue detection, Unity object scanning, OCR, extraction, decompiled game
  code, provider execution, frontend/shell work, keyboard hooks, clipboard writes, companion HTTP
  changes, downloads, web calls, or new dependencies.

Milestone 4B BepInEx bridge optional build and manual verification hardening is implemented.

Completed in the latest session:
- Added `scripts/build_bepinex_bridge.py`, a stdlib-only optional build helper for the 4A C# bridge.
- The helper detects `dotnet`, accepts explicit BepInEx IL2CPP reference DLL paths or established
  local env vars, skips cleanly when tooling or references are missing, and attempts `dotnet build`
  only when both references are supplied.
- Build reports use `schema_version: "bepinex-bridge-build-report.v1"` and include `dotnet_found`,
  `references_supplied`, `build_attempted`, `build_succeeded`, `warning_count`,
  `msb3277_warning_count`, `output_dll_path`, `skipped_reason`, and explicit no-download/no-game-file
  flags.
- Reports redact local reference paths and only write optional JSON under
  `workspace/synthetic-slice/bepinex-bridge/`.
- Formalized the 4B warning policy: `MSB3277` warnings are visible and counted, but do not fail a
  successful optional build by themselves.
- Extended `scripts/check_bepinex_bridge_safety.py` so it verifies ignored `bin/`, `obj/`, and
  `workspace/` roots, checks the optional build helper exists, rejects download/install markers, and
  confirms `check_all` does not require the build helper.
- Added `tests/test_bepinex_bridge_build.py` and extended bridge safety tests for skip behavior,
  command construction, warning parsing, path redaction, output path safety, build failure reporting,
  ignored output roots, no downloads, and no mandatory dotnet requirement.
- Updated `docs/bepinex-bridge.md` and `packages/bepinex-plugin/README.md` with optional build
  usage, `MSB3277` policy, and a synthetic/manual runtime verification checklist.
- Confirmed the default helper invocation skips cleanly when no local refs are visible in the current
  process environment, and an explicit local-ref invocation successfully builds the bridge with
  `33` warnings, all counted as `MSB3277`.
- Did not add game hooks, dialogue detection, Unity object scanning, OCR, extraction, decompiled game
  code, provider execution, frontend/shell work, keyboard hooks, clipboard writes, companion HTTP
  changes, downloads, web calls, or new dependencies.

Milestone 4A safe BepInEx bridge skeleton is implemented.

Completed in the latest session:
- Reused the existing `packages/bepinex-plugin/` scaffold instead of creating a second bridge
  package.
- Added a static-reviewable C# BepInEx IL2CPP plugin skeleton with plugin metadata, safe startup
  logging, BepInEx config bindings, a localhost-only companion client, `/health` check support, and
  manual/synthetic provider annotation send support.
- Added safe config defaults:
  - `Enabled = true`
  - `CompanionServerUrl = "http://127.0.0.1:8765"`
  - `RequestTimeoutMs = 3000`
  - `SendSyntheticEventOnStart = false`
- Added a built-in invented synthetic fake event and committed matching wrapper fixture:
  `tests/fixtures/bepinex_bridge.provider_annotate_request.synthetic.json`.
- The C# skeleton sends only `{ "input_type": "fake_event", "event": ... }` to the existing
  `/synthetic/provider-annotate` companion contract and logs only event id, line id, status, and
  availability metadata.
- Added `scripts/check_bepinex_bridge_safety.py`, a stdlib-only safety checker that validates the
  bridge fixture, localhost defaults, synthetic/manual posture, no secret-looking values, no
  external service URLs, no raw payload logging, and no hook/extraction/OCR markers in C# source.
- Added `tests/test_bepinex_bridge_safety.py` covering fixture shape/schema validity, safe defaults,
  localhost guard, manual project posture, no external/secrets/game-content markers, no hook
  side-effect markers, no raw payload logging, and `check_all` smoke registration.
- Added `python scripts/check_bepinex_bridge_safety.py --quiet` to `scripts/check_all.py`.
- Added `docs/bepinex-bridge.md` and updated the package README/DESIGN with manual build/install
  posture, unavailable-server behavior, synthetic send policy, and explicit non-goals.
- Added a minimal `.csproj` for later manual local builds using user-supplied BepInEx references.
  `dotnet build` is intentionally not required by `check_all` because this environment has no .NET
  SDK and the repo must not commit BepInEx/game binaries.
- Did not add game hooks, Unity object scanning, current dialogue detection, OCR, extraction,
  decompiled game code, provider execution, frontend/shell work, keyboard hooks, clipboard writes,
  companion HTTP changes, auth/TLS/persistence/CORS/database work, or new dependencies.
- Validation completed:
  - `python scripts/check_all.py` passed, including the new BepInEx bridge safety smoke and 287
    unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 287 tests.
  - `npm run check` passed.
  - `python scripts/check_bepinex_bridge_safety.py --quiet` passed.
  - `python -m unittest tests.test_bepinex_bridge_safety -v` passed with 11 tests.

Milestone 3K overlay shell readiness decision and 4A architecture handoff is implemented.

Completed in the latest session:
- Added `docs/adr/0007-overlay-shell-path.md`.
- ADR 0007 compares static review artifacts, a local browser page, companion-served local web page,
  Electron, Tauri, native overlay, and moving next to a BepInEx bridge skeleton.
- Accepted decision: defer Electron/Tauri/native always-on-top shell work and make Milestone 4A a
  synthetic/manual BepInEx bridge skeleton.
- Documented why: 3.x overlay contracts are stable enough for now, while current line/game-state
  capture is the largest remaining unknown.
- Added a Milestone 4A readiness checklist covering C# plugin skeleton, configurable localhost
  companion URL, `/health` check, manual/synthetic event send, safe logging, graceful unavailable
  server behavior, and no real extraction or proprietary content.
- Updated `docs/overlay-prototype.md` to state that the 3.x overlay contract phase is sufficiently
  complete for now and production shell work is deferred.
- Updated devlog handoff files with 3K risks, pending decisions, and the exact 4A prompt.
- Did not add BepInEx code, frontend framework work, JavaScript, Electron/Tauri/native shell,
  always-on-top behavior, keyboard hooks, clipboard writes, provider execution, OCR, extraction,
  companion HTTP changes, or real game content.
- Validation completed:
  - `python scripts/check_all.py` passed, including 276 unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 276 tests.
  - `npm run check` passed.
  - `python scripts/check_overlay_viewmodel_fixtures.py --quiet` passed.
  - `python scripts/check_overlay_state_source_fixtures.py --quiet` passed.
  - `python scripts/render_overlay_review.py --quiet` passed.
  - `python scripts/check_overlay_review_accessibility.py --quiet` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.

Milestone 3J overlay state-source regression fixtures and contract hardening is implemented.

Completed in the latest session:
- Added committed synthetic overlay state-source fixtures for ready compact, ready deep, ready debug,
  no-provider, stale, and error states.
- Added `scripts/check_overlay_state_source_fixtures.py`, a stdlib-only checker with `--quiet` and
  intentional `--write` regeneration.
- The checker rebuilds current state-source outputs from committed synthetic provider fixtures,
  validates state-source shape, safety-scans fixtures, compares canonical JSON, and checks ready
  fixture transition compatibility through the overlay state simulator.
- Added explicit additive no-side-effect aliases to state-source results:
  `provider_call_performed: false` and `companion_contract_changed: false`, while retaining the
  existing `calls_provider: false` and `companion_http_contract_changed: false`.
- Added `tests/test_overlay_state_source_fixtures.py` covering fixture validation, drift detection,
  deterministic regeneration through temporary fixture paths, status-specific shape, safety checks,
  no-provider/stale/error behavior, ready view-model validation, and transition compatibility.
- Added the state-source fixture regression smoke to `scripts/check_all.py`.
- Updated `docs/overlay-prototype.md` and devlog handoff files to document state-source fixtures as a
  future overlay shell handoff contract.
- Did not add real polling loops, timers, background workers, UI shell behavior, JavaScript,
  keyboard hooks, clipboard writes, always-on-top UI, provider execution, companion HTTP changes,
  BepInEx, OCR, extraction, web/API calls, or real game content.

Milestone 3I overlay polling/state-source contract is implemented.

Completed in the latest session:
- Added `scripts/overlay_state_source.py`, a stdlib-only state-source contract layer for turning
  latest companion provider state into a current overlay render state.
- The module exposes `OverlayStateSourceError`, `build_overlay_state_source(...)`,
  `build_overlay_state_from_client(...)`, `collect_overlay_state_source_errors(...)`, and
  `assert_valid_overlay_state_source(...)`.
- State-source results use `schema_version: "overlay-state-source.v1"` and model `ready`,
  `no_provider_state`, `stale`, and `error` statuses.
- Ready/stale states include the active mode, validated mode-specific overlay view model, visibility,
  available actions, deterministic stale threshold, line/update id, optional debug summary, and
  explicit no-side-effect flags.
- No-provider states are represented as valid state-source results rather than crashes. Partial
  provider state, malformed provider payloads, and companion client failures become clear error
  states.
- Stale state is deterministic through explicit `stale=True` or previous-state fallback. No real
  timers, polling loops, daemon threads, or background workers were added.
- Added `scripts/run_overlay_state_source.py`, a CLI with `--server-url`, `--mode`,
  `--self-test`, `--quiet`, and workspace-only `--output` under
  `workspace/synthetic-slice/overlay-prototype/state/`.
- The CLI self-test starts an in-process `127.0.0.1:0` companion server, posts the synthetic fixture
  through the existing provider endpoint, reads latest provider state through `CompanionClient`,
  builds the overlay state-source result, and shuts down cleanly.
- Added `tests/test_overlay_state_source.py` covering ready/no-provider/stale/error states,
  compact/deep/debug view-model validation, previous-state fallback, fake-client flows,
  self-test/CLI behavior, output path safety, transition simulator compatibility, and forbidden
  marker safety.
- Added `python scripts/run_overlay_state_source.py --self-test --quiet` to `scripts/check_all.py`.
- Updated `docs/overlay-prototype.md` and devlog handoff files to document state-source results as a
  future overlay-shell handoff contract, not a real polling loop.
- Did not add real polling loops, timers, background daemon work, JavaScript, frontend frameworks,
  keyboard hooks, clipboard writes, always-on-top UI, provider execution, companion HTTP changes,
  BepInEx, OCR, extraction, web/API calls, or real game content.
- Validation completed:
  - `python scripts/check_all.py` passed, including the new overlay state source smoke and 263 unit
    tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 263 tests.
  - `npm run check` passed.
  - `python scripts/check_overlay_viewmodel_fixtures.py --quiet` passed.
  - `python scripts/render_overlay_review.py --quiet` passed.
  - `python scripts/check_overlay_review_accessibility.py --quiet` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.
  - `python scripts/run_overlay_state_simulator.py --fixture compact --action switch_deep --quiet`
    passed.
  - `python scripts/run_overlay_state_source.py --self-test --quiet` passed.

Milestone 3H declarative overlay action/state transition simulator is implemented.

Completed in the latest session:
- Added `scripts/overlay_state_simulator.py`, a stdlib-only simulator that consumes validated
  compact/deep/debug overlay view models and returns JSON-safe transition previews.
- The simulator exposes `simulate_overlay_action(...)`, `collect_overlay_transition_errors(...)`,
  `assert_valid_overlay_transition(...)`, and `OverlayStateSimulatorError`.
- Transition previews include source mode, action id, Ukrainian action label/hint, allowed/blocked
  status, stable blocked reason, next mode, next visibility, side-effect preview type, optional copy
  preview text, Ukrainian summary, and explicit no-side-effect flags.
- Implemented deterministic previews for mode switching, original/translation/annotation visibility
  toggles, next/previous annotation navigation, copy previews, and hide previews.
- Copy actions return preview text only and never write to the clipboard. Hide actions only set
  `hidden = true` in preview visibility. Navigation actions do not mutate an index.
- Unknown actions, actions absent from the current view model, debug-only actions in player modes,
  malformed view models, invalid visibility state, and unavailable copy sources fail or block
  clearly.
- Transition previews are safety-scanned for `context_packet.game.title`, raw prompt/provider payload
  markers, secrets, private paths, future provider markers, generated HTML markers, external URLs,
  JavaScript markers, and hook/shortcut-looking fields.
- Added `scripts/run_overlay_state_simulator.py`, a fixture-based CLI with `--fixture`,
  `--action`, `--quiet`, and workspace-only `--output` support under
  `workspace/synthetic-slice/overlay-prototype/transitions/`.
- Added `tests/test_overlay_state_simulator.py` covering switch/toggle/navigation/copy/hide
  previews, blocked debug/player actions, unknown and absent actions, malformed visibility, no input
  mutation, safety failures, CLI behavior, and output path safety.
- Added the simulator smoke to `scripts/check_all.py`.
- Updated `docs/overlay-prototype.md` and devlog handoff files to document transition previews as
  declarative/no-side-effect state contracts.
- Did not add keyboard hooks, global hotkeys, clipboard writes, JavaScript, browser shell,
  always-on-top UI, production overlay behavior, companion HTTP changes, provider execution,
  BepInEx, OCR, extraction, or real game content.
- Validation completed:
  - Initial `python scripts/check_all.py` reached functional completion but failed Ruff format-check
    for the two new Python files.
  - `ruff format scripts/overlay_state_simulator.py tests/test_overlay_state_simulator.py` was run.
  - `python scripts/check_all.py` passed, including 246 unit tests and the new overlay state
    transition simulator smoke.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 246 tests.
  - `npm run check` passed.
  - `python scripts/check_overlay_viewmodel_fixtures.py --quiet` passed.
  - `python scripts/render_overlay_review.py --quiet` passed.
  - `python scripts/check_overlay_review_accessibility.py --quiet` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.

Milestone 3G overlay static readability and accessibility review checks are implemented.

Completed in the latest session:
- Added `scripts/check_overlay_review_accessibility.py`, a stdlib-only checker for
  fixture-rendered compact, deep, and debug overlay HTML.
- The checker loads validated committed overlay view-model fixtures, renders HTML in memory with the
  existing overlay renderer, and inspects the result with Python stdlib `html.parser`.
- Added structural checks for `lang="uk"`, nonempty title, exactly one nonempty `h1`, expected
  mode section ids, and sane heading flow.
- Added readability checks for compact brevity, player-facing action hints, deep grouped Ukrainian
  headings, and debug metadata presence.
- Added safety checks so compact/deep still hide raw internal flags and all modes reject rendered
  `context_packet.game.title`, raw prompt/provider payload markers, secrets, private paths, future
  provider markers, external URLs, JavaScript URLs, event-handler attributes, and unescaped script
  tags.
- Escaped unsafe text such as `&lt;script&gt;...&lt;/script&gt;` remains allowed.
- Added `tests/test_overlay_review_accessibility.py` covering passing compact/deep/debug HTML,
  missing language metadata, missing title/h1, heading disorder, raw flags, excessive compact text,
  game-title leakage, escaped unsafe text, unescaped script tags, event-handler attributes, and CLI
  quiet mode.
- Added the checker smoke to `scripts/check_all.py`.
- Updated `docs/overlay-prototype.md` and devlog handoff files to document that these are structural
  readability/accessibility guardrails, not a browser audit or WCAG certification.
- Did not add browser automation, JavaScript, frontend framework work, production overlay behavior,
  keyboard hooks, companion HTTP changes, provider execution, BepInEx, OCR, extraction, or real game
  content.

Milestone 3F overlay interaction state and action contract is implemented.

Completed in the latest session:
- Added `scripts/overlay_actions.py`, a stdlib-only declarative action catalog for overlay view
  models.
- Added mode-specific `visibility` state and `actions` lists inside compact, deep, and debug payloads
  while preserving the existing top-level mode-specific fixture shape.
- Compact/deep view models now expose only player-facing Ukrainian action labels and hints; debug mode
  exposes the full declarative action catalog for developer inspection.
- Visibility defaults are now explicit:
  - compact shows original and Ukrainian summary, hides annotations and debug.
  - deep shows original, Ukrainian rendering, and annotations, hides debug.
  - debug shows original, translation, annotations, and debug metadata.
- Extended `scripts/overlay_viewmodel_validator.py` so fixtures must use known action ids, canonical
  Ukrainian labels/hints, valid allowed modes, correct player/debug flags, and no key-binding fields.
- The validator now rejects `debug_visible = true` in compact/deep modes and rejects debug-only
  actions in player-facing modes.
- Updated `scripts/local_overlay_prototype.py` so compact/deep review HTML renders Ukrainian action
  hints and debug review HTML renders action metadata safely.
- Regenerated the three committed overlay view-model JSON fixtures intentionally with
  `python scripts/check_overlay_viewmodel_fixtures.py --write`.
- Updated overlay prototype, validator, fixture, and review-renderer tests for visibility state,
  action ids, Ukrainian labels/hints, debug-only separation, no key-binding fields, escaping, and
  existing player/debug safety rules.
- Updated `docs/overlay-prototype.md` and devlog handoff files with the declarative-only action
  contract and the next Milestone 3G prompt.
- Did not add keyboard hooks, global shortcuts, clipboard behavior, always-on-top windows, JavaScript,
  frontend frameworks, companion HTTP changes, provider calls, BepInEx, OCR, extraction, or real game
  content.
- Validation completed:
  - `python scripts/check_all.py` passed, including 211 unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 211 tests.
  - `npm run check` passed.
  - `python scripts/check_overlay_viewmodel_fixtures.py --quiet` passed.
  - `python scripts/render_overlay_review.py --quiet` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.

Milestone 3E overlay view-model schema and contract hardening is implemented.

Completed in the latest session:
- Added `scripts/overlay_viewmodel_validator.py`, a stdlib-only contract validator for compact, deep, and debug overlay view models.
- The validator exposes `collect_overlay_viewmodel_errors(...)` and `assert_valid_overlay_view_model(...)` plus `OverlayViewModelValidationError`.
- Common view-model fields are now validated for `schema_version`, `mode`, `source.original_english`, `source.speaker`, `source.scene_id`, `source.conversation_id`, and optional `source.line_id`.
- Compact, deep, and debug mode payloads now have explicit required field/type checks based on the committed fixture contract.
- Player-facing compact/deep validation rejects raw internal flags, provider debug fields, raw prompt/debug payload markers, generated HTML, future provider markers, secrets, private absolute paths, English provider policy notes, and `context_packet.game.title`.
- Debug validation allows raw flags and provider evidence but rejects secrets, raw full prompt markers, private paths, future provider markers, generated HTML, and `context_packet.game.title`.
- Updated `scripts/check_overlay_viewmodel_fixtures.py` so freshly generated view models and committed fixtures both pass through the new contract validator before drift comparison.
- Updated `scripts/render_overlay_review.py` so review HTML refuses invalid fixtures before rendering.
- Added `tests/test_overlay_viewmodel_validator.py` covering valid fixtures, missing required fields, wrong mode, raw player flags, `provider_debug` in deep mode, debug secret/private paths, game-title leakage, generated HTML markers, and fixture-checker error surfacing.
- Updated `docs/overlay-prototype.md` to document the Python validator plus committed JSON fixtures as the current overlay view-model contract.
- Did not add JSON Schema files or dependencies, change schemas, change companion HTTP contracts, call providers, add frontend framework work, or touch real game content.
- Validation completed:
  - `python scripts/check_all.py` passed, including 204 unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 204 tests.
  - `npm run check` passed.
  - `python scripts/check_overlay_viewmodel_fixtures.py --quiet` passed.
  - `python scripts/render_overlay_review.py --quiet` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.

Milestone 3D overlay prototype HTML snapshot review workflow is implemented.

Completed in the latest session:
- Added `scripts/render_overlay_review.py`, a stdlib-only fixture-backed renderer for local overlay review HTML.
- The renderer loads only the committed overlay view-model fixtures and renders them with the existing `render_overlay_html()` helper.
- Default generated outputs are written under ignored `workspace/synthetic-slice/overlay-prototype/review/`:
  - `compact.html`
  - `deep.html`
  - `debug.html`
  - `index.html`
- The renderer supports `--output-root`, `--mode all|compact|deep|debug`, and `--quiet`.
- Unsafe output roots outside `workspace/synthetic-slice/overlay-prototype/review/` are rejected.
- Added HTML safety validation so compact/deep review pages hide raw internal flags and debug review pages remain redacted while still exposing developer metadata.
- Added `tests/test_overlay_review_renderer.py` covering fixture loading, HTML generation, index generation, output path safety, player/debug separation, escaping, game-title exclusion, and no generated HTML under `tests/fixtures`.
- Added `python scripts/render_overlay_review.py --quiet` to `scripts/check_all.py`.
- Updated `docs/overlay-prototype.md` with the manual review command and generated artifact policy.
- Did not change schemas, companion HTTP contracts, provider execution behavior, frontend stack, extraction, BepInEx, OCR, real provider calls, web/API/LLM calls, or production overlay behavior.
- Validation completed:
  - `python scripts/check_all.py` passed, including the new overlay review HTML render smoke and 194 unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 194 tests.
  - `npm run check` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.
  - `python scripts/check_overlay_viewmodel_fixtures.py --quiet` passed.
  - `python scripts/render_overlay_review.py --quiet` passed.

Milestone 3C overlay view-model fixture regression pack is implemented.

Completed in the latest session:
- Updated `scripts/local_overlay_prototype.py` so `build_overlay_view_model(..., mode=...)` returns a mode-specific payload instead of carrying compact, deep, and debug sections together.
- Compact view models now contain only `schema_version`, `mode`, `source`, and `compact`; deep view models contain only `schema_version`, `mode`, `source`, and `deep`; debug view models contain only `schema_version`, `mode`, `source`, and `debug`.
- Added committed synthetic view-model fixtures:
  - `tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json`
  - `tests/fixtures/overlay_prototype.deep.viewmodel.synthetic.json`
  - `tests/fixtures/overlay_prototype.debug.viewmodel.synthetic.json`
- Added `scripts/check_overlay_viewmodel_fixtures.py`, a stdlib-only regression checker with `--quiet` for checks and `--write` for intentional fixture regeneration.
- The fixture checker rebuilds current compact/deep/debug view models from the synthetic fake event -> context packet -> mock provider annotation flow and compares canonical JSON against the committed fixtures.
- The fixture checker rejects raw prompts, generated HTML, private absolute paths, secrets, future provider markers, and `context_packet.game.title` in overlay fixtures.
- Added `tests/test_overlay_viewmodel_fixtures.py` covering compact raw-flag hiding, Ukrainian player labels, deep Ukrainian section structure, debug metadata, forbidden marker safety, renderer escaping, and drift detection.
- Updated `tests/test_local_overlay_prototype.py` for the mode-specific view-model shape.
- Added `python scripts/check_overlay_viewmodel_fixtures.py --quiet` to `scripts/check_all.py`.
- Updated `docs/overlay-prototype.md` to document view-model fixtures as the current overlay UX contract and generated HTML as uncommitted local output.
- Did not change schemas, companion HTTP contracts, provider execution behavior, frontend stack, extraction, BepInEx, OCR, real provider calls, web/API/LLM calls, or production overlay behavior.
- Validation completed:
  - `python scripts/check_all.py` passed, including the new overlay view-model fixture regression and 184 unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 184 tests.
  - `npm run check` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.
  - `python scripts/check_overlay_viewmodel_fixtures.py --quiet` passed.

Milestone 3B overlay UX polish and player/debug separation is implemented.

Completed in the latest session:
- Updated `scripts/local_overlay_prototype.py` so compact and deep modes render player-facing Ukrainian labels and summaries instead of raw internal flags or Python-looking booleans.
- Compact mode now hides raw flags such as `synthetic_fixture`, `mock_provider`, and `prompt_pack_guided`, converts confidence into Ukrainian text, and renders deeper-note availability as `Є глибше пояснення`.
- Deep mode now uses Ukrainian section headings:
  - `Оригінал`
  - `Літературний український варіант`
  - `Що тут відбувається`
  - `Підтекст / іронія / референс`
  - `Тон / голос`
  - `Глосарій`
  - `Ризики / невпевненість`
- English provider/policy notes are suppressed from compact/deep modes and exposed only in debug mode; deterministic Ukrainian fallback text is used for player-facing note groups when the mock provider note text is English/debug-like.
- Debug mode now explicitly carries raw risk flags and raw deep notes while keeping provider metadata, prompt-pack metadata, and privacy/cache dry-run summary redacted.
- Confirmed `context_packet.game.title` is not rendered in compact, deep, or debug HTML.
- Updated `tests/test_local_overlay_prototype.py` to cover raw-flag hiding, Ukrainian player labels, Ukrainian deep grouping, English policy-note suppression, debug raw metadata, escaping, and game-title exclusion.
- Updated `docs/overlay-prototype.md` with the player/debug separation policy.
- Did not change schemas, companion server/client HTTP contracts, provider pipeline output, frontend stack, extraction, BepInEx, OCR, real provider calls, web/API/LLM calls, or production overlay behavior.
- Validation completed:
  - `python scripts/check_all.py` passed, including the local overlay prototype smoke and 177 unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 177 tests.
  - `npm run check` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.

Milestone 3A local overlay prototype consuming the companion server is implemented.

Completed in the latest session:
- Added `scripts/local_overlay_prototype.py`, a stdlib-only overlay view-model and static HTML renderer for provider-backed synthetic annotations.
- The view model exposes compact, deep, and debug sections with original English, Ukrainian concise/literary fields, explanation, notes, glossary, confidence, risk flags, provider metadata, prompt-pack metadata, and a safe provider privacy/cache dry-run summary.
- Added `scripts/run_local_overlay_prototype.py` with `--server-url`, `--mode compact|deep|debug`, `--post-synthetic-event`, `--event`, `--output`, `--json-output`, `--quiet`, and `--self-test`.
- The CLI consumes the existing companion client and `POST /synthetic/provider-annotate`; it does not change the companion HTTP contract.
- `--self-test` starts an in-process `127.0.0.1:0` companion server, posts the synthetic fixture through the provider endpoint, renders an overlay prototype, and shuts down cleanly.
- Generated overlay HTML/JSON is allowed only under ignored `workspace/synthetic-slice/overlay-prototype/`; unsafe output paths are rejected.
- Added `docs/overlay-prototype.md` documenting the local/static/non-production overlay posture.
- Added `tests/test_local_overlay_prototype.py` covering view-model shape, compact/deep/debug rendering, escaping, safe debug metadata, workspace-only outputs, and the CLI self-test.
- Added `python scripts/run_local_overlay_prototype.py --self-test --quiet` to `scripts/check_all.py`.
- Did not add frontend frameworks, production overlay behavior, game integration, BepInEx, OCR, extraction, web/API/LLM/provider calls, raw provider cache writes, or companion HTTP contract changes.
- Validation completed:
  - `python scripts/check_all.py` passed, including the local overlay prototype smoke and 177 unit tests.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 177 tests.
  - `npm run check` passed.
  - `python scripts/run_provider_contract_regression.py --quiet` passed.
  - `python scripts/run_provider_preflight.py --quiet` passed.
  - `python scripts/run_provider_privacy_check.py --quiet` passed.
  - `python scripts/run_local_overlay_prototype.py --self-test --quiet` passed.
  - `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Milestone 2I provider request privacy envelope and cache write dry-run is implemented.

Completed in the latest session:
- Added `scripts/provider_privacy.py`, a stdlib-only privacy/cache planning layer for existing synthetic `ProviderRequest` objects.
- Added deterministic cache keys using SHA-256 over canonical request metadata, text lengths, and text digests without exposing raw source text or full prompt text in printed summaries.
- Added redacted provider privacy envelopes with provider id/mode, prompt pack id/version, context and line ids, synthetic/mock flags, request field presence, text metadata, redacted config summary, cache root, and dry-run cache write plan.
- Added cache write dry-run plans under `workspace/provider-cache/<provider>/<pack>/<cache_key>.json` with `dry_run = true`, `would_write = false`, and `writes_raw_payload = false`.
- Added `scripts/run_provider_privacy_check.py`, defaulting to the synthetic fixture and writing redacted summaries only under ignored `workspace/synthetic-slice/provider-privacy/`.
- Added privacy availability fields to provider preflight plans without changing preflight pass/block behavior.
- Added `docs/provider-privacy-cache-policy.md` documenting what may be logged, what must never be logged, cache key computation, and why raw payload persistence remains deferred.
- Added `tests/test_provider_privacy.py` covering raw text/prompt omission, cache key stability, cache dry-run safety, redaction, blocked future providers, output path safety, fixture metadata isolation, and CLI behavior.
- Added `python scripts/run_provider_privacy_check.py --quiet` to `scripts/check_all.py`.
- Did not change schemas, fixtures, companion server/client HTTP contract, provider execution behavior, or add dependencies.
- Validation completed after formatting the new privacy files:
  - `python scripts/check_all.py` passed, including 165 unit tests, provider preflight smoke, provider privacy smoke, provider contract regression smoke, companion smokes, Ruff check, and Ruff format check.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 165 tests.
  - `npm run check` passed.
  - `python scripts/run_provider_contract_regression.py --quiet` passed.
  - `python scripts/run_provider_preflight.py --quiet` passed.
  - `python scripts/run_provider_privacy_check.py --quiet` passed.
  - `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Milestone 2H provider runtime safety preflight is implemented.

Completed in the latest session:
- Added `scripts/provider_runtime_safety.py`, a stdlib-only dry-run safety layer for future provider execution.
- The preflight builds a redacted provider execution plan with active provider, enabled/implemented state, provider mode, network/secrets/runtime flags, cache-root privacy status, prompt pack id/version, warnings, and blocked reasons.
- `mock` preflight passes with `workspace/provider-cache`, `dry_run = true`, `calls_external_services = false`, no network, no secrets, and no local runtime requirement.
- Future provider ids produce blocked plans before any provider adapter, network, paid API, DeepL, or local runtime path can run.
- Added deterministic redaction for secret-like keys, secret-like values, and absolute/private-looking paths in summaries.
- Added `scripts/run_provider_preflight.py`, defaulting to `config/revachol.example.toml`, printing JSON by default, supporting `--quiet`, and writing only under ignored `workspace/synthetic-slice/provider-preflight/`.
- Added `docs/provider-runtime-safety.md` documenting cache-root policy, redacted summaries, mock default, future-provider opt-in, and offline tests.
- Added `tests/test_provider_runtime_safety.py` covering mock pass, unknown/disabled/unimplemented future provider blocking, external opt-in blocking, cache-root safety, output-path safety, redaction, fixture metadata isolation, and CLI behavior.
- Added `python scripts/run_provider_preflight.py --quiet` to `scripts/check_all.py`.
- Did not change schemas, fixtures, companion server/client HTTP contract, provider execution behavior, or add dependencies.
- Validation completed after formatting the new safety module:
  - `python scripts/check_all.py` passed, including 149 unit tests, provider preflight smoke, provider registry smoke, provider contract regression smoke, companion smokes, Ruff check, and Ruff format check.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 149 tests.
  - `npm run check` passed.
  - `python scripts/run_provider_contract_regression.py --quiet` passed.
  - `python scripts/run_provider_preflight.py --quiet` passed.
  - `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Milestone 2G provider registry and runtime safety gates is implemented.

Completed in the latest session:
- Added `scripts/provider_registry.py`, a stdlib-only registry for provider ids:
  - `mock`
  - `openai_compatible`
  - `deepl_glossary`
  - `local_model`
  - `ensemble_reviewer`
- The only implemented/enabled/default provider is `mock`; all roadmap providers are disabled and unimplemented.
- Added `scripts/run_provider_registry.py --summary` for local registry inspection without provider calls, secrets, network, or runtime adapters.
- Routed `scripts/provider_pipeline.py` provider selection through the registry so unknown, disabled, external-disallowed, and unimplemented providers fail before any adapter can run.
- Removed the redundant future-role list from internal mock provider metadata; public annotation-card metadata and provider contract fixtures remain mock-only.
- Updated `scripts/run_provider_pipeline.py --provider` so registry ids can be passed and disabled roadmap providers fail through runtime safety gates rather than argparse-only choices.
- Updated `config/revachol.example.toml` with explicit mock-only provider settings:
  - `active_provider = "mock"`
  - `allow_external_providers = false`
  - `provider_cache_dir = "workspace/provider-cache"`
  - disabled `[llm.providers.<id>]` roadmap placeholders without inline keys, fake secrets, base URLs, or required env vars.
- Hardened `scripts/validate_config.py` to validate registry ids, active provider selectability, external-provider opt-in, provider cache path safety, and secret-looking inline values.
- Added provider registry, provider pipeline, and config validation tests covering disabled/unimplemented providers, unknown providers, external opt-in, unsafe cache paths, inline secrets, and no fallback to real providers.
- Added the provider registry smoke to `scripts/check_all.py`.
- Updated `docs/api/companion-server-contract.md` to clarify that the HTTP provider endpoint remains mock-only and registry roadmap ids are not part of current runtime responses.
- Did not change schemas, fixtures, companion server endpoints, companion client APIs, or add dependencies.
- Validation completed after formatting the new registry test file:
  - `python scripts/check_all.py` passed, including 132 unit tests, provider registry smoke, provider contract regression smoke, companion smokes, Ruff check, and Ruff format check.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 132 tests.
  - `npm run check` passed.
  - `python scripts/run_provider_contract_regression.py --quiet` passed.
  - `python scripts/run_companion_server.py --smoke-test` passed.
  - `python scripts/run_companion_client.py smoke-test` passed.
  - `python scripts/run_prompt_pack.py --summary` passed.
  - `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Milestone 2F provider contract regression runner and local review handoff is implemented.

Completed in the latest session:
- Added `scripts/run_provider_contract_regression.py`, a stdlib-only runner that starts an in-process `127.0.0.1` companion server on an ephemeral port and shuts it down cleanly.
- The runner posts the raw Milestone 2E request fixtures to `POST /synthetic/provider-annotate`:
  - `tests/fixtures/provider_annotate.fake_event_request.synthetic.json`
  - `tests/fixtures/provider_annotate.context_packet_request.synthetic.json`
- The runner validates the companion envelope, nested `context_packet`, and nested `annotation_card` payloads against the existing schemas.
- The runner compares stable deterministic fields against `tests/fixtures/provider_annotate.success_response.synthetic.json`, including context identity/current-line data, provider metadata, prompt pack metadata, provider debug metadata, risk flags, and English source/original preservation.
- Added optional local handoff artifacts under ignored `workspace/synthetic-slice/provider-contract/`:
  - JSON summary via `--output`
  - Markdown summary via `--markdown`
  - escaped review HTML via `--write-review-html`
- Unsafe output paths outside `workspace/synthetic-slice/provider-contract/` are rejected.
- Added `tests/test_provider_contract_regression.py` covering passing fixtures, both request shapes, stable metadata drift, schema failure reporting, safe/unsafe output paths, review HTML writing, deterministic Markdown, no forbidden markers, and clean localhost-only operation.
- Added `python scripts/run_provider_contract_regression.py --quiet` to `scripts/check_all.py`.
- Updated `docs/api/companion-server-contract.md` to document the regression runner and fixture update expectations.
- Did not change schemas, fixtures, companion server endpoints, companion client APIs, provider pipeline behavior, or add dependencies.

Milestone 2E provider contract fixtures and schema hardening is implemented.

Completed in the latest session:
- Added committed synthetic provider contract fixtures:
  - `tests/fixtures/provider_annotate.fake_event_request.synthetic.json`
  - `tests/fixtures/provider_annotate.context_packet_request.synthetic.json`
  - `tests/fixtures/provider_annotate.success_response.synthetic.json`
- The fixture pair uses one invented synthetic line consistently across fake-event input, context-packet input, and success response.
- The success fixture validates as the standard companion envelope with nested `context_packet` and `annotation_card` payloads.
- Made `provider`, `provider_debug`, and `prompt_pack` explicit optional properties in `specs/annotation-card.schema.json`.
- Kept the schema additive and permissive: no new top-level required fields and no `additionalProperties: false`.
- Removed `future_roles` from public annotation-card provider metadata so committed server/fixture responses do not contain future external-service markers.
- Kept internal provider metadata capable of describing future roles, but public normalized annotation cards now expose only current mock provider posture.
- Added fixture/contract tests proving the fake-event and context-packet request fixtures are accepted by the server and match the committed success response.
- Added drift tests proving the client unwraps the provider response shape, provider metadata is present, `prompt_pack_guided` is present, and unwrapped provider payloads are rejected.
- Added fixture safety checks for URLs, private paths, API-key markers, future external-service markers, and real game title leakage outside schema-required context-packet `game.title`.
- Extended `scripts/validate_schemas.py` so provider contract fixtures are validated by the normal schema validation path and therefore by `check_all`.
- Updated `docs/api/companion-server-contract.md` to document the new fixtures and provider metadata as explicit optional schema fields.
- Resolved the previous pending decision about whether provider metadata should remain permissive-only: it is now explicit optional schema metadata.
- Did not add dependencies, change endpoint shapes, call providers, or use real game dialogue/assets/extracted data.

Milestone 2D companion provider annotation endpoint is implemented.

Completed in the latest session:
- Exposed the prompt-pack-aware deterministic mock provider pipeline through the companion server.
- Added `POST /synthetic/provider-annotate` with explicit wrapper inputs:
  - `{ "input_type": "fake_event", "event": { ... } }`
  - `{ "input_type": "context_packet", "context_packet": { ... } }`
- The provider endpoint does not guess when `input_type` is missing or unknown; it returns `400 invalid_request`.
- Fake-event input is validated and converted with existing synthetic slice helpers before provider annotation.
- Context-packet input is validated against `specs/context-packet.schema.json` before provider annotation.
- Provider annotation returns the existing success envelope with `context_packet` and prompt-pack-aware `annotation_card`.
- Added in-memory latest provider state:
  - `GET /state/latest-provider-context`
  - `GET /state/latest-provider-annotation`
- Added companion client methods and CLI commands for provider annotation and latest provider state.
- Updated `docs/api/companion-server-contract.md` with the new endpoint, accepted request shapes, latest state endpoints, synthetic examples, and deterministic mock-provider policy.
- Extended companion server/client tests for valid fake-event and context-packet provider annotation, missing/unknown `input_type`, missing payloads, invalid fake events, invalid context packets, latest provider state, client methods, and CLI commands.
- Extended the companion client smoke test so `scripts/check_all.py` exercises provider annotation without leaving a long-running server.
- Kept `/synthetic/event`, `/synthetic/eval`, and `/review/latest.html` behavior unchanged.
- Did not change schemas, provider pipeline internals, prompt pack text, config, stable error code names, or add dependencies.

Milestone 2C remains in place:
- Extended provider requests with explicit prompt-pack policy wiring:
  - player-facing language default: `uk`
  - internal guidance language marker: `english_allowed_for_provider_guidance`
  - focused policy refs/sections for spoiler discipline, anti-hallucination, anti-overlocalization, and Russianism/calque avoidance.
- Updated the deterministic mock provider so output includes prompt-pack-guided risk/debug metadata:
  - `synthetic_fixture`
  - `mock_provider`
  - `deterministic_mock_provider`
  - `needs_human_review_before_real_use`
  - `prompt_pack_guided`
- Added provider/debug metadata to normalized annotation cards through permissive additional fields:
  - `provider`
  - `provider_debug`
  - `prompt_pack`
- Hardened provider normalization so it still preserves original English from the context packet, rejects line ID mismatches, requires `provider_debug`, requires focused policy keys, and rejects missing required mock risk flags.
- Switched the synthetic eval harness to run fake event -> context packet -> provider pipeline -> annotation card -> overlay demo -> review HTML.
- Added structural eval score keys for prompt-pack metadata, required output fields, quality priorities, policy coverage, and provider debug coverage.
- Updated the static review renderer debug section to show escaped provider name/role, prompt pack id/version, player-facing language default, and policy note keys.
- Added tests for provider request policy fields, mock provider metadata, normalized prompt-pack metadata, provider debug failure modes, provider-backed eval policy coverage, score degradation when metadata is removed, and review debug rendering.
- Kept companion server/client provider endpoints deferred to Milestone 2D.
- Did not change schemas, prompt pack text, config, companion server endpoints, or add dependencies.

Milestone 2B remains in place:
- Added `prompts/packs/ukrainian_annotation_v1/`, a versioned synthetic-only prompt/style pack.
- Added pack files for system/developer guidance, output contract, style guide, glossary policy, uncertainty policy, spoiler policy, anti-hallucination, anti-overlocalization, Russianism avoidance, and synthetic examples.
- Revised `synthetic_examples.md` into ten richer synthetic quality references covering bureaucratic irony, institutional metaphor, deadpan official voice, idiom/subtext, reference-like phrasing, sarcasm, uncertainty, spoiler safety, Russianism/calque avoidance, and explicit-only Ukrainian cultural adaptation proposals.
- Each numbered synthetic example now carries the same review structure: source, difficulty, bad rendering, concise Ukrainian meaning, literary Ukrainian rendering, deep annotation, tone/voice note, risk flags, and why the improved version is better.
- Added a reviewer checklist for meaning preservation, Ukrainian naturalness, tone, idioms/jokes, uncertainty, spoiler budget, over-localization, and clearly marked cultural proposals.
- Added prompt-pack tests that enforce the numbered example structure, non-empty field bodies, and Ukrainian script in concise/literary Ukrainian fields so shallow rewrites fail loudly.
- Confirmed developer policy that internal provider guidance may be English, but player-facing annotation fields default to Ukrainian unless debug or developer mode is explicitly enabled.
- Added `pack.json` with prompt pack metadata, required output fields, quality priorities, policy file references, synthetic examples reference, and provider pipeline compatibility notes.
- Added `scripts/prompt_pack.py`, a stdlib-only deterministic prompt pack loader with clear `PromptPackError` failures for missing files and malformed metadata.
- Added `scripts/run_prompt_pack.py --summary` for local metadata inspection without provider calls.
- Updated provider requests to include `prompt_pack_id`, `prompt_pack_version`, `prompt_pack_policy_refs`, and `prompt_pack_sections`.
- Provider requests now source required output fields and quality priorities from the loaded prompt pack while keeping mock annotation output deterministic.
- Added tests for prompt pack metadata, markdown loading, missing/malformed pack failures, deterministic loading, synthetic-only safety, CLI summary, and provider request compatibility.
- Integrated a prompt pack smoke command into `scripts/check_all.py`.
- Did not change schemas, config, companion server endpoints, or add dependencies.

Milestone 2A remains in place:
- Added `scripts/provider_pipeline.py`, a stdlib-only provider/prompt scaffold with dataclass request/response/metadata shapes.
- Added deterministic mock provider support only; no real LLM, paid API, DeepL, web, or local model runtime calls exist.
- Added provider request creation from validated context packets, including original text, speaker, scene/conversation metadata, nearby context, spoiler budget, glossary hints, requested output fields, quality priorities, and safety rules.
- Added provider response normalization into schema-valid annotation cards while preserving the English original from the context packet.
- Added clear `ProviderPipelineError` failures for malformed provider output and line ID mismatch.
- Added `scripts/run_provider_pipeline.py` with default synthetic fixture input, optional context packet input, `--provider mock`, workspace-only output, and unsafe path rejection.
- Added provider pipeline tests for request shape, deterministic mock response, annotation-card validation, original preservation, malformed output failures, no private/network/API-key markers, CLI success, and unsafe output rejection.
- Integrated a provider pipeline smoke command into `scripts/check_all.py`.
- Left companion server/client provider endpoints out of Milestone 2A; server exposure should happen after one stable provider CLI/test cycle.
- Did not change schemas, config, or add dependencies.

Milestone 1E remains in place:
- Added `scripts/companion_client.py`, a tiny stdlib-only local contract helper for the companion server.
- Added `scripts/run_companion_client.py` with commands for health, synthetic event posting, latest state reads, review HTML, synthetic eval, and a clean in-process `smoke-test`.
- Hardened server error codes into a small stable set:
  - `not_found`
  - `invalid_json`
  - `invalid_request`
  - `invalid_fake_event`
  - `method_not_allowed`
  - `internal_error`
- Kept the envelope contract unchanged:
  - success: `{"ok": true, "data": ...}`
  - error: `{"ok": false, "error": {"code": "...", "message": "..."}}`
- Kept `latest-review-html` as raw escaped HTML, not JSON.
- Added `docs/api/companion-server-contract.md` with synthetic-only endpoint and envelope examples.
- Added client tests for health, event posting, latest context/annotation/overlay, synthetic eval, raw review HTML, server error envelopes, unavailable server handling, invalid JSON responses, CLI smoke, and synthetic-only contract docs.
- Added server tests for stable error codes and method-not-allowed behavior.
- Integrated `python scripts/run_companion_client.py smoke-test` into `scripts/check_all.py`.
- Did not add dependencies or use real game data, BepInEx, OCR, extraction, web calls, paid APIs, LLM calls, frontend frameworks, auth, TLS, persistence, or CORS work.

Milestone 1D remains in place:
- Added `scripts/companion_server.py`, a stdlib-only `http.server` companion skeleton with in-memory state.
- Added `scripts/run_companion_server.py` with default `--host 127.0.0.1`, default `--port 8765`, and `--smoke-test`.
- Added local JSON endpoints using a consistent envelope:
  - success: `{"ok": true, "data": ...}`
  - error: `{"ok": false, "error": {"code": "...", "message": "..."}}`
- Implemented `GET /health`, latest context/annotation/overlay/eval state endpoints, `POST /synthetic/event`, `POST /synthetic/eval`, and `GET /review/latest.html`.
- Kept `/review/latest.html` generated from the existing escaped static review renderer; before an event exists it returns a `409 invalid_request` JSON error envelope.
- Added endpoint tests for health, valid synthetic event ingestion, invalid JSON, invalid fake event validation, latest state, synthetic eval, review HTML, missing-review errors, unknown routes, and localhost-only test binding.
- Integrated a clean companion server smoke test into `scripts/check_all.py` without leaving a long-running process.
- Did not change schemas or add dependencies.
- Did not rename the repository path. `revachol-ukro-elisium` matches the actual directory; naming cleanup remains a future decision.

Milestone 1D server posture:
- Local/offline/mock-only for now.
- Binds to `127.0.0.1` by default.
- Uses in-memory state only; restarting the server loses latest context/annotation/eval state.
- Is not production security hardened: no auth, TLS, persistence, rate limiting, CORS policy, or multi-client session model yet.
- Future paid API, web retrieval, local extraction, and provider-backed annotation support must remain opt-in and must keep caches/private data under ignored local paths.

Milestone 1C remains in place:
- Added a stdlib-only deterministic structural eval harness for the existing synthetic slice and review renderer.
- Added six invented synthetic eval cases covering bureaucratic irony, idiom/subtext, character voice, reference-like political phrasing, Ukrainian field presence, spoiler safety defaults, glossary presence, and compact/deep usefulness.
- Added `scripts/run_synthetic_eval.py`, which prints a JSON summary by default and rejects unsafe output paths outside `workspace/synthetic-slice/`.
- Added optional per-case review HTML batch output under `workspace/synthetic-slice/eval/`.
- Added structural scores for `section_coverage`, `compact_brevity`, `deep_explanation_presence`, `glossary_coverage`, `risk_flag_coverage`, `spoiler_safety`, and `renderer_completeness`.
- Added tests for eval case validation, synthetic-only safety, deterministic scoring, score degradation on missing sections/glossary, CLI output path safety, and review generation.
- Integrated the synthetic eval smoke into `scripts/check_all.py`.
- Did not change schemas or add dependencies.

Important eval terminology:
- `quality.needs_human_review` is the annotation-card quality boolean used by the structured output.
- `needs_human_review_before_real_use` is a risk flag showing that deterministic synthetic/mock output is not ready for real player-facing use without human review.

Milestone 1B remains in place:
- Added a deliberately boring stdlib-only static HTML review renderer for the existing `overlay_demo` model.
- Extended `scripts/run_synthetic_slice.py` with `--render-review`.
- Kept default output behavior deterministic: review HTML prints to stdout unless `--output` is provided.
- Restricted written generated artifacts to `workspace/synthetic-slice/`; unsafe output paths are rejected with a clear CLI error instead of being normalized.
- Added mandatory HTML escaping coverage, including a test with unsafe synthetic `<script>` text.
- Added tests for compact mode, deep explanation mode, original/translation visibility, Ukrainian fields, idiom/reference/voice sections, glossary terms, confidence, risk flags, and output path safety.
- Integrated the review-renderer smoke command into `scripts/check_all.py`.
- Did not change any schemas.

Milestone 1A remains in place:
- Added `FakeGameEvent` schema plus valid/invalid synthetic fixtures.
- Added a pure stdlib synthetic slice module that validates a fake event, builds a context packet, creates a deterministic mock annotation card, and produces an overlay-facing demo model.
- Added `scripts/run_synthetic_slice.py` to run the full synthetic flow from fixture or supplied synthetic event.
- Added tests for fake event validation, context packet building, deterministic mock annotation output, overlay model shape, full flow, and safety/no private path requirements.
- Integrated a synthetic slice CLI smoke test into `scripts/check_all.py`.
- Kept `specs/annotation-card.schema.json` unchanged: its existing fields plus default allowance for optional extra properties can represent this slice without a backward-compatibility schema change.

Milestone 0 foundation still in place:
- Added explicit ignored private roots for local game data, generated artifacts, caches, vectors, screenshots, audio metadata, and translation memory.
- Added example runtime config and validation for path safety, opt-in provider/network policy, and no inline secrets.
- Added idempotent local workspace bootstrap script.
- Added lightweight schema validation and synthetic fixtures for context packets, annotation cards, glossary entries, and one end-to-end example.
- Added unified check runner and wired it through npm, Justfile, Makefile, and CI.
- Updated the LLM output contract and legal/data safety docs with runtime paid API and opt-in web enrichment policy.

Latest validation run:
- `python -m unittest tests.test_provider_contract_regression -v` passed with 11 tests.
- `python scripts/check_all.py` passed, including 108 unit tests, provider fixture validation, provider pipeline smoke, provider contract regression smoke, prompt pack smoke, companion server smoke, companion client smoke, Ruff check, and Ruff format check.
- `python scripts/validate_schemas.py` passed.
- `python -m unittest discover -s tests -p "test_*.py"` passed with 108 tests.
- `npm run check` passed.
- `python scripts/run_provider_contract_regression.py --quiet` passed.
- `python scripts/run_companion_server.py --smoke-test` passed.
- `python scripts/run_companion_client.py smoke-test` passed.
- `python scripts/run_prompt_pack.py --summary` passed.
- `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Notes:
- `ruff` is installed locally and passed both check and format-check in this session.
- No real extraction, scraping, paid API call, web API call, BepInEx integration, OCR, or copyrighted game content was used.
- `docs/00-project-vision.md` is absent; `docs/00-start-here.md` remains the current vision entrypoint.
