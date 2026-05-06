# Next Actions

After Milestone 2E:

1. Implement Milestone 2F: fixture-backed provider contract regression runner and local review handoff.
2. Keep the provider path deterministic, mock-only, offline, localhost-only, and synthetic-only.
3. Use the new provider contract fixtures as stable inputs and the success fixture as the drift reference.
4. Continue keeping generated outputs under ignored `workspace/synthetic-slice/` paths.
5. Do not start real provider integration until cache/privacy/config boundaries are explicitly designed.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2E. Read AGENTS.md, docs/devlog/*.md, docs/api/companion-server-contract.md, specs/context-packet.schema.json, specs/annotation-card.schema.json, scripts/companion_server.py, scripts/companion_client.py, scripts/provider_pipeline.py, scripts/synthetic_review_renderer.py, tests/fixtures/provider_annotate.*.synthetic.json, and tests/test_provider_contract_fixtures.py. Implement Milestone 2F: fixture-backed provider contract regression runner and local review handoff. Add a stdlib-only CLI that loads the provider_annotate synthetic request/response fixtures, starts an in-process 127.0.0.1 companion server, posts both request fixtures, compares deterministic responses to the success fixture, validates nested context and annotation schemas, and optionally writes a JSON or Markdown summary plus review HTML only under workspace/synthetic-slice/provider-contract/. Add tests for drift detection, unsafe output rejection, fixture-only operation, no external services, and check_all smoke integration. Do not use real Disco Elysium text/assets/audio/screenshots/extracted data, BepInEx, OCR, extraction, web calls, paid APIs, real LLM calls, DeepL calls, local model runtimes, frontend frameworks, production overlay, auth, TLS, persistence, CORS, or new dependencies. Run python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, python scripts/run_companion_server.py --smoke-test, python scripts/run_companion_client.py smoke-test, python scripts/run_prompt_pack.py --summary, and python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet.`
