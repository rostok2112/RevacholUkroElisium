# Next Actions

After Milestone 4A:

1. Treat `packages/bepinex-plugin/` as a static-reviewable synthetic/manual bridge skeleton, not a
   proven runtime plugin yet.
2. Keep the bridge localhost-only and fake-event-only until build/manual verification is hardened.
3. Do not begin current-line detection, game hooks, Unity object scanning, OCR, extraction, or
   decompiled-code research yet.
4. Keep Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, and
   production overlay work deferred.
5. Make the next milestone 4B: bridge build/manual verification hardening before any real
   game-state capture.
6. Keep `dotnet build` optional/skipping unless user-local .NET SDK and BepInEx references are
   available; never commit those local binaries or paths.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4A. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-bridge.md, docs/adr/0007-overlay-shell-path.md, docs/api/companion-server-contract.md, specs/fake-game-event.schema.json, and inspect packages/bepinex-plugin/, scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_bridge_safety.py, and scripts/check_all.py. Implement Milestone 4B: BepInEx bridge build/manual verification hardening. Add a deterministic verification workflow that can compile the C# skeleton only when dotnet and user-local BepInEx references are explicitly available, otherwise skips clearly. Add or refine static checks for the manual build posture, document a localhost companion health/synthetic-send manual smoke path, keep safety logs metadata-only, update docs/devlog, and run the relevant validation suite. Keep it synthetic/manual only: no real dialogue detection, no game hooks, no Unity object scanning, no OCR, no extraction, no decompiled game code, no copyrighted assets, no provider calls, no production overlay, no keyboard hooks, no clipboard writes, no companion HTTP contract changes, and no new heavy dependencies.`
