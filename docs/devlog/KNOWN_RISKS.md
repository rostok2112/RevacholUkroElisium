# Known Risks

- Runtime targeted hook candidate research is now contract-scoped by
  `docs/runtime-targeted-hook-candidate-research-contract.md`,
  `tests/fixtures/runtime_targeted_hook_candidate_research_contract.synthetic.json`, and
  `scripts/check_runtime_targeted_hook_candidate_research_contract.py`.
- The next step is `runtime_targeted_hook_candidate_research_local_report`, which may summarize
  local/private research only with redacted booleans, counts, statuses, and blocker categories.
- The risk remains that targeted research could leak candidate identifiers, decompiled method names,
  signatures, class names, raw logs, screenshots, source text, payload dumps, private paths,
  provider data, or real runtime evidence. These stay forbidden in tracked files.

---

- Runtime current-line capture strategy is now selected as `targeted_hook_research_first` and
  tracked by `docs/runtime-current-line-capture-strategy-decision.md`,
  `tests/fixtures/runtime_current_line_capture_strategy_decision.synthetic.json`, and
  `scripts/check_runtime_current_line_capture_strategy_decision.py`.
- This increases implementation risk if the next step jumps straight to hooks. The contract above
  keeps hook implementation blocked and advances only to a redacted local report step.
- Decompiled identifiers, method signatures, class names, raw logs, screenshots, game text, private
  paths, payload dumps, provider payloads, and real runtime evidence must stay out of tracked files.

---

- Runtime current-line capture spike tooling can enable a synthetic runtime event at startup when
  the user explicitly toggles local BepInEx config. This is still not a real game-text capture path.
- Capture strategy is still undecided. Hooks, broad Unity scanning, OCR, screenshots, game-file
  reads, BepInEx log commits, provider calls, and raw companion payloads remain blocked.
- Redacted capture-spike reports must stay under ignored workspace roots and may contain only
  booleans, counts, status, and blocker categories.
- The next safe step is `runtime_targeted_hook_candidate_research_contract`.

---

- Runtime current-line transport now accepts private runtime text through
  `POST /runtime/current-line` and keeps the latest event in companion memory. This is local-only
  transport, not capture: no hooks, Unity scanning, OCR, game-file reads, BepInEx log reads,
  provider execution, or tracked runtime text are approved.
- `RuntimeCurrentLineTransportEnabled` remains disabled by default in the BepInEx config. Enabling
  it before a local capture spike should be done only for synthetic/manual localhost tests.
- `scripts/run_runtime_current_line_smoke.py` is redacted public evidence only. Generated/private
  runtime reports must stay under ignored workspace roots.
- The runtime capture spike is now implemented; the strategy decision now points to
  `runtime_targeted_hook_candidate_research_contract`.

---

- Runtime translation memory now writes private cache entries under
  `workspace/local-private/runtime-cache/translation-memory/`. The cache may contain real runtime
  source text and Ukrainian translations, so it must remain ignored and must never be copied into
  docs, tests, reports, commits, screenshots, or logs.
- `scripts/run_runtime_translation_memory.py` derives private cache keys internally. Public summaries
  must not expose keys, hashes, filenames, private paths, source text, translated text, prompts, or
  provider payloads.
- `docs/runtime-translation-memory-contract.md`,
  `tests/fixtures/runtime_translation_memory_contract.synthetic.json`,
  `scripts/check_runtime_translation_memory_contract.py`, and
  `scripts/run_runtime_translation_memory.py` do not approve provider execution; they only ensure a
  cache hit prevents repeat translation.
- The runtime current-line transport now exists; the next safe step is
  `runtime_current_line_capture_spike`.

---

- Strict completion now requires manual/local verification evidence in addition to automated
  checks. `docs/milestone-completion-standard.md`,
  `tests/fixtures/milestone_completion_status.synthetic.json`, and
  `scripts/check_milestone_completion_status.py` keep M5 planning blocked while M0-M4 have
  `fully_complete=false`.
- M0 and M1 are now fully complete under the strict standard. The remaining blocker is M2 manual
  private-export verification.
