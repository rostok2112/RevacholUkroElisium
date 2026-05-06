# Next Actions

After Milestone 2D:

1. Implement Milestone 2E: provider contract fixtures and schema/documentation hardening.
2. Add tiny synthetic request/response fixtures for `POST /synthetic/provider-annotate`.
3. Decide whether to formalize `provider`, `provider_debug`, and `prompt_pack` as optional annotation-card schema fields.
4. Add contract drift tests that compare docs/fixtures/client/server shapes where practical.
5. Keep all tests offline, deterministic, synthetic-only, and free of real game content or provider calls.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2D. Read AGENTS.md, docs/devlog/*.md, docs/api/companion-server-contract.md, specs/context-packet.schema.json, specs/annotation-card.schema.json, scripts/companion_server.py, scripts/companion_client.py, scripts/provider_pipeline.py, tests/test_companion_server.py, tests/test_companion_client.py, and tests/test_provider_pipeline.py. Implement Milestone 2E: provider contract fixtures and schema/documentation hardening. Add tiny synthetic fixtures for POST /synthetic/provider-annotate fake_event and context_packet requests plus a representative success response, keep all fixture text invented, add tests proving fixtures validate and match the documented/client/server envelope shape, and decide whether provider, provider_debug, and prompt_pack should become explicit optional annotation-card schema fields. If schema changes are needed, make them additive, optional, backward compatible, and test-covered. Do not call real LLMs, paid APIs, web APIs, DeepL, local model runtimes, OCR, extraction, BepInEx, or use real game content. Keep tests offline and synthetic. Run python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, python scripts/run_companion_server.py --smoke-test, python scripts/run_companion_client.py smoke-test, python scripts/run_prompt_pack.py --summary, and python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet.`
