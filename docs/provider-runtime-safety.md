# Provider Runtime Safety

Milestone 2H adds a dry-run preflight layer for future provider execution.

Current runtime behavior remains mock-only:

- `mock` is the only implemented and enabled provider.
- Future provider ids are registry roadmap metadata only.
- Preflight never calls network services, paid APIs, DeepL, local model runtimes, or provider adapters.
- Companion server/client HTTP contracts are unchanged.

## Cache Roots

Provider caches may contain prompts, copyrighted source lines, model outputs, or review traces later.
They must stay under ignored/private roots. The example config uses:

```text
workspace/provider-cache
```

Repo-local cache paths outside ignored private roots, such as `docs/provider-cache`, are rejected.
Absolute paths outside the repo are treated as private user paths and are redacted in summaries.

## Redaction

Preflight summaries redact:

- secret-like keys such as API keys, tokens, passwords, credentials, and bearer values
- secret-looking values such as `sk-...`, bearer tokens, or inline `api_key=...`
- absolute/private-looking filesystem paths

Redaction protects logs and summaries only. Future real provider adapters still need separate request
payload privacy, cache retention, retry, and auditing policy before they can be enabled.

## Tests

Tests and CI must remain offline and synthetic. Use:

```text
python scripts/run_provider_preflight.py --quiet
python scripts/check_all.py
```

Generated preflight artifacts must stay under:

```text
workspace/synthetic-slice/provider-preflight/
```
