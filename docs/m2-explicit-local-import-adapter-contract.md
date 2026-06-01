# M2 Explicit Local-Import Adapter Contract

Original `M2 - Local extraction import` remains active and incomplete. This static contract defines
the boundary for a later explicit local-import adapter. It does not read or parse a local export,
import a database, build a line index, build a context graph, or complete any original M2
criterion.

## Explicit Input Boundary

A future adapter may accept exactly one user-selected export file under:

```text
workspace/local-private/extraction-indexing/input/
```

The user must copy or place the export under the ignored workspace root and pass its exact path.
The future adapter must not infer, discover, or search for an export.

This contract does not approve:

- directories as adapter inputs;
- external absolute paths;
- recursive discovery or arbitrary drive traversal;
- automatic Steam or game-install scanning;
- reading the selected file in this contract slice.

## Future Dry-Run Boundary

The first future implementation must remain metadata-summary-only. It may report:

- whether the explicit file exists;
- whether the selected input is a file;
- the file size in bytes;
- redacted blocker categories;
- schema compatibility as deferred.

Future private output is allowed only under:

```text
workspace/local-private/extraction-indexing/import/
```

Tracked output must not contain local paths, filenames, file contents, extracted text, payloads,
logs, screenshots, OCR output, save data, decompiled data, provider payloads, or runtime evidence.

## Safety Boundary

This contract does not permit:

- real local-export reads or parsing;
- real DB import;
- line-index or context-graph construction from private input;
- automatic Steam, game-install, or drive scanning;
- BepInEx or game-log reads;
- screenshots, OCR, saves, or decompiled-code work;
- current-line capture, UI text reading, Unity scanning, hooks, or Harmony patches;
- provider execution or companion HTTP contract changes;
- committed extracted text, payloads, indexes, or private paths.

## Fixture And Checker

The machine-readable scope fixture is:

```text
docs/m2-explicit-local-import-adapter-contract.md
tests/fixtures/m2_explicit_local_import_adapter_scope.synthetic.json
scripts/check_m2_explicit_local_import_adapter_contract.py
```

Validate the contract with:

```powershell
python scripts/check_m2_explicit_local_import_adapter_contract.py --quiet
```

The next allowed step is:

```text
m2_explicit_local_import_adapter_dry_run
```
