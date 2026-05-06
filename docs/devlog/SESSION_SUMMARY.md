# Session Summary

Milestone 2A provider abstraction and prompt pipeline skeleton is implemented on top of the existing synthetic context and annotation contracts.

Completed in the latest session:
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
- `python -m unittest tests.test_provider_pipeline -v` passed with 11 tests.
- `python scripts/check_all.py` passed, including 64 unit tests, provider pipeline smoke, companion server smoke, companion client smoke, Ruff check, and Ruff format check.
- `python scripts/validate_schemas.py` passed.
- `python -m unittest discover -s tests -p "test_*.py"` passed with 64 tests.
- `npm run check` passed.
- `python scripts/run_companion_server.py --smoke-test` passed.
- `python scripts/run_companion_client.py smoke-test` passed.
- `python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet` passed.

Notes:
- `ruff` is installed locally and passed both check and format-check in this session.
- No real extraction, scraping, paid API call, web API call, BepInEx integration, OCR, or copyrighted game content was used.
- `docs/00-project-vision.md` is absent; `docs/00-start-here.md` remains the current vision entrypoint.
