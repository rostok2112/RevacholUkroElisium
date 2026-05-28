# Known Risks

- Milestone 5A.4 reviews private dry-run summaries only. It cannot prove private input content shape,
  extraction correctness, index usefulness, or game data compatibility.
- `ready_for_hash_decision=true` means only that a later hash decision contract can be discussed. It
  must not be treated as approval to compute hashes, read contents, or build private indexes.
- Local review JSON/Markdown under `workspace/local-private/extraction-indexing/review/` is ignored,
  but it can still reveal private metadata counts and sizes if copied into tracked files or chat.
- A malformed or verbose dry-run summary can contain private paths. Keep review outputs redacted and
  do not commit private summaries or reviews.
- Milestone 5A.3 reads filesystem metadata for one explicit workspace-private input. It still can
  reveal local file existence, counts, sizes, and directory structure in ignored local summaries.
- `scripts/run_private_input_adapter_dry_run.py --verbose` may show private local paths for the
  user's own debugging. Do not paste verbose output into tracked docs, tests, fixtures, commits, or
  chat.
- The dry-run helper deliberately does not compute hashes. Adding hashes later is a privacy decision
  because hashes can still identify known private files.
- A future private index construction step must not treat a successful dry-run as approval to read,
  store, or commit real extracted text.
- Milestone 5A.2 defines a private input adapter contract only. It does not prove real input
  compatibility, extraction correctness, private index usefulness, or runtime integration.
- The future private input root `workspace/local-private/extraction-indexing/input/` is ignored, but
  ignored inputs can still leak if copied into tracked docs, tests, fixtures, reports, commits, or
  chat.
- Dry-run metadata summaries can reveal local file presence, sizes, counts, and hashes. Treat them
  as private local diagnostics unless a later checker explicitly approves a committed redacted form.
- Do not relax the 5A.2 fixture to allow external absolute paths, automatic game-install scanning,
  arbitrary drive scans, BepInEx log reads, save parsing, screenshots, OCR, current-line capture, UI
  text reading, Unity scanning, hooks/Harmony, decompiled-code details, companion HTTP contract
  changes, real provider execution, or committed real content without a separate safety review.
- Milestone 5A.1 proves only deterministic indexing over committed synthetic records. It does not
  prove real extraction, real file compatibility, game data shape, private index usefulness, or
  runtime integration.
- The synthetic index fixture contains invented text by design. Do not replace it with real
  extracted text, raw localization rows, screenshots, OCR output, BepInEx logs, save data, private
  paths, provider payloads, or decompiled game-code details.
- `scripts/run_synthetic_extraction_indexer.py --output` can write under
  `workspace/local-private/extraction-indexing/`. That directory is ignored, but generated private
  indexes still must not be copied into tracked docs, tests, fixtures, reports, commits, or chat.
- A future user-selected private input adapter must define input placement, validation, deletion,
  and redacted reporting before any real local input reads occur.
- Milestone 5A has a scope contract and a synthetic indexer/private index contract only. Real
  extraction/indexing implementation remains blocked until a user-selected private input adapter
  contract is approved.
- The future private index root `workspace/local-private/extraction-indexing/` is ignored, but
  ignored paths can still leak if copied into docs, tests, fixtures, reports, commits, or chat.
  Keep raw extracted text, localization dumps, game logs, screenshots, save data, private paths, and
  generated indexes out of tracked files.
- Metadata-only file summaries and hashes can still reveal local file presence. Treat them as
  private local diagnostics unless a later checker explicitly approves a redacted synthetic form.
- Do not relax the 5A scope fixture to allow automatic game-install scanning, current-line capture,
  UI text reading, Unity scanning, hooks/Harmony, OCR, decompiled game-code details, companion HTTP
  contract changes, real provider execution, or committed real content without a separate safety
  review.
- Milestone 4 closeout workflow smoke proves only the redacted synthetic/manual bridge-to-overlay
  path and local workflow repeatability. It still does not prove current-line capture, real text
  capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider execution,
  production overlay shell behavior, or companion HTTP contract changes.
- True Milestone 5A remains unstarted. When it begins, local extraction/indexing outputs must stay
  ignored/private and must not introduce committed game dialogue, assets, screenshots, raw logs,
  private paths, extracted databases, provider payloads, or workspace artifacts.
- Do not mislabel Milestone 4 closeout / local bridge workflow polish as top-level Milestone 5A.
  True Milestone 5A has not started yet and should remain reserved for the real extraction/indexing
  adapter, local-only.
