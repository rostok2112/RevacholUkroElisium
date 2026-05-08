# Next Actions

After Milestone 3A:

1. Keep the overlay prototype local/static and synthetic-only until a real overlay shell is planned.
2. Use `python scripts/run_local_overlay_prototype.py --self-test --quiet` before changing overlay view-model or rendering behavior.
3. Keep generated overlay artifacts under `workspace/synthetic-slice/overlay-prototype/`.
4. Do not render raw prompt pack text, full provider requests, secrets, private absolute paths, or raw provider cache payloads in debug mode.
5. Do not change the companion HTTP provider contract for overlay work without updating the contract docs, client tests, and provider regression runner.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3A. Read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, docs/api/companion-server-contract.md, scripts/local_overlay_prototype.py, scripts/run_local_overlay_prototype.py, scripts/companion_client.py, scripts/companion_server.py, and tests/test_local_overlay_prototype.py. Implement Milestone 3B: local overlay prototype mode/state contract hardening. Add fixture-backed overlay view-model examples for compact, deep, and debug modes; add regression tests that lock HTML/JSON output shape without committing generated workspace artifacts; keep all data synthetic, localhost-only, stdlib-only, no frontend framework, no real game integration, no extraction, no web/API/LLM calls, no provider execution, no raw prompt/cache logging, and run python scripts/check_all.py plus provider preflight, privacy check, contract regression, and overlay self-test.`
