# Known Risks

- Milestone 3I models overlay state-source behavior only. It does not prove real polling cadence,
  lifecycle management, shell rendering, focus behavior, or in-game placement.
- Milestone 3I staleness is deterministic and explicit. There is still no real clock, timer loop, or
  expiry policy for a live overlay shell.
- Milestone 3I CLI self-test uses the existing deterministic mock provider endpoint to seed latest
  provider state; the state-source module itself does not call providers directly.
- Milestone 3I does not add committed state-source fixtures yet. Drift is covered by unit tests and a
  smoke command; Milestone 3J should lock representative ready/no-data/stale/error state outputs if
  the contract remains stable.
- Milestone 3H simulates overlay transitions only. It does not prove real runtime state management,
  keyboard behavior, clipboard behavior, always-on-top behavior, focus behavior, or shell integration.
- Milestone 3H copy and hide actions are previews. Future shell work must keep the boundary clear
  between preview metadata and actual clipboard/UI side effects.
- Milestone 3H transition summaries can include source English for `copy_original`; this remains
  synthetic-only in committed fixtures and checks, and must not become a public/raw real-game logging
  surface.
- Milestone 3H does not add committed transition preview fixtures yet. Drift is covered by tests and
  a smoke command; Milestone 3I should lock representative previews as JSON fixtures if the contract
  remains stable.
- Milestone 3G adds static readability/accessibility guardrails, but they are not a browser audit,
  WCAG certification, visual regression suite, or real player usability test.
- Milestone 3G parses generated HTML strings with Python stdlib only. It can catch structural drift,
  raw debug leaks, and obvious safety issues, but it cannot prove focus behavior, screen-reader
  behavior, contrast, text overflow, or in-game placement.
- The Milestone 3G compact brevity thresholds are deterministic guardrails for the current synthetic
  fixture, not a final product readability model.
- Milestone 3F adds declarative overlay actions and visibility state, but it still does not implement
  real keyboard hooks, clipboard behavior, always-on-top windows, or a live overlay shell.
- Milestone 3F visibility state is a static fixture/default contract, not runtime state management.
- Milestone 3F action catalog changes are overlay contract changes. Update action helpers, validator
  rules, fixtures, tests, and docs together.
- Debug mode carries the full declarative action catalog. Future rendering work must keep debug-only
  actions such as `switch_debug` out of compact/deep player-facing modes.