- The local bridge workflow wrapper is a convenience coordinator only. Do not treat a green doctor or
  post phase as approval for current-line capture, real text capture, UI text reading, Unity
  scanning, hooks/Harmony, OCR, extraction, real provider execution, companion HTTP contract
  changes, polling loops, timers, background workers, or production overlay shell behavior.
- The doctor phase can report setup readiness, but it cannot prove the user-local game launch or
  BepInEx runtime behavior happened. Runtime evidence must still remain redacted and ignored.
- The workflow wrapper may edit user-local BepInEx config through existing helpers. Always run
  `python scripts/run_local_bridge_workflow.py --phase cleanup --auto-discover` after local smoke
  runs to restore metadata probe and synthetic send flags to false.
- Staged-artifact detection is a guardrail, not a substitute for reviewing `git status` before
  committing. Keep workspace outputs, reports, generated HTML, logs, screenshots, `bin/`, `obj/`,
  game files, provider payloads, and private paths out of git.
- The overlay refresh readiness helper summarizes metadata only. Do not treat
  `overlay_html_review_ready` as approval for a production overlay shell, polling loop, timer,
  background worker, current-line capture, real text capture, UI text reading, Unity scanning,
  hooks/Harmony, OCR, extraction, real provider execution, or companion HTTP contract changes.
- Helper self-test mode uses committed synthetic provider fixtures and proves only the readiness
  summarizer path. It does not prove a running companion server, a real game launch, BepInEx runtime
  behavior, or real provider integration.
- Written overlay refresh readiness summaries are workspace-only artifacts under
  `workspace/synthetic-slice/overlay-refresh-readiness/` and must not be committed.
- The overlay refresh/readiness contract is metadata-only and static. Do not treat it as approval for
  polling loops, timers, background workers, production shell behavior, real provider execution,
  companion HTTP contract changes, current-line capture, real text capture, UI text reading, Unity
  scanning, hooks/Harmony, OCR, or extraction.
- The refresh readiness fixture records `bridge_to_overlay_smoke_passed=true`, but all dangerous
  permissions remain false. Future edits to the fixture are contract decisions and must be reviewed
  with docs and tests.
- ADR 0010 allows only metadata-only overlay refresh/readiness contract planning. Do not treat the
  passed bridge-to-overlay smoke as permission for runtime implementation, current-line capture, real
  text capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider
  execution, production overlay shell behavior, or companion HTTP contract changes.
- The post bridge-to-overlay decision fixture records `bridge_to_overlay_smoke_passed=true`, but all
  capture/provider/contract/shell permissions remain false. Future edits to that fixture are
  contract decisions and must be reviewed with docs and tests.
- The bridge-to-overlay smoke wrapper summarizes latest provider state without printing payloads.
  If overlay construction fails, keep debugging evidence redacted into blocker categories instead of
  committing companion payloads, generated HTML, or raw logs.
- A successful bridge-to-overlay synthetic smoke proves only the invented bridge event can reach
  companion latest provider state and build current overlay contracts. It is not evidence of
  current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction,
  real provider execution, or production overlay readiness.
- Optional bridge-to-overlay smoke summaries and generated HTML are local workspace artifacts only;
  do not commit files under `workspace/synthetic-slice/bepinex-bridge/bridge-to-overlay-smoke/` or
  `workspace/synthetic-slice/overlay-prototype/bridge-to-overlay-smoke/`.
- The companion-connected synthetic smoke temporarily enables the existing
  `SendSyntheticEventOnStart` config key. Always restore it with `--disable-synthetic-send` after
  the local run.
- A successful synthetic provider send proves only localhost companion reachability and invented
  fake-event delivery. It is not evidence of current-line capture, UI text reading, Unity scanning,
  provider execution, or companion contract readiness.
- Redacted helper detection is intentionally limited to bridge-owned markers. If ordinary Unity or
  BepInEx noise appears in raw logs, do not broaden checks to parse dialogue or game content.
- The local metadata probe smoke helper can edit the user-owned BepInEx config and copy the bridge
  DLL into `BepInEx/plugins/`. Keep those writes bounded to the discovered/provided install and use
  `--disable-probe` after the smoke.
- The helper reads only `BepInEx/LogOutput.log`, but that file remains a raw local runtime artifact.
  Do not commit it, paste it into docs, or store it under tracked paths.
