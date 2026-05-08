# Next Actions

After Milestone 3B:

1. Keep compact/deep modes player-facing and Ukrainian by default.
2. Keep raw provider flags, English provider notes, policy evidence, and privacy/cache internals in debug mode only.
3. Use `python scripts/run_local_overlay_prototype.py --self-test --quiet` before changing overlay rendering behavior.
4. Keep generated overlay artifacts under `workspace/synthetic-slice/overlay-prototype/`.
5. Do not change the companion HTTP provider contract for overlay work without updating the contract docs, client tests, and provider regression runner.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3B. Read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, docs/api/companion-server-contract.md, scripts/local_overlay_prototype.py, scripts/run_local_overlay_prototype.py, scripts/companion_client.py, scripts/companion_server.py, and tests/test_local_overlay_prototype.py. Implement Milestone 3C: overlay view-model fixture regression pack. Add tiny synthetic committed fixtures for compact, deep, and debug overlay view models plus focused regression tests that lock player/debug separation, Ukrainian labels, raw-flag hiding, debug metadata, escaping, and no rendering of context_packet.game.title. Do not commit generated HTML artifacts; keep all data synthetic, localhost-only, stdlib-only, no frontend framework, no real game integration, no extraction, no web/API/LLM calls, no provider execution, no raw prompt/cache logging, and run python scripts/check_all.py plus provider preflight, privacy check, contract regression, and overlay self-test.`
