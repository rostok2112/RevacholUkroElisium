# Decisions Pending

- The M2 context-graph contract is defined. Implement `m2_context_graph_implementation` next as the
  third original M2 criterion slice.
- Keep generated graphs, line indexes, private DB artifacts, extracted text, private paths,
  payloads, reports, source-text duplication in graph output, arbitrary future-branch traversal,
  game scanning, runtime reads, companion changes, providers, and committed private artifacts
  blocked.
- The M2 line-index implementation is added. Define `m2_context_graph_contract` next to scope the
  third original M2 criterion.
- Keep generated line indexes, private DB artifacts, extracted text, private paths, payloads,
  reports, graphs, context-graph construction, retrieval-bucket mapping, game scanning, runtime
  reads, companion changes, providers, and committed private artifacts blocked.
- The M2 local import review gate is implemented. Implement `m2_line_index_implementation` next
  only after a passing redacted local-import summary review.
- Keep context-graph construction, retrieval-bucket mapping, game scanning, runtime reads,
  companion changes, provider execution, committed extracted text, private paths, payloads,
  private DB artifacts, line indexes, graphs, and reports blocked.
- The M2 line-index contract is defined. Implement `m2_line_index_implementation` next as the
  second original M2 criterion slice.
- Keep context-graph construction, retrieval-bucket mapping, game scanning, runtime reads,
  companion changes, provider execution, committed extracted text, private paths, payloads,
  private DB artifacts, line indexes, graphs, and reports blocked.
- The M2 local import implementation is added. Define `m2_line_index_contract` next to scope the
  second original M2 criterion.
- Keep generated private DB artifacts, extracted text, private paths, payloads, reports, indexes,
  context-graph construction, retrieval-bucket mapping, game scanning, runtime reads, companion
  changes, providers, and committed private artifacts blocked.
- The M2 local import final approval contract is defined. Implement
  `m2_local_import_implementation` next as the first original M2 criterion slice.
- Keep line-index construction, context-graph construction, retrieval-bucket mapping, game
  scanning, runtime reads, companion changes, provider execution, committed extracted text, private
  paths, payloads, private DB artifacts, indexes, and reports blocked.
- The M2 explicit local-import context-edge integrity dry-run review gate is implemented. Define
  `m2_local_import_final_approval_contract` next as the final static approval boundary before the
  first real M2 criterion can begin.
- Keep selected-export reopening during review, id emission, relation emission, duplicate tuple
  emission, retrieval-bucket mapping, real DB import, line-index construction, context-graph
  construction, and every original M2 completion flag false.
- The M2 explicit local-import context-edge integrity dry-run is implemented. Add
  `m2_explicit_local_import_context_edge_integrity_dry_run_review_gate` next using redacted
  summary evidence only.
- Keep selected-export reopening during review, id emission, relation emission, duplicate tuple
  emission, retrieval-bucket mapping, real DB import, line-index construction, context-graph
  construction, and every original M2 completion flag false.
- The M2 explicit local-import context-edge integrity contract is defined. Implement
  `m2_explicit_local_import_context_edge_integrity_dry_run` next as an aggregate-only dry-run.
- Keep id emission, id normalization, id hashing, relation emission, retrieval-bucket mapping,
  real DB import, line-index construction, context-graph construction, and every original M2
  completion flag false.
- The M2 explicit local-import context-edge reference dry-run review gate is implemented. Define
  `m2_explicit_local_import_context_edge_integrity_contract` next as a static boundary only.
- Keep selected-export reopening during review, id emission, id normalization, id hashing,
  self-edge checks, duplicate-edge checks, retrieval-bucket mapping, real DB import, line-index
  construction, context-graph construction, and every original M2 completion flag false.
- The M2 explicit local-import context-edge reference dry-run is implemented. Add
  `m2_explicit_local_import_context_edge_reference_dry_run_review_gate` next using redacted summary
  evidence only.