- Redacted log checks can miss useful debugging nuance. If a startup issue needs deeper analysis,
  inspect raw logs locally and translate findings into redacted booleans/categories before sharing.
- Steam autodiscovery is best-effort and bounded. If it fails, pass `--game-dir` and explicit
  BepInEx reference DLL paths rather than broadening discovery to drive-wide scans.
- A generated metadata probe report proves only allowlisted startup markers were observed. It does
  not prove current-line capture, UI visibility, scene state, game-state detection, or translation
  readiness.
- Milestone 4N makes the 4M counters manually verifiable, but verified counters still prove only
  startup metadata posture. They are not evidence of current-line capture, UI visibility, scene
  state, or game-state detection.
- Completed metadata probe reports must remain local and redacted. Do not commit raw logs,
  screenshots, private paths, stack traces, payload dumps, or real reports while verifying the 4M
  counters.
- Milestone 4M implements inert metadata counters, but they are still not runtime capture evidence.
  Do not treat `metadata_snapshot_created_count`, `health_check_observed_count`, or
  `synthetic_send_configured_count` as current-line, UI, scene, or game-state observation.
- The metadata probe remains disabled by default. Any manual enabled run must stay local, redacted,
  and ignored; completed real reports, logs, screenshots, payloads, and private paths must not be
  committed.
- Any future expansion beyond the 4M counters must update the bridge safety checker before or with
  implementation and still keep capture/provider/contract permissions closed unless a later safety
  review explicitly changes them.
- Milestone 4L allows planning a minimal 4M inert metadata implementation without a reviewed local
  report. That waiver is narrow and must not be reused for UI/scene probes, capture, hooks, OCR,
  extraction, provider calls, or companion contract changes.
- The 4L scope fixture sets `implementation_allowed_next=true`, but only while every capture,
  hook/scanning, provider, and companion contract permission remains false.
- Milestone 4M must update bridge safety checks before or with any C# changes, otherwise the inert
  metadata scope can drift into runtime inspection by accident.
- Milestone 4K allows metadata-only extension discussion only. It must not be treated as approval for
  implementation, current-line capture, real text capture, UI text reading, Unity scanning, hooks,
  OCR, extraction, provider calls, companion contract changes, or shell work.
- The metadata extension gate fixture intentionally closes implementation and capture permissions.
  Any future change to that fixture is a contract decision and must be reviewed with ADR/docs/tests.
- A future `ready_for_metadata_only_extension_implementation` state would still not approve text
  capture or companion contract changes; it would only allow a separately scoped metadata-only
  runtime expansion.
- Milestone 4J review readiness is discussion-only. It must not be treated as approval for
  current-line capture, UI text reading, hooks, OCR, extraction, provider calls, or companion
  contract changes.
- The metadata probe reviewer validates report shape and redaction, but it still cannot prove the
  user-local observations are true or complete.
- Review summaries intentionally omit report notes and any free-text evidence, so the local redacted
  report may need human review for nuance while staying ignored.
- Milestone 4I makes metadata probe manual verification easier, but it still relies on user-local
  observation. The repo does not commit raw evidence, screenshots, logs, or completed real reports.
- The metadata probe report template is safe by construction, but a filled local report can still be
  misleading or incomplete. Treat it as a redacted summary, not as an audit log.
- Passing `scripts/check_bepinex_metadata_probe_report.py` proves only that the report is
  metadata-only and redacted. It does not approve current-line capture, UI text reading, hooks, OCR,
  extraction, provider calls, or companion contract changes.
- The 4I workflow deliberately defers metadata probe report readiness review to Milestone 4J. Do not
  infer readiness from a valid report fixture or template alone.
- Milestone 4H adds C# metadata probe code, but it is disabled by default and logs only a safe
  snapshot when manually enabled. It still does not prove runtime usefulness.
- The metadata probe log may help confirm startup posture, but it must not grow into text capture,
  runtime object inspection, raw payload logging, screenshots, or local path logging.
- Milestone 4G is a static gate and committed synthetic fixture only. It does not prove metadata
  probe runtime feasibility or authorize probe implementation.
- A valid metadata probe report proves only that the report shape stayed metadata-only and redacted.
  It does not approve current-line capture, hooks, OCR, extraction, Unity scanning, provider calls,
  or companion contract changes.
- The metadata probe checker intentionally lists forbidden concepts as rejection markers. Safety
  tooling must keep distinguishing policy/checker text from runtime implementation code.
