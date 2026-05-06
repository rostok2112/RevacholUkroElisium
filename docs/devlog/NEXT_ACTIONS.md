# Next Actions

After Milestone 2A:

1. Implement Milestone 2B: prompt quality pack and Ukrainian annotation style guide.
2. Add versioned prompt/style guidance for synthetic provider requests, preserving English canonical text and Ukrainian literary nuance.
3. Add synthetic prompt fixtures or golden prompt snapshots that do not contain real game content.
4. Add tests for prompt-pack loading, style guide safety rules, and provider request compatibility.
5. Decide whether to expose provider annotation through companion server/client after the style pack stabilizes.
6. Keep real extraction, BepInEx, OCR, paid APIs, web calls, real LLM calls, DeepL calls, local model runtime calls, production overlay work, frontend frameworks, and real game assets out of tests and the public repo.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2A. Read AGENTS.md, docs/devlog/*.md, docs/05-quality-model.md, docs/08-overlay-ux.md, specs/llm-output-contract.md, scripts/provider_pipeline.py, and prompts/system/*.md, then implement Milestone 2B: prompt quality pack and Ukrainian annotation style guide. Add versioned prompt/style guidance for the provider pipeline using synthetic-only examples, covering Ukrainian concise meaning, literary rendering, idiom/reference/subtext explanation, character voice, uncertainty/risk flags, spoiler discipline, anti-hallucination, Russianism avoidance, and no silent over-localization. Add tests that prompt-pack loading and provider request compatibility are deterministic, offline, and synthetic-only. Do not call real LLMs, paid APIs, web APIs, DeepL, local model runtimes, OCR, extraction, BepInEx, or use real game content. Run python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, python scripts/run_companion_server.py --smoke-test, python scripts/run_companion_client.py smoke-test, and python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet.`
