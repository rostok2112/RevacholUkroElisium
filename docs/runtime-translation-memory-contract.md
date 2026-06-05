# Runtime Translation Memory Contract

Runtime-first translation must check local translation memory before any provider call. This keeps
repeated visible lines from being translated twice during play.

This contract is local/private only. It does not approve provider execution, game-file extraction,
automatic game scanning, OCR, screenshots, BepInEx log reads, game capture hooks, or committed
runtime artifacts.

## Private Roots

Runtime translation-memory inputs and outputs must stay under ignored workspace roots:

```text
workspace/local-private/runtime-events/
workspace/local-private/runtime-annotations/
workspace/local-private/runtime-cache/translation-memory/
workspace/local-private/runtime-cache/translation-memory-summary/
```

The cache is checked before provider execution. On a cache hit, provider execution is not required.
On a cache miss, provider execution may be required by a later approved runtime translation step, but
provider implementation is not part of this contract.

## Keying

The preferred key is a stable `line_id` from the runtime event. If no `line_id` is available, a
fallback private content key may be derived only inside the ignored cache helper. Public summaries
must not emit keys, hashes, source text, Ukrainian text, prompts, payloads, provider responses,
filenames, or private paths.

## Helper

The machine-readable guardrail is:

```text
docs/runtime-translation-memory-contract.md
tests/fixtures/runtime_translation_memory_contract.synthetic.json
scripts/check_runtime_translation_memory_contract.py
```

The implementation helper is:

```text
scripts/run_runtime_translation_memory.py
```

It supports `lookup`, `store`, and `lookup-or-store` modes. It may write cache entries only under
`workspace/local-private/runtime-cache/translation-memory/` and may write redacted summaries only
under `workspace/local-private/runtime-cache/translation-memory-summary/`.

The companion runtime endpoint now applies this lookup when receiving:

```text
POST /runtime/current-line
```

The endpoint stores the latest runtime event in memory and returns redacted translation-memory
status. It does not execute providers. Runtime capture hooks remain a later local spike.

The targeted hook research boundary is now contract-scoped by:

```text
docs/runtime-targeted-hook-candidate-research-contract.md
```

The next runtime-first step is:

```text
runtime_private_hook_descriptor_local_validation_review_gate
```
