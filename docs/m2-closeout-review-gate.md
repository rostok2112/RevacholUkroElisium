# M2 Closeout Review Gate

Original `M2 - Local extraction import` has three completion criteria:

```text
Import locally extracted DB.
Build line index.
Build context graph.
```

This gate reviews only redacted review evidence for those three criteria. It does not reopen the
selected private export, private imported DB, private line-index artifact, or private context graph.
It does not read game files, scan installs, read BepInEx logs, call providers, change companion
contracts, or commit generated private artifacts.

## Required Evidence

The closeout reviewer consumes only:

```text
workspace/local-private/extraction-indexing/import/db-review/
workspace/local-private/extraction-indexing/import/line-index-review/
workspace/local-private/extraction-indexing/import/context-graph-review/
```

The required schemas are:

```text
m2-local-import-review.v1
m2-line-index-review.v1
m2-context-graph-review.v1
```

All three reviews must be valid, unblocked, and ready. The closeout review may then mark original
M2 complete at the private implementation-path level without committing private artifacts.

Under `docs/milestone-completion-standard.md`, that implementation-path completion is not strict
full completion. Tracked M2 status must distinguish:

```text
automated_complete
manual_verification_required
manual_verification_complete
fully_complete
```

M2 `fully_complete` remains false until the user runs one explicit private export through local
import, line index, context graph, and closeout review.

## Output Boundary

Optional closeout JSON or Markdown may be written only under:

```text
workspace/local-private/extraction-indexing/import/m2-closeout-review/
```

Closeout output may contain only aggregate readiness booleans, redacted blockers, completion
booleans, and the next safe step. It must not include paths, filenames, record ids, line ids, edge
ids, relation values, source text, tags, metadata values, hashes, logs, payloads, or runtime
evidence.

## Guardrails

The closeout gate is implemented by:

```text
scripts/review_m2_closeout.py
tests/fixtures/m2_closeout_review_decision.synthetic.json
tests/fixtures/m2_manual_private_export_verification_report.synthetic.json
scripts/review_m2_manual_private_export_verification.py
docs/milestone-completion-standard.md
```

Validate it with:

```powershell
python scripts/review_m2_closeout.py --self-test --quiet
```

After a passing closeout review and owner chat attestation, the next strict completion step is:

```text
m3_manual_runtime_verification
```