- Keep selected-export reopening during review, id emission, id normalization, id hashing,
  self-edge checks, duplicate-edge checks, retrieval-bucket mapping, real DB import, line-index
  construction, context-graph construction, and every original M2 completion flag false.
- The context-edge reference dry-run intentionally applies no decode-size cap. Preserve that
  explicit memory-risk tradeoff unless a later contract revisits it.
- The M2 explicit local-import context-edge reference contract is defined. Implement
  `m2_explicit_local_import_context_edge_reference_dry_run` next as a redacted membership-check
  dry-run only.
- Keep edge id emission, record id emission, self-edge checks, duplicate-edge checks, graph
  construction, real DB import, line-index construction, context-graph construction, and every
  original M2 completion flag false.
- The M2 explicit local-import context-edge shape dry-run review gate is implemented. Define
  `m2_explicit_local_import_context_edge_reference_contract` next as a static boundary only.
- Keep selected-export reopening during review, edge id emission, edge reference validation,
  self-edge checks, duplicate-edge checks, record traversal, real DB import, line-index
  construction, context-graph construction, and every original M2 completion flag false.
- The M2 explicit local-import context-edge shape dry-run is implemented. Add
  `m2_explicit_local_import_context_edge_shape_dry_run_review_gate` next using redacted summary
  evidence only.
- Keep selected-export reopening during review, edge id emission, edge reference validation,
  self-edge checks, duplicate-edge checks, record traversal, real DB import, line-index
  construction, context-graph construction, and every original M2 completion flag false.
- The context-edge shape dry-run intentionally applies no decode-size cap. Preserve that explicit
  memory-risk tradeoff unless a later contract revisits it.
- The M2 explicit local-import context-edge shape contract is defined. Implement
  `m2_explicit_local_import_context_edge_shape_dry_run` next for all-context-edge top-level shape
  checks only.
- Keep edge id emission, edge reference validation, self-edge checks, duplicate-edge checks,
  record traversal, real DB import, line-index construction, context-graph construction, and every
  original M2 completion flag false.
- The M2 explicit local-import record-shape dry-run review gate is implemented. Define
  `m2_explicit_local_import_context_edge_shape_contract` next as a static boundary only.
- Keep selected-export reopening during review, record-value traversal, tag traversal, metadata
  traversal, context-edge inspection, real DB import, line-index construction, context-graph
  construction, and every original M2 completion flag false.
- The M2 explicit local-import record-shape dry-run is implemented. Add
  `m2_explicit_local_import_record_shape_dry_run_review_gate` next using redacted summary evidence
  only.
- Keep selected-export reopening during review, record-value emission, tag traversal, metadata
  traversal, context-edge traversal, real DB import, line-index construction, context-graph
  construction, and every original M2 completion flag false.
- The record-shape dry-run intentionally applies no decode-size cap. Preserve that explicit
  memory-risk tradeoff unless a later contract revisits it.
- The M2 explicit local-import record-shape contract is defined. Implement
  `m2_explicit_local_import_record_shape_dry_run` next for all-record top-level shape checks only.
- Keep record-value inspection, source-text emission, tag traversal, metadata traversal,
  context-edge inspection, real DB import, line-index construction, context-graph construction,
  and every original M2 completion flag false.
- The M2 explicit local-import schema-compatibility dry-run review gate is implemented. Define
  `m2_explicit_local_import_record_shape_contract` next as a static boundary only.
- Keep selected-export reopening during review, nested traversal, record-shape inspection, real DB
  import, line-index construction, context-graph construction, and every original M2 completion
  flag false.
- The M2 explicit local-import schema-compatibility dry-run is implemented. Add
  `m2_explicit_local_import_schema_compatibility_dry_run_review_gate` next using redacted
  compatibility-summary evidence only.
- Keep export reopening during review, nested traversal, nested-value emission, real DB import,
  line-index construction, context-graph construction, and every original M2 completion flag false.
