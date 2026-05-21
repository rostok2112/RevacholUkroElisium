# BepInEx Plugin Design

## Milestone 4A boundary

The bridge is currently a synthetic/manual communication skeleton only. It exists to prove a safe
shape for future game-to-companion communication before any real game-state capture is attempted.

## Responsibilities now

- Load as a BepInEx plugin skeleton.
- Bind safe config defaults.
- Check the localhost companion `/health` endpoint.
- Optionally send one built-in synthetic fake event when explicitly configured.
- Provide safe logs for enabled/disabled state, companion availability, event id, line id, and HTTP
  status.
- Match the Milestone 4C manual log contract in
  `tests/fixtures/bepinex_bridge.log_contract.synthetic.json`.

## Anti-goals now

- No real dialogue detection.
- No game hooks or Unity object scanning.
- No OCR, extraction, decompiled game-code integration, or bundled translation database.
- No cloud calls, provider execution, keyboard hooks, clipboard writes, or production overlay shell.
- No hard dependency on the companion server being available.

## Future

- User-local manual runtime smoke report capture and redaction checks.
- Manual in-game command or debug panel for sending the synthetic event.
- Carefully scoped current-line detection research after the skeleton proves safe installation and
  localhost communication.
- Later shell/window work only after bridge feasibility is better understood.

## Milestone 4B build posture

`scripts/build_bepinex_bridge.py` can optionally compile the bridge when `dotnet` and user-local
BepInEx IL2CPP references are supplied. The helper skips cleanly otherwise, reports warning counts,
and remains outside mandatory `check_all`.

`MSB3277` reference-version warnings are visible and allowed in 4B if the build succeeds and the
static safety checks pass. They are not hidden, and later runtime testing can decide whether the
reference set needs cleanup.

## Milestone 4C runtime smoke posture

Manual runtime verification is documented under `docs/manual-smoke/`. The repo commits expected log
snippets and forbidden log categories, but does not commit local runtime logs or reports. The bridge
still has no game hooks, Unity object scanning, current-line detection, OCR, extraction, provider
execution, keyboard hooks, clipboard writes, or companion HTTP contract changes.

## Milestone 4D report posture

Manual smoke evidence is summarized through a redacted JSON report contract only. The committed
fixture is synthetic and marked `not_run`; user-local reports belong under
`workspace/synthetic-slice/bepinex-bridge/runtime-smoke/` and are validated with
`scripts/check_bepinex_runtime_smoke_report.py`. The checker rejects raw logs, stack traces, payload
dumps, private paths, screenshots/assets/audio markers, real game content markers, hooks,
OCR/extraction/decompiled markers, provider execution markers, and non-localhost URLs.
