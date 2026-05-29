# Extraction Indexing Private Index Construction Contract

Milestone 5A.9 defines the contract for a future private index builder. It is a contract milestone
only. It does not implement private index construction.

This contract does not approve real extraction from game files, file content reads, file content
hashing, path string hashing, filename hashing, automatic game-install scanning, BepInEx log reads,
save parsing, screenshots, OCR, current-line capture, UI text reading, Unity scanning,
hooks/Harmony, decompiled game-code work, companion HTTP contract changes, provider execution, or
committed real extracted text.

## Allowed Future Inputs

A later milestone may scope a private index builder only from already-redacted local/private
evidence:

- committed synthetic fixture indexes;
- redacted private input dry-run metadata summaries;
- reviewed dry-run summary hash evidence;
- explicit false safety flags and blocker categories.

Those inputs are metadata and readiness evidence. They are not file contents and are not a private
text corpus.

## Forbidden Inputs And Fields

A future private index must not include or derive tracked artifacts from:

- file contents;
- real game text;
- filenames;
- path strings;
- raw payloads;
- raw logs;
- screenshots or OCR output;
- save files;
- decompiled code;
- provider payloads;
- companion runtime data;
- BepInEx logs;
- Steam or game install scans.

Private index fields must remain redacted. A future builder contract must define exact output fields
before any implementation reads private content or writes an index from private input.

## Private Output Boundary

Any future private index construction output must remain under:

```text
workspace/local-private/extraction-indexing/index/
```

The root is ignored because it is under `workspace/`. Generated private indexes, hash evidence,
dry-run summaries, reports, and review artifacts from local private runs must not be committed.

## Decision

Milestone 5A.9 records:

```text
private_index_builder_allowed_next: false
private_index_construction_allowed_next: "contract_defined_only"
```

This means the shape of a future builder can be discussed, but implementation remains blocked. The
next safe step is a private index builder dry-run contract or implementation plan that still does
not read private file contents unless explicitly approved by a later milestone.

## Fixture And Checker

This contract file is:

```text
docs/extraction-indexing-private-index-construction-contract.md
```

The machine-readable 5A.9 contract fixture is:

```text
tests/fixtures/private_index_construction_contract.synthetic.json
```

Validate it with:

```powershell
python scripts/check_private_index_construction_contract.py --quiet
```

The fixture keeps builder implementation blocked, limits output roots to
`workspace/local-private/extraction-indexing/index/`, and keeps all capture, extraction, content,
path, provider, and companion-contract permissions false.

## Milestone 5A.10 Dry-Run Helper

Milestone 5A.10 adds a stdlib-only dry-run helper:

```powershell
python scripts/run_private_index_builder_dry_run.py --dry-run-summary <summary.json> --summary-hash <hash.json>
```

The helper accepts only:

- a redacted private input dry-run summary under `workspace/local-private/extraction-indexing/`;
- a redacted dry-run summary hash output under
  `workspace/local-private/extraction-indexing/hash/`.

Optional output is limited to:

```text
workspace/local-private/extraction-indexing/index/
```

The output schema is `private-index-dry-run.v1`. It records only redacted metadata: source summary
validity, hash validity, file and directory counts, the total size value already present in the
summary, digest presence, blocker categories, and explicit false safety flags. It does not include
the digest value, input paths, filenames, canonical JSON, original summary contents, raw logs, raw
payloads, screenshots, OCR output, save data, provider payloads, generated real indexes, or real
text.

This dry-run is not private index construction from real text. It still does not read original
private inputs, read file contents, hash file contents, hash paths, hash filenames, scan game
installs, read BepInEx logs, parse saves, call providers, change companion HTTP contracts, or approve
real extraction.
