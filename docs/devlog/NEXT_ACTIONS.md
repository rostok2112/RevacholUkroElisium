# Next Actions

After Milestone 2I:

1. Keep provider runtime behavior mock-only until explicit real-provider adapters are implemented.
2. Run `python scripts/run_provider_preflight.py --quiet`, `python scripts/run_provider_privacy_check.py --quiet`, and `python scripts/run_provider_contract_regression.py --quiet` before changing provider execution, logging, cache, or HTTP response shapes.
3. Keep generated provider privacy artifacts under `workspace/synthetic-slice/provider-privacy/`.
4. Do not persist raw provider request/response payloads yet; cache write plans remain dry-run only.
5. Treat cache keys as local identifiers derived from request structure, not public analytics.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2I. Read AGENTS.md, docs/devlog/*.md, docs/api/companion-server-contract.md, docs/provider-runtime-safety.md, docs/provider-privacy-cache-policy.md, scripts/companion_server.py, scripts/companion_client.py, scripts/synthetic_review_renderer.py, scripts/provider_pipeline.py, scripts/provider_privacy.py, and tests/test_companion_client.py. Implement Milestone 3A: local overlay prototype consuming companion server. Build a minimal local/static or CLI-driven overlay prototype that consumes existing companion server/client synthetic endpoints and renders original English, Ukrainian concise/literary fields, annotations, risk/confidence, and provider/prompt-pack debug metadata. Keep it synthetic-only, offline, localhost-only, no frontend framework unless already present, no real game integration, no extraction, no web/API/LLM calls, no companion HTTP contract breaking changes, and run python scripts/check_all.py plus provider preflight, provider privacy check, and provider contract regression.`
