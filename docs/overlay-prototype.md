# Local Overlay Prototype

Milestone 3A adds a local static overlay prototype for synthetic review and client-contract work.
It is not a production overlay, not game integration, and not an always-on-top window.

The prototype consumes the existing localhost companion client/provider annotation contract:

```text
synthetic fake event -> /synthetic/provider-annotate -> context packet + annotation card -> overlay view model
```

## What It Shows

- Compact mode: original English, concise Ukrainian meaning, human-readable Ukrainian confidence
  and risk status, whether deeper notes are available, and concise Ukrainian action hints.
- Deep mode: original English, literary Ukrainian rendering, explanation, idiom/reference/subtext
  notes, tone/voice notes, glossary terms, spoiler status, uncertainty/risk summary, and
  Ukrainian action hints for moving through annotation content.
- Debug mode: provider metadata, prompt pack metadata, and a redacted provider privacy/cache dry-run
  summary, plus the full declarative action catalog for developer inspection.

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

Milestone 3C adds committed JSON view-model fixtures. Milestone 3E hardens those fixtures with a
stdlib-only Python validator in `scripts/overlay_viewmodel_validator.py`. Together, the fixtures and
validator are the current overlay view-model contract:

```text
tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json
tests/fixtures/overlay_prototype.deep.viewmodel.synthetic.json
tests/fixtures/overlay_prototype.debug.viewmodel.synthetic.json
```

The fixtures are mode-specific:

- Compact fixtures contain only `schema_version`, `mode`, `source`, and `compact`.
- Deep fixtures contain only `schema_version`, `mode`, `source`, and `deep`.
- Debug fixtures contain only `schema_version`, `mode`, `source`, and `debug`.

Common stable fields:

- `schema_version`
- `mode`
- `source.original_english`
- `source.speaker`
- `source.scene_id`
- `source.conversation_id`
- `source.line_id`

Each mode payload also carries declarative interaction state:

- `visibility.original_visible`
- `visibility.translation_visible`
- `visibility.annotations_visible`
- `visibility.debug_visible`
- `visibility.current_mode`
- `visibility.available_modes`
- `actions`

Actions are contract metadata only. They describe the controls a future overlay shell may expose, but
they do not implement keyboard hooks, global shortcuts, clipboard behavior, an always-on-top window,
or any live UI shell.

Each action has:

- `id`
- `label_uk`
- `hint_uk`
- `allowed_modes`
- `player_facing`
- `debug_only`

Player-facing action labels and hints are Ukrainian. Compact and deep fixtures expose only
player-facing actions. Debug fixtures carry the full declarative action catalog, including the
developer-only switch into debug mode, so future clients can inspect the whole contract safely.

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

Future overlay clients should consume the JSON view models. They should not parse generated review
HTML, which is only a local human-inspection artifact.

## HTML Review Workflow

Milestone 3D adds a fixture-backed HTML review workflow:

```text
python scripts/render_overlay_review.py --quiet
```

This renders the committed JSON view-model fixtures into local review files under:

```text
workspace/synthetic-slice/overlay-prototype/review/
```

Default output files:

- `compact.html`
- `deep.html`
- `debug.html`
- `index.html`

The review renderer is intentionally fixture-based. It does not start the companion server, call the
mock provider pipeline, regenerate fixtures, contact a network service, or read local game data. Its
purpose is human inspection of the current committed overlay UX contract.

The review HTML is generated output and must stay uncommitted. The compact and deep pages are
player-facing snapshots and must hide raw internal flags. The debug page is developer-facing and may
show raw provider metadata only in redacted form.

## Static Readability Checks

Milestone 3G adds a fixture-backed structural readability/accessibility checker:

```text
python scripts/check_overlay_review_accessibility.py --quiet
```

The checker renders compact, deep, and debug HTML from committed JSON view-model fixtures in memory
and inspects the result with Python stdlib `html.parser`.

It checks:

- `lang="uk"`
- nonempty title and `h1`
- sane heading order for the static prototype
- expected compact/deep/debug section ids
- visible player-facing action hints in compact/deep
- compact-mode brevity
- grouped Ukrainian deep-mode headings
- debug metadata presence and redaction
- no raw internal flags in compact/deep
- no rendered `context_packet.game.title`
- no raw prompt, secret, private path, future provider marker, external URL, JavaScript URL, event
  handler attribute, or unescaped script tag

This is a structural guardrail only. It is not a browser accessibility audit, not WCAG
certification, not visual testing, and not a substitute for later real overlay usability review.

## Transition Preview Simulator

Milestone 3H adds a declarative overlay action/state transition simulator:

```text
python scripts/run_overlay_state_simulator.py --fixture compact --action switch_deep --quiet
```