- The compatibility dry-run intentionally applies no decode-size cap. Preserve that explicit
  memory-risk tradeoff unless a later contract revisits it.
- The M2 explicit local-import schema-compatibility contract is defined. Implement
  `m2_explicit_local_import_schema_compatibility_dry_run` next as an envelope-only redacted check.
- Keep nested traversal, nested-value emission, source-text emission, metadata-content inspection,
  real DB import, line-index construction, context-graph construction, and every original M2
  completion flag false.
- The M2 explicit local-import adapter dry-run review gate is implemented. Define
  `m2_explicit_local_import_schema_compatibility_contract` next as a static boundary only.
- Keep selected-export reopening, schema compatibility inspection, file-content reads, parsing,
  real DB import, line-index construction, context-graph construction, and every original M2
  completion flag false.
- The M2 explicit local-import adapter dry-run is implemented. Add
  `m2_explicit_local_import_adapter_dry_run_review_gate` next using redacted summary evidence only.
- Keep selected-export reopening, file-content reads, parsing, schema compatibility inspection,
  real DB import, line-index construction, context-graph construction, and every original M2
  completion flag false.
- The M2 explicit local-import adapter contract is defined. Implement
  `m2_explicit_local_import_adapter_dry_run` next for one explicit workspace-private export file.
- Keep file-content reads, parsing, real DB import, line-index construction, context-graph
  construction, and every original M2 completion flag false in that dry-run.
- The M2 synthetic context-graph builder review gate is implemented. Define
  `m2_explicit_local_import_adapter_contract` next without reading a local export or implementing
  the adapter.
- Keep every original M2 completion flag false. A passing review authorizes only static contract
  design for one explicit workspace-private local export.
- The M2 synthetic context-graph builder dry-run is implemented. Define
  `m2_synthetic_context_graph_builder_review_gate` next using redacted synthetic evidence only.
- Keep original M2 context-graph completion false. The dry-run projects committed invented fixture
  metadata only; it is not a graph built from a local export.
- The M2 synthetic context-graph contract is defined. Implement
  `m2_synthetic_context_graph_builder_dry_run` next using committed invented fixture relations only.
- Keep graph construction from private input, arbitrary future-branch traversal, and all original
  M2 completion flags false until separately approved implementation slices are reviewed.
- The M2 synthetic line-index builder review gate is implemented. Define
  `m2_synthetic_context_graph_contract` next using invented fixture relations only.
- Keep context-graph construction and all original M2 completion flags false until separately
  approved implementation slices are designed, reviewed, and validated.
- The M2 synthetic line-index builder dry-run is implemented. Define
  `m2_synthetic_line_index_builder_review_gate` next using redacted synthetic evidence only.
- Keep original M2 line-index completion false. The dry-run projects committed invented fixture
  metadata only; it is not a line index built from a local export.
- The M2 synthetic line-index output contract is defined. Implement
  `m2_synthetic_line_index_builder_dry_run` next using the committed invented import fixture only.
- Keep original M2 line-index completion false until a separately approved real local-import path
  and line-index implementation are designed, reviewed, and validated.
- The M2 synthetic import format contract now defines stable synthetic line records and
  `previous_visible`, `nearby_branch`, and `player_option` edges. Define
  `m2_synthetic_import_validator_or_line_index_contract` next.
- Decide whether the next static slice should specify a reusable synthetic fixture validator or
  the line-index output contract first. Do not read a local export in that decision slice.
- Keep original M2 incomplete until locally extracted DB import, line index construction, and
  context graph construction are separately implemented and reviewed.
- ADR 0012 defines the original M2 local extraction import scope. Define
  `m2_synthetic_import_format_contract` next using invented synthetic records only.
- Decide the synthetic import envelope, record identity fields, line-index inputs, and context-graph
  relationship fields before any importer reads a real local export.
