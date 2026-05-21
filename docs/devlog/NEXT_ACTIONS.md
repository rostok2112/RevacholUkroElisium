# Next Actions

After Milestone 4C:

1. Treat the BepInEx bridge as buildable only through the optional local helper when user-local
   BepInEx references are supplied.
2. Keep `check_all` independent of `dotnet`, BepInEx binaries, and any local game install.
3. Keep `MSB3277` warnings visible and counted; do not hide them unless a later runtime milestone
   deliberately pins/cleans references.
4. Use `docs/manual-smoke/bepinex-bridge-runtime-smoke.md` and the committed log contract fixture for
   user-local runtime verification.
5. Do not begin current-line detection, game hooks, Unity object scanning, OCR, extraction, or
   decompiled-code research yet.
6. Keep Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, and
   production overlay work deferred.
7. Make the next milestone 4D: redacted manual runtime smoke report template/checker before any real
   game-state capture.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4C. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-bridge-runtime-smoke.md, docs/manual-smoke/bepinex-bridge-log-contract.md, packages/bepinex-plugin/README.md, packages/bepinex-plugin/DESIGN.md, and inspect scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_bridge_safety.py, and tests/fixtures/bepinex_bridge.log_contract.synthetic.json. Implement Milestone 4D: redacted manual runtime smoke report template and checker. Add a local-only report template/checker for users to summarize manual bridge startup, health, unavailable-server, and optional synthetic-send observations without committing raw logs. Reports must be redacted, synthetic/manual only, workspace-only when generated, and must not include game text, private paths, raw payloads, stack traces, hooks, OCR/extraction/decompiled markers, provider calls, production overlay work, keyboard hooks, clipboard writes, companion HTTP contract changes, downloads, or new heavy dependencies. Update docs/devlog and run the relevant validation suite.`