- The M2 manual gate may use chat attestation as evidence, but only redacted boolean/status fields
  may be committed. Do not commit private export paths, generated DBs, line indexes, context graphs,
  review files, logs, source text, ids, or payloads.
- The M1 manual gate may use chat attestation as evidence, but only redacted boolean/status fields
  may be committed. Do not commit generated synthetic review artifacts from `workspace/`.
- The M0 manual gate may use chat attestation as evidence, but only redacted boolean/status fields
  may be committed. Do not commit conversation text if it includes private paths, logs,
  screenshots, extracted text, or payload details.
- Roadmap criteria are allowed to evolve. The risk is uncontrolled drift; every change must update
  `tasks/milestones.md`, docs, and the relevant checker/fixture evidence.
- Do not convert manual evidence into committed private paths, real extracted text, screenshots,
  generated DBs, indexes, context graphs, logs, provider payloads, `bin`, or `obj`.

---

- M4 closeout (`docs/m4-closeout.md`, `tests/fixtures/m4_closeout.synthetic.json`, and
  `scripts/check_m4_closeout.py`) marks original M4 complete only at the local browser shell level.
  It does not approve native always-on-top packaging, Electron/Tauri setup, global keyboard hooks,
  game input hooks, clipboard writes, provider execution, companion HTTP changes, OCR, Unity
  scanning, hooks/Harmony, screenshots, private paths, raw provider payloads, or committed generated
  shell artifacts.
- The next approved roadmap step is `m5_maximum_quality_pipeline_planning`.
- M4 page-local hotkeys (`scripts/run_m4_overlay_shell.py`) are browser-page event listeners only.
  They must not become global keyboard hooks, game input hooks, clipboard writes, native shell
  behavior, provider calls, companion HTTP changes, screenshot capture, or private path logging.
- The next approved M4 step is `m4_closeout`.
- M4 Genius card shell (`scripts/run_m4_overlay_shell.py`) reuses the existing deep view model. It
  must not drift into a second annotation schema, raw source-text duplication, line-id display,
  provider payload display, private path display, screenshot capture, clipboard writes, global
  keyboard hooks, or companion HTTP changes.
- The next approved M4 step is `m4_overlay_hotkeys`.
- M4 compact translation shell (`scripts/run_m4_overlay_shell.py`) is a local browser HTML helper,
  not native always-on-top packaging. It intentionally avoids duplicating original/source text in
  player-facing compact shell HTML. Future changes must not turn compact rendering into raw text,
  debug metadata, provider payload, private path, screenshot, clipboard, global hotkey, or companion
  contract output.
- The next approved M4 step is `m4_genius_card_shell`.
- M4 overlay shell contract (`docs/m4-overlay-shell-contract.md`,
  `tests/fixtures/m4_overlay_shell_contract.synthetic.json`, and
  `scripts/check_m4_overlay_shell_contract.py`) defines a local browser shell boundary only. It
  does not implement compact translation, Genius card, hotkeys, native always-on-top behavior,
  Electron/Tauri setup, global keyboard hooks, clipboard writes, provider execution, companion HTTP
  changes, OCR, Unity scanning, hooks/Harmony, game-file reads, BepInEx log reads, screenshots,
  private paths, or committed generated shell artifacts.
- The next approved M4 step is `m4_compact_translation_shell`.
- M4 scope recovery (`docs/m4-real-overlay-scope.md`,
  `tests/fixtures/m4_real_overlay_scope.synthetic.json`, and
  `scripts/check_m4_real_overlay_scope.py`) makes original `M4 - Real overlay` active, but it does
  not implement compact translation, Genius card, hotkeys, native always-on-top behavior,
  Electron/Tauri setup, global keyboard hooks, clipboard writes, provider execution, companion HTTP
  changes, OCR, Unity scanning, hooks/Harmony, game-file reads, BepInEx log reads, or committed
  generated shell artifacts.
- The next approved M4 step is `m4_overlay_shell_contract`; keep it limited to the overlay shell
  boundary so M4 does not turn into an unbounded chain.
