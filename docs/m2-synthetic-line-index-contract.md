# M2 Synthetic Line-Index Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the metadata-only shape of a future synthetic line index. It does not build an index, import a real
database, read a private input, or build a context graph.

The controlling input contract is:

```text
docs/m2-synthetic-import-format-contract.md
specs/m2-synthetic-import-db.schema.json
scripts/m2_synthetic_import_validator.py
tests/fixtures/m2_synthetic_import_db.synthetic.json
```

## Synthetic Line-Index Envelope

Committed line-index fixtures use:

```text
schema_version: "m2-synthetic-line-index.v1"
source_schema_version: "m2-synthetic-import-db.v1"
source_kind: "synthetic_fixture"
```

The fixture contains deterministic metadata entries sorted by `line_id`. Each entry contains:

- `line_id`;
- `record_id`;
- `conversation_id`;
- `speaker_id`;
- `context_placeholder`;
- sorted synthetic `context_tags`.

Each entry maps exactly once to a committed invented import record. This contract deliberately
excludes `source_text`, filenames, paths, hashes, payload dumps, logs, and context edges. A
line-index fixture is not a context graph and is not an index built from private content.

## Safety Boundary

The line-index contract does not permit:

- source text or extracted content in committed line-index fixtures;
- real DB import or local private-input reads;
- generated real indexes or tracked private outputs;
- automatic Steam, game-install, or drive scanning;
- BepInEx or game-log reads;
- filenames, path strings, hashes, raw payloads, or runtime evidence;
- screenshots, OCR, save parsing, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes.

## Fixture And Checker

The canonical line-index contract is:

```text
docs/m2-synthetic-line-index-contract.md
```

The portable structural schema and committed synthetic fixture are:

```text
specs/m2-synthetic-line-index.schema.json
tests/fixtures/m2_synthetic_line_index.synthetic.json
```

Validate the static contract with:

```powershell
python scripts/check_m2_synthetic_line_index_contract.py --quiet
```

Original M2 remains incomplete after this contract. The only allowed next step is:

```text
m2_synthetic_line_index_builder_dry_run
```

## Synthetic Builder Dry-Run

The approved synthetic-only builder is:

```text
scripts/run_m2_synthetic_line_index_builder_dry_run.py
```

It reads one explicit invented synthetic import JSON, validates it with
`scripts/m2_synthetic_import_validator.py`, and projects only the metadata fields defined above.
It does not include source text or context edges. Optional generated output is allowed only under:

```text
workspace/local-private/extraction-indexing/import/line-index/
```

Validate the committed invented fixture mapping with:

```powershell
python scripts/run_m2_synthetic_line_index_builder_dry_run.py --check-fixture --quiet
```

This dry-run does not complete the original M2 line-index criterion. The next allowed step is:

```text
m2_synthetic_line_index_builder_review_gate
```

## Synthetic Builder Review Gate

The redacted synthetic-only review helper is:

```text
scripts/review_m2_synthetic_line_index_builder_dry_run.py
```

It reads only generated metadata-only dry-run output under the ignored private line-index root and
emits redacted review evidence under:

```text
workspace/local-private/extraction-indexing/import/line-index-review/
```

Validate the review gate without real or private input with:

```powershell
python scripts/review_m2_synthetic_line_index_builder_dry_run.py --self-test --quiet
```

The review gate does not complete the original M2 line-index criterion and does not approve
context-graph construction. The next allowed step is:

```text
m2_synthetic_context_graph_contract
```

## Synthetic Context-Graph Contract

The approved metadata-only graph contract is:

```text
docs/m2-synthetic-context-graph-contract.md
specs/m2-synthetic-context-graph.schema.json
tests/fixtures/m2_synthetic_context_graph.synthetic.json
scripts/check_m2_synthetic_context_graph_contract.py
```

It reuses line-index metadata nodes and invented import relations only. It does not construct a
graph, include source text, or complete any original M2 criterion. The next allowed step is:

```text
m2_synthetic_context_graph_builder_dry_run
```
