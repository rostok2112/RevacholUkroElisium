# M4 Real Overlay Scope

Original `M4 - Real overlay` criteria from `tasks/milestones.md`:

```text
Compact translation.
Genius card.
Hotkeys.
```

M4 is active. The criteria are not complete yet.

## Existing Work To Reuse

Do not recreate the existing overlay contract path. M4 starts from:

- `docs/overlay-prototype.md`
- `docs/overlay-refresh-readiness-contract.md`
- `scripts/local_overlay_prototype.py`
- `scripts/overlay_state_source.py`
- `scripts/overlay_actions.py`
- `scripts/overlay_viewmodel_validator.py`
- `scripts/render_overlay_review.py`
- `scripts/check_overlay_review_accessibility.py`
- committed overlay view-model and state-source fixtures under `tests/fixtures/`

These artifacts already define compact, deep, debug, action, state-source, review, accessibility,
and refresh-readiness behavior for synthetic/local validation. They are the baseline for M4.

## M4 Implementation Boundary

M4 may add a local browser overlay shell that consumes validated overlay state and renders:

- compact Ukrainian translation;
- a Genius-style expandable annotation card from the existing deep view model;
- page-local hotkeys.

Generated shell output must stay under ignored local workspace roots. Public fixtures remain
synthetic only.

M4 does not approve native always-on-top packaging, Electron/Tauri setup, global keyboard hooks,
clipboard writes, OCR, Unity scanning, hooks/Harmony, provider execution, companion HTTP contract
changes, game-file reads, BepInEx log reads, screenshots, private paths, raw provider payloads, or
committed generated shell artifacts.

## Guardrail

The M4 scope fixture and checker are:

```text
docs/m4-real-overlay-scope.md
tests/fixtures/m4_real_overlay_scope.synthetic.json
scripts/check_m4_real_overlay_scope.py
```

Validate with:

```powershell
python scripts/check_m4_real_overlay_scope.py --quiet
```

The next bounded M4 step is:

```text
m4_overlay_shell_contract
```
