# M2 Line Index Contract

Original `M2 - Local extraction import` remains active. The first implementation path now exists:
`scripts/run_m2_local_import.py` can import one explicit workspace-private
`m2-local-private-export.v1` JSON export into an ignored private DB artifact.

This contract defines the next original M2 criterion boundary:

```text
Build line index.
```

This slice does not build the line index. It approves only the next implementation slice:

```text
m2_line_index_implementation
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

The next implementation may build one private line-index artifact under:

```text
workspace/local-private/extraction-indexing/import/line-index/
```

The line index is private output. It may contain private ids and source text only inside the
ignored private artifact. It must not be committed, printed, copied to docs, copied to review
Markdown, included in reports, or exposed in public summaries.

## Required Line-Index Boundary

The next implementation must:

- accept only the exact imported DB path passed by the user;
- reject directories, symlinks, external absolute paths, `..`, and discovery;
- require the private DB schema version `m2-local-import-db.v1`;
- read only the selected private DB artifact;
- build deterministic line-index entries from top-level `records`;
- keep record ids, line ids, conversation ids, speaker ids, context placeholders, source text, tags,
  and metadata only inside ignored private output;
- emit only redacted aggregate status to stdout;
- keep original M2 context-graph criterion incomplete.

The next implementation must not:

- scan directories or game installs;
- read Steam folders, game files, saves, screenshots, OCR output, decompiled code, or runtime logs;
- read provider payloads or call providers;
- change companion HTTP contracts;
- hash ids, paths, filenames, content, or values;
- build a context graph;
- map retrieval buckets;
- commit generated line indexes, private DB artifacts, extracted text, private paths, payloads, or
  reports.

## Public Summary Boundary

Public summary output may include only redacted aggregate fields:

```text
input_exists
input_kind
private_db_schema_version_matches
records_count
line_index_entry_count
line_index_output_written
line_index_status
blocker_categories
```

It must not include input paths, output paths, filenames, record ids, line ids, source text,
speaker labels, tags, metadata values, hashes, logs, payloads, or runtime evidence.

## Fixture And Checker

The machine-readable guardrail is:

```text
docs/m2-line-index-contract.md
tests/fixtures/m2_line_index_scope.synthetic.json
scripts/check_m2_line_index_contract.py
```

Validate the static contract with:

```powershell
python scripts/check_m2_line_index_contract.py --quiet
```

The next allowed step is:

```text
m2_line_index_implementation
```
