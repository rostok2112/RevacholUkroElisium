# Next Actions

After strict M0-M4 completion recovery:

1. Treat `docs/milestone-completion-standard.md`,
   `tests/fixtures/milestone_completion_status.synthetic.json`, and
   `scripts/check_milestone_completion_status.py` as the active roadmap completion guardrail.
2. M0-M4 are not fully complete under the strict definition until required manual/local
   verification evidence is recorded.
3. Treat the roadmap as amendable through documented review, not frozen; then complete M0 manual
   verification and proceed sequentially through M1, M2, M3, and M4.
4. Keep private/generated reports and artifacts out of git.

Recommended next safe step:

- Owner replies with the M0 approval or rejection text. If approved, record the redacted
  attestation and advance to `m1_manual_synthetic_slice_review`.

---

After M4 closeout:

1. Treat `docs/m4-closeout.md`, `tests/fixtures/m4_closeout.synthetic.json`, and
   `scripts/check_m4_closeout.py` as the M4 completion guardrail.
2. M4 is closed at the local browser shell level: compact translation, Genius card, and page-local
   hotkeys are implemented.
3. Start original `M5 - Maximum quality pipeline` with planning/scope recovery before
   implementation.
4. Keep native always-on-top packaging, Electron/Tauri setup, global keyboard hooks, clipboard
   writes, provider execution, companion HTTP changes, OCR, Unity scanning, hooks/Harmony,
   screenshots, private paths, generated shell artifacts, raw provider payloads, `bin`, and `obj`
   blocked unless a later milestone scopes them.

Recommended next safe step:

- Define `m5_maximum_quality_pipeline_planning`.

---

After M4 page-local hotkeys:

1. Treat `scripts/run_m4_overlay_shell.py` and `tests/test_m4_overlay_shell.py` as the implementation
   guardrail for all three original M4 criteria.
2. Add only M4 closeout next.
3. Close M4 only if compact translation, Genius card, and page-local hotkeys are all present and
   reviewed.
4. Keep native always-on-top packaging, Electron/Tauri setup, global keyboard hooks, clipboard
   writes, provider execution, companion HTTP changes, OCR, Unity scanning, hooks/Harmony,
   screenshots, private paths, and committed generated shell artifacts blocked.

Recommended next safe step:

- Implement `m4_closeout`.

---

After M4 Genius card shell:

1. Treat `scripts/run_m4_overlay_shell.py` and `tests/test_m4_overlay_shell.py` as the compact and
   Genius shell guardrail.
2. Add only page-local hotkeys next.
3. Hotkeys must affect only the loaded browser page: compact visibility, Genius card open/close,
   and debug view only when explicitly enabled.
4. Keep native always-on-top packaging, Electron/Tauri setup, global keyboard hooks, clipboard
   writes, provider execution, companion HTTP changes, OCR, Unity scanning, hooks/Harmony,
   screenshots, private paths, and committed generated shell artifacts blocked.

Recommended next safe step:

- Implement `m4_overlay_hotkeys`.

---

After M4 compact translation shell:

1. Treat `scripts/run_m4_overlay_shell.py` and `tests/test_m4_overlay_shell.py` as the compact
   shell implementation guardrail.
2. Compact shell rendering consumes only validated compact view models and writes generated HTML
   only under `workspace/local-private/overlay/`.
3. Add only Genius card rendering next, using the existing deep view model.
4. Keep hotkeys, native always-on-top packaging, Electron/Tauri setup, global keyboard hooks,
   clipboard writes, provider execution, companion HTTP changes, OCR, Unity scanning,
   hooks/Harmony, screenshots, private paths, and committed generated shell artifacts blocked.

Recommended next safe step:

- Implement `m4_genius_card_shell`.

---

After M4 overlay shell contract:

1. Treat `docs/m4-overlay-shell-contract.md`,
   `tests/fixtures/m4_overlay_shell_contract.synthetic.json`, and
   `scripts/check_m4_overlay_shell_contract.py` as the shell boundary.
2. Implement only compact translation shell rendering next.
3. Reuse existing validated compact view models and keep generated shell output under
   `workspace/local-private/overlay/`.
4. Keep Genius card, hotkeys, native always-on-top packaging, Electron/Tauri setup, global keyboard
   hooks, clipboard writes, provider execution, companion HTTP changes, OCR, Unity scanning,
   hooks/Harmony, game-file reads, BepInEx log reads, screenshots, private paths, and committed
   generated shell artifacts blocked.

Recommended next safe step:

- Implement `m4_compact_translation_shell`.

---

After M4 real overlay scope recovery:

1. Treat `docs/m4-real-overlay-scope.md`,
   `tests/fixtures/m4_real_overlay_scope.synthetic.json`, and
   `scripts/check_m4_real_overlay_scope.py` as the M4 scope boundary.
2. Reuse the existing overlay view-model fixtures, validators, action previews, state-source
   fixtures, review renderer, accessibility checks, and refresh-readiness helper.
3. Keep original M4 criteria incomplete until separately implemented: compact translation, Genius
   card, and hotkeys.
4. Keep the next step contract-only and limited to the overlay shell boundary.

Recommended next safe step:

- Define `m4_overlay_shell_contract`.

---

After M3 closeout:

1. Treat `docs/m3-closeout.md`, `tests/fixtures/m3_closeout.synthetic.json`, and
   `scripts/check_m3_closeout.py` as the M3 completion guardrail.
2. M3 is closed: current-line event, line-ID matching, and debug console are implemented under the
   redacted/local boundaries documented in the closeout.
3. Start original `M4 - Real overlay` with scope recovery before implementation, because earlier
   overlay/prototype work exists and must be mapped before building new behavior.
4. Keep raw game text, extracted DBs, private indexes, logs, screenshots, provider payloads,
   private paths, `bin`, and `obj` out of git.

Recommended next safe step:

- Implement `m4_real_overlay_scope_recovery`.

---

After M3 debug console:

1. Treat `packages/bepinex-plugin/src/DebugCommandHandler.cs`,
   `tests/fixtures/m3_debug_console.synthetic.json`, and `scripts/check_m3_debug_console.py` as
   the guardrail for the third original M3 criterion.
2. Allowed commands are only `bridge_status`, `synthetic_send`, `current_line_event_status`, and
   `matcher_status`; all outputs remain redacted.
3. Keep raw text dumps, payload dumps, ID dumps, provider calls, companion HTTP contract changes,
   game-file reads, BepInEx log reads, UI text reading, Unity scanning, hooks/Harmony, OCR,
   committed generated outputs, screenshots, private paths, `bin`, and `obj` blocked.
4. Add one M3 closeout review gate next, closing M3 only if all three original criteria remain
   implemented and guarded.

Recommended next safe step:

- Implement `m3_closeout`.

---

After M3 line-ID matching:

1. Treat `scripts/run_m3_line_id_match.py`,
   `tests/fixtures/m3_line_id_matching.synthetic.json`, and `tests/test_m3_line_id_match.py` as the
   guardrail for the second original M3 criterion.
2. Matching is exact ID membership only: one redacted current-line event JSON under
   `workspace/local-private/bepinex/current-line/` against one ignored private M2 line-index
   artifact under `workspace/local-private/extraction-indexing/import/line-index/`.
3. Keep fuzzy matching, raw text emission, ID emission, provider calls, companion HTTP contract
   changes, game-file reads, BepInEx log reads, UI text reading, Unity scanning, hooks/Harmony,
   OCR, debug console work, committed generated outputs, screenshots, private paths, `bin`, and
   `obj` blocked.
4. Implement only the minimal debug console next.

Recommended next safe step:

- Implement `m3_debug_console`.

---

After M3 current-line event implementation:

1. Treat `packages/bepinex-plugin/src/CurrentLineEventFactory.cs`,
   `tests/fixtures/m3_current_line_event_implementation.synthetic.json`, and
   `scripts/check_m3_current_line_event_implementation.py` as the guardrail for the first original
   M3 criterion.
2. The current-line event path remains disabled by default and emits only redacted bridge-owned
   metadata. It does not send providers, change companion HTTP contracts, capture raw text, read UI
   text, scan Unity objects, read game files, or read BepInEx logs.
3. Implement only line-ID matching next, using the M2 private line-index boundary already developed.
4. Keep debug console work separate.

Recommended next safe step:

- Implement `m3_line_id_matching`.

---

After M3 current-line event contract:

1. Treat `docs/m3-current-line-event-contract.md`,
   `tests/fixtures/m3_current_line_event_contract.synthetic.json`, and
   `scripts/check_m3_current_line_event_contract.py` as the static guardrail for the first original
   M3 criterion.
2. Implement only the minimal disabled-by-default, local-only current-line event path next.
3. Keep raw text capture, UI text reading, broad Unity scanning, hooks/Harmony, OCR, provider
   execution, companion HTTP contract changes, line-ID matching, private line-index reads, debug
   console work, game-file reads, BepInEx log reads, committed logs, screenshots, private paths,
   `bin`, and `obj` blocked.
