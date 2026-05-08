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

## View-Model Fixtures

Milestone 3C adds committed JSON view-model fixtures as the current overlay UX contract:

```text
tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json
tests/fixtures/overlay_prototype.deep.viewmodel.synthetic.json
tests/fixtures/overlay_prototype.debug.viewmodel.synthetic.json
```

The fixtures are mode-specific:

- Compact fixtures contain only `schema_version`, `mode`, `source`, and `compact`.
- Deep fixtures contain only `schema_version`, `mode`, `source`, and `deep`.
- Debug fixtures contain only `schema_version`, `mode`, `source`, and `debug`.

This keeps player-facing modes free of raw internal flags and provider internals. Debug mode is the
only committed view model that carries raw flags, provider metadata, prompt-pack metadata, and the
redacted privacy/cache dry-run summary.

Use the fixture checker before changing overlay view-model behavior:

```text
python scripts/check_overlay_viewmodel_fixtures.py --quiet
```

Fixture updates must be intentional:

```text
python scripts/check_overlay_viewmodel_fixtures.py --write
```

Generated HTML remains a local review artifact and is not committed. The fixture checker validates
that the committed JSON view models do not contain generated HTML, raw prompt text, secrets, private
absolute paths, future provider markers, or `context_packet.game.title`.

## Current Limits

- Synthetic-only public data.
- Localhost-only companion access.
- Deterministic mock provider only.
- No frontend framework, JavaScript, external CSS, assets, OCR, BepInEx, extraction, real provider
  call, web call, paid API call, DeepL call, or local model runtime.

Future milestones can use this view-model shape as a handoff point for a real overlay shell after the
local HTTP contract, privacy policy, and player-facing UX are more stable.
