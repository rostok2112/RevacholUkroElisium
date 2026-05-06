# Next Actions

After Milestone 1D:

1. Implement Milestone 1E as a local synthetic client/contract hardening slice.
2. Add a tiny stdlib polling client or CLI demo that reads the companion server endpoints and prints an overlay-facing compact/deep state.
3. Add contract docs for companion server clients: request/response envelopes, error codes, state endpoints, and localhost/offline/mock limitations.
4. Add tests for client behavior using an in-process localhost server; do not require a long-running server.
5. Keep server state in memory unless a future milestone explicitly adds ignored local persistence.
6. Keep paid APIs, web retrieval, extraction, BepInEx, OCR, production overlay work, frontend frameworks, and real game assets out of tests and out of the public repo.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 1D. Read AGENTS.md and docs/devlog/*.md, then implement Milestone 1E: a stdlib-only local companion client/contract hardening slice. Reuse the existing companion server in-process for tests, add a tiny polling client or CLI demo that reads /health, /state/latest-context, /state/latest-annotation, /state/latest-overlay-demo, and /review/latest.html, and document the server envelope/error contract for future overlay and BepInEx clients. Keep everything synthetic/offline/mock-only, bind tests to 127.0.0.1, do not use real game content, BepInEx, OCR, extraction, web calls, paid APIs, LLM calls, frontend frameworks, production overlay work, auth, TLS, or new dependencies. Run python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, and python scripts/run_companion_server.py --smoke-test.`
