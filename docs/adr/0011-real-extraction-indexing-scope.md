# ADR 0011: Real extraction/indexing scope

## Roadmap Placement

The unchanged canonical roadmap is `tasks/milestones.md`. This ADR and the later 5A-labelled
contracts form an internal safety-preparation workstream inside active
`M2 - Local extraction import`. They are not the original top-level
`M5 - Maximum quality pipeline`, which has not started.

## Status

Accepted.

## Context

Expanded Milestone 4 bridge/workflow validation is closed. The project has proved the safe
synthetic/manual path:

```text
real local game launch -> BepInEx bridge -> synthetic send -> companion mock provider state -> overlay readiness
```

The internal 5A-labelled workstream prepares the real extraction/indexing adapter, local-only.
Before any adapter reads user files or writes private indexes, the project needs a scope and safety
contract that keeps public repo data synthetic and keeps user-owned extraction output ignored.

This decision is docs/static-contract work only. It does not implement extraction, indexing,
current-line capture, UI text reading, Unity scanning, hooks/Harmony, OCR, production overlay shell
behavior, real provider execution, or companion HTTP contract changes.

## Decision

Milestone 5A starts with a contract only. Real extraction/indexing implementation remains blocked
until a later approved step defines a synthetic indexer and private index contract.

Allowed future local-only sources are limited to:

- committed synthetic fixtures;
- user-selected private inputs placed under ignored workspace paths;
- metadata-only file presence, count, and hash summaries kept local/private;
- a local-only private index under `workspace/local-private/extraction-indexing/`.

This contract does not approve automatic scanning of the game install. A later adapter must require
explicit user-selected inputs and must keep private outputs under ignored workspace paths.

The allowed private output root for a future local index is:

```text
workspace/local-private/extraction-indexing/
```

The root is intentionally under ignored `workspace/`. Real extracted text, raw tables, local
database dumps, private paths, generated indexes, and diagnostic reports from real inputs must not
be committed.

## Forbidden Sources And Artifacts

The 5A contract keeps these forbidden for committed repo content and for unapproved implementation:

- real game text committed to the repo;
- raw localization dumps committed to the repo;
- screenshots or screen captures;
- OCR output;
- BepInEx or game logs containing real text;
- game save files;
- arbitrary game-file or game-install scanning;
- Unity object scanning;
- current-line capture;
- UI text reading;
- hooks or Harmony patches;
- decompiled game code, class names, method names, or signatures when risky;
- raw extracted payloads in tracked docs, tests, or fixtures;
- companion HTTP contract changes;
- real provider execution.

If a later local-only adapter needs to describe private inputs, it may record redacted booleans,
counts, hashes, and blocker categories only. It must not copy raw extracted text or payloads into
tracked files.

## Minimum Checks Before Implementation

Before any real extraction/indexing adapter is implemented, a later milestone must:

- define the synthetic indexer and private index JSON contract;
- add a checker that rejects unsafe output roots and raw text/payload markers;
- prove all generated real-input outputs stay under ignored workspace roots;
- use only synthetic fixtures in committed tests;
- require explicit user-selected input paths for any private local run;
- document how private indexes are deleted or regenerated;
- keep current-line capture, UI text reading, Unity scanning, hooks/Harmony, OCR, companion contract
  changes, and provider execution closed.

## Fixture And Checker

The machine-readable contract fixture is:

```text
tests/fixtures/extraction_indexing_scope.synthetic.json
```

Validate it with:

```powershell
python scripts/check_extraction_indexing_scope.py --quiet
```

The fixture is synthetic-only. It records the 5A local-only boundary, the ignored private output
root, and the rule that implementation is not yet approved.

## Milestone 5A.1 Synthetic Indexer Contract

Milestone 5A.1 defines the synthetic indexer and private index contract in:

```text
docs/extraction-indexing-private-index-contract.md
tests/fixtures/extraction_index_source_records.synthetic.json
tests/fixtures/extraction_index.synthetic.json
scripts/run_synthetic_extraction_indexer.py
scripts/check_extraction_index_contract.py
```

The indexer reads only committed synthetic source records by default, builds a deterministic
`schema_version: "extraction-index.v1"` index, and can write generated private-index output only
under:

```text
workspace/local-private/extraction-indexing/
```

This satisfies the synthetic indexer/private index contract prerequisite only. It does not approve
real extraction from game files, automatic game-install scanning, current-line capture, UI text
reading, Unity scanning, hooks/Harmony, OCR, decompiled game-code work, companion HTTP contract
changes, provider execution, or committed real extracted text.

## Milestone 5A.2 Private Input Adapter Contract

Milestone 5A.2 defines the user-selected private input adapter boundary in:

```text
docs/extraction-indexing-private-input-adapter-contract.md
tests/fixtures/extraction_private_input_adapter_scope.synthetic.json
scripts/check_extraction_private_input_adapter_contract.py
```

The contract remains docs/static-contract only. It does not read private inputs and does not
implement extraction. A later adapter may be planned only around one explicit user-selected file or
directory placed under:

```text
workspace/local-private/extraction-indexing/input/
```

Any future output remains limited to:

```text
workspace/local-private/extraction-indexing/
```

The default future mode is dry-run metadata summary only: redacted booleans, counts, schema status,
and blocker categories. Hashes require a later hash contract before any implementation. External
absolute input paths, automatic game-install scanning, arbitrary drive scans, BepInEx log reads,
screenshots, OCR, save parsing, current-line capture, UI text reading, Unity scanning,
hooks/Harmony, decompiled game-code work, companion HTTP contract changes, real provider execution,
and committed real extracted text remain closed.

## Milestone 5A.5 Private Input Hash Decision Contract

Milestone 5A.5 defines the hash decision boundary in:

```text
docs/extraction-indexing-private-input-hash-contract.md
tests/fixtures/private_input_hash_decision.synthetic.json
scripts/check_private_input_hash_decision_contract.py
```

The decision remains contract-only. Hash implementation is not approved. File content hashing and
path string hashing remain forbidden because they can become stable identifiers for private files
or local structures. The only future hash topic left open is a later contract for hashing an
already-redacted dry-run summary object that passed the 5A.4 review helper.

Private index construction from real input remains blocked. The 5A.5 contract does not approve real
extraction from game files, automatic game-install scanning, current-line capture, UI text reading,
Unity scanning, hooks/Harmony, OCR, decompiled game-code work, companion HTTP contract changes,
provider execution, or committed real extracted text.

## Milestone 5A.6 Dry-Run Summary Hash Contract

Milestone 5A.6 defines the dry-run summary hash contract in:

```text
docs/extraction-indexing-dry-run-summary-hash-contract.md
tests/fixtures/dry_run_summary_hash_contract.synthetic.json
scripts/check_dry_run_summary_hash_contract.py
```

The contract allows only a future dry-run over canonical redacted summary metadata. Hash
implementation is still blocked. File content hashing, path string hashing, filename hashing, raw
payload/log hashing, private index construction, real extraction, automatic game-install scanning,
current-line capture, UI text reading, Unity scanning, hooks/Harmony, OCR, decompiled game-code
work, companion HTTP contract changes, provider execution, and committed real extracted text remain
closed.

## Milestone 5A.9 Private Index Construction Contract

Milestone 5A.9 defines the private index construction contract in:

```text
docs/extraction-indexing-private-index-construction-contract.md
tests/fixtures/private_index_construction_contract.synthetic.json
scripts/check_private_index_construction_contract.py
```

The contract defines only the future construction boundary. It keeps
`private_index_builder_allowed_next=false` and
`private_index_construction_allowed_next="contract_defined_only"`. Any future private index output
is limited to:

```text
workspace/local-private/extraction-indexing/index/
```

File contents, real game text, filenames, path strings, raw payloads/logs, screenshots, OCR, save
data, decompiled data, provider payloads, companion runtime data, game-install scans, and committed
real extracted text remain forbidden.

## Consequences

Pros:

- Lets true Milestone 5A begin without reading real game files.
- Keeps public repo artifacts limited to docs, tooling, schemas, and synthetic fixtures.
- Establishes a private output root before any adapter writes indexes.
- Makes accidental capture or automatic scanning a testable contract violation.

Cons:

- Real extraction/indexing remains unimplemented.
- Useful local data still cannot be committed.
- The actual private index shape and adapter behavior need another approved contract step.
