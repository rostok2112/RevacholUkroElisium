# ADR 0011: Real extraction/indexing scope

## Status

Accepted.

## Context

Expanded Milestone 4 bridge/workflow validation is closed. The project has proved the safe
synthetic/manual path:

```text
real local game launch -> BepInEx bridge -> synthetic send -> companion mock provider state -> overlay readiness
```

True Milestone 5A is the real extraction/indexing adapter, local-only. Before any adapter reads user
files or writes private indexes, the project needs a scope and safety contract that keeps public
repo data synthetic and keeps user-owned extraction output ignored.

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