4. Keep the next step limited to the current-line event implementation criterion.

Recommended next safe step:

- Implement `m3_current_line_event_implementation`.

---

After M3 BepInEx bridge scope recovery:

1. Treat `docs/m3-bepinex-bridge-scope.md`,
   `tests/fixtures/m3_bepinex_bridge_scope.synthetic.json`, and
   `scripts/check_m3_bepinex_bridge_scope.py` as the M3 baseline guardrail.
2. Reuse the existing BepInEx bridge skeleton, optional build helper, runtime smoke workflow,
   metadata probe workflow, bridge-to-overlay synthetic smoke, and local bridge workflow wrapper.
3. Keep original M3 criteria incomplete until separately implemented: emit current line event,
   match line IDs, and debug console.
4. Keep the next step contract-only and limited to the current-line event criterion.

Recommended next safe step:

- Define `m3_current_line_event_contract`.

---

After the original M2 closeout review gate:

1. Treat `scripts/review_m2_closeout.py`,
   `docs/m2-closeout-review-gate.md`, and
   `tests/fixtures/m2_closeout_review_decision.synthetic.json` as the redacted closeout boundary
   for original M2.
2. The reviewer reads only ignored redacted review JSON from the local-import, line-index, and
   context-graph review roots. It never reopens the selected export, private DB, private
   line-index, or private context-graph artifact.
3. A passing closeout marks original M2 complete at the private implementation-path level without
   committing private artifacts.

Recommended next safe step:

- Implement `m3_bepinex_bridge_scope_recovery`.

---

After the original M2 context-graph implementation:

1. Treat `scripts/run_m2_context_graph.py` as the third original M2 implementation slice: one
   explicit private DB artifact plus one explicit private line-index artifact plus one redacted
   line-index review to one ignored private context-graph artifact under
   `workspace/local-private/extraction-indexing/import/context-graph/`.
2. Keep generated graphs, line indexes, private DB artifacts, extracted text, private paths,
   payloads, reports, game scanning, runtime reads, companion changes, providers, and committed
   private artifacts blocked.
3. Add a redacted context-graph review gate before M2 closeout. The review must read only
   `m2-context-graph-summary.v1` JSON under
   `workspace/local-private/extraction-indexing/import/context-graph-summary/` and must never
   reopen the private graph, DB, line index, or selected export.

Recommended next safe step:

- Implement `m2_context_graph_review_gate`.

---

After the original M2 context-graph review gate:

1. Treat `scripts/review_m2_context_graph.py` and
   `tests/fixtures/m2_context_graph_review_decision.synthetic.json` as the redacted review
   boundary for the third original M2 implementation slice.
2. The reviewer reads only ignored redacted context-graph summary JSON under
   `workspace/local-private/extraction-indexing/import/context-graph-summary/` and never reopens
   the selected export, private DB, private line-index, or private context-graph artifact.
3. A passing review allows only `m2_closeout_review_gate`; generated private artifacts, game
   scanning, runtime reads, companion changes, providers, and committed private artifacts remain
   blocked.

Recommended next safe step:

- Implement `m2_closeout_review_gate`.

---

After the original M2 line-index review gate:

1. Treat `scripts/review_m2_line_index.py` and
   `tests/fixtures/m2_line_index_review_decision.synthetic.json` as the redacted review boundary
   for the second original M2 implementation slice.
2. The reviewer reads only ignored redacted line-index summary JSON under
   `workspace/local-private/extraction-indexing/import/line-index-summary/` and never reopens the
   private DB or private line-index artifact.
3. A passing review allows only the already-scoped `m2_context_graph_implementation`; generated
   graphs, game scanning, runtime reads, companion changes, providers, and committed private
   artifacts remain blocked.

Recommended next safe step:

- Implement `m2_context_graph_implementation`.

---

After the original M2 context-graph contract:

1. Treat `docs/m2-context-graph-contract.md`,
   `tests/fixtures/m2_context_graph_scope.synthetic.json`, and
   `scripts/check_m2_context_graph_contract.py` as the static approval boundary for the third
   original M2 criterion.
2. Require `m2_line_index_review_gate` evidence before `m2_context_graph_implementation`: one
   explicit private imported DB artifact plus one explicit private line-index artifact to one
   ignored private context-graph artifact under
   `workspace/local-private/extraction-indexing/import/context-graph/`.
3. Keep generated graphs, line indexes, private DB artifacts, extracted text, private paths,
   payloads, reports, game scanning, runtime reads, companion changes, providers, source-text
   duplication in graph output, arbitrary future-branch traversal, and committed private artifacts
   blocked.

Recommended next safe step:

- Implement `m2_line_index_review_gate`.

---

After the original M2 line-index implementation:

1. Treat `scripts/run_m2_line_index.py` as the second original M2 implementation slice: one
   explicit private imported DB artifact plus one redacted local-import review to one ignored
   private line-index artifact under
   `workspace/local-private/extraction-indexing/import/line-index/`.
2. Keep generated line indexes, private DB artifacts, extracted text, private paths, payloads,
   reports, and graphs out of tracked files, chat, review Markdown, and commits.
3. Keep context-graph construction, retrieval-bucket mapping, game scanning, runtime reads,
   companion changes, providers, and committed private artifacts blocked.

Recommended next safe step:

- Define `m2_context_graph_contract`.

---

After the original M2 local import review gate:

1. Treat `scripts/review_m2_local_import.py` and
   `tests/fixtures/m2_local_import_review_decision.synthetic.json` as the redacted review boundary
   for the first original M2 implementation slice.
2. The reviewer reads only ignored redacted local-import summary JSON under
   `workspace/local-private/extraction-indexing/import/db-summary/` and never reopens the selected
   export or private DB artifact.
3. A passing review allows only the already-scoped `m2_line_index_implementation`; context-graph
   construction, retrieval-bucket mapping, game scanning, runtime reads, companion changes,
   providers, and committed private artifacts remain blocked.

Recommended next safe step:

- Implement `m2_line_index_implementation`.

---

After the original M2 line-index contract:

1. Treat `docs/m2-line-index-contract.md`,
   `tests/fixtures/m2_line_index_scope.synthetic.json`, and
   `scripts/check_m2_line_index_contract.py` as the static approval boundary for the second
   original M2 criterion.
2. Require `m2_local_import_review_gate` evidence before `m2_line_index_implementation`: one
   explicit private imported DB artifact under `workspace/local-private/extraction-indexing/import/db/`
   to one ignored private line-index artifact under
   `workspace/local-private/extraction-indexing/import/line-index/`.
3. Keep context-graph construction, retrieval-bucket mapping, game scanning, runtime reads,
   companion changes, providers, and committed private artifacts blocked.

Recommended next safe step:

- Implement `m2_local_import_review_gate`.

---

After the original M2 local import implementation:

1. Treat `scripts/run_m2_local_import.py` as the first original M2 implementation slice: one
   explicit workspace-private `m2-local-private-export.v1` JSON export to one ignored private DB
   artifact under `workspace/local-private/extraction-indexing/import/db/`.
2. Keep generated private DB artifacts, extracted text, private paths, payloads, reports, and
   indexes out of tracked files, chat, review Markdown, and commits.
3. Keep context-graph construction, retrieval-bucket mapping, game scanning, runtime reads,
   companion changes, providers, and committed private artifacts blocked.

Recommended next safe step:

- Implement `m2_local_import_review_gate`.

---

After the original M2 local import final approval contract:

1. Treat `docs/m2-local-import-final-approval-contract.md`,
   `tests/fixtures/m2_local_import_final_approval_scope.synthetic.json`, and
   `scripts/check_m2_local_import_final_approval_contract.py` as the final static approval boundary
   for the first original M2 criterion.
2. Implement only `m2_local_import_implementation` next: one explicit workspace-private
   `m2-local-private-export.v1` JSON export to one ignored private DB artifact under
   `workspace/local-private/extraction-indexing/import/db/`.
3. Keep line-index construction, context-graph construction, retrieval-bucket mapping, game
   scanning, runtime reads, companion changes, providers, and committed private artifacts blocked.

Recommended next safe step:

- Implement `m2_local_import_implementation`.

---

After the original M2 explicit local-import context-edge integrity dry-run review gate:

1. Treat `scripts/review_m2_explicit_local_import_context_edge_integrity_dry_run.py` and
   `tests/fixtures/m2_explicit_local_import_context_edge_integrity_dry_run_review_decision.synthetic.json`
   as the redacted context-edge integrity evidence boundary.
2. Keep export reopening during review, id emission, relation emission, duplicate tuple emission,
   retrieval-bucket mapping, real DB import, index construction, graph construction, and every
   original M2 completion flag blocked.
3. Define only the final local-import approval contract next.

Recommended next safe step:

- Define `m2_local_import_final_approval_contract`.

---

