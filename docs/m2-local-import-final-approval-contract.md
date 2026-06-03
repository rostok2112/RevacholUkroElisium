# M2 Local Import Final Approval Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract is the
final approval boundary before the first original M2 criterion may be implemented:

```text
Import locally extracted DB.
```

This slice does not import a DB, build a line index, build a context graph, or complete any
original M2 criterion. It approves only the next implementation slice for one explicit
workspace-private JSON export.

## Approved Next Implementation Boundary

The next implementation may read exactly one user-selected UTF-8 JSON export under:

```text
workspace/local-private/extraction-indexing/input/
```

The selected export must use:

```text
schema_version: "m2-local-private-export.v1"
```

The next implementation may parse the previously reviewed envelope, record objects, and
context-edge objects to build a local private imported DB artifact. It may write only under:

```text
workspace/local-private/extraction-indexing/import/db/
```

The imported DB artifact is private output. It must not be committed, printed, copied to docs,
included in reports, or exposed in review Markdown.

## Required Import Boundary

The next implementation must:

- accept only the exact path passed by the user;
- reject directories, symlinks, external absolute paths, `..`, and discovery;
- avoid Steam, game-install, drive, and BepInEx log scanning;
- preserve record ids, line ids, speaker/context placeholders, source text, tags, metadata, and
  context edges only inside ignored private output;
- emit only redacted aggregate status to stdout;
- keep original M2 line-index and context-graph criteria incomplete.

The next implementation must not:

- commit extracted text, private paths, payloads, generated private DB artifacts, indexes, or
  reports;
- build a line index;
- build a context graph;
- map retrieval buckets;
- hash ids, paths, filenames, content, or values;
- read game files, saves, screenshots, OCR output, decompiled code, or runtime logs;
- add current-line capture, UI text reading, Unity scanning, hooks, providers, or companion HTTP
  contract changes.

## Fixture And Checker

The machine-readable approval fixture is:

```text
docs/m2-local-import-final-approval-contract.md
tests/fixtures/m2_local_import_final_approval_scope.synthetic.json
scripts/check_m2_local_import_final_approval_contract.py
```

Validate the static contract with:

```powershell
python scripts/check_m2_local_import_final_approval_contract.py --quiet
```

The next allowed step is:

```text
m2_local_import_implementation
```

## Implementation Result

The approved implementation is:

```text
scripts/run_m2_local_import.py
```

It accepts one explicit workspace-private `m2-local-private-export.v1` JSON file and writes one
ignored private DB artifact under:

```text
workspace/local-private/extraction-indexing/import/db/
```

Public output remains a redacted aggregate summary. Private record values, source text, ids,
metadata, and context edges are preserved only inside the ignored private DB artifact. The helper
does not build a line index, build a context graph, map retrieval buckets, scan game installs, read
runtime logs, call providers, or change companion contracts.

Validate the implementation smoke with:

```powershell
python scripts/run_m2_local_import.py --self-test --quiet
```

After a successful private import, the next M2 step is:

```text
m2_line_index_contract
```

The line-index contract is tracked in:

```text
docs/m2-line-index-contract.md
tests/fixtures/m2_line_index_scope.synthetic.json
scripts/check_m2_line_index_contract.py
```
