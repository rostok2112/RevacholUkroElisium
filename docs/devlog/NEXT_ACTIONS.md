# Next Actions

After Milestone 3C:

1. Treat the three committed overlay view-model JSON fixtures as the current overlay UX contract.
2. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay view-model behavior.
3. Regenerate overlay view-model fixtures only with `python scripts/check_overlay_viewmodel_fixtures.py --write`, and review the JSON diff intentionally.
4. Keep generated overlay HTML under ignored `workspace/synthetic-slice/overlay-prototype/`; do not commit generated HTML snapshots.
5. Keep compact/deep modes player-facing and Ukrainian by default; raw provider flags and provider internals belong in debug mode only.
6. Do not change the companion HTTP provider contract for overlay work without updating the contract docs, client tests, and provider regression runner.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3C. Read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, docs/api/companion-server-contract.md, scripts/local_overlay_prototype.py, scripts/run_local_overlay_prototype.py, scripts/check_overlay_viewmodel_fixtures.py, tests/test_local_overlay_prototype.py, and tests/test_overlay_viewmodel_fixtures.py. Implement Milestone 3D: overlay prototype HTML snapshot review workflow. Add a local-only stdlib CLI path that renders compact/deep/debug HTML from the committed overlay view-model fixtures into ignored workspace/synthetic-slice/overlay-prototype/review/, add tests that player HTML hides raw flags and debug HTML stays redacted, keep generated HTML uncommitted, keep all data synthetic/offline/localhost-only, no frontend framework, no production overlay, no BepInEx/OCR/extraction, no web/API/LLM/provider calls, and run python scripts/check_all.py plus the overlay fixture checker and overlay self-test.`
