# Local Overlay Prototype

Milestone 3A adds a local static overlay prototype for synthetic review and client-contract work.
It is not a production overlay, not game integration, and not an always-on-top window.

The prototype consumes the existing localhost companion client/provider annotation contract:

```text
synthetic fake event -> /synthetic/provider-annotate -> context packet + annotation card -> overlay view model
```

## What It Shows

- Compact mode: original English, concise Ukrainian meaning, human-readable Ukrainian confidence
  and risk status, and whether deeper notes are available.
- Deep mode: original English, literary Ukrainian rendering, explanation, idiom/reference/subtext
  notes, tone/voice notes, glossary terms, spoiler status, and uncertainty/risk summary.
- Debug mode: provider metadata, prompt pack metadata, and a redacted provider privacy/cache dry-run
  summary.

Compact and deep modes are player-facing. They must not show raw internal flags such as
`synthetic_fixture`, `mock_provider`, or `prompt_pack_guided`. They should use Ukrainian labels and
short Ukrainian summaries instead of Python/debug-looking booleans.

Deep mode groups player-facing content as:

- Оригінал
- Літературний український варіант
- Що тут відбувається
- Підтекст / іронія / референс
- Тон / голос
- Глосарій
- Ризики / невпевненість

English provider notes, policy evidence, and raw model/provider metadata belong in debug mode unless
they are explicitly source/original text.

Debug mode must not show raw prompt pack text, full provider request bodies, secrets, API-key-shaped
values, private absolute paths, or generated cache payloads.

## Local Output Policy

The CLI writes generated HTML/JSON only under:

```text
workspace/synthetic-slice/overlay-prototype/
```

Unsafe output paths are rejected. Generated overlay artifacts are local review outputs and should not
be committed.

## Current Limits

- Synthetic-only public data.
- Localhost-only companion access.
- Deterministic mock provider only.
- No frontend framework, JavaScript, external CSS, assets, OCR, BepInEx, extraction, real provider
  call, web call, paid API call, DeepL call, or local model runtime.

Future milestones can use this view-model shape as a handoff point for a real overlay shell after the
local HTTP contract, privacy policy, and player-facing UX are more stable.