The simulator consumes validated compact, deep, or debug JSON view models and returns a transition
preview. It does not mutate the input view model and does not implement a real UI side effect.

Transition previews include:

- source mode and requested action id
- Ukrainian action label and hint
- whether the action is allowed
- a stable blocked reason when it is not allowed
- next mode and next visibility preview
- side-effect type: `none`, `copy_preview`, or `hide_preview`
- copy preview text for copy actions, without writing to the clipboard
- a Ukrainian human-facing summary
- explicit flags showing no clipboard write, keyboard hook, companion server call, provider call, or
  input mutation happened

Mode switches and visibility toggles only preview the next state. Copy actions only expose the text
that a future shell could copy. Hide only sets `hidden = true` in the preview visibility. Navigation
actions preview movement through annotation notes without changing a real index.

The simulator blocks unknown actions, actions absent from the current view model, debug-only actions
from compact/deep modes, actions not allowed in the current mode, malformed view models, and invalid
visibility state. Transition summaries are scanned for the same safety posture: no rendered
`context_packet.game.title`, raw prompts, secrets, private paths, future provider markers, generated
HTML payloads, or external URLs.

Generated transition summaries, when requested, are local artifacts only and must stay under:

```text
workspace/synthetic-slice/overlay-prototype/transitions/
```

This is still declarative contract work. It is not keyboard hooks, global hotkeys, clipboard
integration, an always-on-top window, JavaScript, a browser shell, or production overlay behavior.

## State Source Contract

Milestone 3I adds a side-effect-free state-source contract for future overlay shells:

```text
python scripts/run_overlay_state_source.py --self-test --quiet
```

The state-source layer reads the latest provider context and annotation through the existing
companion client contract and turns them into a current overlay render state. It does not change the
companion HTTP API and does not implement a polling loop.

State-source results use `schema_version: "overlay-state-source.v1"` and model:

- `ready`: latest provider context and annotation were available and produced a valid overlay view
  model.
- `no_provider_state`: no latest provider context or annotation is available yet.
- `stale`: an existing view model is being reused deterministically as stale state.
- `error`: companion client, partial-state, or malformed provider-state failures.

Ready and stale results include:

- current mode
- validated mode-specific overlay view model
- visibility state
- available actions
- stale-after threshold, currently deterministic and not time-driven
- latest line/update id when available
- safe debug summary in debug mode

All state-source results explicitly report that no polling loop, timer, background thread, provider
call, companion HTTP contract change, UI side effect, or clipboard write happened. Staleness is
represented by explicit inputs such as `stale=True` or previous state fallback; there is no real
timer and no flaky time-based behavior.

Generated state-source summaries, when requested, are local artifacts only and must stay under:

```text
workspace/synthetic-slice/overlay-prototype/state/
```

## State Source Fixtures

Milestone 3J adds committed synthetic JSON fixtures for the state-source contract:

```text
tests/fixtures/overlay_state_source.ready.compact.synthetic.json
tests/fixtures/overlay_state_source.ready.deep.synthetic.json
tests/fixtures/overlay_state_source.ready.debug.synthetic.json
tests/fixtures/overlay_state_source.no_provider_state.synthetic.json
tests/fixtures/overlay_state_source.stale.synthetic.json
tests/fixtures/overlay_state_source.error.synthetic.json
```

Use the fixture checker before changing state-source behavior:

```text
python scripts/check_overlay_state_source_fixtures.py --quiet
```

Fixture updates must be intentional:

```text
python scripts/check_overlay_state_source_fixtures.py --write
```

Ready fixtures embed validated mode-specific overlay view models. The stale fixture reuses a
validated previous view model with deterministic stale metadata. The no-provider fixture represents
absence as a valid state, not a crash. The error fixture is redacted and must not include raw
provider payloads, prompts, secrets, private paths, generated HTML, future provider markers, or
`context_packet.game.title`.

The fixtures and checker are the current state-source handoff contract for a future overlay shell.
They still do not implement polling cadence, timers, retries, background workers, UI side effects, or
provider execution.

This is a future-shell handoff contract. It is not a daemon, live polling loop, browser shell,
JavaScript runtime, keyboard hook, clipboard integration, always-on-top overlay, provider execution,
or production UI.

## Current Limits

- Synthetic-only public data.
- Localhost-only companion access.
- Deterministic mock provider only.
- No frontend framework, JavaScript, external CSS, browser automation, assets, OCR, BepInEx,
  extraction, real provider call, web call, paid API call, DeepL call, or local model runtime.

Future milestones can use this view-model shape as a handoff point for a real overlay shell after the
local HTTP contract, privacy policy, and player-facing UX are more stable.
