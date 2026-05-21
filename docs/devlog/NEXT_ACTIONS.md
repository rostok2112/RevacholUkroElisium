# Next Actions

After Milestone 4D:

1. Treat manual runtime smoke evidence as redacted summaries only; keep raw BepInEx/game logs,
   screenshots, private paths, payload dumps, and stack traces out of git.
2. Store any user-local report templates or completed reports only under
   `workspace/synthetic-slice/bepinex-bridge/runtime-smoke/`.
3. Keep `check_all` independent of a real runtime report, `dotnet`, BepInEx binaries, and any local
   game install.
4. Continue using `docs/manual-smoke/bepinex-bridge-runtime-smoke.md`,
   `docs/manual-smoke/bepinex-bridge-log-contract.md`, and
   `docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md` for user-local verification.
5. Do not begin game hooks, dialogue detection, Unity object scanning, OCR, extraction, or
   decompiled-code research until a later scoped milestone explicitly does so.
6. Keep Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, and
   production overlay work deferred.
7. Make the next milestone 4E: manual runtime smoke evidence review and bridge readiness decision
   before any current-line capture research.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4D. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-bridge-runtime-smoke.md, docs/manual-smoke/bepinex-bridge-log-contract.md, docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md, packages/bepinex-plugin/README.md, packages/bepinex-plugin/DESIGN.md, and inspect scripts/check_bepinex_bridge_safety.py, scripts/check_bepinex_runtime_smoke_report.py, scripts/build_bepinex_bridge.py, tests/test_bepinex_runtime_smoke_report.py, tests/test_bepinex_bridge_safety.py, and tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json. Implement Milestone 4E: manual runtime smoke evidence review and bridge readiness decision. Review the redacted report workflow, document how to evaluate a user-supplied local smoke report, add any needed report summary/review helper that remains workspace-only and synthetic/manual, decide whether the bridge is ready for a later narrowly scoped current-line capture research milestone, update docs/devlog, and run the relevant validation suite. Do not add game hooks, dialogue detection, Unity object scanning, OCR, extraction, decompiled-code work, provider execution, shell work, keyboard hooks, clipboard writes, companion HTTP contract changes, downloads, or new dependencies.`
