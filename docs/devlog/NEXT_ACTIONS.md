# Next Actions

After Milestone 4L:

1. Treat `docs/bepinex-metadata-only-extension-scope.md` as the 4M scope boundary.
2. Keep `tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json` in sync with any
   intentional 4M scope change.
3. 4M may implement only inert counters/booleans, disabled by default, with explicit false capture
   flags.
4. Keep text capture, current-line capture, UI text reading, Unity scanning, hooks, OCR, extraction,
   provider calls, and companion contract changes disallowed.
5. Keep `MetadataProbeEnabled=false` and `MetadataProbeLogOnStart=false` as source defaults unless
   4M adds a new disabled-by-default config inside the same safety boundary.
6. Do not commit completed real metadata probe reports, raw BepInEx/game logs, screenshots, private
   paths, payload dumps, save files, OCR output, stack traces, or real game text.
7. Use Milestone 4M to implement only the inert metadata counters/booleans contract and update
   bridge safety checks before or with implementation.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4L. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-metadata-only-extension-scope.md, docs/adr/0009-metadata-only-extension-gate.md, docs/bepinex-metadata-probe-gate.md, docs/bepinex-bridge.md, packages/bepinex-plugin/DESIGN.md, scripts/check_bepinex_bridge_safety.py, packages/bepinex-plugin/src/MetadataProbe.cs, packages/bepinex-plugin/src/RevacholCompanionBridgePlugin.cs, and tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json. Implement Milestone 4M: inert metadata-only C# extension. Add only disabled-by-default safe counters/booleans allowed by the 4L scope contract, update bridge safety checks/tests before or with implementation, keep all capture flags false, do not read UI text, do not detect current line/dialogue, do not scan Unity objects, do not add hooks/Harmony patches/OCR/extraction/game-file reads/log parsing/screenshots/provider calls/companion HTTP contract changes/shell work/keyboard hooks/clipboard writes/downloads/new dependencies, and run the full validation suite.`
