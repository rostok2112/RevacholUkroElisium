# Next Actions

After Milestone 2H:

1. Keep provider runtime behavior mock-only until a later milestone adds explicit real-provider adapters.
2. Run `python scripts/run_provider_preflight.py --quiet` and `python scripts/run_provider_contract_regression.py --quiet` before changing provider execution or response shapes.
3. Keep generated provider preflight artifacts under `workspace/synthetic-slice/provider-preflight/`.
4. Keep provider cache roots under ignored/private paths such as `workspace/provider-cache`.
5. Treat redaction as log/summary safety only; future real provider payloads still need separate privacy review.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2H. Read AGENTS.md, docs/devlog/*.md, docs/provider-runtime-safety.md, docs/api/companion-server-contract.md, config/revachol.example.toml, scripts/provider_registry.py, scripts/provider_runtime_safety.py, scripts/provider_pipeline.py, scripts/run_provider_preflight.py, scripts/run_provider_pipeline.py, and tests/test_provider_runtime_safety.py. Implement Milestone 2I: provider request privacy envelope and cache write dry-run. Add stdlib-only helpers that wrap provider requests in a redacted logging envelope, compute deterministic cache keys from synthetic provider requests without storing raw source text in public outputs, and dry-run planned cache writes under workspace/provider-cache. Keep real providers disabled/unimplemented, do not call external services, do not persist real request payloads, do not change the companion HTTP contract, and run python scripts/check_all.py plus provider preflight and contract regression.`