After the original M2 explicit local-import context-edge integrity dry-run:

1. Treat `scripts/run_m2_explicit_local_import_context_edge_integrity_dry_run.py` as the
   aggregate-only self-edge and duplicate-edge dry-run over one explicit workspace-private export.
2. Keep ids, relation values, duplicate tuples, source text, paths, filenames, hashes, logs,
   payloads, and runtime evidence out of stdout, output JSON, tracked files, reports, and commits.
3. Keep retrieval-bucket mapping, real DB import, line-index construction, context-graph
   construction, and every original M2 completion flag blocked.
4. Add only a redacted review gate for the integrity summary next.

Recommended next safe step:

- Implement `m2_explicit_local_import_context_edge_integrity_dry_run_review_gate`.

---

After the original M2 explicit local-import context-edge integrity contract:

1. Treat `docs/m2-explicit-local-import-context-edge-integrity-contract.md`,
   `tests/fixtures/m2_explicit_local_import_context_edge_integrity_scope.synthetic.json`, and
   `scripts/check_m2_explicit_local_import_context_edge_integrity_contract.py` as the static
   context-edge integrity guardrail.
2. Keep id emission, id normalization, id hashing, relation emission, retrieval-bucket mapping,
   graph construction, real DB import, index construction, and every original M2 completion flag
   blocked.
3. Implement only the bounded context-edge integrity dry-run next.

Recommended next safe step:

- Implement `m2_explicit_local_import_context_edge_integrity_dry_run`.

---

After the original M2 explicit local-import context-edge reference dry-run review gate:

1. Treat `scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py` and
   `tests/fixtures/m2_explicit_local_import_context_edge_reference_dry_run_review_decision.synthetic.json`
   as the redacted context-edge reference evidence boundary.
2. Keep export reopening during review, id emission, id normalization, id hashing, self-edge
   checks, duplicate-edge checks, retrieval-bucket mapping, real DB import, index construction,
   graph construction, and every original M2 completion flag blocked.
3. Define only the static context-edge integrity contract next.

Recommended next safe step:

- Define `m2_explicit_local_import_context_edge_integrity_contract`.

---

After the original M2 explicit local-import context-edge reference dry-run:

1. Treat `scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py` as the one-file,
   membership-only reference helper.
2. Keep id emission, id normalization, id hashing, self-edge checks, duplicate-edge checks,
   retrieval-bucket mapping, graph construction, real DB import, index construction, and every
   original M2 completion flag blocked.
3. Add only a redacted review gate for the context-edge reference summary next.

Recommended next safe step:

- Implement `m2_explicit_local_import_context_edge_reference_dry_run_review_gate`.

---

After the original M2 explicit local-import context-edge reference contract:

1. Treat `docs/m2-explicit-local-import-context-edge-reference-contract.md`,
   `tests/fixtures/m2_explicit_local_import_context_edge_reference_scope.synthetic.json`, and
   `scripts/check_m2_explicit_local_import_context_edge_reference_contract.py` as the static
   context-edge reference guardrail.
2. Keep edge id emission, record id emission, self-edge checks, duplicate-edge checks, graph
   construction, real DB import, index construction, and every original M2 completion flag blocked.
3. Implement only the bounded context-edge reference dry-run next.

Recommended next safe step:

- Implement `m2_explicit_local_import_context_edge_reference_dry_run`.

---

After the original M2 explicit local-import context-edge shape dry-run review gate:

1. Treat `scripts/review_m2_explicit_local_import_context_edge_shape_dry_run.py` and
   `tests/fixtures/m2_explicit_local_import_context_edge_shape_dry_run_review_decision.synthetic.json`
   as the redacted context-edge shape evidence boundary.
2. Keep export reopening during review, edge id emission, edge reference validation, self-edge
   checks, duplicate-edge checks, record traversal, real DB import, index construction, graph
   construction, and every original M2 completion flag blocked.
3. Define only the static context-edge reference contract next.

Recommended next safe step:

- Define `m2_explicit_local_import_context_edge_reference_contract`.

---

After the original M2 explicit local-import context-edge shape dry-run:

1. Treat `scripts/run_m2_explicit_local_import_context_edge_shape_dry_run.py` as the one-file,
   all-context-edge top-level shape helper.
2. Keep edge id emission, edge reference validation, self-edge checks, duplicate-edge checks,
   record traversal, real DB import, index construction, graph construction, and every original M2
   completion flag blocked.
3. Add only a redacted review gate for the context-edge shape summary next.

Recommended next safe step:

- Implement `m2_explicit_local_import_context_edge_shape_dry_run_review_gate`.

---

After the original M2 explicit local-import context-edge shape contract:

1. Treat `docs/m2-explicit-local-import-context-edge-shape-contract.md`,
   `tests/fixtures/m2_explicit_local_import_context_edge_shape_scope.synthetic.json`, and
   `scripts/check_m2_explicit_local_import_context_edge_shape_contract.py` as the context-edge
   shape guardrail.
2. Keep edge-value emission, edge-reference validation, self-edge checks, duplicate-edge checks,
   record traversal, real DB import, index construction, graph construction, and every original M2
   completion flag blocked.
3. Implement only the bounded context-edge shape dry-run next.

Recommended next safe step:

- Implement `m2_explicit_local_import_context_edge_shape_dry_run`.

---

After the original M2 explicit local-import record-shape dry-run review gate:

1. Treat `scripts/review_m2_explicit_local_import_record_shape_dry_run.py` and
   `tests/fixtures/m2_explicit_local_import_record_shape_dry_run_review_decision.synthetic.json`
   as the redacted record-shape evidence boundary.
2. Keep export reopening during review, record-value traversal, tag traversal, metadata traversal,
   context-edge inspection, real DB import, index construction, graph construction, and every
   original M2 completion flag blocked.
3. Define only the static context-edge shape contract next.

Recommended next safe step:

- Define `m2_explicit_local_import_context_edge_shape_contract`.

---

After the original M2 explicit local-import record-shape dry-run:

1. Treat `scripts/run_m2_explicit_local_import_record_shape_dry_run.py` as the one-file,
   all-record top-level shape helper.
2. Keep record-value emission, tag traversal, metadata traversal, context-edge traversal, real DB
   import, index construction, graph construction, and every original M2 completion flag blocked.
3. Add only a redacted review gate for the record-shape summary next.

Recommended next safe step:

- Implement `m2_explicit_local_import_record_shape_dry_run_review_gate`.

---

After the original M2 explicit local-import record-shape contract:

1. Treat `docs/m2-explicit-local-import-record-shape-contract.md`,
   `tests/fixtures/m2_explicit_local_import_record_shape_scope.synthetic.json`, and
   `scripts/check_m2_explicit_local_import_record_shape_contract.py` as the record-only guardrail.
2. Keep record-value inspection, source-text emission, tag traversal, metadata traversal,
   context-edge traversal, real DB import, indexing, graph construction, and every original M2
   completion flag blocked.
3. Implement only the bounded record-shape dry-run next.

Recommended next safe step:

- Implement `m2_explicit_local_import_record_shape_dry_run`.

---

After the original M2 explicit local-import schema-compatibility dry-run review gate:

1. Treat `scripts/review_m2_explicit_local_import_schema_compatibility_dry_run.py` and
   `tests/fixtures/m2_explicit_local_import_schema_compatibility_dry_run_review_decision.synthetic.json`
   as the redacted compatibility-evidence boundary.
2. Keep export reopening during review, nested traversal, record-shape inspection, real DB import,
   index construction, graph construction, and every original M2 completion flag blocked.
3. Define only the static record-shape contract next.

Recommended next safe step:

- Define `m2_explicit_local_import_record_shape_contract`.

---

After the original M2 explicit local-import schema-compatibility dry-run:

1. Treat `scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py` as the one-file,
   envelope-only private compatibility helper.
2. Keep nested traversal, nested-value emission, real DB import, index construction, graph
   construction, and every original M2 completion flag blocked.
3. Add only a redacted review gate for the compatibility summary next.

Recommended next safe step:

- Implement `m2_explicit_local_import_schema_compatibility_dry_run_review_gate`.

---

After the original M2 explicit local-import schema-compatibility contract:

1. Treat `docs/m2-explicit-local-import-schema-compatibility-contract.md`,
   `tests/fixtures/m2_explicit_local_import_schema_compatibility_scope.synthetic.json`, and
   `scripts/check_m2_explicit_local_import_schema_compatibility_contract.py` as the envelope-only
   compatibility guardrail.
2. Keep nested traversal, nested-value emission, parsing beyond the envelope, real DB import,
   indexing, graph construction, and every original M2 completion flag blocked.
3. Implement only the bounded compatibility dry-run next.

Recommended next safe step:

- Implement `m2_explicit_local_import_schema_compatibility_dry_run`.

---

After the original M2 explicit local-import adapter dry-run review gate:

