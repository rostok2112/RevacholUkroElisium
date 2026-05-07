# Next Actions

After Milestone 2G:

1. Keep the provider runtime path mock-only until a later milestone adds explicit real-provider adapters.
2. Run `python scripts/run_provider_contract_regression.py --quiet` before changing provider HTTP response shapes or provider metadata.
3. Keep `provider`, `provider_debug`, and `prompt_pack` runtime metadata free of roadmap provider ids.
4. Keep provider caches under ignored private roots such as `workspace/provider-cache`.
5. Treat registry roadmap ids as config/CLI planning metadata only; they are not current runtime annotation providers.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2G. Read AGENTS.md, docs/devlog/*.md, docs/api/companion-server-contract.md, config/revachol.example.toml, scripts/provider_registry.py, scripts/provider_pipeline.py, scripts/run_provider_pipeline.py, scripts/validate_config.py, tests/test_provider_registry.py, tests/test_provider_pipeline.py, and tests/test_config_validation.py. Implement Milestone 2H: provider request/cache policy preflight. Add stdlib-only dry-run checks that provider requests and future provider configs declare ignored cache roots, redact secret-like config values from summaries, and produce a mock-only provider execution plan. Keep real providers disabled and unimplemented, do not call external services, do not require secrets, do not change the companion HTTP contract, and run python scripts/check_all.py plus the provider contract regression.`