- Keep original M2 incomplete until locally extracted DB import, line index construction, and
  context graph construction are separately implemented and reviewed.
- `tasks/milestones.md` remains the unchanged canonical roadmap. Original `M0 - Repo and contracts`
  and `M1 - Synthetic vertical slice` are complete. Original `M2 - Local extraction import` is
  active.
- Milestone 5A.11 closes the internal 5A safety-preparation workstream at the local-only, redacted
  dry-run evidence level. Retire the undefined `milestone_5b_planning` placeholder.
- Define the original M2 local extraction import scope contract before adding any runtime behavior,
  real extraction, private file-content reads, game-file reads, scanning, capture, provider
  execution, or companion contract changes.
- Do not treat the 5A closeout as approval for generated real indexes or committed extracted text.
- Milestone 5A.10 now has a private index builder dry-run. Decide whether the next step is a
  redacted `private-index-dry-run.v1` review gate or a schema refinement before any broader private
  index construction discussion.
- Decide whether future dry-run index evidence should ever include digest linkage, and keep any such
  decision away from paths, filenames, file contents, raw summaries, provider payloads, or real text.
- Real extraction, private file content reads, generated real indexes, file/path/filename hashes,
  automatic game-install scanning, and committed real text remain blocked.
- Milestone 5A.9 now has a private index construction contract. Decide whether to implement a
  private index builder dry-run that consumes only synthetic/redacted fixture evidence.
- Decide the exact dry-run builder input fixture, output summary shape, deletion/regeneration
  workflow, and checker rules before any private index builder code is added.
- Real extraction, private file content reads, generated real indexes, path/filename hashes,
  automatic game-install scanning, and committed real text remain blocked.
- Milestone 5A.8 now has a dry-run summary hash evidence gate. Decide whether to define a private
  index construction contract next.
- Decide what private index construction would be allowed to consume from private inputs, what
  content remains forbidden, and what redacted evidence is required before any implementation.
- Private index implementation, real extraction, file content hashes, path hashes, filename hashes,
  automatic game-install scanning, BepInEx log reads, and committed real text remain blocked.
- Milestone 5A.7 now has a dry-run summary hash helper. Decide whether to add a redacted review gate
  for hash outputs before any private index construction discussion.
- Decide what evidence a hash-output review must include and whether repeated private summary hashes
  are useful enough to justify the remaining privacy risk.
- Private index construction, file content reads, content hashes, path hashes, filename hashes, real
  extraction, and committed real text remain blocked.
- Milestone 5A.6 now has a dry-run summary hash contract. Decide whether to implement the next step
  as a dry-run summary hash dry-run. That implementation step is now complete; future work should
  review the hash output before broader private-index decisions.
- Decide the hash review helper behavior, deletion/regeneration workflow, and checker rules before
  any broader hash artifact workflow is approved.
- File content hashing, path string hashing, filename hashing, raw payload/log hashing, real
  extraction, and private index construction remain blocked.
- Milestone 5A.5 now has a private input hash decision contract. Decide whether to define a dry-run
  summary hash contract next. That decision is now closed by the 5A.6 contract; future work must
  start with a dry-run summary hash dry-run if explicitly approved.
- The canonical redacted summary fields, excluded fields, private output path, and checker rules are
  now defined by 5A.6. Decide implementation details only within that boundary.
- File content hashing, path string hashing, real extraction, and private index construction remain
  blocked.
- Milestone 5A.4 has a dry-run evidence review and decision fixture. Its hash decision follow-up is
  now closed by the 5A.5 contract; future hash work must start with the dry-run summary hash
  contract.
- Decide whether any redacted dry-run summary hash style is safe for private inputs, whether hashing
  remains deferred, and whether hashes should be opt-in even after a later contract exists.
- Decide what evidence would be required before private index construction can move from blocked to
  discussion-ready; 5A.4 keeps it blocked.
