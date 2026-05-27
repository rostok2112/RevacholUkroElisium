# Metadata-Only Overlay Refresh Readiness Contract

This contract defines how a future overlay shell may reason about refresh readiness using only
metadata already available from the localhost companion and overlay validation layers.

It is docs/static-contract work only. It does not implement polling, timers, retries, background
workers, production shell behavior, companion HTTP changes, provider execution, or any capture path.

## Readiness States

The ordered readiness states are:

- `no_companion`: the companion health check is unavailable or failed.
- `companion_available`: `GET /health` is available and reports the synthetic localhost companion.
- `no_provider_state`: latest provider context and annotation are both absent.
- `provider_state_ready`: latest provider context and latest provider annotation both exist.
- `overlay_state_ready`: the provider state produced a valid `overlay-state-source.v1` result.
- `overlay_view_ready`: the state-source result contains a valid overlay view model.
- `overlay_html_review_ready`: the view model can render review HTML in memory and pass the
  existing structural accessibility checks.
- `stale`: a previous valid overlay view state is being reused as explicit stale state.
- `error`: a redacted companion, provider-state, state-source, view-model, or review-validation
  failure occurred.

These states are metadata status labels for a future shell handoff. They are not a live refresh loop
and do not imply any UI side effect.

## Existing Contract Mapping

The readiness contract maps to existing stable pieces:

- Companion health: `GET /health` from `docs/api/companion-server-contract.md`.
- Provider state existence: `GET /state/latest-provider-context` and
  `GET /state/latest-provider-annotation`.
- Overlay state-source: `schema_version: "overlay-state-source.v1"` from
  `scripts/overlay_state_source.py`.
- View-model validation: the committed overlay view-model validator and fixtures.
- HTML review validation: in-memory review rendering plus
  `scripts/check_overlay_review_accessibility.py`.

The existing state-source statuses remain authoritative for state-source output:

- `ready`
- `no_provider_state`
- `stale`
- `error`

The higher-level readiness states above simply add companion, view-model, and review-check steps
around that existing contract.

## Allowed Metadata Inputs

A future metadata-only refresh helper may use only redacted metadata such as:

- companion health available: yes/no;
- latest provider context exists: yes/no;
- latest provider annotation exists: yes/no;
- overlay state-source status;
- overlay state-source validation status;
- overlay view-model validation status;
- in-memory HTML review render status;
- in-memory structural accessibility validation status;
- redacted stale/error status;
- safe counters or timestamps only when they are local, redacted, and not committed from a real run.

It may also carry safe booleans already used by the bridge-to-overlay smoke wrapper, such as whether
raw logs, raw provider payloads, screenshots, provider calls, and companion contract changes were
not performed.

## Forbidden Inputs

The refresh readiness contract must not consume or store:

- real game text;
- UI text;
- current line content;
- runtime Unity object names;
- runtime scene names;
- screenshots;
- OCR output;
- raw BepInEx or game logs;
- raw provider payload dumps;
- private paths;
- companion HTTP contract changes;
- real provider calls.

If a future helper needs to explain one of these boundaries, it should use a redacted boolean or
blocker category, not raw evidence.

## Fixture And Checker

The committed synthetic fixture is:

```text
tests/fixtures/overlay_refresh_readiness_contract.synthetic.json
```

Validate it with:

```powershell
python scripts/check_overlay_refresh_readiness_contract.py --quiet
```

The fixture records that the bridge-to-overlay smoke passed and that the contract is metadata-only.
All capture, scanning, provider, shell, polling, and companion-contract permissions remain false.

## Next Step

The next safe step after this contract is a separately approved metadata-only overlay refresh helper.
That helper may summarize readiness using the states above, but it must still avoid capture, real
provider execution, production shell behavior, and companion HTTP contract changes.
