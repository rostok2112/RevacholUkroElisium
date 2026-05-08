# Next Actions

After Milestone 3E:

1. Treat the Python validator plus the three committed overlay view-model JSON fixtures as the current overlay UX contract.
2. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay view-model behavior.
3. Use `python scripts/render_overlay_review.py --quiet` to regenerate local HTML review artifacts from validated fixtures.
4. Regenerate overlay view-model fixtures only with `python scripts/check_overlay_viewmodel_fixtures.py --write`, and review the JSON diff intentionally.
5. Keep generated overlay HTML under ignored `workspace/synthetic-slice/overlay-prototype/review/`; do not commit generated HTML snapshots.
6. Keep compact/deep modes player-facing and Ukrainian by default; raw provider flags and provider internals belong in debug mode only.
7. Future overlay clients should consume validated JSON view models, not parse generated review HTML.
8. Do not change the companion HTTP provider contract for overlay work without updating the contract docs, client tests, and provider regression runner.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3E. Read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, scripts/local_overlay_prototype.py, scripts/overlay_viewmodel_validator.py, scripts/check_overlay_viewmodel_fixtures.py, scripts/render_overlay_review.py, tests/test_local_overlay_prototype.py, tests/test_overlay_viewmodel_validator.py, tests/test_overlay_viewmodel_fixtures.py, and tests/test_overlay_review_renderer.py. Implement Milestone 3F: overlay interaction state and action contract. Add a stdlib-only synthetic view-model extension for visibility state, available mode actions, and human-facing Ukrainian action labels/hints, validate it without leaking raw debug flags into compact/deep modes, update fixtures intentionally, render review HTML from validated fixtures, keep generated HTML uncommitted, no frontend framework, no production overlay, no keyboard hooks, no companion HTTP contract changes, no BepInEx/OCR/extraction, no web/API/LLM/provider calls, and run python scripts/check_all.py plus overlay validator, fixture, review renderer, and self-test checks.`
