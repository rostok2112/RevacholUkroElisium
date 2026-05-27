# Extraction Indexing Private Index Contract

Milestone 5A.1 defines the first synthetic indexer and private index contract. It is
implementation-adjacent, but it is still synthetic/private-index work only.

This contract does not implement real extraction from game files, automatic game-install scanning,
current-line capture, UI text reading, Unity scanning, hooks/Harmony, OCR, decompiled game-code
work, companion HTTP contract changes, provider execution, or production overlay shell behavior.

## Private Index Schema

Private indexes use:

```text
schema_version: "extraction-index.v1"
```

The index object contains:

- `records`: deterministic record summaries derived from source records;
- `terms`: deterministic term-to-record mappings;
- `record_count`: number of indexed records;
- `source_digest`: SHA-256 digest of the canonical source-record fixture;
- `generated_from_synthetic_fixture`: `true` for committed fixtures;
- `private_index_root`: `workspace/local-private/extraction-indexing/`;
- `safety_flags`: explicit false flags for real game text, raw payloads, automatic scanning,
  game-file reads, BepInEx log reads, screenshots, OCR, hooks, Unity scanning, current-line capture,
  UI text reading, decompiled-code details, companion contract changes, and provider execution.

Committed index fixtures may include only invented synthetic terms and hashes. Future user-local
private indexes must remain under the ignored private output root and must not be committed.

## Synthetic Source Records

Committed source records use:

```text
schema_version: "extraction-index-source-records.v1"
```

Allowed committed source record fields are:

- stable synthetic ids such as `synthetic.extract.001`;
- invented `source_text`;
- synthetic speaker or context labels;
- synthetic context tags;
- glossary-like synthetic tokens;
- redacted metadata proving the fixture is synthetic.

Committed source fixtures must not include real game dialogue, character names, item names, quest
names, location names, screenshots, logs, extracted localization, private paths, raw payloads, or
external URLs.

## Metadata-Only Local Input Summaries

A later local-only adapter may summarize user-selected private inputs only as redacted metadata:

- file presence;
- file count;
- byte count;
- stable hashes;
- blocker categories;
- schema/version compatibility status.

These summaries are private diagnostics. They must stay ignored unless a later checker explicitly
defines a committed synthetic/redacted form. The synthetic indexer in this milestone does not read
real local inputs.

## Private Output Root

The only allowed private index output root is:

```text
workspace/local-private/extraction-indexing/
```

The root is under ignored `workspace/`. Generated private indexes, summaries, and reports from
real-input experiments must not be committed.

## Fixture And Checker

Committed synthetic fixtures:

```text
tests/fixtures/extraction_index_source_records.synthetic.json
tests/fixtures/extraction_index.synthetic.json
```

Build or validate the deterministic synthetic index with:

```powershell
python scripts/run_synthetic_extraction_indexer.py --check-fixture --quiet
```

Validate the contract, fixtures, and deterministic output with:

```powershell
python scripts/check_extraction_index_contract.py --quiet
```

## Forbidden Tracked Artifacts

Do not commit:

- real game text;
- raw localization dumps;
- BepInEx or game logs;
- screenshots or OCR output;
- save files;
- private absolute paths;
- decompiled game-code details;
- raw extracted payloads;
- generated private indexes from real inputs;
- provider payloads or real provider outputs.

Automatic game-install scanning remains disallowed. Any future real adapter must require explicit
user-selected private inputs and a separate approved implementation plan.