- M3 closeout (`docs/m3-closeout.md`, `tests/fixtures/m3_closeout.synthetic.json`, and
  `scripts/check_m3_closeout.py`) marks original M3 complete only under the redacted/local
  implementation boundaries. It does not approve raw text capture/dumps, provider calls, companion
  HTTP contract changes, game-file reads, BepInEx log reads, UI text reading, Unity scanning,
  hooks/Harmony, OCR, screenshots, private paths, `bin`, or `obj`.
- The next approved roadmap step is `m4_real_overlay_scope_recovery`.
- M3 debug console (`packages/bepinex-plugin/src/DebugCommandHandler.cs`,
  `tests/fixtures/m3_debug_console.synthetic.json`, and `scripts/check_m3_debug_console.py`) is a
  redacted command surface only. Do not expand it into raw text dumps, payload dumps, ID dumps,
  provider calls, companion HTTP contract changes, game-file reads, BepInEx log reads, UI text
  reading, Unity scanning, hooks/Harmony, OCR, or committed runtime artifacts.
- The next approved M3 step is `m3_closeout`; it closes only after the three original M3
  criteria are implemented and guarded.
- M3 line-ID matching (`scripts/run_m3_line_id_match.py`,
  `tests/fixtures/m3_line_id_matching.synthetic.json`, and `tests/test_m3_line_id_match.py`) reads
  an ignored private line-index artifact. It must never emit line IDs, record IDs, source text,
  private paths, hashes, logs, payloads, or runtime evidence.
- The next approved M3 step is `m3_debug_console`; keep it limited to the original debug
  console criterion.
- M3 current-line event implementation (`packages/bepinex-plugin/src/CurrentLineEventFactory.cs`,
  `tests/fixtures/m3_current_line_event_implementation.synthetic.json`, and
  `scripts/check_m3_current_line_event_implementation.py`) is disabled by default and redacted.
  Do not expand it into raw text capture, UI text reading, Unity scanning, hooks/Harmony, OCR,
  provider calls, companion HTTP contract changes, line-index reads, or debug console commands.
- The next approved M3 step is `m3_line_id_matching`; keep it limited to exact line-ID
  matching.
- M3 current-line event contract (`docs/m3-current-line-event-contract.md`,
  `tests/fixtures/m3_current_line_event_contract.synthetic.json`, and
  `scripts/check_m3_current_line_event_contract.py`) defines only a later minimal event
  implementation. It must not be expanded into raw dialogue capture, UI text reading, broad Unity
  scanning, hooks/Harmony, OCR, provider calls, companion HTTP contract changes, line-ID matching,
  private line-index reads, or debug console work.
- The next approved M3 step is `m3_current_line_event_implementation`; keep it limited to the
  current-line event criterion.
- M3 scope recovery (`docs/m3-bepinex-bridge-scope.md`,
  `tests/fixtures/m3_bepinex_bridge_scope.synthetic.json`, and
  `scripts/check_m3_bepinex_bridge_scope.py`) reuses former bridge/workflow work only as a
  baseline. Do not treat the existing synthetic event, metadata probe, or local workflow wrapper as
  real current-line capture, line-ID matching, or debug console completion.
- Avoid adding unbounded contract/review chains inside M3. The next approved step is
  `m3_current_line_event_contract`.
- `scripts/review_m2_closeout.py` reviews only redacted review JSON from the M2 import, line-index,
  and context-graph review roots. It must not be changed to reopen private artifacts, selected
  exports, game files, logs, screenshots, provider payloads, or runtime evidence unless a later
  contract explicitly scopes that behavior.
- M2 closeout means the three original criteria have implementation paths and redacted review
  evidence. It does not permit committing generated private DB artifacts, line indexes, context
  graphs, extracted text, private paths, payloads, reports, or runtime artifacts.
- `scripts/review_m2_context_graph.py` reviews only redacted context-graph summary JSON. It must
  not be changed to reopen private context-graph artifacts, private DB artifacts, private line-index
  artifacts, or selected exports unless a later contract explicitly scopes that behavior.
- Optional context-graph summary and review output under
  `workspace/local-private/extraction-indexing/import/context-graph-summary/` and
  `workspace/local-private/extraction-indexing/import/context-graph-review/` must stay ignored and
  out of tracked files, chat, reports, and review Markdown.
