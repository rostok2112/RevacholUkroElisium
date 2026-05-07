# Session Summary

Milestone 2H provider runtime safety preflight is implemented.

Completed in the latest session:
- Added `scripts/provider_runtime_safety.py`, a stdlib-only dry-run safety layer for future provider execution.
- The preflight builds a redacted provider execution plan with active provider, enabled/implemented state, provider mode, network/secrets/runtime flags, cache-root privacy status, prompt pack id/version, warnings, and blocked reasons.
- `mock` preflight passes with `workspace/provider-cache`, `dry_run = true`, `calls_external_services = false`, no network, no secrets, and no local runtime requirement.
- Future provider ids produce blocked plans before any provider adapter, network, paid API, DeepL, or local runtime path can run.
- Added deterministic redaction for secret-like keys, secret-like values, and absolute/private-looking paths in summaries.
- Added `scripts/run_provider_preflight.py`, defaulting to `config/revachol.example.toml`, printing JSON by default, supporting `--quiet`, and writing only under ignored `workspace/synthetic-slice/provider-preflight/`.
- Added `docs/provider-runtime-safety.md` documenting cache-root policy, redacted summaries, mock default, future-provider opt-in, and offline tests.
- Added `tests/test_provider_runtime_safety.py` covering mock pass, unknown/disabled/unimplemented future provider blocking, external opt-in blocking, cache-root safety, output-path safety, redaction, fixture metadata isolation, and CLI behavior.
- Added `python scripts/run_provider_preflight.py --quiet` to `scripts/check_all.py`.
- Did not change schemas, fixtures, companion server/client HTTP contract, provider execution behavior, or add dependencies.
- Validation completed after formatting the new safety module:
  - `python scripts/check_all.py` passed, including 149 unit tests, provider preflight smoke, provider registry smoke, provider contract regression smoke, companion smokes, Ruff check, and Ruff format check.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 149 tests.
  - `npm run check` passed.
  - `python scripts/run_provider_contract_regression.py --quiet` passed.
  - `python scripts/run_provider_preflight.py --quiet` passed.
  - `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Milestone 2G provider registry and runtime safety gates is implemented.

Completed in the latest session:
- Added `scripts/provider_registry.py`, a stdlib-only registry for provider ids:
  - `mock`
  - `openai_compatible`
  - `deepl_glossary`
  - `local_model`
  - `ensemble_reviewer`
- The only implemented/enabled/default provider is `mock`; all roadmap providers are disabled and unimplemented.
- Added `scripts/run_provider_registry.py --summary` for local registry inspection without provider calls, secrets, network, or runtime adapters.
- Routed `scripts/provider_pipeline.py` provider selection through the registry so unknown, disabled, external-disallowed, and unimplemented providers fail before any adapter can run.
- Removed the redundant future-role list from internal mock provider metadata; public annotation-card metadata and provider contract fixtures remain mock-only.
- Updated `scripts/run_provider_pipeline.py --provider` so registry ids can be passed and disabled roadmap providers fail through runtime safety gates rather than argparse-only choices.
- Updated `config/revachol.example.toml` with explicit mock-only provider settings:
  - `active_provider = "mock"`
  - `allow_external_providers = false`
  - `provider_cache_dir = "workspace/provider-cache"`
  - disabled `[llm.providers.<id>]` roadmap placeholders without inline keys, fake secrets, base URLs, or required env vars.
- Hardened `scripts/validate_config.py` to validate registry ids, active provider selectability, external-provider opt-in, provider cache path safety, and secret-looking inline values.
- Added provider registry, provider pipeline, and config validation tests covering disabled/unimplemented providers, unknown providers, external opt-in, unsafe cache paths, inline secrets, and no fallback to real providers.
- Added the provider registry smoke to `scripts/check_all.py`.
- Updated `docs/api/companion-server-contract.md` to clarify that the HTTP provider endpoint remains mock-only and registry roadmap ids are not part of current runtime responses.
- Did not change schemas, fixtures, companion server endpoints, companion client APIs, or add dependencies.
- Validation completed after formatting the new registry test file:
  - `python scripts/check_all.py` passed, including 132 unit tests, provider registry smoke, provider contract regression smoke, companion smokes, Ruff check, and Ruff format check.
  - `python scripts/validate_schemas.py` passed.
  - `python -m unittest discover -s tests -p "test_*.py"` passed with 132 tests.
  - `npm run check` passed.
  - `python scripts/run_provider_contract_regression.py --quiet` passed.
  - `python scripts/run_companion_server.py --smoke-test` passed.
  - `python scripts/run_companion_client.py smoke-test` passed.
  - `python scripts/run_prompt_pack.py --summary` passed.
  - `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Milestone 2F provider contract regression runner and local review handoff is implemented.

