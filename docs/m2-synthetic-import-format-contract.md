# M2 Synthetic Import Format Contract

Original `M2 - Local extraction import` remains active and incomplete. This contract defines an
invented synthetic fixture format before any importer is implemented or any local export is read.
It is controlled by `docs/adr/0012-m2-local-extraction-import-scope.md`.

This contract does not import a real database, read a private input, build a line index, build a
context graph, scan a game installation, or add runtime capture behavior.

## Synthetic Import Envelope

Committed synthetic import fixtures use:

```text
schema_version: "m2-synthetic-import-db.v1"
source_kind: "synthetic_fixture"
```

The envelope contains:

- `records`: invented line-shaped records for later synthetic validator and index-contract work;
- `context_edges`: synthetic relations between records;
- `metadata`: fixture-only provenance and explicit incomplete-M2 markers;
- `safety_flags`: explicit false flags for real content, local reads, scanning, capture, provider,
  and companion-contract behavior.

Each synthetic record contains:

- `record_id` and `line_id`: stable ids under `synthetic.m2.line.*`;
- `conversation_id`: a stable id under `synthetic.m2.conversation.*`;
- `speaker_id`: a stable id under `synthetic.m2.speaker.*`;
- `speaker_label`: a `synthetic_*` placeholder;
- `context_placeholder`: a `synthetic_*` placeholder;
- `source_text`: invented fixture text only;
- `context_tags`: synthetic context labels;
- `redacted_metadata`: fixture-only and invented-text markers.

Each context edge contains:

- `from_record_id`;
- `to_record_id`;
- `relation`: one of `previous_visible`, `nearby_branch`, or `player_option`.

Edges are contract examples only. They do not claim that a context graph has been built.

## Safety Boundary

Committed fixtures may contain invented synthetic text only. They must not contain real game
dialogue, extracted localization, character names, item names, quest names, location names,
screenshots, logs, payload dumps, private paths, URLs, or secrets.

This contract does not permit:

- real DB import or local private-input reads;
- automatic Steam, game-install, or drive scanning;
- BepInEx or game-log reads;
- screenshots, OCR, save parsing, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes;
- committed extracted text, indexes, payloads, or private paths.

Invented-text provenance is a human-reviewed fixture rule. The checker reinforces it with stable
synthetic ids, explicit redacted metadata, safety flags, and unsafe-marker rejection.

## Fixture And Checker

The canonical format contract is:

```text
docs/m2-synthetic-import-format-contract.md
```

The committed invented fixture is:

```text
tests/fixtures/m2_synthetic_import_db.synthetic.json
```

Validate it with:

```powershell
python scripts/check_m2_synthetic_import_format.py --quiet
```

Original M2 remains incomplete after this contract. The only allowed next step is:

```text
m2_synthetic_import_validator_or_line_index_contract
```