- `scripts/run_m2_context_graph.py` can write a private context-graph artifact containing private
  ids under `workspace/local-private/extraction-indexing/import/context-graph/`. That output must
  never be committed, pasted into chat, copied into docs, review Markdown, reports, or public
  generated artifacts.
- The context-graph implementation reads one private DB artifact, one private line-index artifact,
  and one redacted line-index review artifact only. Do not change it to discover directories, read
  game files, consume raw exports, duplicate source text into graph nodes, or emit ids/relation
  values in public summaries.
- `scripts/review_m2_line_index.py` reviews only redacted line-index summary JSON. It must not be
  changed to reopen private line-index artifacts or private DB artifacts unless a later contract
  explicitly scopes that behavior.
- Optional line-index summary and review output under
  `workspace/local-private/extraction-indexing/import/line-index-summary/` and
  `workspace/local-private/extraction-indexing/import/line-index-review/` must stay ignored and out
  of tracked files, chat, reports, and review Markdown.
- A future `m2_context_graph_implementation` may read one ignored private DB artifact and one
  ignored private line-index artifact, then write a private context graph under
  `workspace/local-private/extraction-indexing/import/context-graph/`. That graph may contain
  private ids and must never be committed, pasted into chat, copied into docs, review Markdown,
  reports, or generated public artifacts.
- The M2 context-graph contract allows relation-to-retrieval-bucket mapping only inside the private
  graph implementation. Do not expand it into arbitrary future-branch traversal, runtime capture,
  provider execution, companion contract changes, or public summaries containing ids, relation
  values, source text, paths, filenames, logs, hashes, or payloads.
- `scripts/run_m2_line_index.py` can write a private line-index artifact containing private ids and
  source text under `workspace/local-private/extraction-indexing/import/line-index/`. That output
  must never be committed, pasted into chat, copied into docs, review Markdown, reports, or public
  generated artifacts.
- The line-index implementation reads one private imported DB artifact and one redacted review
  artifact only. Do not change it to discover directories, read game files, or consume raw exports.
- `scripts/review_m2_local_import.py` reviews only redacted import-summary JSON. It must not be
  changed to reopen private DB artifacts or selected exports unless a later contract explicitly
  scopes that behavior.
- Optional local-import summary and review output under
  `workspace/local-private/extraction-indexing/import/db-summary/` and
  `workspace/local-private/extraction-indexing/import/db-review/` must stay ignored and out of
  tracked files, chat, reports, and review Markdown.
- A future `m2_line_index_implementation` may read one ignored private DB artifact and write a
  private line-index artifact under `workspace/local-private/extraction-indexing/import/line-index/`.
  That line index may contain private ids and source text and must never be committed, pasted into
  chat, copied into docs, review Markdown, reports, or generated public artifacts.
- The line-index contract approves only indexing from the selected private DB artifact. It does not
  permit context-graph construction, retrieval-bucket mapping, game scanning, runtime reads,
  providers, companion contract changes, or committed private artifacts.
- `scripts/run_m2_local_import.py` can write a private DB artifact containing extracted/private
  values under `workspace/local-private/extraction-indexing/import/db/`. That directory is ignored
  and must never be committed, pasted into chat, copied into docs, review Markdown, reports, or
  generated indexes.
- The local import implementation decodes the selected JSON export in memory with no size cap,
  consistent with earlier M2 dry-runs. A large selected export can consume substantial memory.
- The local import implementation does not build a line index or context graph. Do not treat the
  private DB artifact as searchable index evidence.
- The M2 local import final approval contract permits only the next local-import implementation
  slice. Do not treat it as completion of original M2 or permission to build a line index, build a
  context graph, map retrieval buckets, scan game installs, change companion contracts, or commit
  private artifacts.
- A future `m2_local_import_implementation` may read and parse one explicit private JSON export and
  write private DB output under `workspace/local-private/extraction-indexing/import/db/`. That
  private DB output must stay ignored and out of tracked files, chat, review Markdown, reports, and
  commits.
- The M2 context-edge integrity dry-run review gate reads redacted summary JSON only. A passing
  review permits a final local-import approval contract discussion, not DB import, line-index
  construction, context-graph construction, retrieval-bucket mapping, or any original M2 completion
  flag.
