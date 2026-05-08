# Next Actions

After Milestone 3D:

1. Treat the three committed overlay view-model JSON fixtures as the current overlay UX contract.
2. Use `python scripts/render_overlay_review.py --quiet` to regenerate local HTML review artifacts from the committed fixtures.
3. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay view-model behavior.
4. Regenerate overlay view-model fixtures only with `python scripts/check_overlay_viewmodel_fixtures.py --write`, and review the JSON diff intentionally.
5. Keep generated overlay HTML under ignored `workspace/synthetic-slice/overlay-prototype/review/`; do not commit generated HTML snapshots.
6. Keep compact/deep modes player-facing and Ukrainian by default; raw provider flags and provider internals belong in debug mode only.
7. Do not change the companion HTTP provider contract for overlay work without updating the contract docs, client tests, and provider regression runner.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3D. Read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, scripts/local_overlay_prototype.py, scripts/check_overlay_viewmodel_fixtures.py, scripts/render_overlay_review.py, tests/test_local_overlay_prototype.py, tests/test_overlay_viewmodel_fixtures.py, and tests/test_overlay_review_renderer.py. Implement Milestone 3E: overlay view-model schema and contract hardening. Add a stdlib-validated JSON schema or schema-like validator for the compact/deep/debug overlay view-model fixtures, wire it into the fixture checker and check_all, document the stable fields for future overlay clients, keep generated HTML uncommitted, keep compact/deep player-facing and debug redacted, use only synthetic fixtures, no frontend framework, no production overlay, no companion HTTP contract changes, no BepInEx/OCR/extraction, no web/API/LLM/provider calls, and run python scripts/check_all.py plus overlay fixture and review renderer checks.`