Completed in the latest session:
- Added `scripts/run_provider_contract_regression.py`, a stdlib-only runner that starts an in-process `127.0.0.1` companion server on an ephemeral port and shuts it down cleanly.
- The runner posts the raw Milestone 2E request fixtures to `POST /synthetic/provider-annotate`:
  - `tests/fixtures/provider_annotate.fake_event_request.synthetic.json`
  - `tests/fixtures/provider_annotate.context_packet_request.synthetic.json`
- The runner validates the companion envelope, nested `context_packet`, and nested `annotation_card` payloads against the existing schemas.
- The runner compares stable deterministic fields against `tests/fixtures/provider_annotate.success_response.synthetic.json`, including context identity/current-line data, provider metadata, prompt pack metadata, provider debug metadata, risk flags, and English source/original preservation.
- Added optional local handoff artifacts under ignored `workspace/synthetic-slice/provider-contract/`:
  - JSON summary via `--output`
  - Markdown summary via `--markdown`
  - escaped review HTML via `--write-review-html`
- Unsafe output paths outside `workspace/synthetic-slice/provider-contract/` are rejected.
- Added `tests/test_provider_contract_regression.py` covering passing fixtures, both request shapes, stable metadata drift, schema failure reporting, safe/unsafe output paths, review HTML writing, deterministic Markdown, no forbidden markers, and clean localhost-only operation.
- Added `python scripts/run_provider_contract_regression.py --quiet` to `scripts/check_all.py`.
- Updated `docs/api/companion-server-contract.md` to document the regression runner and fixture update expectations.
- Did not change schemas, fixtures, companion server endpoints, companion client APIs, provider pipeline behavior, or add dependencies.

Milestone 2E provider contract fixtures and schema hardening is implemented.

Completed in the latest session:
- Added committed synthetic provider contract fixtures:
  - `tests/fixtures/provider_annotate.fake_event_request.synthetic.json`
  - `tests/fixtures/provider_annotate.context_packet_request.synthetic.json`
  - `tests/fixtures/provider_annotate.success_response.synthetic.json`
- The fixture pair uses one invented synthetic line consistently across fake-event input, context-packet input, and success response.
- The success fixture validates as the standard companion envelope with nested `context_packet` and `annotation_card` payloads.
- Made `provider`, `provider_debug`, and `prompt_pack` explicit optional properties in `specs/annotation-card.schema.json`.
- Kept the schema additive and permissive: no new top-level required fields and no `additionalProperties: false`.
- Removed `future_roles` from public annotation-card provider metadata so committed server/fixture responses do not contain future external-service markers.
- Kept internal provider metadata capable of describing future roles, but public normalized annotation cards now expose only current mock provider posture.
- Added fixture/contract tests proving the fake-event and context-packet request fixtures are accepted by the server and match the committed success response.
- Added drift tests proving the client unwraps the provider response shape, provider metadata is present, `prompt_pack_guided` is present, and unwrapped provider payloads are rejected.
- Added fixture safety checks for URLs, private paths, API-key markers, future external-service markers, and real game title leakage outside schema-required context-packet `game.title`.
- Extended `scripts/validate_schemas.py` so provider contract fixtures are validated by the normal schema validation path and therefore by `check_all`.
- Updated `docs/api/companion-server-contract.md` to document the new fixtures and provider metadata as explicit optional schema fields.
- Resolved the previous pending decision about whether provider metadata should remain permissive-only: it is now explicit optional schema metadata.
- Did not add dependencies, change endpoint shapes, call providers, or use real game dialogue/assets/extracted data.

Milestone 2D companion provider annotation endpoint is implemented.

Completed in the latest session:
- Exposed the prompt-pack-aware deterministic mock provider pipeline through the companion server.
- Added `POST /synthetic/provider-annotate` with explicit wrapper inputs:
  - `{ "input_type": "fake_event", "event": { ... } }`
  - `{ "input_type": "context_packet", "context_packet": { ... } }`
- The provider endpoint does not guess when `input_type` is missing or unknown; it returns `400 invalid_request`.
- Fake-event input is validated and converted with existing synthetic slice helpers before provider annotation.
- Context-packet input is validated against `specs/context-packet.schema.json` before provider annotation.
- Provider annotation returns the existing success envelope with `context_packet` and prompt-pack-aware `annotation_card`.
- Added in-memory latest provider state:
  - `GET /state/latest-provider-context`
  - `GET /state/latest-provider-annotation`