- Keep optional context-edge integrity review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/context-edge-integrity-review/` and out of
  tracked files, chat, reports, and commits.
- The M2 explicit local-import context-edge integrity dry-run reopens one explicit private UTF-8
  JSON export, decodes it with no size cap, and counts self-edge and duplicate-edge occurrences in
  memory. A large selected file may consume substantial memory.
- The dry-run output is aggregate-only. Do not treat it as permission to emit ids, relation values,
  duplicate tuples, source text, paths, filenames, hashes, logs, payloads, or runtime evidence.
- Keep optional context-edge integrity dry-run JSON under
  `workspace/local-private/extraction-indexing/import/context-edge-integrity/` and out of tracked
  files, chat, reports, and commits.
- A future `m2_explicit_local_import_context_edge_integrity_dry_run_review_gate` must read only
  redacted integrity summary JSON and must not reopen the selected export.
- The M2 explicit local-import context-edge integrity contract is static policy only. Do not
  describe it as reopening or decoding an export, checking real edges, emitting ids or relation
  values, mapping retrieval buckets, importing a DB, building an index, or constructing a graph.
- A future `m2_explicit_local_import_context_edge_integrity_dry_run` may count self-edges and
  duplicate edges only as aggregate redacted evidence. It must not emit duplicate tuples, normalize
  ids, hash ids, map retrieval buckets, or construct graph edges.
- Keep future optional context-edge integrity summaries under
  `workspace/local-private/extraction-indexing/import/context-edge-integrity/` and out of tracked
  files, chat, reports, and commits.
- The M2 context-edge reference dry-run review gate reads redacted summary JSON only. A passing
  review permits a static context-edge integrity contract discussion, not export reopening, id
  emission, id normalization, id hashing, self-edge checks, duplicate-edge checks,
  retrieval-bucket mapping, DB import, index construction, or graph construction.
- Keep optional context-edge reference review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/context-edge-reference-review/` and out of
  tracked files, chat, reports, and commits.
- The M2 explicit local-import context-edge reference dry-run reopens one explicit private UTF-8
  JSON export, decodes it with no size cap, and builds an in-memory top-level record-id set. A
  large selected file may consume substantial memory.
- Keep optional context-edge reference dry-run JSON under
  `workspace/local-private/extraction-indexing/import/context-edge-reference/` and out of tracked
  files, chat, reports, and commits.
- A future `m2_explicit_local_import_context_edge_reference_dry_run_review_gate` must read
  redacted summary JSON only. It must not reopen the selected export, emit ids, normalize ids, hash
  ids, check self-edges, deduplicate edges, map retrieval buckets, import a DB, construct an index,
  or construct a graph.
- The M2 explicit local-import context-edge reference contract is static policy only. Do not
  describe it as reopening or decoding an export, validating real references, emitting ids,
  checking self-edges, deduplicating edges, importing a DB, building an index, or constructing a
  graph.
- A future `m2_explicit_local_import_context_edge_reference_dry_run` may compare edge ids against
  the decoded top-level record-id set in memory only, but must emit aggregate counts and blockers
  only. It must not emit ids, normalize ids, hash ids, check self-edges, deduplicate edges, or build
  a graph.
- Keep future optional context-edge reference summaries under
  `workspace/local-private/extraction-indexing/import/context-edge-reference/` and out of tracked
  files, chat, reports, and commits.
- The M2 context-edge shape dry-run review gate reads redacted summary JSON only. A passing review
  permits a static context-edge reference contract discussion, not export reopening, edge id
  emission, reference validation, self-edge checks, duplicate-edge checks, DB import, index
  construction, or graph construction.
