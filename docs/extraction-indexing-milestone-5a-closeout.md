# Extraction Indexing Milestone 5A Closeout

The unchanged canonical roadmap remains `tasks/milestones.md`. In that original roadmap, this
5A-labelled work is an internal safety-preparation workstream inside active
`M2 - Local extraction import`. It is not the original top-level `M5 - Maximum quality pipeline`.

Milestone 5A closes with a local-only, redacted evidence path. It established scope contracts,
synthetic fixtures, metadata-only dry-runs, and private workspace boundaries before any real
extraction/indexing behavior is approved.

This closeout does not claim real extraction. It does not approve reading game files, scanning
Steam/game installs, reading BepInEx logs, capturing current-line text, reading UI text, scanning
Unity objects, adding hooks/Harmony patches, running OCR, parsing saves, using decompiled game code,
changing companion HTTP contracts, calling providers, or committing extracted game text.

## Delivered Safe Path

Milestone 5A delivered:

- the local-only extraction/indexing scope contract in ADR 0011;
- a deterministic synthetic indexer and private index format contract;
- an explicit user-selected private input adapter contract;
- a metadata-only private input dry-run;
- a redacted private input dry-run review gate;
- a private input hash decision contract;
- a canonical redacted dry-run summary hash contract and dry-run helper;
- a redacted dry-run summary hash evidence gate;
- a private index construction contract;
- a private index builder dry-run that consumes redacted metadata evidence only.

The implemented private input and private index dry-runs operate only on explicit ignored workspace
paths and redacted metadata. They do not read or index private file contents. Generated local
summaries, hash outputs, reviews, and dry-run index previews remain ignored private artifacts under
`workspace/local-private/extraction-indexing/`.

## Explicitly Not Implemented

Milestone 5A does not implement:

- real extraction from game files;
- reading Steam/game directories;
- automatic game-install or drive scanning;
- BepInEx log reading;
- current-line capture;
- UI text reading;
- Unity object scanning;
- hooks/Harmony patches;
- screenshots or OCR;
- save-file parsing;
- decompiled-code workflows;
- provider execution;
- companion HTTP contract changes;
- committed extracted text, localization dumps, or generated real indexes.

## Evidence And Checks

This closeout document is:

```text
docs/extraction-indexing-milestone-5a-closeout.md
```

The closeout fixture is:

```text
tests/fixtures/extraction_indexing_5a_closeout.synthetic.json
```

Validate it with:

```powershell
python scripts/check_extraction_indexing_5a_closeout.py --quiet
```

The checker verifies that the safe 5A milestones are recorded, risky capabilities remain false, the
tracked evidence stays redacted, and the recommended next step remains narrow.

## Next Safe Step

The recorded next step is:

```text
m2_local_extraction_import_scope_contract
```

This means the internal 5A safety-preparation workstream is closed while original
`M2 - Local extraction import` remains active. The undefined `milestone_5b_planning` placeholder is
retired because it was never part of the original roadmap. The next task is an M2 local extraction
import scope contract. It does not approve real extraction, game-file reads, private file-content
reads, capture, scanning, hooks, OCR, provider execution, or committed real text.