- Added companion client methods and CLI commands for provider annotation and latest provider state.
- Updated `docs/api/companion-server-contract.md` with the new endpoint, accepted request shapes, latest state endpoints, synthetic examples, and deterministic mock-provider policy.
- Extended companion server/client tests for valid fake-event and context-packet provider annotation, missing/unknown `input_type`, missing payloads, invalid fake events, invalid context packets, latest provider state, client methods, and CLI commands.
- Extended the companion client smoke test so `scripts/check_all.py` exercises provider annotation without leaving a long-running server.
- Kept `/synthetic/event`, `/synthetic/eval`, and `/review/latest.html` behavior unchanged.
- Did not change schemas, provider pipeline internals, prompt pack text, config, stable error code names, or add dependencies.

Milestone 2C remains in place:
- Extended provider requests with explicit prompt-pack policy wiring:
  - player-facing language default: `uk`
  - internal guidance language marker: `english_allowed_for_provider_guidance`
  - focused policy refs/sections for spoiler discipline, anti-hallucination, anti-overlocalization, and Russianism/calque avoidance.
- Updated the deterministic mock provider so output includes prompt-pack-guided risk/debug metadata:
  - `synthetic_fixture`
  - `mock_provider`
  - `deterministic_mock_provider`
  - `needs_human_review_before_real_use`
  - `prompt_pack_guided`
- Added provider/debug metadata to normalized annotation cards through permissive additional fields:
  - `provider`
  - `provider_debug`
  - `prompt_pack`
- Hardened provider normalization so it still preserves original English from the context packet, rejects line ID mismatches, requires `provider_debug`, requires focused policy keys, and rejects missing required mock risk flags.
- Switched the synthetic eval harness to run fake event -> context packet -> provider pipeline -> annotation card -> overlay demo -> review HTML.
- Added structural eval score keys for prompt-pack metadata, required output fields, quality priorities, policy coverage, and provider debug coverage.
- Updated the static review renderer debug section to show escaped provider name/role, prompt pack id/version, player-facing language default, and policy note keys.
- Added tests for provider request policy fields, mock provider metadata, normalized prompt-pack metadata, provider debug failure modes, provider-backed eval policy coverage, score degradation when metadata is removed, and review debug rendering.
- Kept companion server/client provider endpoints deferred to Milestone 2D.
- Did not change schemas, prompt pack text, config, companion server endpoints, or add dependencies.

Milestone 2B remains in place:
- Added `prompts/packs/ukrainian_annotation_v1/`, a versioned synthetic-only prompt/style pack.
- Added pack files for system/developer guidance, output contract, style guide, glossary policy, uncertainty policy, spoiler policy, anti-hallucination, anti-overlocalization, Russianism avoidance, and synthetic examples.
- Revised `synthetic_examples.md` into ten richer synthetic quality references covering bureaucratic irony, institutional metaphor, deadpan official voice, idiom/subtext, reference-like phrasing, sarcasm, uncertainty, spoiler safety, Russianism/calque avoidance, and explicit-only Ukrainian cultural adaptation proposals.
- Each numbered synthetic example now carries the same review structure: source, difficulty, bad rendering, concise Ukrainian meaning, literary Ukrainian rendering, deep annotation, tone/voice note, risk flags, and why the improved version is better.
- Added a reviewer checklist for meaning preservation, Ukrainian naturalness, tone, idioms/jokes, uncertainty, spoiler budget, over-localization, and clearly marked cultural proposals.
- Added prompt-pack tests that enforce the numbered example structure, non-empty field bodies, and Ukrainian script in concise/literary Ukrainian fields so shallow rewrites fail loudly.
- Confirmed developer policy that internal provider guidance may be English, but player-facing annotation fields default to Ukrainian unless debug or developer mode is explicitly enabled.
- Added `pack.json` with prompt pack metadata, required output fields, quality priorities, policy file references, synthetic examples reference, and provider pipeline compatibility notes.
- Added `scripts/prompt_pack.py`, a stdlib-only deterministic prompt pack loader with clear `PromptPackError` failures for missing files and malformed metadata.
- Added `scripts/run_prompt_pack.py --summary` for local metadata inspection without provider calls.
- Updated provider requests to include `prompt_pack_id`, `prompt_pack_version`, `prompt_pack_policy_refs`, and `prompt_pack_sections`.
- Provider requests now source required output fields and quality priorities from the loaded prompt pack while keeping mock annotation output deterministic.
- Added tests for prompt pack metadata, markdown loading, missing/malformed pack failures, deterministic loading, synthetic-only safety, CLI summary, and provider request compatibility.
- Integrated a prompt pack smoke command into `scripts/check_all.py`.
- Did not change schemas, config, companion server endpoints, or add dependencies.

