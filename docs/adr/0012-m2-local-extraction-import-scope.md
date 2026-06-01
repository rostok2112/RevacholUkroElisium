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
