# M2 Context Graph Contract

Original `M2 - Local extraction import` remains active. The first two implementation paths now
exist:

```text
scripts/run_m2_local_import.py
scripts/run_m2_line_index.py
```

This contract defines the third original M2 criterion boundary:

```text
Build context graph.
```

This slice does not build the graph. It requires a redacted line-index review before the graph
implementation slice:

```text
m2_line_index_review_gate
```

## Approved Next Implementation Boundary

The next implementation may read exactly one private imported DB artifact under:

```text
workspace/local-private/extraction-indexing/import/db/
```

The imported DB artifact must use:

```text
schema_version: "m2-local-import-db.v1"
```

After a passing line-index review, the graph implementation may read exactly one private line-index
artifact under:

```text
workspace/local-private/extraction-indexing/import/line-index/
```

The line-index artifact must use:

```text
schema_version: "m2-line-index.v1"
```

The required review helper is:

```text
scripts/review_m2_line_index.py
tests/fixtures/m2_line_index_review_decision.synthetic.json
```

After that review, the graph implementation may write one private context-graph artifact under:

```text
workspace/local-private/extraction-indexing/import/context-graph/
```

The graph output is private. It may contain private ids only inside the ignored private artifact.
It must not be committed, printed, copied to docs, copied to review Markdown, included in reports,
or exposed in public summaries.

## Required Context-Graph Boundary

The next implementation must:

- accept only the exact imported DB path and line-index path passed by the user;
- reject directories, symlinks, external absolute paths, `..`, and discovery;
- require private DB schema version `m2-local-import-db.v1`;
- require private line-index schema version `m2-line-index.v1`;
- build deterministic graph nodes from private line-index entries;
- build deterministic graph edges from private DB `context_edges`;
- map relation values only as:
  - `previous_visible` to `visible_history`;
  - `nearby_branch` to `nearby_tree`;
  - `player_option` to `player_options`;
- keep default spoiler budget `none`;
- keep arbitrary future-branch traversal forbidden;
- emit only redacted aggregate status to stdout.

The next implementation must not:

- scan directories or game installs;
- read Steam folders, game files, saves, screenshots, OCR output, decompiled code, or runtime logs;
- read provider payloads or call providers;
- change companion HTTP contracts;
- hash ids, paths, filenames, content, or values;
- duplicate source text into the context graph;
- commit generated context graphs, line indexes, private DB artifacts, extracted text, private
  paths, payloads, or reports.

## Private Graph Shape

The future private graph artifact must use:

```text
schema_version: "m2-context-graph.v1"
```

Allowed top-level fields are:

```text
schema_version
source_db_schema_version
source_line_index_schema_version
source_kind
nodes
edges
metadata
```

Allowed node fields are:

```text
record_id
line_id
conversation_id
speaker_id
context_placeholder
context_tags
redacted_metadata
```

Allowed edge fields are:

```text
from_record_id
to_record_id
relation
retrieval_bucket
```

`source_text` stays in the private line index and must not be duplicated into graph nodes.

## Public Summary Boundary

Public summary output may include only redacted aggregate fields:

```text
db_input_exists
line_index_input_exists
db_schema_version_matches
line_index_schema_version_matches
node_count
edge_count
context_graph_output_written
context_graph_status
blocker_categories
```

It must not include input paths, output paths, filenames, record ids, line ids, source text,
speaker labels, relation values, tags, metadata values, hashes, logs, payloads, or runtime
evidence.

## Fixture And Checker

The machine-readable guardrail is:

```text
docs/m2-context-graph-contract.md
tests/fixtures/m2_context_graph_scope.synthetic.json
scripts/check_m2_context_graph_contract.py
```

Validate the static contract with:

```powershell
python scripts/check_m2_context_graph_contract.py --quiet
```

The next allowed step is:

```text
m2_line_index_review_gate
```