Milestone 2A remains in place:
- Added `scripts/provider_pipeline.py`, a stdlib-only provider/prompt scaffold with dataclass request/response/metadata shapes.
- Added deterministic mock provider support only; no real LLM, paid API, DeepL, web, or local model runtime calls exist.
- Added provider request creation from validated context packets, including original text, speaker, scene/conversation metadata, nearby context, spoiler budget, glossary hints, requested output fields, quality priorities, and safety rules.
- Added provider response normalization into schema-valid annotation cards while preserving the English original from the context packet.
- Added clear `ProviderPipelineError` failures for malformed provider output and line ID mismatch.
- Added `scripts/run_provider_pipeline.py` with default synthetic fixture input, optional context packet input, `--provider mock`, workspace-only output, and unsafe path rejection.
- Added provider pipeline tests for request shape, deterministic mock response, annotation-card validation, original preservation, malformed output failures, no private/network/API-key markers, CLI success, and unsafe output rejection.
- Integrated a provider pipeline smoke command into `scripts/check_all.py`.
- Left companion server/client provider endpoints out of Milestone 2A; server exposure should happen after one stable provider CLI/test cycle.
- Did not change schemas, config, or add dependencies.

Milestone 1E remains in place:
- Added `scripts/companion_client.py`, a tiny stdlib-only local contract helper for the companion server.
- Added `scripts/run_companion_client.py` with commands for health, synthetic event posting, latest state reads, review HTML, synthetic eval, and a clean in-process `smoke-test`.
- Hardened server error codes into a small stable set:
  - `not_found`
  - `invalid_json`
  - `invalid_request`
  - `invalid_fake_event`
  - `method_not_allowed`
  - `internal_error`
- Kept the envelope contract unchanged:
  - success: `{"ok": true, "data": ...}`
  - error: `{"ok": false, "error": {"code": "...", "message": "..."}}`
- Kept `latest-review-html` as raw escaped HTML, not JSON.
- Added `docs/api/companion-server-contract.md` with synthetic-only endpoint and envelope examples.
- Added client tests for health, event posting, latest context/annotation/overlay, synthetic eval, raw review HTML, server error envelopes, unavailable server handling, invalid JSON responses, CLI smoke, and synthetic-only contract docs.
- Added server tests for stable error codes and method-not-allowed behavior.
- Integrated `python scripts/run_companion_client.py smoke-test` into `scripts/check_all.py`.
- Did not add dependencies or use real game data, BepInEx, OCR, extraction, web calls, paid APIs, LLM calls, frontend frameworks, auth, TLS, persistence, or CORS work.

Milestone 1D remains in place:
- Added `scripts/companion_server.py`, a stdlib-only `http.server` companion skeleton with in-memory state.
- Added `scripts/run_companion_server.py` with default `--host 127.0.0.1`, default `--port 8765`, and `--smoke-test`.
- Added local JSON endpoints using a consistent envelope:
  - success: `{"ok": true, "data": ...}`
  - error: `{"ok": false, "error": {"code": "...", "message": "..."}}`
- Implemented `GET /health`, latest context/annotation/overlay/eval state endpoints, `POST /synthetic/event`, `POST /synthetic/eval`, and `GET /review/latest.html`.
- Kept `/review/latest.html` generated from the existing escaped static review renderer; before an event exists it returns a `409 invalid_request` JSON error envelope.
- Added endpoint tests for health, valid synthetic event ingestion, invalid JSON, invalid fake event validation, latest state, synthetic eval, review HTML, missing-review errors, unknown routes, and localhost-only test binding.
- Integrated a clean companion server smoke test into `scripts/check_all.py` without leaving a long-running process.
- Did not change schemas or add dependencies.
- Did not rename the repository path. `revachol-ukro-elisium` matches the actual directory; naming cleanup remains a future decision.

Milestone 1D server posture:
- Local/offline/mock-only for now.
- Binds to `127.0.0.1` by default.
- Uses in-memory state only; restarting the server loses latest context/annotation/eval state.
- Is not production security hardened: no auth, TLS, persistence, rate limiting, CORS policy, or multi-client session model yet.
- Future paid API, web retrieval, local extraction, and provider-backed annotation support must remain opt-in and must keep caches/private data under ignored local paths.

