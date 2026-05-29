# Extraction Indexing Private Input Adapter Contract

Milestone 5A.2 defines how a future adapter may accept user-selected private inputs. It is
docs/static-contract work only. It does not implement real private input reading.

This contract does not approve automatic game-install scanning, arbitrary drive scanning, real
extraction, BepInEx log reads, save-file parsing, screenshots, OCR, current-line capture, UI text
reading, Unity scanning, hooks/Harmony, decompiled game-code work, companion HTTP contract changes,
provider execution, or committed real extracted text.

## Allowed Future Input Model

A future private input adapter may accept only one explicit user-selected input at a time:

- one file under `workspace/local-private/extraction-indexing/input/`; or
- one directory under `workspace/local-private/extraction-indexing/input/`.

External absolute paths are deferred. For this contract, the user must copy or place private inputs
under the ignored input root first. The future adapter must read only the explicit path supplied by
the user and must not infer or discover a game install.

The default future mode is dry-run metadata summary only. A dry-run summary may include:

- input exists: yes/no;
- input kind: file/directory/unsupported;
- file count;
- byte count;
- stable hash summaries only after a later hash contract explicitly allows them;
- schema/version compatibility status;
- redacted blocker categories.

Dry-run summaries must not include raw text, raw payloads, paths outside the allowed workspace root,
logs, screenshots, OCR output, save data, decompiled names, provider payloads, or game content.

## Private Roots

Allowed private input root:

```text
workspace/local-private/extraction-indexing/input/
```

Allowed private output root:

```text
workspace/local-private/extraction-indexing/
```

Both roots are under ignored `workspace/`. Generated summaries, private inputs, private indexes, and
real-input reports must not be committed.

## Forbidden Input Types

The future adapter must not accept or read:

- automatically discovered Steam or game install paths;
- arbitrary drive roots;
- BepInEx logs;
- game logs;
- screenshots or screen captures;
- OCR output;
- save files;
- decompiled game code;
- Unity runtime objects;
- current-line capture streams;
- UI text-reading streams;
- hook/Harmony outputs;
- companion payload dumps;
- provider payloads or real provider outputs.

## Fixture And Checker

The machine-readable fixture is:

```text
tests/fixtures/extraction_private_input_adapter_scope.synthetic.json
```

Validate it with:

```powershell
python scripts/check_extraction_private_input_adapter_contract.py --quiet
```

The fixture records that implementation remains blocked and that a later private input adapter must
be explicit, dry-run-first, local-only, and workspace-private.

## Milestone 5A.3 Dry-Run Helper

Milestone 5A.3 implements the first private input adapter dry-run helper:

```powershell
python scripts/run_private_input_adapter_dry_run.py --input workspace/local-private/extraction-indexing/input/<selected-file-or-directory>
```

The helper reads only filesystem metadata for the one explicit selected path. It accepts input only
under `workspace/local-private/extraction-indexing/input/` and may write a redacted JSON summary only
under `workspace/local-private/extraction-indexing/`.

The dry-run summary uses:

```text
schema_version: "private-input-adapter-dry-run-summary.v1"
```

It may report only:

- whether the input exists;
- `input_kind`: file, directory, missing, or unsupported;
- file count;
- directory count;
- total size in bytes;
- the allowed private input/output roots;
- redacted blocker categories;
- explicit false safety flags for raw text, raw payloads, automatic scanning, logs, screenshots,
  OCR, saves, hooks, Unity scanning, current-line capture, UI text reading, decompiled code,
  companion contract changes, and provider calls.

Although the 5A.2 contract allows future hash summaries, 5A.3 deliberately defers hashes. The helper
sets `hashes_computed=false`, does not read file contents, and does not build an index from private
input. Default output redacts private absolute paths. `--verbose` may show local paths for the user,
but it still must not print file contents.

## Milestone 5A.4 Dry-Run Evidence Review

Milestone 5A.4 adds a redacted local review helper for dry-run summaries:

```powershell
python scripts/review_private_input_adapter_dry_run.py --summary workspace/local-private/extraction-indexing/<dry-run-summary>.json
```

The review helper reads only the dry-run summary JSON. It never reopens the selected private input,
never reads file contents, and never builds an index. The summary must live under
`workspace/local-private/extraction-indexing/`; optional JSON or Markdown review output may be
written only under:

```text
workspace/local-private/extraction-indexing/review/
```

Review output uses:

```text
schema_version: "private-input-adapter-dry-run-review.v1"
```

It reports only redacted validity, counts, total size from the summary, blocker categories, and
decision readiness flags. `ready_for_hash_decision=true` means only that a later hash decision
contract can be discussed. It does not approve hashing. `ready_for_private_index_decision` remains
false in 5A.4.

The machine-readable 5A.4 decision fixture is:

```text
tests/fixtures/private_input_dry_run_decision.synthetic.json
```

It keeps real extraction, private index construction, automatic game-install scanning, current-line
capture, UI text reading, Unity scanning, hooks/Harmony, OCR, decompiled-code work, companion
contract changes, provider execution, and committed real text closed.

## Milestone 5A.5 Hash Decision Contract

Milestone 5A.5 defines the private input hash decision boundary in:

```text
docs/extraction-indexing-private-input-hash-contract.md
tests/fixtures/private_input_hash_decision.synthetic.json
scripts/check_private_input_hash_decision_contract.py
```

The decision remains contract-only. Hash implementation is not allowed in 5A.5. File content
hashing and path string hashing remain forbidden, and private index construction from private input
remains blocked.

The only future hash topic left open is a later contract for hashing an already-redacted dry-run
summary object that passed the 5A.4 review helper. That later contract must define canonical JSON,
excluded fields, and private output rules before any hash is computed.

Milestone 5A.6 defines that dry-run summary hash contract in:

```text
docs/extraction-indexing-dry-run-summary-hash-contract.md
tests/fixtures/dry_run_summary_hash_contract.synthetic.json
scripts/check_dry_run_summary_hash_contract.py
```

It defines canonical redacted summary metadata as the only possible future hash input, but still
does not implement hashing. File content hashing, path string hashing, filename hashing, raw
payload/log hashing, real extraction, and private index construction remain blocked.

## Relationship To 5A.1

Milestone 5A.1 produced the synthetic indexer/private index contract:

```text
docs/extraction-indexing-private-index-contract.md
scripts/run_synthetic_extraction_indexer.py
scripts/check_extraction_index_contract.py
```

Milestone 5A.2 does not change that indexer into a real adapter. The next safe implementation step,
if approved later, is a dry-run private input adapter that reports only metadata summaries and still
does not build an index from real text by default.
