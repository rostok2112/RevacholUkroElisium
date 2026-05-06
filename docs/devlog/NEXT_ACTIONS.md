# Next Actions

After Milestone 2F:

1. Implement Milestone 2G: provider registry and opt-in runtime safety gates before any real provider integration.
2. Keep the default provider path deterministic, mock-only, offline, localhost-only, and synthetic-only.
3. Add provider capability/config scaffolding without calling real APIs or requiring secrets.
4. Keep real provider runtime work blocked behind explicit config, private cache roots, and tests that use mocks only.
5. Continue running the fixture-backed provider contract regression before changing provider HTTP response shapes.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2F. Read AGENTS.md, docs/devlog/*.md, docs/api/companion-server-contract.md, config/revachol.example.toml, scripts/provider_pipeline.py, scripts/run_provider_contract_regression.py, scripts/companion_server.py, scripts/companion_client.py, specs/llm-output-contract.md, and specs/annotation-card.schema.json. Implement Milestone 2G: provider registry and opt-in runtime safety gates. Add stdlib-only provider registry/config scaffolding for mock, future OpenAI-compatible, future DeepL helper, future local model, and future ensemble reviewer roles, but implement only the deterministic mock provider. Real providers must remain disabled unless explicitly configured, tests must not require secrets or network, runtime caches must point to ignored private paths, and server/client behavior must remain mock-only by default. Add tests for provider registry metadata, disabled-by-default real providers, secret-free config validation, cache path safety, no external calls, and provider contract regression still passing. Do not use real Disco Elysium text/assets/audio/screenshots/extracted data, BepInEx, OCR, extraction, web calls, paid APIs, real LLM calls, DeepL calls, local model runtimes, frontend frameworks, production overlay, auth, TLS, persistence, CORS, database work, or new dependencies. Run python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, python scripts/run_provider_contract_regression.py --quiet, python scripts/run_companion_server.py --smoke-test, python scripts/run_companion_client.py smoke-test, python scripts/run_prompt_pack.py --summary, and python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet.`