Milestone 1C remains in place:
- Added a stdlib-only deterministic structural eval harness for the existing synthetic slice and review renderer.
- Added six invented synthetic eval cases covering bureaucratic irony, idiom/subtext, character voice, reference-like political phrasing, Ukrainian field presence, spoiler safety defaults, glossary presence, and compact/deep usefulness.
- Added `scripts/run_synthetic_eval.py`, which prints a JSON summary by default and rejects unsafe output paths outside `workspace/synthetic-slice/`.
- Added optional per-case review HTML batch output under `workspace/synthetic-slice/eval/`.
- Added structural scores for `section_coverage`, `compact_brevity`, `deep_explanation_presence`, `glossary_coverage`, `risk_flag_coverage`, `spoiler_safety`, and `renderer_completeness`.
- Added tests for eval case validation, synthetic-only safety, deterministic scoring, score degradation on missing sections/glossary, CLI output path safety, and review generation.
- Integrated the synthetic eval smoke into `scripts/check_all.py`.
- Did not change schemas or add dependencies.

Important eval terminology:
- `quality.needs_human_review` is the annotation-card quality boolean used by the structured output.
- `needs_human_review_before_real_use` is a risk flag showing that deterministic synthetic/mock output is not ready for real player-facing use without human review.

Milestone 1B remains in place:
- Added a deliberately boring stdlib-only static HTML review renderer for the existing `overlay_demo` model.
- Extended `scripts/run_synthetic_slice.py` with `--render-review`.
- Kept default output behavior deterministic: review HTML prints to stdout unless `--output` is provided.
- Restricted written generated artifacts to `workspace/synthetic-slice/`; unsafe output paths are rejected with a clear CLI error instead of being normalized.
- Added mandatory HTML escaping coverage, including a test with unsafe synthetic `<script>` text.
- Added tests for compact mode, deep explanation mode, original/translation visibility, Ukrainian fields, idiom/reference/voice sections, glossary terms, confidence, risk flags, and output path safety.
- Integrated the review-renderer smoke command into `scripts/check_all.py`.
- Did not change any schemas.

Milestone 1A remains in place:
- Added `FakeGameEvent` schema plus valid/invalid synthetic fixtures.
- Added a pure stdlib synthetic slice module that validates a fake event, builds a context packet, creates a deterministic mock annotation card, and produces an overlay-facing demo model.
- Added `scripts/run_synthetic_slice.py` to run the full synthetic flow from fixture or supplied synthetic event.
- Added tests for fake event validation, context packet building, deterministic mock annotation output, overlay model shape, full flow, and safety/no private path requirements.
- Integrated a synthetic slice CLI smoke test into `scripts/check_all.py`.
- Kept `specs/annotation-card.schema.json` unchanged: its existing fields plus default allowance for optional extra properties can represent this slice without a backward-compatibility schema change.

Milestone 0 foundation still in place:
- Added explicit ignored private roots for local game data, generated artifacts, caches, vectors, screenshots, audio metadata, and translation memory.
- Added example runtime config and validation for path safety, opt-in provider/network policy, and no inline secrets.
- Added idempotent local workspace bootstrap script.
- Added lightweight schema validation and synthetic fixtures for context packets, annotation cards, glossary entries, and one end-to-end example.
- Added unified check runner and wired it through npm, Justfile, Makefile, and CI.
- Updated the LLM output contract and legal/data safety docs with runtime paid API and opt-in web enrichment policy.

Latest validation run:
- `python -m unittest tests.test_provider_contract_regression -v` passed with 11 tests.
- `python scripts/check_all.py` passed, including 108 unit tests, provider fixture validation, provider pipeline smoke, provider contract regression smoke, prompt pack smoke, companion server smoke, companion client smoke, Ruff check, and Ruff format check.
- `python scripts/validate_schemas.py` passed.
- `python -m unittest discover -s tests -p "test_*.py"` passed with 108 tests.
- `npm run check` passed.
- `python scripts/run_provider_contract_regression.py --quiet` passed.
- `python scripts/run_companion_server.py --smoke-test` passed.
- `python scripts/run_companion_client.py smoke-test` passed.
- `python scripts/run_prompt_pack.py --summary` passed.
- `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Notes:
- `ruff` is installed locally and passed both check and format-check in this session.
- No real extraction, scraping, paid API call, web API call, BepInEx integration, OCR, or copyrighted game content was used.
- `docs/00-project-vision.md` is absent; `docs/00-start-here.md` remains the current vision entrypoint.