- Keep optional context-edge shape review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/context-edge-shape-review/` and out of
  tracked files, chat, reports, and commits.
- A future `m2_explicit_local_import_context_edge_reference_contract` must remain static policy
  only and define a separately reviewed boundary before any edge ids are validated against records.
- The M2 explicit local-import context-edge shape dry-run reopens one explicit private UTF-8 JSON
  export, decodes it with no size cap, and checks all context-edge objects in memory. A large
  selected file may consume substantial memory.
- Keep optional context-edge shape dry-run JSON under
  `workspace/local-private/extraction-indexing/import/context-edge-shape/` and out of tracked
  files, chat, reports, and commits.
- A future `m2_explicit_local_import_context_edge_shape_dry_run_review_gate` must read redacted
  summary JSON only. It must not reopen the selected export, emit edge ids, validate references,
  check self-edges, deduplicate edges, traverse records, or construct a graph.
- The M2 explicit local-import context-edge shape contract is static policy only. Do not describe it
  as reopening or decoding an export, inspecting real context edges, validating references,
  importing a DB, building an index, or constructing a graph.
- A future `m2_explicit_local_import_context_edge_shape_dry_run` may inspect all context-edge
  objects but must check top-level keys, immediate types, and relation vocabulary only. It must not
  emit edge ids, validate record references, check self-edges, deduplicate edges, or construct a
  graph.
- Keep future optional context-edge shape summaries under
  `workspace/local-private/extraction-indexing/import/context-edge-shape/` and out of tracked
  files, chat, reports, and commits.
- The M2 record-shape dry-run review gate reads redacted summary JSON only. A passing review
  permits a static context-edge shape contract discussion, not export reopening, edge traversal,
  DB import, index construction, or graph construction.
- Keep optional record-shape review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/record-shape-review/` and out of tracked
  files, chat, reports, and commits.
- A future `m2_explicit_local_import_context_edge_shape_contract` must remain static policy only
  and define a separately reviewed boundary before any context-edge shapes are inspected.
- The M2 explicit local-import record-shape dry-run reopens one explicit private UTF-8 JSON export,
  decodes it with no size cap, and checks all record objects in memory. A large selected file may
  consume substantial memory.
- Keep optional record-shape dry-run JSON under
  `workspace/local-private/extraction-indexing/import/record-shape/` and out of tracked files,
  chat, reports, and commits.
- A future `m2_explicit_local_import_record_shape_dry_run_review_gate` must read redacted summary
  JSON only. It must not reopen the selected export or traverse record values, tags, metadata, or
  context edges.
- The M2 explicit local-import record-shape contract is static policy only. Do not describe it as
  reopening or decoding an export, inspecting real records, importing a DB, building an index, or
  constructing a graph.
- A future `m2_explicit_local_import_record_shape_dry_run` may inspect all record objects but must
  check top-level keys and types only. It must not inspect, compare, normalize, hash, log, or emit
  private record values.
- Keep future optional record-shape summaries under
  `workspace/local-private/extraction-indexing/import/record-shape/` and out of tracked files,
  chat, reports, and commits.
- Context-edge inspection remains deferred to a separate contract after record-shape review.
- The M2 schema-compatibility dry-run review gate reads redacted summary JSON only. A passing review
  permits a static record-shape contract discussion, not export reopening, nested traversal,
  record-shape inspection, DB import, index construction, or graph construction.
- Keep optional schema-compatibility review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/schema-compatibility-review/` and out of
  tracked files, chat, reports, and commits.
- A future `m2_explicit_local_import_record_shape_contract` must remain static policy only and
  define a separately reviewed boundary before any nested record values are inspected.
- The M2 explicit local-import schema-compatibility dry-run decodes one explicit private UTF-8 JSON
  file with no size cap. A large selected file may consume substantial memory.
- Keep schema-compatibility dry-run output under
  `workspace/local-private/extraction-indexing/import/schema-compatibility/` and out of tracked
  files, chat, reports, and commits.
- A future `m2_explicit_local_import_schema_compatibility_dry_run_review_gate` must inspect only a
  redacted compatibility summary. It must not reopen the selected export or traverse nested values.
- The M2 explicit local-import schema-compatibility contract is static policy only. Do not describe
  it as reopening or decoding an export, parsing nested values, importing a DB, building an index,
  or constructing a graph.
- A future `m2_explicit_local_import_schema_compatibility_dry_run` may decode one explicit UTF-8
  JSON object and inspect top-level envelope fields and aggregate counts only.
- Keep optional compatibility summaries under
  `workspace/local-private/extraction-indexing/import/schema-compatibility/` and out of tracked
  files, chat, reports, and commits.
- The M2 explicit local-import adapter dry-run review gate reads redacted summary JSON only. A
  passing review permits a static schema-compatibility contract discussion, not export reopening,
  schema inspection, parsing, or real DB import.
- Keep optional adapter dry-run review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/adapter-dry-run-review/` and out of tracked
  files, chat, reports, and commits.
