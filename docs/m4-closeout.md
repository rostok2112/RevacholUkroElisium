# M4 Closeout

Original `M4 - Real overlay` criteria from `tasks/milestones.md`:

```text
Compact translation.
Genius card.
Hotkeys.
```

M4 is complete at the guarded local browser shell level.

Under `docs/milestone-completion-standard.md`, local browser shell completion is not strict full
completion. Tracked M4 status must distinguish:

```text
automated_complete
manual_verification_required
manual_verification_complete
fully_complete
```

M4 `fully_complete` remains false until the generated local overlay shell is opened and compact
translation, Genius card, and page-local hotkeys are manually verified.

## Completed Criteria

- Compact translation: implemented by `scripts/run_m4_overlay_shell.py`, guarded by
  `tests/test_m4_overlay_shell.py`.
- Genius card: implemented by `scripts/run_m4_overlay_shell.py` using the existing deep overlay
  view model and browser `<details>/<summary>`.
- Hotkeys: implemented by `scripts/run_m4_overlay_shell.py` as page-local browser event listeners.

## Boundaries Still Closed

M4 does not add native always-on-top packaging, Electron/Tauri setup, global keyboard hooks, game
input hooks, clipboard writes, OCR, Unity scanning, hooks/Harmony, provider execution, companion
HTTP contract changes, game-file reads, BepInEx log reads, screenshots, private paths, raw provider
payloads, committed generated shell artifacts, `bin`, or `obj`.

Generated shell HTML is local/private output under:

```text
workspace/local-private/overlay/
```

## Guardrail

The M4 closeout fixture and checker are:

```text
docs/m4-closeout.md
tests/fixtures/m4_closeout.synthetic.json
scripts/check_m4_closeout.py
```

Validate with:

```powershell
python scripts/check_m4_closeout.py --quiet
```

The next bounded roadmap step is:

```text
m5_maximum_quality_pipeline_planning
```