- Milestone 5A.3 now has a private input adapter dry-run. Decide whether the metadata-only summaries
  are sufficient to scope a later private index construction contract.
- Decide whether content hashes should remain deferred, become opt-in, or require a separate
  privacy review before any real private input hash is computed.
- Decide the next private-index construction boundary before any helper reads file contents or
  builds indexes from real input.
- Milestone 5A.2 now has a private input adapter contract. Decide whether to implement the next
  step as a dry-run metadata adapter that reads one explicit workspace-private input and emits only
  redacted booleans, counts, hashes, schema status, and blocker categories.
- Decide the exact dry-run summary fields, file/directory traversal bounds under the selected input,
  deletion/regeneration workflow, and checker rules before any real input reads occur.
- Decide whether support for external absolute input paths should remain deferred or require a
  separate safety contract after the workspace-private dry-run path is proven.
- Milestone 5A.1 now has a synthetic indexer/private index contract. Decide the next 5A step as a
  user-selected private input adapter contract before any real local input reads.
- Decide whether future private inputs must be copied under `workspace/local-private/` first or may
  be referenced by explicit user-provided paths with redacted summaries only.
- Decide the private input summary fields, deletion/regeneration workflow, and checker rules before
  implementing any real input adapter.
- Milestone 5A scope/safety was followed by the synthetic indexer/private index contract. The next
  decision is the user-selected private input adapter contract before any adapter reads real local
  inputs.
- Decide the private index shape, redacted summary fields, deletion/regeneration behavior, and
  checker rules for `workspace/local-private/extraction-indexing/` before implementation.
- Expanded Milestone 4 bridge/workflow validation is closed. Decide the exact Milestone 5A
  extraction/indexing adapter implementation plan only after the scope contract is followed by a
  synthetic indexer/private index contract.
- Milestone naming is corrected: local bridge workflow polish is Milestone 4 closeout, not
  top-level Milestone 5A. True Milestone 5A has not started yet and remains the real
  extraction/indexing adapter, local-only.
- Decide whether `scripts/run_local_bridge_workflow.py` is sufficient as the repeatable local smoke
  entrypoint, or whether future packaging should add a higher-level shell script after another
  redacted local pass.
- Decide whether the workflow doctor summary is enough to support a production-overlay shell
  contract planning decision, still as docs/static-contract work first and still without capture,
  polling, provider execution, or companion contract changes.
- The metadata-only overlay refresh readiness helper is now implemented. Decide whether its redacted
  summary is enough to scope a future production-overlay shell contract, or whether another
  docs/static review gate is needed first.
- Decide whether future overlay shell planning should consume the helper summary directly or define
  a separate shell-readiness fixture before any runtime shell work begins.
- Decide whether the bridge-to-overlay wrapper should remain a smoke helper only, or whether later
  overlay-shell planning needs a separate contract artifact. Do not treat the helper as a production
  overlay shell.
- After the companion-connected synthetic smoke runs, decide whether redacted evidence of companion
  health availability and the invented synthetic provider send is sufficient for the next
  synthetic/manual bridge step.
- Decide whether to keep using the existing metadata-probe helper for companion-connected smoke or
  split a wrapper only if the workflow grows beyond config toggles and redacted marker checks.
- After the user runs the local metadata probe smoke helper against the Steam install, decide whether
  the redacted report is enough to debug setup/build/install/config issues or whether another local
  smoke pass is needed.
- Decide whether Steam/BepInEx autodiscovery needs more bounded install-location candidates after
  the first real local test. Do not replace bounded discovery with recursive drive scanning.
- Milestone 4N aligned manual verification for the 4M counters. Decide in 4O whether a redacted
  local report containing those counters is sufficient for later metadata-only discussion.
- Milestone 4M implemented only the 4L-scoped inert metadata counters/booleans. Decide later whether
  user-local evidence is sufficient to discuss any broader metadata-only extension.