1. Treat `scripts/review_m2_explicit_local_import_adapter_dry_run.py` and
   `tests/fixtures/m2_explicit_local_import_adapter_dry_run_review_decision.synthetic.json` as the
   redacted one-file metadata review boundary.
2. Keep selected-export reopening, schema inspection, parsing, real DB import, index construction,
   graph construction, and every original M2 completion flag blocked.
3. Define only the static schema-compatibility contract next.

Recommended next safe step:

- Define `m2_explicit_local_import_schema_compatibility_contract`.

---

After the original M2 explicit local-import adapter dry-run:

1. Treat `scripts/run_m2_explicit_local_import_adapter_dry_run.py` as a one-file,
   metadata-summary-only helper.
2. Keep parsing, schema compatibility inspection, real DB import, line-index construction,
   context-graph construction, discovery, and every original M2 completion flag blocked.
3. Add only a redacted review gate for the dry-run summary next.

Recommended next safe step:

- Implement `m2_explicit_local_import_adapter_dry_run_review_gate`.

---

After the original M2 explicit local-import adapter contract:

1. Treat `docs/m2-explicit-local-import-adapter-contract.md`,
   `tests/fixtures/m2_explicit_local_import_adapter_scope.synthetic.json`, and
   `scripts/check_m2_explicit_local_import_adapter_contract.py` as the one-file private-input
   guardrail.
2. Keep local-export reads, parsing, real DB import, indexing, graph construction, automatic
   discovery, and every original M2 completion flag blocked.
3. Implement only a metadata-summary dry-run for one explicit workspace-private file next.

Recommended next safe step:

- Implement `m2_explicit_local_import_adapter_dry_run`.

---

After the original M2 synthetic context-graph builder review gate:

1. Treat `scripts/review_m2_synthetic_context_graph_builder_dry_run.py` and
   `tests/fixtures/m2_synthetic_context_graph_builder_review_decision.synthetic.json` as the
   redacted synthetic graph review boundary.
2. Keep real DB import, local-export reads, private-input reads, adapter implementation, arbitrary
   future branches, and every original M2 completion flag blocked.
3. Define only the explicit local-import adapter contract next.

Recommended next safe step:

- Define `m2_explicit_local_import_adapter_contract`.

---

After the original M2 synthetic context-graph builder dry-run:

1. Treat `scripts/run_m2_synthetic_context_graph_builder_dry_run.py` as an invented-fixture-only
   metadata projection helper.
2. Keep real DB import, private-input reads, original M2 context-graph completion, arbitrary future
   branches, and runtime behavior blocked.
3. Keep generated dry-run output private under
   `workspace/local-private/extraction-indexing/import/context-graph/`.

Recommended next safe step:

- Define `m2_synthetic_context_graph_builder_review_gate`.

---

After the original M2 synthetic context-graph contract:

1. Treat `docs/m2-synthetic-context-graph-contract.md`,
   `specs/m2-synthetic-context-graph.schema.json`,
   `tests/fixtures/m2_synthetic_context_graph.synthetic.json`, and
   `scripts/check_m2_synthetic_context_graph_contract.py` as the metadata-only graph guardrail.
2. Keep graph construction, real DB import, private-input reads, arbitrary future branches, and
   every original M2 completion flag blocked.
3. Implement only a synthetic context-graph builder dry-run next.

Recommended next safe step:

- Implement `m2_synthetic_context_graph_builder_dry_run`.

---

After the original M2 synthetic line-index builder review gate:

1. Treat `scripts/review_m2_synthetic_line_index_builder_dry_run.py` and
   `tests/fixtures/m2_synthetic_line_index_builder_review_decision.synthetic.json` as the redacted
   synthetic review boundary.
2. Keep real DB import, private-input reads, original M2 line-index completion, and context-graph
   construction blocked.
3. Define only the synthetic context-graph contract next.

Recommended next safe step:

- Define `m2_synthetic_context_graph_contract`.

---

After the original M2 synthetic line-index builder dry-run:

1. Treat `scripts/run_m2_synthetic_line_index_builder_dry_run.py` as a fixture-only metadata
   projection helper.
2. Keep real DB import, private-input reads, source text, graph edges, line-index completion, and
   context-graph construction blocked.
3. Keep generated dry-run output private under
   `workspace/local-private/extraction-indexing/import/line-index/`.

Recommended next safe step:

- Define `m2_synthetic_line_index_builder_review_gate`.

---

After the original M2 synthetic line-index contract:

1. Treat `docs/m2-synthetic-line-index-contract.md`,
   `specs/m2-synthetic-line-index.schema.json`,
   `tests/fixtures/m2_synthetic_line_index.synthetic.json`, and
   `scripts/check_m2_synthetic_line_index_contract.py` as the metadata-only line-index guardrail.
2. Keep real DB import, private-input reads, line-index building, and context-graph construction
   blocked.
3. Keep source text, graph edges, filenames, paths, hashes, payloads, logs, and runtime evidence
   out of committed line-index fixtures.

Recommended next safe step:

- Implement `m2_synthetic_line_index_builder_dry_run`.

---

After the reusable M2 synthetic import validator:

1. Treat `specs/m2-synthetic-import-db.schema.json`,
   `scripts/m2_synthetic_import_validator.py`, and
   `scripts/check_m2_synthetic_import_format.py` as the synthetic-only input boundary.
2. Keep private-input reads, directory discovery, real DB import, line-index construction, and
   context-graph construction blocked.
3. Define the synthetic line-index output contract next.

---

After the original M2 synthetic import format contract:

1. Treat `docs/m2-synthetic-import-format-contract.md`,
   `tests/fixtures/m2_synthetic_import_db.synthetic.json`, and
   `scripts/check_m2_synthetic_import_format.py` as the invented-fixture-only M2 format guardrail.
2. Keep original M2 incomplete: no real DB importer, line index, or context graph exists yet.
3. Keep local-input reads, game scans, log reads, capture behavior, provider execution, companion
   contract changes, generated real indexes, and committed extracted text blocked.

Recommended next safe step:

