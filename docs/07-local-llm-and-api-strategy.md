# Local LLM and API Strategy

## Strategy

Use cloud frontier models for maximum quality and local models for privacy, fallback, batching, and experimentation.

The orchestrator must be model-agnostic:
- OpenAI-compatible API adapter,
- Anthropic adapter,
- DeepL adapter,
- local OpenAI-compatible adapter,
- deterministic mock adapter for tests.

## Recommended quality tiers

### Tier 0 — deterministic tests

No API. Golden fixtures only.

### Tier 1 — cheap baseline

DeepL with glossary + local QA checks.

### Tier 2 — good interactive mode

One strong LLM for translation + one lightweight QA pass.

### Tier 3 — maximum quality mode

Ensemble:
- DeepL glossary baseline,
- frontier LLM literary translator,
- separate context annotator,
- separate QA reviewer,
- optional local model as second opinion,
- human review for golden lines.

## AMD RX 7900 XTX note

Do not hard-code a local runtime. Support any OpenAI-compatible local server:
- LM Studio,
- llama.cpp server,
- Ollama where available,
- vLLM/ROCm if the user's environment supports it.

Local models are useful but should not be assumed to beat top paid APIs on Ukrainian literary nuance.
