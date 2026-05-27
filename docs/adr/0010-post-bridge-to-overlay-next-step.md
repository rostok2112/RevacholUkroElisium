# ADR 0010: Post bridge-to-overlay next step

## Status

Accepted.

## Context

The redacted local bridge-to-overlay synthetic smoke passed. The proven path is:

```text
real Steam game -> BepInEx bridge -> synthetic send -> companion mock provider state -> overlay state-source/view-model/html/accessibility validation
```

The evidence is tracked only as redacted booleans and status notes. Raw logs, provider payloads,
workspace reports, generated HTML, screenshots, private paths, game text, and runtime artifacts were
not committed.

This success proves the synthetic/manual bridge-to-overlay route can work end to end, but it does
not prove current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR,
extraction, real provider execution, production overlay readiness, or companion HTTP contract
readiness.

## Options Considered

### A. Packaging and manual workflow polish

- Enables: easier local repeat runs, clearer setup, less operator error.
- Safety: allowed as supporting work if it stays local, redacted, and synthetic/manual.
- Limitation: does not define overlay refresh/readiness semantics.
- Status: allowed as support work.

### B. Metadata-only overlay refresh/readiness contract

- Enables: a later overlay shell to know when synthetic/latest provider state is ready, stale, or
  missing without current-line capture.
- Safety: allowed as docs/static-contract work because it can stay metadata-only and redacted.
- Limitation: must not add polling loops, production shell behavior, provider calls, or companion
  contract changes yet.
- Status: recommended next step.

### C. Companion state polling/readiness contract

- Enables: eventual shell refresh behavior around latest provider state.
- Safety: potentially allowed later, but only after the metadata-only overlay refresh contract
  defines what safe readiness means.
- Limitation: could be mistaken for production overlay behavior if scoped too early.
- Status: defer until option B is documented.

### D. Current-line capture research

- Enables: continued architecture discussion of possible future capture approaches.
- Safety: already covered by ADR 0008 as research only.
- Limitation: no implementation, no runtime probing, no real text capture.
- Status: keep separate and research-only.

### E. Current-line capture implementation

- Enables: real in-game line detection if a safe approach were later approved.
- Safety: not approved. The current evidence is synthetic/manual only.
- Limitation: would require a separate legal/privacy/runtime safety review and local-only proof.
- Status: disallowed.

## Decision

Proceed next to:

```text
metadata_only_overlay_refresh_readiness_contract
```

Packaging and manual workflow polish may happen as supporting work. Companion polling/readiness is
deferred until the metadata-only overlay refresh/readiness contract defines safe states and
boundaries.

The bridge-to-overlay smoke success does not approve runtime implementation work beyond
docs/static-contract planning. It also does not approve current-line capture, real text capture, UI
text reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider execution, production
overlay shell behavior, or companion HTTP contract changes.

The committed decision fixture is:

```text
tests/fixtures/post_bridge_to_overlay_next_step.synthetic.json
```

The follow-up metadata-only refresh/readiness contract is:

```text
docs/overlay-refresh-readiness-contract.md
tests/fixtures/overlay_refresh_readiness_contract.synthetic.json
scripts/check_overlay_refresh_readiness_contract.py
```

## Consequences

Pros:

- Keeps the successful synthetic path moving toward a useful overlay contract.
- Avoids treating synthetic provider state as evidence of real current-line capture.
- Gives safety tooling a machine-readable gate for the next planning step.

Cons:

- Current-line capture remains unimplemented.
- Production overlay behavior remains out of scope.
- Companion polling cadence and refresh behavior still need a later contract.
