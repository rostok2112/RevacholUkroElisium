# Next Actions

After Milestone 4K:

1. Treat ADR 0009 as the current gate: the project is ready for metadata-only extension discussion
   only, not implementation.
2. Keep `tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json` in sync with any
   intentional gate decision change.
3. Keep `implementation_allowed=false`, `text_capture_allowed=false`,
   `current_line_capture_allowed=false`, and `companion_contract_change_allowed=false` until a later
   approved milestone changes the gate.
4. Review local metadata probe reports only with `scripts/review_bepinex_metadata_probe_report.py`
   and keep reports/reviews under the ignored workspace metadata-probe root.
5. Keep `MetadataProbeEnabled=false` and `MetadataProbeLogOnStart=false` as source defaults.
6. Do not commit completed real metadata probe reports, raw BepInEx/game logs, screenshots, private
   paths, payload dumps, save files, OCR output, stack traces, or real game text.
7. Use Milestone 4L to define the exact metadata-only extension scope contract and approval packet,
   still without runtime implementation or capture.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4K. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/adr/0009-metadata-only-extension-gate.md, docs/bepinex-metadata-probe-gate.md, docs/bepinex-bridge.md, packages/bepinex-plugin/DESIGN.md, scripts/check_bepinex_bridge_safety.py, and tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json. Implement Milestone 4L: metadata-only extension scope contract. Define the exact future metadata-only extension scope and approval packet, still without runtime implementation, current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider execution, companion HTTP contract changes, shell work, committed logs, committed screenshots, committed real reports, downloads, or new dependencies.`
