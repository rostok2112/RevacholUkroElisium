# Next Actions

After Milestone 2C:

1. Implement Milestone 2D: expose the mock provider pipeline through the local companion server/client contract.
2. Add a tiny `POST /synthetic/provider-annotate` endpoint only for synthetic context packets or fake events, using the existing envelope contract.
3. Add companion client support and API contract docs for the provider endpoint.
4. Keep provider endpoint responses schema-valid, prompt-pack-aware, and mock-only/offline.
5. Keep all tests offline, deterministic, synthetic-only, and free of real game content or provider calls.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2C. Read AGENTS.md, docs/devlog/*.md, docs/api/companion-server-contract.md, docs/05-quality-model.md, specs/context-packet.schema.json, specs/annotation-card.schema.json, scripts/companion_server.py, scripts/companion_client.py, scripts/provider_pipeline.py, scripts/synthetic_slice.py, and tests/test_companion_server.py, tests/test_companion_client.py, tests/test_provider_pipeline.py. Implement Milestone 2D: expose the prompt-pack-aware mock provider pipeline through the local companion server/client contract. Add a minimal localhost-only POST /synthetic/provider-annotate endpoint that accepts either a synthetic context packet or synthetic fake game event, validates input, runs only the deterministic mock provider pipeline, returns the standard JSON envelope with context packet and annotation card, stores latest provider annotation state if low-risk, and updates the companion client plus API contract docs. Do not call real LLMs, paid APIs, web APIs, DeepL, local model runtimes, OCR, extraction, BepInEx, or use real game content. Keep tests offline and synthetic. Run python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, python scripts/run_companion_server.py --smoke-test, python scripts/run_companion_client.py smoke-test, python scripts/run_prompt_pack.py --summary, and python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet.`