- Milestone 3E hardens the overlay contract structurally, but it still does not prove production UI quality, accessibility, timing, or in-game placement.
- The Milestone 3E Python validator is intentionally stricter than the old fixture checker. Any deliberate view-model contract change must update validator rules, fixtures, tests, and docs together.
- The Milestone 3E contract is Python-enforced, not a portable JSON Schema yet. Future non-Python overlay clients may need generated schema docs or a formal schema once the shape stabilizes further.
- Milestone 3D HTML review files are generated local artifacts for human inspection only. They are not visual golden snapshots, browser-compatibility tests, or production overlay assets.
- Milestone 3D renders from committed JSON fixtures, so stale fixtures will produce stale review HTML until `scripts/check_overlay_viewmodel_fixtures.py` is run and fixture changes are reviewed.
- The Milestone 3D review index is static and deliberately boring; it does not represent final navigation, hotkeys, focus management, or in-game placement.
- Milestone 3C view-model fixtures lock overlay structure and player/debug separation, but they do not prove real overlay placement, timing, readability, accessibility, or in-game interaction quality.
- Milestone 3C makes `build_overlay_view_model(..., mode=...)` mode-specific. Any future caller that expects compact, deep, and debug sections in one payload must be updated deliberately.
- Overlay fixture updates are now contract changes. Use `scripts/check_overlay_viewmodel_fixtures.py --write` only when the JSON diff is intended and reviewed.
- The committed overlay fixtures are synthetic-only regression artifacts; generated HTML remains local workspace output and must not be committed.
- Milestone 3B improves player/debug separation, but the overlay prototype is still static HTML and not representative of real in-game placement, timing, accessibility, focus, or hotkey behavior.
- Milestone 3B uses deterministic Ukrainian fallback text when mock provider notes are English/debug-like. Real provider output will need stricter language-contract validation before player-facing use.
- Compact/deep modes now hide raw internal flags; future debugging work must avoid reintroducing those flags into player-facing UI.
- The Milestone 3A overlay prototype is static HTML for local review only. It is not an always-on-top window, production overlay, game integration, or accessibility-reviewed player UI.
- Milestone 3A debug mode intentionally shows only provider/prompt-pack metadata and a redacted privacy/cache dry-run summary. It must not grow into raw prompt, full provider request, secret, private path, or raw cache payload logging.
- The Milestone 3A CLI depends on a running localhost companion server for normal latest-state rendering unless `--self-test` or `--post-synthetic-event` is used.
- Generated Milestone 3A overlay artifacts are local review outputs under `workspace/synthetic-slice/overlay-prototype/` and must not be committed.
- The repo uses a lightweight local JSON Schema subset validator for Milestone 0 instead of the full `jsonschema` package.
- No real game extraction exists yet; all public fixtures are synthetic.
- Paid APIs and web retrieval are runtime policy/config only right now; tests and CI must stay mocked and offline.
- Runtime caches may contain copyrighted lines or model outputs later, so they must stay under ignored private roots.
- The Milestone 1A mock annotation output is deterministic and synthetic; it is not a quality translation engine.
- The Milestone 1B review renderer is static HTML for local review only; no production overlay UI exists yet.
- The Milestone 1C eval harness scores structural coverage only. It does not measure real semantic accuracy, Ukrainian literary quality, or player comprehension yet.
- Multiple Milestone 1C cases currently share the same deterministic mock annotation output, so score variation mostly comes from input glossary/context shape and tampering tests.
- The Milestone 1D companion server is a stdlib localhost skeleton only. It is not production security hardened.
- The Milestone 1D server stores latest context/annotation/overlay/eval state in memory only; state disappears on restart.
- The Milestone 1D default bind is `127.0.0.1`, but the CLI allows an explicit different host. Do not expose it beyond localhost without a later security review.
- The Milestone 1D HTTP API has no auth, TLS, persistence, rate limiting, CORS policy, or multi-client session model yet.
- The Milestone 1E companion client is a local contract helper only, not a production SDK.
- The Milestone 1E API contract is still synthetic/offline/mock-only and may need versioning before real overlay or bridge clients depend on it.
- Server/client tests cover localhost behavior only and intentionally do not exercise non-localhost networking.
- The Milestone 2A provider abstraction proves provider contract shape only; the mock provider is not a translation quality engine.
- Milestone 2A provider output intentionally overlaps earlier deterministic mock annotation behavior until Milestone 2B adds richer prompt/style guidance.
- Companion server/client provider endpoints are exposed, but they remain deterministic mock-only and should not be treated as real provider integration.
- Future real providers need cache/privacy enforcement and explicit opt-in config before any runtime calls are enabled.
- The Milestone 2B prompt pack is policy scaffolding only; it does not prove real Ukrainian translation quality by itself.
- Milestone 2B tests now catch shallow structural rewrites of `synthetic_examples.md`, but they still cannot judge the real literary quality of every example.
- Prompt pack text is included in provider requests, which is useful for contract tests but may need trimming or references-only mode before real provider calls.
- Milestone 2C proves prompt-pack policy wiring through the mock provider and eval harness, but it still does not measure semantic translation quality or real player comprehension.
- Milestone 2E formalized `provider`, `provider_debug`, and `prompt_pack` as explicit optional annotation-card schema fields; future metadata shape changes should update schema, fixtures, docs, and tests together.
- Milestone 2D exposes provider annotation over localhost HTTP, but it is still deterministic mock-only and not a real provider integration.
- Milestone 2D latest provider context/annotation state is in-memory only and disappears on server restart.
- The provider endpoint accepts only explicit `input_type` wrappers. Future clients must not rely on unwrapped payload guessing.
- Provider contract fixtures are intentionally thin and synthetic; they lock the local HTTP shape, not translation quality.
- The Milestone 2F provider contract regression runner catches local HTTP shape drift, but it still compares deterministic mock-provider behavior only.
- Milestone 2F review handoff HTML is generated output under ignored workspace paths; it must not be committed as a production overlay artifact.
- Milestone 2G registry roadmap provider ids exist in config/CLI metadata, but they are disabled and unimplemented; they must not leak into public runtime annotation responses or provider contract fixtures.
- Milestone 2G config validation is stricter around provider ids and cache paths; private user configs may need migration from older provider table names.
- Provider selection gates prevent accidental real-provider fallback now, but future real adapters will still need cache privacy, prompt redaction, retry policy, and legal/safety review before use.
- Milestone 2H preflight redaction protects logs and summaries only; it does not replace future real provider request-payload privacy, retention, or audit policy.
- Milestone 2H allows absolute cache roots outside the repo as assumed-private user paths and redacts them in summaries; review this before real provider writes are enabled.
- Milestone 2H preflight can list roadmap provider ids in planning output, but runtime annotation-card metadata and committed provider response fixtures must remain mock-only.
- Milestone 2I cache keys are derived from request metadata and text digests. They avoid raw text exposure but should still be treated as local cache identifiers, not public analytics.
- Milestone 2I privacy envelopes are logging/cache summaries only; they do not implement real payload encryption, deletion, retention, or audit guarantees.
- Milestone 2I cache write plans remain dry-run only. Do not add raw provider request/response persistence without a new privacy review.
- The provider success fixture includes the schema-required `game.title` constant inside context-packet `game.title`; keep that exception narrow and do not allow real game title strings in free-text fixture fields.
- Public annotation-card `provider` metadata omits future provider role lists to keep committed fixtures free of external-service markers.
- Existing legacy `prompts/few-shot/synthetic-examples.md` appears mojibaked and was left untouched; the new pack has fresh UTF-8 synthetic examples.
- Unsafe review output paths are rejected rather than normalized. Future tools should keep this explicit behavior unless there is a documented reason to change it.
- The annotation-card schema was not changed for Milestone 1A. Optional helper fields validate because the schema does not forbid additional properties.
