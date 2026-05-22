# Next Actions

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
