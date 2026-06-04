# M3 Closeout

Original `M3 - BepInEx bridge` criteria from `tasks/milestones.md`:

```text
Emit current line event.
Match line IDs.
Debug console.
```

M3 is complete at the guarded implementation level.

## Completed Criteria

- Current-line event: implemented by `packages/bepinex-plugin/src/CurrentLineEventFactory.cs`,
  guarded by `tests/fixtures/m3_current_line_event_implementation.synthetic.json` and
  `scripts/check_m3_current_line_event_implementation.py`.
- Line-ID matching: implemented by `scripts/run_m3_line_id_match.py`, guarded by
  `tests/fixtures/m3_line_id_matching.synthetic.json` and `tests/test_m3_line_id_match.py`.
- Debug console: implemented by `packages/bepinex-plugin/src/DebugCommandHandler.cs`, guarded by
  `tests/fixtures/m3_debug_console.synthetic.json` and `scripts/check_m3_debug_console.py`.

## Boundaries Still Closed

M3 does not commit raw game text, extracted DBs, private indexes, private paths, logs, screenshots,
provider payloads, `bin`, or `obj`. M3 does not add OCR, broad Unity scanning, hooks/Harmony,
provider execution, companion HTTP contract changes, game-file reads, BepInEx log reads, raw text
dumps, payload dumps, or ID dumps.

The current-line event and debug console are disabled by default. The matcher reads ignored private
inputs only when explicitly invoked and emits redacted summaries only.

## Guardrail

The M3 closeout fixture and checker are:

```text
docs/m3-closeout.md
tests/fixtures/m3_closeout.synthetic.json
scripts/check_m3_closeout.py
```

Validate with:

```powershell
python scripts/check_m3_closeout.py --quiet
```

The next bounded roadmap step is:

```text
m4_real_overlay_scope_recovery
```