- Define `m2_synthetic_import_validator_or_line_index_contract`.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the M2 synthetic import format contract. First inspect git status and read AGENTS.md, tasks/milestones.md, docs/devlog/*.md, docs/adr/0012-m2-local-extraction-import-scope.md, docs/m2-synthetic-import-format-contract.md, tests/fixtures/m2_synthetic_import_db.synthetic.json, and scripts/check_m2_synthetic_import_format.py. Define the next M2 synthetic import validator or line-index contract only. Keep original M2 incomplete. Do not read real local inputs, import a real DB, read game files, scan Steam/game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, generated real indexes, committed extracted text, downloads, or new dependencies.`

---

After the original M2 local extraction import scope contract:

1. Treat `docs/adr/0012-m2-local-extraction-import-scope.md`,
   `tests/fixtures/m2_local_extraction_import_scope.synthetic.json`, and
   `scripts/check_m2_local_extraction_import_scope.py` as the active original-M2 guardrail.
2. Keep original M2 incomplete: no locally extracted DB import, line index, or context graph exists
   yet.
3. Keep real local-input reads, game-file reads, automatic scanning, capture paths, OCR, hooks,
   providers, companion contract changes, generated real indexes, and committed extracted text
   blocked.

Recommended next safe step:

- Define `m2_synthetic_import_format_contract` using invented synthetic records only.

Exact resume prompt:

`Continue in revachol-ukro-elisium after ADR 0012 defined the original M2 local extraction import scope. First inspect git status and read AGENTS.md, tasks/milestones.md, docs/devlog/*.md, docs/adr/0012-m2-local-extraction-import-scope.md, tests/fixtures/m2_local_extraction_import_scope.synthetic.json, and scripts/check_m2_local_extraction_import_scope.py. Define the M2 synthetic import format contract only. Use invented synthetic fixtures and keep implementation blocked. Do not read real local inputs, read game files, scan Steam/game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, generated real indexes, committed extracted text, downloads, or new dependencies.`

---

Canonical roadmap recovery:

1. Treat `tasks/milestones.md` as the unchanged original roadmap.
2. Treat original `M0 - Repo and contracts` and `M1 - Synthetic vertical slice` as complete.
3. Treat original `M2 - Local extraction import` as active.
4. Treat the completed 5A-labelled series as an internal M2 safety-preparation workstream.
5. Do not use the retired `milestone_5b_planning` placeholder. Original
   `M5 - Maximum quality pipeline` has not started.

After Milestone 5A.11 closeout:

1. Treat `docs/extraction-indexing-milestone-5a-closeout.md`,
   `tests/fixtures/extraction_indexing_5a_closeout.synthetic.json`, and
   `scripts/check_extraction_indexing_5a_closeout.py` as the Milestone 5A closeout record.
2. Treat the internal 5A safety-preparation workstream as closed at the local-only, redacted dry-run
   evidence level. Original `M2 - Local extraction import` remains active. The 5A closeout does not
   claim real extraction or approve reading game files or private file contents.
3. Keep real extraction, automatic game-install scanning, BepInEx log reads, current-line capture,
   UI text reading, Unity scanning, hooks/Harmony, OCR, save parsing, decompiled-code work, companion
   HTTP contract changes, provider execution, generated real indexes, and committed real extracted
   text blocked.

Recommended next safe step:

- Define the original M2 local extraction import scope contract. Do not start real extraction
  implicitly.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the internal 5A safety-preparation workstream closed at the local-only, redacted dry-run evidence level. The unchanged original roadmap in tasks/milestones.md controls: M0 and M1 are complete, and M2 - Local extraction import is active. First inspect git status and read AGENTS.md, tasks/milestones.md, docs/devlog/*.md, docs/extraction-indexing-milestone-5a-closeout.md, tests/fixtures/extraction_indexing_5a_closeout.synthetic.json, and scripts/check_extraction_indexing_5a_closeout.py. Define the M2 local extraction import scope contract before implementing it. Do not implement real extraction, read private file contents, read game files, scan Steam/game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, generated real indexes, committed real extracted text, downloads, or new dependencies without a separate approved scope.`

---

After Milestone 5A.10 private index builder dry-run:

1. Use `scripts/run_private_index_builder_dry_run.py` only with a redacted dry-run summary under
   `workspace/local-private/extraction-indexing/` and a redacted hash output under
   `workspace/local-private/extraction-indexing/hash/`.
2. Keep optional dry-run index output under `workspace/local-private/extraction-indexing/index/` and
   out of git.
3. Treat `private-index-dry-run.v1` as a redacted preview only. It does not contain text records,
   paths, filenames, digest values, original summaries, canonical JSON, raw payloads, logs, or
   provider data.
4. Keep real extraction, private file content reads, generated real indexes, file content hashing,
   path string hashing, filename hashing, automatic game-install scanning, BepInEx log reads,
   screenshots, OCR, current-line capture, UI text reading, Unity scanning, hooks/Harmony,
   decompiled-code work, companion HTTP contract changes, provider execution, and committed real
   extracted text blocked.

Recommended next safe step:

- Add a redacted review gate for `private-index-dry-run.v1` output, or refine the private index
  dry-run schema, before any real private index construction from content is considered.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.10 private index builder dry-run. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/extraction-indexing-private-index-construction-contract.md, docs/extraction-indexing-private-index-contract.md, scripts/run_private_index_builder_dry_run.py, scripts/review_private_input_adapter_dry_run.py, scripts/review_dry_run_summary_hash.py, and tests/fixtures/private_index_dry_run.synthetic.json. Implement the next 5A step only as a redacted private index dry-run review gate or schema refinement unless explicitly approved otherwise. Do not read original private inputs, read file contents, build indexes from real text, include paths or filenames, include digest values from private runs, hash file contents, hash paths, hash filenames, scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.9 private index construction contract:

1. Treat `docs/extraction-indexing-private-index-construction-contract.md`,
   `tests/fixtures/private_index_construction_contract.synthetic.json`, and
   `scripts/check_private_index_construction_contract.py` as the current guardrail.
2. Keep future private index output under `workspace/local-private/extraction-indexing/index/` and
   out of git.
3. Treat `private_index_construction_allowed_next="contract_defined_only"` as contract scope only.
   It does not approve a builder implementation.
4. Keep real extraction, file content reads, file content hashing, path string hashing, filename
   hashing, automatic game-install scanning, BepInEx log reads, screenshots, OCR, current-line
   capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP
   contract changes, provider execution, generated real indexes, and committed real extracted text
   blocked.

Recommended next safe step:

- Plan a private index builder dry-run that consumes only synthetic/redacted fixtures and still does
  not read private file contents.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.9 private index construction contract. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/extraction-indexing-private-index-construction-contract.md, docs/extraction-indexing-private-index-contract.md, scripts/check_private_index_construction_contract.py, scripts/run_synthetic_extraction_indexer.py, and tests/fixtures/private_index_construction_contract.synthetic.json. Implement the next 5A step only as a private index builder dry-run if explicitly approved: it may consume synthetic/redacted fixture evidence and write only under workspace/local-private/extraction-indexing/index/. Do not read private file contents, build indexes from real text, hash file contents, hash paths, hash filenames, scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.8 dry-run summary hash evidence gate:

1. Use `scripts/review_dry_run_summary_hash.py` only on hash output JSON under
   `workspace/local-private/extraction-indexing/hash/`.
2. Keep optional review JSON/Markdown under
   `workspace/local-private/extraction-indexing/hash-review/` and out of git.
3. Treat `ready_for_private_index_decision=true` as permission to discuss a later private index
   construction contract only. It does not approve private index implementation.
4. Keep private index construction, real extraction, file content hashing, path string hashing,
   filename hashing, automatic game-install scanning, BepInEx log reads, screenshots, OCR,
   current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work,
   companion HTTP contract changes, provider execution, generated real indexes, and committed real
   extracted text blocked.

Recommended next safe step:

- Define a private index construction contract before any helper reads private file contents or
  builds an index from private input.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.8 dry-run summary hash evidence gate. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/extraction-indexing-private-index-contract.md, docs/extraction-indexing-dry-run-summary-hash-contract.md, scripts/review_dry_run_summary_hash.py, scripts/run_dry_run_summary_hash.py, and tests/fixtures/dry_run_summary_hash_decision.synthetic.json. Implement the next 5A step only as a private index construction contract unless explicitly approved otherwise. Do not build private indexes, read original private input contents, hash file contents, hash paths, hash filenames, scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.7 dry-run summary hash dry-run:

1. Use `scripts/run_dry_run_summary_hash.py` only on reviewed dry-run summary JSON under
   `workspace/local-private/extraction-indexing/`.
2. Keep optional hash output under `workspace/local-private/extraction-indexing/hash/` and out of
   git.
3. Treat the hash digest as private metadata. It can still identify a distinctive local summary even
   though it does not include raw text, paths, filenames, or contents.
4. Keep file content hashing, path string hashing, filename hashing, raw payload/log hashing,
   private index construction, real extraction, automatic game-install scanning, BepInEx log reads,
   screenshots, OCR, current-line capture, UI text reading, Unity scanning, hooks/Harmony,
   decompiled-code work, companion HTTP contract changes, provider execution, generated real
   indexes, and committed real extracted text blocked.

Recommended next safe step:

- Add a redacted review gate for dry-run summary hash output before deciding whether any private
  index construction discussion can start.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.7 dry-run summary hash dry-run. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/extraction-indexing-dry-run-summary-hash-contract.md, scripts/run_dry_run_summary_hash.py, scripts/review_private_input_adapter_dry_run.py, and tests/fixtures/dry_run_summary_hash.synthetic.json. Implement the next 5A step only as a redacted dry-run summary hash review gate unless explicitly approved otherwise. Do not read original private inputs, read file contents, hash file contents, hash paths, hash filenames, build private indexes, scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.6 dry-run summary hash contract:

1. Treat `docs/extraction-indexing-dry-run-summary-hash-contract.md`,
   `tests/fixtures/dry_run_summary_hash_contract.synthetic.json`, and
   `scripts/check_dry_run_summary_hash_contract.py` as the current summary-hash guardrail.
2. Keep `hash_implementation_allowed_next=false`. The contract defines a future hash input shape
   only; it does not approve hash computation.
3. Future hash work may consider only canonical redacted dry-run summary metadata after the 5A.4
   review rules pass.
4. Keep file content hashing, path string hashing, filename hashing, raw payload/log hashing,
   private index construction, real extraction, automatic game-install scanning, BepInEx log reads,
   screenshots, OCR, current-line capture, UI text reading, Unity scanning, hooks/Harmony,
   decompiled-code work, companion HTTP contract changes, provider execution, generated real
   indexes, and committed real extracted text blocked.

Recommended next safe step:

- Implement a dry-run summary hash dry-run only if explicitly approved. It should hash only a
  canonical redacted summary object, write only under `workspace/local-private/extraction-indexing/`,
  and keep all file content/path/filename hashing blocked.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.6 dry-run summary hash contract. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/extraction-indexing-dry-run-summary-hash-contract.md, docs/extraction-indexing-private-input-hash-contract.md, scripts/check_dry_run_summary_hash_contract.py, scripts/run_private_input_adapter_dry_run.py, and scripts/review_private_input_adapter_dry_run.py. Implement the next 5A step only as a dry-run summary hash dry-run if explicitly approved: hash only canonical redacted dry-run summary metadata that passed review, write only under workspace/local-private/extraction-indexing/, and do not hash file contents, paths, filenames, raw payloads, logs, screenshots, OCR output, saves, decompiled output, provider payloads, generated indexes, or real game text. Do not build private indexes, scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.5 private input hash decision contract:

1. Treat `docs/extraction-indexing-private-input-hash-contract.md`,
   `tests/fixtures/private_input_hash_decision.synthetic.json`, and
   `scripts/check_private_input_hash_decision_contract.py` as the current hash guardrail.
2. Keep `hash_implementation_allowed_next=false`, `file_content_hashing_allowed=false`, and
   `path_string_hashing_allowed=false`.
3. Treat `dry_run_summary_hashing_allowed_next="decision_pending"` as permission to define a later
   dry-run summary hash contract only. It does not approve any hash computation.
4. Keep private index construction, real extraction, automatic game-install scanning, BepInEx log
   reads, save parsing, screenshots, OCR, current-line capture, UI text reading, Unity scanning,
   hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution,
   generated real indexes, and committed real extracted text blocked.

Recommended next safe step:

- Define a dry-run summary hash contract that specifies canonical redacted summary fields, excluded
  fields, local private output paths, and review rules before any hash is computed.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.5 private input hash decision contract. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/extraction-indexing-private-input-hash-contract.md, docs/extraction-indexing-private-input-adapter-contract.md, docs/extraction-indexing-private-index-contract.md, scripts/check_private_input_hash_decision_contract.py, scripts/run_private_input_adapter_dry_run.py, and scripts/review_private_input_adapter_dry_run.py. Implement the next 5A step only as a dry-run summary hash contract unless explicitly approved otherwise. Do not compute hashes, read file contents, build private indexes, scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.4 private input dry-run evidence review:

1. Use `scripts/review_private_input_adapter_dry_run.py` only on dry-run summary JSON under
   `workspace/local-private/extraction-indexing/`.
2. Keep optional review JSON/Markdown under `workspace/local-private/extraction-indexing/review/`
   and out of git.
3. Treat `ready_for_hash_decision=true` as permission to discuss a later hash decision contract
   only. It does not approve content hashing.
4. Keep `ready_for_private_index_decision=false`; private index construction from real input remains
   blocked.
5. Do not add automatic game-install scanning, arbitrary drive scans, BepInEx log reads, save
   parsing, screenshots, OCR, current-line capture, UI text reading, Unity scanning, hooks/Harmony,
   decompiled-code work, companion HTTP contract changes, provider execution, production overlay
   shell behavior, committed real extracted text, or private index construction.

Recommended next safe step:

- Define a private input hash decision contract. It should decide whether hashes are allowed, what
  kind of hashes are safe, and how to avoid identifying or exposing private files before any hash is
  computed.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.4 private input dry-run evidence review. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/extraction-indexing-private-input-adapter-contract.md, docs/extraction-indexing-private-index-contract.md, scripts/run_private_input_adapter_dry_run.py, scripts/review_private_input_adapter_dry_run.py, tests/fixtures/private_input_dry_run_decision.synthetic.json, and tests/test_private_input_adapter_dry_run_review.py. Implement the next 5A step only as a private input hash decision contract unless explicitly approved otherwise. Do not compute hashes, read file contents, build indexes from real input, scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.3 private input adapter dry-run:

1. Use `scripts/run_private_input_adapter_dry_run.py` only for one explicit file or directory under
   `workspace/local-private/extraction-indexing/input/`.
2. Treat the summary as private local metadata. It can reveal file existence, counts, and sizes even
   though it does not include contents or hashes.
3. Keep any `--output` summaries under `workspace/local-private/extraction-indexing/` and out of git.
4. Do not add automatic game-install scanning, arbitrary drive scans, BepInEx log reads, save
   parsing, screenshots, OCR, content hashing, private index construction from real input,
   current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work,
   companion HTTP contract changes, provider execution, production overlay shell behavior, or
   committed real extracted text.

Recommended next safe step:

- Decide whether dry-run metadata summaries are sufficient to approve a later private index
  construction contract. That next decision should still happen before any real input text is read or
  indexed.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.3 private input adapter dry-run. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/adr/0011-real-extraction-indexing-scope.md, docs/extraction-indexing-private-index-contract.md, docs/extraction-indexing-private-input-adapter-contract.md, scripts/run_private_input_adapter_dry_run.py, scripts/run_synthetic_extraction_indexer.py, and tests/test_private_input_adapter_dry_run.py. Decide the next 5A step only as a private index construction contract or another metadata-only review gate unless explicitly approved otherwise. Do not scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, content hashing, generated real indexes from private text, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.2 private input adapter contract:

1. Treat `docs/extraction-indexing-private-input-adapter-contract.md`,
   `tests/fixtures/extraction_private_input_adapter_scope.synthetic.json`, and
   `scripts/check_extraction_private_input_adapter_contract.py` as the current guardrail.
2. Keep future user-selected private inputs under
   `workspace/local-private/extraction-indexing/input/`; external absolute paths are deferred.
3. Keep future private summaries and indexes under `workspace/local-private/extraction-indexing/`
   and out of git.
4. Do not add automatic game-install scanning, arbitrary drive scans, BepInEx log reads, save
   parsing, screenshots, OCR, current-line capture, UI text reading, Unity scanning, hooks/Harmony,
   decompiled-code work, companion HTTP contract changes, provider execution, production overlay
   shell behavior, or committed real extracted text.

Recommended next safe step:

- Implement a dry-run private input adapter only if explicitly approved. It should read only one
  explicit workspace-private input and emit redacted metadata summaries by default, not real text or
  indexes from real content.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.2 private input adapter contract. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/adr/0011-real-extraction-indexing-scope.md, docs/extraction-indexing-private-index-contract.md, docs/extraction-indexing-private-input-adapter-contract.md, tests/fixtures/extraction_private_input_adapter_scope.synthetic.json, scripts/check_extraction_private_input_adapter_contract.py, and scripts/run_synthetic_extraction_indexer.py. Implement the next 5A step only as a private input adapter dry-run if explicitly approved: read one user-selected input under workspace/local-private/extraction-indexing/input/ and emit redacted metadata summaries under workspace/local-private/extraction-indexing/. Do not scan game installs or drives, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP contract changes, provider execution, production overlay shell work, generated real indexes, committed real extracted text, downloads, or new dependencies.`

---

After Milestone 5A.1 synthetic indexer and private index contract:

1. Treat `scripts/run_synthetic_extraction_indexer.py` as a synthetic-only helper. It is not a real
   extraction adapter and must not be pointed at game files.
2. Validate the contract with `python scripts/check_extraction_index_contract.py --quiet`.
3. Keep generated private index output under `workspace/local-private/extraction-indexing/` and out
   of git.
4. Do not add automatic game-install scanning, BepInEx log reads, screenshots, OCR, current-line
   capture, UI text reading, Unity scanning, hooks/Harmony, decompiled-code work, companion HTTP
   contract changes, provider execution, or production overlay shell behavior.

Recommended next safe step:

- Define a user-selected private input adapter contract. It should describe how a user will
  explicitly place or point to private local inputs under ignored workspace paths before any real
  adapter reads them.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 5A.1 synthetic indexer/private index contract. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/adr/0011-real-extraction-indexing-scope.md, docs/extraction-indexing-private-index-contract.md, scripts/run_synthetic_extraction_indexer.py, scripts/check_extraction_index_contract.py, and tests/fixtures/extraction_index.synthetic.json. Implement the next 5A step only as a user-selected private input adapter contract unless explicitly approved otherwise. Keep committed data synthetic/redacted; keep private outputs under workspace/local-private/extraction-indexing/. Do not read real game files, scan the game install automatically, commit game text or localization dumps, read BepInEx logs, read saves, read screenshots, run OCR, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, decompiled game-code work, companion HTTP contract changes, real provider execution, production overlay shell work, downloads, or new dependencies.`

---

After the Milestone 5A extraction/indexing scope contract:

1. Treat true Milestone 5A as started only at the docs/static-contract layer. Real
   extraction/indexing implementation remains blocked.
2. Use `docs/adr/0011-real-extraction-indexing-scope.md`,
   `tests/fixtures/extraction_indexing_scope.synthetic.json`, and
   `scripts/check_extraction_indexing_scope.py` as the current guardrail.
3. Keep future private indexes under `workspace/local-private/extraction-indexing/`; do not commit
   private indexes, raw extracted text, localization dumps, game logs, screenshots, save files,
   private paths, or generated real-input reports.
4. Do not add automatic game-install scanning, current-line capture, UI text reading, Unity
   scanning, hooks/Harmony, OCR, decompiled game-code work, companion HTTP contract changes, real
   provider execution, production overlay shell behavior, downloads, or new dependencies.

Recommended next safe step:

- Define the synthetic indexer and private index contract before any adapter touches user-selected
  private inputs.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the Milestone 5A extraction/indexing scope contract. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/adr/0011-real-extraction-indexing-scope.md, tests/fixtures/extraction_indexing_scope.synthetic.json, scripts/check_extraction_indexing_scope.py, docs/local-workflow.md, and docs/09-legal-and-data-safety.md. Implement the next 5A step only as a synthetic indexer and private index contract unless explicitly approved otherwise. Keep committed data synthetic/redacted; keep private outputs under workspace/local-private/extraction-indexing/. Do not read real game files, scan the game install automatically, commit game text or localization dumps, read BepInEx logs, read saves, add current-line capture, UI text reading, Unity scanning, hooks/Harmony, OCR, decompiled game-code work, companion HTTP contract changes, real provider execution, production overlay shell work, downloads, or new dependencies.`

---

After Milestone 4 closeout workflow smoke:

1. Treat expanded Milestone 4 bridge/workflow validation as closed. The BepInEx bridge skeleton has
   been over-validated through redacted runtime smoke, companion-connected synthetic smoke,
   bridge-to-overlay synthetic smoke, overlay refresh readiness, and the local workflow wrapper.
2. True Milestone 5A has not started yet. Milestone 5A remains: real extraction/indexing adapter,
   local-only.
3. Keep workspace reports, generated HTML, raw logs, screenshots, `bin/`, `obj/`, game files,
   provider payloads, and private paths out of git.
4. Do not infer current-line capture, real text capture, UI text reading, Unity scanning,
   hooks/Harmony, OCR, extraction, real provider execution, production overlay shell behavior, or
   companion HTTP contract changes from the Milestone 4 closeout smoke.

Recommended next safe step:

- Start true Milestone 5A only when explicitly requested: real extraction/indexing adapter,
  local-only, with a fresh plan that keeps committed data synthetic/redacted and private local
  extraction artifacts ignored.

Exact resume prompt:

`Continue in revachol-ukro-elisium after expanded Milestone 4 bridge/workflow validation was closed. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/local-workflow.md, docs/bepinex-bridge.md, and docs/09-legal-and-data-safety.md. True Milestone 5A has not started yet. Plan Milestone 5A: real extraction/indexing adapter, local-only. Keep committed data limited to schemas, tooling, docs, and synthetic fixtures; keep local extraction outputs ignored/private. Do not commit game dialogue, assets, audio, screenshots, extracted databases, private paths, raw logs, provider payloads, workspace artifacts, bin, or obj. Do not add current-line capture, UI text reading, Unity scanning, hooks/Harmony, OCR, companion HTTP contract changes, real provider execution, production overlay shell behavior, downloads, or new dependencies without an explicit safety plan.`

---

After local bridge workflow polish:

Milestone naming correction: local bridge workflow polish is Milestone 4 closeout, not top-level
Milestone 5A. The BepInEx bridge skeleton is completed and over-validated by redacted runtime smoke.
True Milestone 5A has not started yet; the next top-level milestone after bridge closeout remains
Milestone 5A: real extraction/indexing adapter, local-only.

1. Use `python scripts/run_local_bridge_workflow.py --phase doctor --auto-discover` before local
   smoke runs to catch missing setup and staged runtime artifacts without exposing private paths by
   default.
2. For the current synthetic path, use the wrapper sequence:
   `--phase prepare-bridge-to-overlay-smoke`, manual game launch/close,
   `--phase post-bridge-to-overlay-smoke --write-report`, then `--phase cleanup`.
3. Keep `scripts/run_overlay_refresh_readiness.py --quiet` as the final metadata-only readiness
   summary after a successful local smoke.
4. Do not commit `workspace/synthetic-slice/`, reports, generated HTML, logs, screenshots, `bin/`,
   `obj/`, game files, provider payloads, or private paths.
5. Keep current-line capture, real text capture, UI text reading, Unity scanning, hooks/Harmony,
   OCR, extraction, real provider execution, companion HTTP contract changes, polling loops, timers,
   background workers, and production overlay shell work closed.

Recommended next safe step:

- Finish any remaining bridge closeout cleanup with the polished wrapper, then start true Milestone
  5A only when explicitly requested: real extraction/indexing adapter, local-only.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4 closeout / local bridge workflow polish. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/local-workflow.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, scripts/run_local_bridge_workflow.py, scripts/run_bridge_to_overlay_synthetic_smoke.py, and scripts/run_overlay_refresh_readiness.py. Treat the BepInEx bridge skeleton as completed and over-validated by redacted runtime smoke. Do not call this top-level Milestone 5A. True Milestone 5A has not started yet and is real extraction/indexing adapter, local-only. Use the workflow wrapper only for redacted local synthetic smoke orchestration; do not launch the game automatically, print raw logs, dump provider payloads, commit workspace artifacts, add C# behavior, add companion HTTP endpoints, call real providers, implement polling/timers/background workers, implement production overlay shell behavior, or add current-line capture, real text capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, downloads, or new dependencies.`

---

After the metadata-only overlay refresh readiness helper:

1. Treat `scripts/run_overlay_refresh_readiness.py` as a redacted readiness summarizer only. It is
   not a polling loop, timer, background worker, production overlay shell, provider runner, or
   capture path.
2. Use `python scripts/run_overlay_refresh_readiness.py --quiet` only when a local companion server
   is intentionally running, and use `--self-test --quiet` for fixture-only validation.
3. Keep any written summaries under `workspace/synthetic-slice/overlay-refresh-readiness/`; do not
   commit workspace summaries, provider payloads, generated HTML, logs, screenshots, or private
   paths.
4. Keep current-line capture, real text capture, UI text reading, Unity scanning, hooks/Harmony,
   OCR, extraction, real provider execution, companion HTTP contract changes, polling loops, timers,
   background workers, and production overlay shell work closed.

Recommended next safe step:

- Decide whether the redacted helper summary is enough to scope a future production-overlay shell
  contract, still as docs/static-contract work first and still without capture, polling, provider
  execution, or companion contract changes.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the metadata-only overlay refresh readiness helper. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/overlay-refresh-readiness-contract.md, docs/overlay-prototype.md, docs/bepinex-bridge.md, scripts/run_overlay_refresh_readiness.py, scripts/overlay_state_source.py, scripts/local_overlay_prototype.py, scripts/check_overlay_review_accessibility.py, and tests/test_overlay_refresh_readiness_helper.py. Use only redacted helper summaries, not raw provider payloads, generated HTML, logs, screenshots, private paths, game files, or workspace artifacts. Decide the next safe step for production-overlay shell contract planning, still without current-line capture, real text capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider execution, companion HTTP contract changes, polling loops, timers, background workers, downloads, or new dependencies.`

---

After the metadata-only overlay refresh/readiness contract:

1. Treat the contract as a static handoff only. It defines readiness labels and safe metadata inputs;
   it does not implement polling, timers, retries, background workers, production shell behavior, or
   companion HTTP changes.
2. Use `docs/overlay-refresh-readiness-contract.md`,
   `tests/fixtures/overlay_refresh_readiness_contract.synthetic.json`, and
   `scripts/check_overlay_refresh_readiness_contract.py` as the current guardrail.
3. Keep current-line capture, real text capture, UI text reading, Unity scanning, hooks/Harmony,
   OCR, extraction, real provider execution, and production overlay shell work closed.

Recommended next safe step:

- Scope a small metadata-only overlay refresh helper that summarizes the contract states from
  existing companion/state-source/view-model/review checks, still without runtime capture,
  companion contract changes, polling loops, timers, or production shell behavior.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the metadata-only overlay refresh/readiness contract. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/overlay-refresh-readiness-contract.md, docs/overlay-prototype.md, docs/bepinex-bridge.md, scripts/check_overlay_refresh_readiness_contract.py, scripts/overlay_state_source.py, scripts/local_overlay_prototype.py, scripts/run_bridge_to_overlay_synthetic_smoke.py, and tests/fixtures/overlay_refresh_readiness_contract.synthetic.json. Plan or implement a metadata-only overlay refresh helper only if approved: it may summarize companion health, latest provider-state presence, overlay state-source status, view-model validation, and in-memory review/accessibility status; it must not launch the game, poll continuously, add timers/background workers, capture current lines, read UI text, scan Unity objects, use hooks/Harmony, run OCR, extract data, call real providers, change companion HTTP contracts, implement a production shell, commit runtime artifacts, print raw logs, or dump provider payloads.`

---

After ADR 0010:

1. Treat the successful bridge-to-overlay synthetic smoke as sufficient evidence to plan only a
   metadata-only overlay refresh/readiness contract.
2. Keep packaging/manual workflow polish allowed as support work, but do not turn the smoke wrapper
   into a production overlay shell.
3. Do not infer current-line capture, real text capture, UI text reading, Unity scanning,
   hooks/Harmony, OCR, extraction, real provider execution, production overlay readiness, or
   companion HTTP contract readiness from the passed smoke.
4. Keep the post-smoke decision gate tracked in
   `docs/adr/0010-post-bridge-to-overlay-next-step.md` and
   `tests/fixtures/post_bridge_to_overlay_next_step.synthetic.json`.

Recommended next safe step:

- Define the metadata-only overlay refresh/readiness contract: safe states, stale/no-provider
  behavior, redacted status fields, and boundaries for a future shell handoff, still with no runtime
  implementation, no capture, no real provider calls, and no companion HTTP contract changes.

Exact resume prompt:

`Continue in revachol-ukro-elisium after ADR 0010 accepted the post bridge-to-overlay next step. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/adr/0010-post-bridge-to-overlay-next-step.md, docs/overlay-prototype.md, docs/bepinex-bridge.md, scripts/overlay_state_source.py, scripts/local_overlay_prototype.py, scripts/run_bridge_to_overlay_synthetic_smoke.py, scripts/check_bepinex_bridge_safety.py, and tests/fixtures/post_bridge_to_overlay_next_step.synthetic.json. Implement the metadata-only overlay refresh/readiness contract as docs/static-contract work only: define safe ready/stale/no-provider/error refresh states and handoff fields for a future overlay shell, still without current-line capture, real text capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider execution, companion HTTP contract changes, production shell work, committed runtime artifacts, raw logs, raw provider payloads, screenshots, downloads, or new dependencies.`

---

After the bridge-to-overlay synthetic smoke passed:

1. Treat the successful smoke as evidence only for the synthetic/manual path from
   game/BepInEx/bridge synthetic event to companion mock provider state to overlay
   state-source/view-model/review validation.
2. Keep workspace reports, generated overlay HTML, raw `LogOutput.log`, companion/provider
   payloads, screenshots, private paths, game files, logs, and runtime artifacts out of git.
3. Do not infer current-line capture, real text capture, UI text reading, Unity scanning,
   hooks/Harmony, OCR, extraction, real provider execution, production overlay readiness, or
   companion HTTP contract readiness from this result.
4. Keep `MetadataProbeEnabled=false`, `MetadataProbeLogOnStart=false`, and
   `SendSyntheticEventOnStart=false` restored after smoke testing.

Recommended next safe decision step:

- Decide in docs whether the synthetic/manual bridge-to-overlay path is sufficient to begin planning
  a later metadata-only overlay refresh/readiness contract, still with no current-line capture, no
  real text capture, no UI text reading, no Unity scanning, no hooks, no OCR, no extraction, no real
  provider execution, and no companion HTTP contract changes.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the redacted bridge-to-overlay synthetic smoke passed. First inspect git status and read AGENTS.md, docs/devlog/*.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, docs/bepinex-bridge.md, docs/overlay-prototype.md, scripts/run_bridge_to_overlay_synthetic_smoke.py, scripts/run_bepinex_metadata_probe_local_smoke.py, scripts/overlay_state_source.py, and scripts/local_overlay_prototype.py. Use only tracked redacted evidence notes, not raw logs, provider payloads, report contents, screenshots, generated HTML, private paths, game files, or runtime artifacts. Decide the next safe synthetic/manual bridge-to-overlay planning step after successful companion mock provider state and overlay state/view/review validation, still without current-line capture, real text capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider execution, companion HTTP contract changes, production overlay shell work, committed logs, committed screenshots, committed reports, downloads, or new dependencies.`

---

After bridge-to-overlay synthetic smoke prep:

1. Start the localhost companion server with `python scripts/run_companion_server.py`.
2. Run `python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase prepare --auto-discover`
   before manually launching the game.
3. Manually launch and close the game; do not paste or commit raw logs.
4. Run
   `python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase post --auto-discover --write-report`.
5. Review only the redacted bridge-to-overlay summary. Do not commit workspace reports, generated
   overlay HTML, raw provider payloads, raw BepInEx logs, screenshots, private paths, or game text.
6. Restore local config with
   `python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase cleanup --auto-discover`.

Recommended next step:

- Run the bridge-to-overlay synthetic smoke locally and record only a redacted result note if the
  wrapper reports bridge log readiness, latest provider state presence, overlay state-source
  validity, view-model validity, and in-memory review accessibility validity.

Exact resume prompt:

`Continue in revachol-ukro-elisium after bridge-to-overlay synthetic smoke prep. First inspect git status and use only redacted helper output, not raw logs, report contents, companion payloads, screenshots, private paths, generated HTML, or runtime artifacts. Start/verify the local companion server, run python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase prepare --auto-discover, wait for the user to manually launch and close the game, then run python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase post --auto-discover --write-report and python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase cleanup --auto-discover. Report only redacted booleans for bridge log readiness, latest provider state, overlay state-source/view-model/review validation, and cleanup; still do not add current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction, real provider execution, companion HTTP contract changes, committed logs, screenshots, reports, generated HTML, downloads, or dependencies.`

---

After the companion-connected synthetic bridge smoke passed:

1. Treat the successful smoke as evidence only for localhost companion availability, invented
   synthetic provider-event delivery, bridge startup, the metadata-probe snapshot, and safe 4M
   counters.
2. Keep the completed local report, raw `LogOutput.log`, companion response payloads, screenshots,
   private paths, and runtime artifacts out of git.
3. Do not infer current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR,
   extraction, real provider execution, or companion HTTP contract readiness from this result.
4. Decide the next safe bridge step in docs first: either repeat the companion-connected smoke if
   more local confidence is needed, or scope another synthetic/manual-only bridge check that still
   does not read game text.
5. Keep `MetadataProbeEnabled=false`, `MetadataProbeLogOnStart=false`, and
   `SendSyntheticEventOnStart=false` restored after smoke testing.

Recommended next step:

- Add a small docs/static decision note for whether the successful companion-connected synthetic
  smoke is enough to continue synthetic/manual bridge hardening, while keeping all capture and
  companion-contract permissions closed.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the companion-connected synthetic bridge smoke passed. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, docs/manual-smoke/bepinex-bridge-runtime-smoke.md, docs/bepinex-bridge.md, scripts/run_bepinex_metadata_probe_local_smoke.py, scripts/run_companion_server.py, scripts/run_companion_client.py, and packages/bepinex-plugin/src/*.cs. Use only tracked redacted evidence notes, not raw logs, report contents, companion payloads, screenshots, private paths, or runtime artifacts. Decide the next synthetic/manual bridge hardening step after successful localhost companion health and invented synthetic provider-event delivery, still without current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction, real provider execution, companion HTTP contract changes, committed logs, committed screenshots, committed real reports, downloads, or new dependencies.`

---

After companion-connected synthetic bridge smoke prep:

1. Start the localhost companion server with `python scripts/run_companion_server.py`.
2. Verify health with `python scripts/run_companion_client.py health`.
3. Prepare the local game config with
   `python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --enable-probe --enable-synthetic-send`.
4. Manually launch and close the game; do not paste or commit raw logs.
5. Run the redacted post-run check with
   `python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --check-log --write-report`.
6. Validate/review the workspace-only report, optionally query synthetic provider latest state
   locally, and then restore config with
   `python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --disable-probe --disable-synthetic-send`.

Recommended next step:

- Run the companion-connected synthetic smoke locally and record only a redacted result note if the
  bridge observes companion availability and the invented synthetic provider event.

Exact resume prompt:

`Continue in revachol-ukro-elisium after companion-connected synthetic bridge smoke prep. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, docs/manual-smoke/bepinex-bridge-runtime-smoke.md, docs/bepinex-bridge.md, scripts/run_bepinex_metadata_probe_local_smoke.py, scripts/run_companion_server.py, scripts/run_companion_client.py, and packages/bepinex-plugin/src/*.cs. Use only redacted helper output and workspace-only reports. Run the local companion-connected synthetic smoke manually with the companion server, then summarize only booleans for health/synthetic-send observations; still do not add current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider execution, companion HTTP contract changes, committed logs, screenshots, or runtime reports.`

---

After the redacted local metadata-probe smoke passed:

1. Treat the successful smoke as evidence only for bridge startup, the metadata-probe snapshot, and
   the safe 4M counters.
2. Keep the completed local report, raw `LogOutput.log`, screenshots, private paths, and runtime
   artifacts out of git.
3. Do not infer current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR,
   extraction, provider execution, or companion HTTP contract readiness from this result.
4. Use the redacted evidence to decide the next metadata-only planning step. Any future runtime
   expansion still needs a separate scope, tests, and safety-check updates before implementation.
5. Keep `MetadataProbeEnabled=false` and `MetadataProbeLogOnStart=false` as the restored local
   default after smoke testing.

Recommended next step:

- Add a small docs/static decision note or ADR update that says the local metadata-probe startup
  smoke is ready for human review of the next metadata-only planning step, while keeping all capture
  and companion-contract permissions closed.

Exact resume prompt:

`Continue in revachol-ukro-elisium after the redacted local metadata-probe smoke passed. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, docs/bepinex-metadata-only-extension-scope.md, docs/bepinex-metadata-probe-gate.md, and docs/adr/0009-metadata-only-extension-gate.md. Use only the tracked redacted evidence note, not raw logs or report contents. Decide the next metadata-only planning step after successful startup/counter smoke, still without C# behavior changes, current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider execution, companion HTTP contract changes, committed logs, committed screenshots, committed real reports, downloads, or new dependencies.`