- Milestone 4L waived the reviewed local metadata report requirement only for the minimal 4M inert
  scope. Decide later whether any broader probe requires a ready reviewed report before
  implementation.
- Milestone 4K accepted ADR 0009: the project is ready for metadata-only extension discussion only,
  not broad implementation.
- Any future move from `ready_for_metadata_only_extension_discussion` to
  `ready_for_metadata_only_extension_implementation` requires a ready local review or documented
  no-review exception, explicit approval, disabled defaults, no text capture, and no companion HTTP
  contract changes.
- Any future metadata probe expansion requires separate approval and must keep
  `current_line_capture_enabled=false` and `real_text_captured=false` until a later safety review
  changes that boundary.
- Milestone 4F added a redacted runtime smoke report review helper. Actual user-local evidence still
  needs to be reviewed before probe implementation work begins.
- Milestone 4E accepted ADR 0008: keep current-line capture unimplemented and continue
  manual/synthetic bridge events until redacted runtime smoke evidence is reviewed.
- Milestone 4B decided optional C# compilation should skip cleanly when `dotnet` or user-local
  BepInEx references are missing, and should remain outside mandatory `check_all`.
- Decide whether later runtime testing requires pinning/cleaning BepInEx/.NET references to reduce
  `MSB3277` warnings, or whether warnings can remain documented.
- Decide how a future manual in-game trigger should work without global keyboard hooks, clipboard
  writes, or production overlay behavior.
- Whether to add a full JSON Schema dependency later or keep the local validator small.
- Whether the companion server starts as Python, TypeScript, or a split service.
- Which overlay stack to use for the first real UI prototype after bridge feasibility is proven.
- How to structure lawful opt-in web enrichment and source attribution.
- Whether to rename or alias `docs/00-start-here.md` as `docs/00-project-vision.md`.
- Whether to keep the actual repository spelling `revachol-ukro-elisium` long-term or introduce a documented `elysium` alias later.
- Whether future review artifacts should stay static HTML, add Markdown output, or wait for a real overlay prototype.
- Which synthetic eval dimensions should graduate from Milestone 1C checks into the long-term eval framework.
- Milestone 1D chose a stdlib `http.server` skeleton first; decide later whether to keep it, wrap it, or replace it with a production service framework.
- How soon to split deterministic mocks from future provider-backed translation/annotation adapters.
- Milestone 1E chose a tiny stdlib local client and API contract doc before provider work.
- Milestone 2A provider abstractions live under `scripts/` initially; decide later when to move toward a package layout.
- How to version provider prompt contracts before real paid API or local model adapters are enabled.
- Milestone 2B introduced a dedicated prompt/style pack manifest at `prompts/packs/ukrainian_annotation_v1/pack.json`.
- Whether the companion provider annotation endpoint needs explicit API versioning before real overlay or bridge clients depend on it.
- Whether provider requests should carry full prompt pack text or only stable prompt pack references for real runtime providers.
- How debug/developer mode should expose internal English provider guidance without leaking it into default player-facing Ukrainian annotation.
- Milestone 2C deferred companion server/client provider exposure to Milestone 2D after the provider/eval wiring passed one stable CLI/test cycle.
- Milestone 2D kept stable error codes unchanged and maps invalid context packets to `invalid_request`; decide later whether a dedicated `invalid_context_packet` code is worth the contract churn.
- Milestone 2E made `provider`, `provider_debug`, and `prompt_pack` explicit optional annotation-card schema fields.
- Milestone 2E removed `future_roles` from public annotation-card/server response provider metadata; Milestone 2G moved future provider capability planning into the registry. Decide later which registry fields become stable user-facing config.
- Milestone 2F added a fixture-backed provider contract regression runner; decide later how fixture update approval should work once real provider adapters are introduced.
- When real provider adapters are introduced, decide the exact opt-in UX for `allow_external_providers`, cache roots, provider-specific credentials, and any paid API warning surfaces.
- Decide whether `paid_runtime_allowed` should remain separate from `allow_external_providers` or be folded into a clearer provider safety policy before real integrations.
- Decide whether future real provider cache roots must be repo-local ignored paths only, or whether absolute outside-repo private paths should remain allowed.
- Decide the long-term redaction policy for provider request payloads, cache keys, and debug logs before storing real prompt/model traces.
- Decide whether future provider cache entries should store raw payloads, encrypted payloads, structured redacted payloads, or hashes-only records.
- Decide cache retention/deletion/audit rules before enabling real provider persistence.
- Milestone 3A chose a stdlib static HTML overlay prototype first; decide later whether the real overlay shell should be native, webview, game-adjacent, or another UI stack.
- Decide which Milestone 3A overlay view-model fields should become a stable public overlay contract before real overlay/BepInEx clients consume them.
- Decide whether Milestone 3B Ukrainian fallback note text should remain overlay-owned or move into the provider/prompt-pack contract once real providers exist.
- Milestone 3C uses committed JSON fixtures, not a JSON Schema, as the overlay view-model contract. Decide when the overlay view model needs a formal schema.
- Milestone 3C made overlay view models mode-specific. Decide whether a future overlay client also needs an aggregate all-modes payload.
- Decide the review/approval process for intentional overlay fixture rewrites once visual review and real overlay shell work begin.
- Milestone 3D keeps generated HTML review artifacts out of git. Decide later whether any browser screenshot baselines are worth adding once a real overlay shell exists.
- Decide whether the Milestone 3D review index should stay static HTML or become part of a richer local review dashboard after schema hardening.
- Milestone 3E chose a stdlib Python validator instead of JSON Schema files for mode-specific safety checks. Decide later whether to generate a portable schema once the overlay view model stabilizes.
- Decide whether future non-Python overlay clients consume a documented contract page, generated schema, or a small shared package for view-model validation.
- Milestone 3F added a declarative action catalog and visibility state only. Decide later which real
  overlay shell maps these action ids to actual controls.