- A future `m2_explicit_local_import_schema_compatibility_contract` must define the narrowest safe
  inspection boundary before any adapter reopens a selected export.
- The M2 explicit local-import adapter dry-run reads filesystem metadata for one selected private
  file only. Do not describe it as parsing an export, importing a DB, building an index, or
  constructing a graph.
- Keep optional dry-run summaries under
  `workspace/local-private/extraction-indexing/import/adapter-dry-run/` and out of tracked files,
  chat, reports, and commits.
- A future `m2_explicit_local_import_adapter_dry_run_review_gate` must inspect only redacted dry-run
  summaries and must not reopen the selected export.
- The M2 explicit local-import adapter contract is static guardrail work only. Do not describe it
  as permission to read or parse an export, import a DB, build an index, or construct a graph.
- A future `m2_explicit_local_import_adapter_dry_run` must accept one explicit workspace-private
  file only and summarize filesystem metadata without reading file contents.
- The M2 synthetic context-graph builder review gate is redacted evidence only. A passing review is
  permission to define `m2_explicit_local_import_adapter_contract`, not to read a local export or
  implement an adapter.
- Keep generated context-graph review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/context-graph-review/` and out of tracked
  files, chat, reports, and commits.
- The M2 synthetic context-graph builder dry-run projects committed invented fixture metadata only.
  Do not describe it as a graph built from a local export or completion of the original M2 graph
  criterion.
- Keep optional context-graph builder output under
  `workspace/local-private/extraction-indexing/import/context-graph/` and out of tracked files,
  chat, reports, and commits.
- A future `m2_synthetic_context_graph_builder_review_gate` must emit redacted evidence only and
  must not approve arbitrary future branches or graph construction from private input.
- The M2 synthetic context-graph fixture is static metadata-only contract evidence. Do not
  describe it as a built context graph or completion of the original M2 graph criterion.
- A future `m2_synthetic_context_graph_builder_dry_run` must remain invented-fixture-only, preserve
  spoiler budget `none`, and reject arbitrary future-branch traversal.
- The M2 synthetic line-index builder review gate is redacted evidence only. A passing review is
  permission to define a synthetic context-graph contract, not to construct a graph or mark any
  original M2 criterion complete.
- Keep generated line-index review JSON and Markdown under
  `workspace/local-private/extraction-indexing/import/line-index-review/` and out of tracked files,
  chat, reports, and commits.
- The M2 synthetic line-index builder dry-run is a metadata-only projection over invented fixture
  records. Do not describe it as a line index built from a local export or as completion of the
  original M2 line-index criterion.
- Keep optional builder output under
  `workspace/local-private/extraction-indexing/import/line-index/` and out of tracked files, chat,
  reports, and commits.
- The M2 synthetic line-index fixture is metadata-only contract evidence. It is not an index built
  from a local export and must not be described as completing the original M2 line-index criterion.
- A future `m2_synthetic_line_index_builder_dry_run` must remain invented-fixture-only and must not
  copy source text, graph edges, filenames, paths, hashes, payloads, logs, or runtime evidence into
  output.
- The M2 synthetic import format contract defines invented records and relation edges only. It does
  not implement real DB import, line indexing, context-graph construction, or private-content reads.
- `m2_synthetic_import_validator_or_line_index_contract` must remain synthetic/static until a
  separately approved implementation slice exists. A passing fixture checker is not permission to
  read a local export or scan a game installation.
- Invented fixture provenance is partly a human-review responsibility. Keep synthetic ids,
  placeholder fields, explicit false safety flags, and denylist checks intact.
- ADR 0012 defines only the original M2 scope. It does not implement locally extracted DB import,
  line indexing, context graph construction, or private-content reads.
- `m2_synthetic_import_format_contract` must remain invented-fixture-only. Do not let the next
  contract become implicit permission to read a local export or scan a game installation.
- `tasks/milestones.md` is the unchanged canonical roadmap. Original `M2 - Local extraction import`
  is active. Do not confuse the internal 5A-labelled safety-preparation series with original
  `M5 - Maximum quality pipeline`, which has not started.
- Milestone 5A.11 closes the internal 5A workstream at the redacted dry-run evidence level only. Do
  not summarize it as completed real extraction or completed real indexing.
- The retired `milestone_5b_planning` placeholder was never part of the original roadmap. Do not
  let the 5A closeout fixture become implicit permission to read game files, private file contents,
  BepInEx logs, screenshots, saves, or decompiled output.
- Local summaries, hashes, reviews, and dry-run index previews remain private even when they contain
  only counts, sizes, booleans, and redacted evidence. Keep them out of tracked files and chat.
- Milestone 5A.10 builds only a redacted private index dry-run preview. A passing dry-run must not
  be mistaken for permission to build an index from private file contents or real text.
- `private-index-dry-run.v1` can still reveal metadata counts and total size values inherited from
  the dry-run summary. Keep local outputs under
  `workspace/local-private/extraction-indexing/index/` and out of tracked files, chat, reports, and
  commits.
- The 5A.10 helper deliberately does not link a summary to a hash when no safe shared identifier is
  available. Do not add path-, filename-, content-, or digest-bearing linkage without a later safety
  contract.
- Milestone 5A.9 defines private index construction only as a contract. A future builder dry-run
  must not be mistaken for permission to read private file contents or build an index from real
  text.
- Even under `workspace/local-private/extraction-indexing/index/`, generated private indexes can
  leak private metadata if copied into tracked files, chat, reports, or commits.
- Future private indexes must not include filenames, path strings, raw payloads/logs, screenshots,
  OCR, save data, decompiled data, provider payloads, companion runtime data, or game-install scan
  evidence.
- Milestone 5A.8 reviews dry-run summary hash outputs only. A passing review does not approve
  private index construction, real extraction, file content reads, file content hashes, path hashes,
  filename hashes, or committed extracted text.
- Hash review JSON/Markdown under `workspace/local-private/extraction-indexing/hash-review/` is
  ignored, but it can still expose local readiness decisions if copied into tracked files or chat.
- `ready_for_private_index_decision=true` means only that a later private index construction
  contract can be discussed. It must not be treated as implementation approval.
- Milestone 5A.7 computes a SHA-256 digest only over canonical redacted dry-run summary metadata.
  The digest is still private metadata and can identify repeated or distinctive local summaries.
- Hash output under `workspace/local-private/extraction-indexing/hash/` is ignored, but it must not
  be copied into tracked docs, fixtures, commits, chat, or reports from real private runs.
- The helper rejects excluded and unknown source-summary fields. Future summary shape changes must
  update the 5A.6 contract, tests, and helper together rather than silently dropping new fields.
- A successful hash dry-run does not approve private index construction, file content reads, content
  hashes, path hashes, filename hashes, real extraction, or committed extracted text.
- Milestone 5A.6 defines a future canonical redacted summary hash input, but does not approve hash
  implementation. Treat it as a contract gate, not executable hashing permission.
- Redacted dry-run summary hashes can still become stable identifiers if counts, sizes, blockers, or
  other metadata are too distinctive. Keep the canonical field list narrow and reviewed before
  implementation.
- Filename hashing and path hashing remain blocked because they can reveal local layout or identify
  private files even without raw contents.
- Future hash dry-runs must not include timestamps, report paths, verbose path fields, generated
  indexes, raw logs, payloads, screenshots, OCR output, save data, provider payloads, or game text.
- Milestone 5A.5 is a hash decision contract only. It does not approve hash implementation, file
  content hashing, path string hashing, private index construction, real extraction, or committed
  real text.
- Even a future hash of redacted dry-run metadata can become a stable private identifier if the
  canonical input includes enough file counts, sizes, blockers, or timing-like fields. Define exact
  included and excluded fields before computing any hash.
- File content hashes and path string hashes remain especially risky because they can identify known
  private files or local layouts even when raw text is absent.
- Do not treat `dry_run_summary_hashing_allowed_next="decision_pending"` as implementation approval.
  It only means a later dry-run summary hash contract can be discussed.
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
