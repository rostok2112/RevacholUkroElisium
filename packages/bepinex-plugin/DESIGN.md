# BepInEx Plugin Design

## M3 baseline reuse

M3 scope recovery is tracked in:

```text
docs/m3-bepinex-bridge-scope.md
tests/fixtures/m3_bepinex_bridge_scope.synthetic.json
scripts/check_m3_bepinex_bridge_scope.py
```

The existing skeleton, optional build helper, runtime smoke workflow, metadata probe workflow, and
local workflow wrapper are reused as baseline. They do not complete original M3 yet.

Original M3 still requires:

- emit current line event;
- match line IDs;
- debug console.

The first M3 criterion is scoped by:

```text
docs/m3-current-line-event-contract.md
tests/fixtures/m3_current_line_event_contract.synthetic.json
scripts/check_m3_current_line_event_contract.py
```

The next allowed M3 step is `m3_current_line_event_implementation`. Line-ID matching and debug
console work remain separate criteria.

The current-line event implementation is guarded by:

```text
packages/bepinex-plugin/src/CurrentLineEventFactory.cs
tests/fixtures/m3_current_line_event_implementation.synthetic.json
scripts/check_m3_current_line_event_implementation.py
```

It is disabled by default and emits redacted bridge-owned metadata only. The next bounded step is
`m3_line_id_matching`.

M3 line-ID matching is guarded by:

```text
scripts/run_m3_line_id_match.py
tests/fixtures/m3_line_id_matching.synthetic.json
tests/test_m3_line_id_match.py
```

The matcher uses exact `line_id` membership only against an ignored private M2 line-index artifact.
The next bounded step is `m3_debug_console`.

## Milestone 4A boundary

The bridge is currently a synthetic/manual communication skeleton only. It exists to prove a safe
shape for future game-to-companion communication before any real game-state capture is attempted.

## Responsibilities now

- Load as a BepInEx plugin skeleton.
- Bind safe config defaults.
- Check the localhost companion `/health` endpoint.
- Optionally send one built-in synthetic fake event when explicitly configured.
- Provide safe logs for enabled/disabled state, companion availability, event id, line id, and HTTP
  status.
- Match the Milestone 4C manual log contract in
  `tests/fixtures/bepinex_bridge.log_contract.synthetic.json`.

## Anti-goals now

- No real dialogue detection.
- No game hooks or Unity object scanning.
- No OCR, extraction, decompiled game-code integration, or bundled translation database.
- No cloud calls, provider execution, keyboard hooks, clipboard writes, or production overlay shell.
- No hard dependency on the companion server being available.

## Future

- User-local manual runtime smoke report capture and redaction checks.
- Manual in-game command or debug panel for sending the synthetic event.
- Carefully scoped current-line detection research after the skeleton proves safe installation and
  localhost communication.
- Later shell/window work only after bridge feasibility is better understood.

## Milestone 4B build posture

`scripts/build_bepinex_bridge.py` can optionally compile the bridge when `dotnet` and user-local
BepInEx IL2CPP references are supplied. The helper skips cleanly otherwise, reports warning counts,
and remains outside mandatory `check_all`.

`MSB3277` reference-version warnings are visible and allowed in 4B if the build succeeds and the
static safety checks pass. They are not hidden, and later runtime testing can decide whether the
reference set needs cleanup.

## Milestone 4C runtime smoke posture

Manual runtime verification is documented under `docs/manual-smoke/`. The repo commits expected log
snippets and forbidden log categories, but does not commit local runtime logs or reports. The bridge
still has no game hooks, Unity object scanning, current-line detection, OCR, extraction, provider
execution, keyboard hooks, clipboard writes, or companion HTTP contract changes.

## Milestone 4D report posture

Manual smoke evidence is summarized through a redacted JSON report contract only. The committed
fixture is synthetic and marked `not_run`; user-local reports belong under
`workspace/synthetic-slice/bepinex-bridge/runtime-smoke/` and are validated with
`scripts/check_bepinex_runtime_smoke_report.py`. The checker rejects raw logs, stack traces, payload
dumps, private paths, screenshots/assets/audio markers, real game content markers, hooks,
OCR/extraction/decompiled markers, provider execution markers, and non-localhost URLs.

## Milestone 4E capture research posture

ADR 0008 (`docs/adr/0008-current-line-capture-research.md`) compares future current-line capture
approaches and keeps implementation deferred. The bridge remains synthetic/manual until redacted
runtime smoke evidence is reviewed.

Future capture probes must begin metadata-only and disabled by default. Acceptable local experiment
output is limited to booleans, safe counters, synthetic event ids, bridge-generated line ids, and
redacted smoke reports. Do not commit real dialogue text, screenshots, audio, extracted localization
files, save files, OCR output, decompiled code or risky decompiled names, private paths, runtime logs
with game text, or raw companion payloads containing real game text.

Milestone 4F should review runtime smoke evidence before any metadata-only current-line probe is
scoped. It should not add real text capture, game hooks, OCR, extraction, or companion contract
changes.

## Milestone 4F evidence review posture

`scripts/review_bepinex_runtime_smoke_report.py` reviews a redacted user-local smoke report and can
write a redacted readiness summary under ignored workspace paths. It never reads BepInEx logs, game
logs, screenshots, game files, companion state, or provider outputs. A ready review means only that
evidence is complete enough to discuss a later metadata-only probe; it does not approve capture.

## Milestone 4G metadata probe gate posture

