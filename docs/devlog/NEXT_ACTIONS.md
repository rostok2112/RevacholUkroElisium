# Next Actions

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
