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
- stable hash summaries;
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