`docs/bepinex-metadata-probe-gate.md` defines the static safety gate for metadata-only probe work.
Probe behavior must stay disabled by default and bounded by a ready 4F review plus a separate
approval step before any future expansion.

The only acceptable future probe outputs before another safety review are booleans, safe counters,
synthetic ids, safe status/error codes, and explicit `current_line_capture_enabled = false` /
`real_text_captured = false` markers. Real text capture, hooks, Unity text scanning, OCR,
extraction, provider execution, raw payloads, screenshots, and committed runtime logs remain outside
the bridge design.

## Milestone 4H metadata probe skeleton posture

The C# bridge now includes a disabled-by-default metadata probe skeleton. It has two false defaults:
`MetadataProbeEnabled` and `MetadataProbeLogOnStart`.

When both are manually enabled, the bridge may log one startup metadata snapshot. The snapshot is
limited to booleans, safe counters, synthetic/manual status, and hard false markers for
`real_text_captured`, `current_line_capture_enabled`, `ui_probe_attempted`, and
`scene_probe_attempted`.

The skeleton does not call companion endpoints, create request payloads, read runtime text, inspect
objects, parse logs, read files, capture screenshots, or approve future text capture.

## Milestone 4I metadata probe manual verification posture

`docs/manual-smoke/bepinex-metadata-probe-smoke.md` documents how a user can manually enable the
disabled probe, observe one metadata-only startup summary, and then disable it again. The workflow
records only redacted booleans and counters in local reports under
`workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.

`scripts/write_bepinex_metadata_probe_report.py` writes a blank workspace-only template, and
`scripts/check_bepinex_metadata_probe_report.py` validates completed local summaries. Neither helper
reads logs, game files, screenshots, companion state, or provider output.

Milestone 4I deliberately does not add a metadata probe review helper. That readiness review is
deferred to Milestone 4J and still must not approve text capture by itself.

## Milestone 4J metadata probe review posture

`scripts/review_bepinex_metadata_probe_report.py` reviews a redacted user-local metadata probe
report and can write redacted JSON/Markdown summaries under ignored workspace review paths. It never
reads logs, game files, screenshots, companion state, or provider output.

`readiness_status = "ready"` means only that the report is complete enough to discuss a later
metadata-only extension. It does not approve current-line capture, UI text reading, real text
capture, hooks, OCR, extraction, provider execution, or companion contract changes.

## Milestone 4K metadata-only extension decision posture

ADR 0009 (`docs/adr/0009-metadata-only-extension-gate.md`) records that the project is ready for
metadata-only extension discussion only. Runtime implementation remains blocked until a later
approved milestone has either a ready local metadata probe review or a documented decision to proceed
without one.

The gate fixture (`tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json`) keeps
`implementation_allowed=false`, `text_capture_allowed=false`, `current_line_capture_allowed=false`,
and `companion_contract_change_allowed=false`. Future extension scope is limited to safe booleans,
safe counters, bridge-generated synthetic ids, redacted status codes, and explicit false capture
flags.

## Milestone 4L metadata-only extension scope posture

`docs/bepinex-metadata-only-extension-scope.md` defines the exact 4M scope contract. The matching
fixture is `tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json`.

4M may be planned without a reviewed local metadata report only for this minimal inert scope:
non-negative counters, plugin lifecycle booleans, companion health booleans, synthetic-send
booleans, probe attempted/completed booleans, and explicit false capture flags. Runtime behavior
must remain disabled by default.

The scope still forbids current-line capture, real text capture, UI text reading, Unity scanning,
hooks, OCR, extraction, provider execution, companion HTTP contract changes, companion metadata
payloads, private paths, raw payload logging, and runtime scene or object names.

## Milestone 4M inert metadata extension posture

The C# probe now implements only the inert 4L-approved snapshot extension: local counters for
metadata snapshot creation, health-check observation, and synthetic-send configuration. These
counters are derived from existing startup booleans and are not persisted or sent anywhere.

The probe remains disabled by default and still does not read runtime text, inspect game/UI state,
scan Unity objects, parse logs, read files, capture screenshots, call new companion endpoints, or
create metadata payloads. All capture flags remain explicit false values.

## Milestone 4N manual counter verification posture

Manual verification for the 4M counters is documentation and report-contract work only. A local run
may summarize `metadata_snapshot_created_count`, `health_check_observed_count`, and
`synthetic_send_configured_count` in a redacted workspace report, but the repo must not commit raw
logs, screenshots, private paths, payload dumps, real game text, or completed real reports.

The verification path does not change C# behavior, does not approve capture, and does not add
companion metadata payloads or endpoints.

The local preparation helper is `scripts/run_bepinex_metadata_probe_local_smoke.py`. It may perform
bounded Steam autodiscovery, build/install the existing bridge DLL, toggle
`MetadataProbeEnabled`, `MetadataProbeLogOnStart`, and the existing `SendSyntheticEventOnStart`
bridge config key, and read only `BepInEx/LogOutput.log` after the user manually launches and
closes the game. It never launches the game, recursively scans drives, stores or prints raw logs,
parses dialogue, reads arbitrary game files, calls providers, scans Unity objects, or changes the
companion HTTP contract.

For companion-connected synthetic smoke, the helper may summarize only bridge-owned companion
health and synthetic-send markers as redacted booleans. The companion server/client stay the
existing localhost tools (`scripts/run_companion_server.py` and `scripts/run_companion_client.py`);
there are no new endpoints, provider calls, or C# behavior changes. The local config toggle flags
are `--enable-synthetic-send` before the manual run and `--disable-synthetic-send` during cleanup.