- Milestone 4F reviews redacted report summaries only. It does not prove the underlying manual smoke
  observations are true, complete, or reproducible.
- `ready_for_next_phase = true` is not approval for current-line capture, hooks, OCR, extraction, or
  companion contract changes. It only says the redacted evidence is complete enough for human review.
- Review summaries intentionally omit report notes and evidence text, so they may hide useful nuance.
  Keep the full redacted report local and ignored if more context is needed.
- Milestone 4E is an architecture decision only. It does not prove current-line capture feasibility,
  runtime UI observability, method patch viability, or legal safety for real text capture.
- ADR 0008 discusses risky approaches such as OCR, broad UI observation, and method patching so they
  can be explicitly deferred; discussion in docs is not approval to implement them.
- Future metadata-only probes may still reveal sensitive local state if logging is sloppy. Keep
  probe outputs to booleans, safe counters, synthetic ids, bridge-generated line ids, and redacted
  reports until a later safety review approves more.
- Milestone 4D validates redacted report shape and forbidden markers only. It does not prove a real
  manual smoke happened, that the plugin loaded in a user install, or that companion communication
  succeeded at runtime.
- User-local runtime reports can still omit important context. Treat them as summaries for review,
  not as raw evidence or audit logs.
- Runtime smoke report templates and completed reports must remain under the ignored workspace report
  root; raw BepInEx/game logs, screenshots, stack traces, payload dumps, and private paths must not
  be committed.
- Milestone 4C documents manual runtime verification and log expectations only. It still does not
  prove runtime loading, plugin lifecycle behavior, or game compatibility.
- Manual BepInEx/game logs remain user-local artifacts. Do not commit raw runtime logs, stack traces,
  local install paths, screenshots, or smoke reports.
- The log contract allows exception type and message for unavailable companion warnings, but not
  stack traces, payloads, response bodies, or private paths.
- Milestone 4B proves an optional local compile path only when `dotnet` and user-local BepInEx IL2CPP
  references are supplied. It still does not prove runtime loading inside the game.
- Local BepInEx IL2CPP builds may emit `MSB3277` assembly-version warnings. 4B counts and documents
  them, but intentionally does not fail a successful optional build solely because of those warnings.
- Build reports redact local reference paths, but generated reports and DLL outputs remain local
  artifacts under ignored `workspace/`, `bin/`, and `obj/` paths and must not be committed.
- The optional build helper does not download toolchains or references. Users remain responsible for
  their own local .NET/BepInEx install.
- Milestone 4A adds a BepInEx bridge skeleton only. It does not prove C# compilation, BepInEx
  runtime loading, game compatibility, install flow, or current-line detection.
- `dotnet build` is intentionally not a required part of `check_all` because the repo does not carry
  BepInEx assemblies and must stay usable without local game/mod toolchains.
- The bridge has a manual `.csproj` that expects user-local BepInEx references. Those paths and
  binaries must remain private and uncommitted.
- `SendSyntheticEventOnStart` defaults to false. Enabling it still sends only invented synthetic text
  to the local companion mock-provider endpoint; it must not become real game-content capture without
  a later milestone and safety review.
- Static bridge safety checks catch obvious scope creep, but they are not a substitute for runtime
  testing inside a user-owned local install.
- Milestone 3K is an architecture decision only. It does not prove BepInEx feasibility, current-line
  detection, install flow, build tooling, or runtime compatibility.
- Deferring shell work means generated HTML and JSON fixtures remain review contracts, not a
  player-ready overlay window.
- Milestone 4A must remain synthetic/manual first. Accidentally emitting real game text, decompiled
  code, assets, screenshots, or extracted databases would violate the repo safety model.
- The future shell stack remains undecided. ADR 0007 only chooses to defer that decision until bridge
  feasibility is better understood.
- Milestone 3J locks state-source fixture shape, so intentional state-source contract changes now
  require coordinated updates to builder code, fixtures, checker, tests, and docs.
- Milestone 3J ready debug fixture is larger than player-mode fixtures because it embeds developer
  metadata. Keep it reviewable and redacted; do not let it grow into raw prompt or payload logging.
- Milestone 3J fixtures are structural regression artifacts. They do not prove real polling cadence,
  retries, live shell lifecycle, focus behavior, or in-game placement.
- Milestone 3J adds additive alias no-side-effect fields. Future clients should treat both the old
  and clearer alias names as contract fields until a later versioning decision is made.
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
