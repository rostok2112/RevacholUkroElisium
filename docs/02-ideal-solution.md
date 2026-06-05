# Ideal Solution

## Name

**Revachol Ukrainian Companion**

## One-sentence architecture

A BepInEx game bridge emits the current dialogue node into a local companion service, which retrieves full local context, generates high-quality Ukrainian translation and annotations through an ensemble pipeline, and renders them in a low-friction overlay with click-to-expand "Genius-like" explanations.

## Main modules

### 1. Game Bridge

Responsibilities:

- detect current dialogue line/node,
- expose speaker, conversation, location, skill voice, branch/options, variables if available,
- emit events over localhost WebSocket/HTTP,
- optionally support hot reload and debug console.

Preferred base of knowledge:
- Disco Translator 2 for database extraction and live string reload concepts.
- DiscoTranslatorFinalCut for text/image/audio extraction concepts.
- BepInEx IL2CPP as mod loader path.

### 2. Context Engine

Responsibilities:

- import locally extracted database,
- build searchable dialogue graph,
- build spoiler-aware context packets,
- retrieve nearby nodes and prior player choices,
- map audio/voice clips when available,
- maintain translation memory and glossary.

### 3. Translation Orchestrator

Pipeline:

1. Normalize current line and metadata.
2. Check runtime translation memory.
3. Retrieve context.
4. Apply glossary and style constraints.
5. Generate baseline translation only on cache miss.
6. Generate annotation only on cache miss.
7. Run QA agents:
   - terminology consistency,
   - voice preservation,
   - spoiler safety,
   - Ukrainian idiom sanity,
   - "too literal / too free" check.
8. Save accepted result in translation memory.

Runtime translation memory is tracked by
`docs/runtime-translation-memory-contract.md`,
`tests/fixtures/runtime_translation_memory_contract.synthetic.json`,
`scripts/check_runtime_translation_memory_contract.py`, and
`scripts/run_runtime_translation_memory.py`. Runtime current-line transport and synthetic capture
spike tooling now exist, and targeted hook research is contract-scoped by
`docs/runtime-targeted-hook-candidate-research-contract.md`. The next runtime-first step is the
redacted report review gate, decision contract, and private descriptor contract, which now advance
only to `runtime_private_hook_descriptor_local_validation_review_gate`.

### 4. Overlay

Modes:

- Compact: one-line Ukrainian translation below/near original.
- Annotation: hover/click reveals idiom/subtext.
- Deep Context: side card with tree/lore/audio notes.
- Debug: shows line IDs, retrieval sources, model outputs, eval score.

### 5. Evaluation Studio

A small local UI/CLI for reviewing golden lines, comparing engines, and approving final translations.

## Not the main path

- Phone translation.
- Manual Google Lens.
- Raw OCR-only loop.
- Blind use of the old Ukrainian AI patch as final truth.
- Full replacement without original/annotation layer.