- Decide whether future key bindings, clipboard actions, and hide/show behavior live in the overlay
  shell, companion client, or a separate local input layer.
- Decide whether action/visibility metadata should later be exported as a portable schema for
  non-Python overlay clients.
- Milestone 3G added stdlib static HTML readability/accessibility guardrails. Decide later whether to
  add browser automation, screenshot baselines, or formal accessibility tooling once a real overlay
  shell exists.
- Decide whether compact-mode brevity limits should become configurable once synthetic fixtures no
  longer represent the full range of annotation length.
- Milestone 3H added declarative transition previews only. Decide later whether the real overlay shell
  consumes these previews directly or implements its own runtime state manager using the same action
  ids.
- Decide whether transition preview fixtures should become a committed overlay state contract later.
- Decide which layer eventually owns real clipboard writes, hide/show behavior, and keyboard mapping;
  they are intentionally outside the simulator.
- Milestone 3I added a state-source contract but no real polling loop. Decide later whether the live
  overlay shell owns polling cadence, debounce, retry, and stale-state expiry.
- Milestone 3J made state-source result fixtures a committed overlay shell handoff contract.
- Decide whether future non-Python overlay clients need a portable schema for state-source results or
  should consume generated contract docs from the Python validator/tests.
- Decide whether a later state-source schema version should keep both no-side-effect alias names or
  consolidate around one naming convention.
- Decide the review process for intentional state-source fixture updates once a real overlay shell
  starts consuming these fixtures.
- Milestone 3K accepted ADR 0007: defer Electron/Tauri/native overlay shell work and move next to a
  synthetic/manual BepInEx bridge skeleton.
- Decide after Milestone 4A whether the bridge should remain manual/synthetic longer or begin
  carefully scoped current-line detection research.
- Decide later whether the first real shell should be a local browser page, companion-served page,
  Electron, Tauri, or native overlay after the bridge proves useful state emission.
