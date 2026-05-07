# Provider Privacy And Cache Policy

Milestone 2I adds a redacted provider request privacy envelope and cache-write dry-run.

This is not provider execution and not raw payload persistence. It exists so future real provider
work has a safe logging/cache shape before any external adapter is enabled.

## May Be Logged

Provider privacy summaries may include:

- provider id and provider mode
- prompt pack id/version
- context packet id and line id
- synthetic/mock flags
- request field presence
- text lengths and item counts
- SHA-256 digests and deterministic cache keys
- redacted config summaries
- cache root display path
- dry-run cache write plans

## Must Never Be Logged

Provider privacy summaries must not include:

- raw source text
- full prompt pack text or policy sections
- full provider request bodies
- secrets, tokens, passwords, credentials, or API-key-shaped values
- private absolute paths
- real game content beyond schema-required metadata exceptions already documented in the API contract

## Cache Keys

Cache keys use stdlib SHA-256 over canonical JSON containing request identifiers, prompt pack
metadata, requested output fields, quality priorities, spoiler budget, glossary hints, text field
lengths, and text field SHA-256 digests.

Printed cache keys use:

```text
provider-cache-v1.<32 hex chars>
```

The key does not reveal raw text, but it is still derived from request content. Treat it as a local
cache identifier, not public analytics.

## Cache Writes

Milestone 2I creates only a dry-run cache write plan. It does not write raw provider requests or
responses. Planned paths are relative to ignored private roots, for example:

```text
workspace/provider-cache/mock/ukrainian_annotation_v1/provider-cache-v1.<hash>.json
```

Generated redacted privacy summaries may be written only under:

```text
workspace/synthetic-slice/provider-privacy/
```

Future real provider cache persistence still needs retention, deletion, encryption, and audit policy
before it can be enabled.
