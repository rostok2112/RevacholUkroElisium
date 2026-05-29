# Extraction Indexing Dry-Run Summary Hash Contract

Milestone 5A.6 defines the contract for a later hash dry-run over redacted private input adapter
summaries. It is a contract milestone only. It does not implement hashing.

This contract does not approve file content hashing, path string hashing, filename hashing, private
index construction, real extraction, automatic game-install scanning, BepInEx log reads, save
parsing, screenshots, OCR, current-line capture, UI text reading, Unity scanning, hooks/Harmony,
decompiled game-code work, companion HTTP contract changes, provider execution, or committed real
extracted text.

## Allowed Future Hash Input

A later milestone may define a dry-run hash over a canonical redacted summary object only. The input
must be derived from:

```text
schema_version: "private-input-adapter-dry-run-summary.v1"
```

The summary must first satisfy the 5A.4 review rules from
`scripts/review_private_input_adapter_dry_run.py`. The future hash input must include only stable,
redacted scalar metadata fields such as:

- summary schema version;
- input exists flag;
- input kind;
- file count;
- directory count;
- total size in bytes;
- traversal limit;
- traversal truncated flag;
- allowed root marker;
- private output root marker;
- dry-run flag;
- paths redacted flag;
- redacted blocker categories;
- explicit false safety flags.

These fields can describe private metadata counts and status. They must not include content, names,
paths, raw evidence, or generated indexes.

## Forbidden Hash Inputs

The future hash input must exclude:

- file contents;
- private path strings;
- filenames or directory names unless they are synthetic/redacted fixture names;
- verbose dry-run fields such as `input_path`, `allowed_root_path`, or `output_path`;
- raw logs;
- raw payloads;
- screenshots or screen captures;
- OCR output;
- save files;
- decompiled output;
- provider payloads;
- generated private indexes;
- timestamps;
- report paths;
- free-text private evidence;
- BepInEx or game log data;
- any real game text or extracted localization.

Hashing any of those inputs remains forbidden after 5A.6.

## Canonicalization Rules For Later Work

Any later implementation must define a canonical JSON object before hashing:

- UTF-8 encoded JSON;
- sorted object keys;
- deterministic separators;
- stable scalar values only;
- normalized blocker categories in sorted order;
- no path-bearing fields;
- no content-bearing fields;
- no timestamps or environment-specific values;
- no raw payload, log, screenshot, save, provider, or generated-index data.

5A.6 defines those requirements but does not add code that computes a hash.

## Private Output Boundary

Any future local hash dry-run output must remain ignored and private under:

```text
workspace/local-private/extraction-indexing/
```

No real-input hash artifacts may be committed. Tracked files may contain only this contract, checker
code, and synthetic fixtures.

## Fixture And Checker

This contract file is:

```text
docs/extraction-indexing-dry-run-summary-hash-contract.md
```

The machine-readable 5A.6 contract fixture is:

```text
tests/fixtures/dry_run_summary_hash_contract.synthetic.json
```

Validate it with:

```powershell
python scripts/check_dry_run_summary_hash_contract.py --quiet
```

The fixture records that hash implementation remains blocked, canonical redacted summary hashing is
contract-defined only, file content/path/filename/raw-payload hashing is forbidden, and private
index construction remains blocked.

## Milestone 5A.7 Dry-Run Summary Hash Helper

Milestone 5A.7 implements the first dry-run hash helper:

```powershell
python scripts/run_dry_run_summary_hash.py --summary workspace/local-private/extraction-indexing/<dry-run-summary>.json
```

The helper reads only the dry-run summary JSON. It never reopens the selected private input, never
reads file contents, and never builds a private index. The source summary must live under:

```text
workspace/local-private/extraction-indexing/
```

Optional hash output may be written only under:

```text
workspace/local-private/extraction-indexing/hash/
```

Hash output uses:

```text
schema_version: "dry-run-summary-hash.v1"
```

The output contains only a SHA-256 digest over canonical redacted summary metadata, a field count,
and explicit false safety flags. It does not include the canonical JSON, source summary contents,
source path, filenames, private paths, raw payloads, raw logs, screenshots, OCR output, provider
payloads, generated indexes, file contents, or real game text.

The synthetic expected hash fixture is:

```text
tests/fixtures/dry_run_summary_hash.synthetic.json
```

## Relationship To 5A.5

Milestone 5A.5 is recorded in:

```text
docs/extraction-indexing-private-input-hash-contract.md
tests/fixtures/private_input_hash_decision.synthetic.json
scripts/check_private_input_hash_decision_contract.py
```

5A.5 left only the dry-run summary hash contract open. 5A.6 defines that contract, but still does
not approve hash implementation. The next safe step is a dry-run summary hash dry-run, not file
content hashing, path hashing, private index construction, or real extraction.
