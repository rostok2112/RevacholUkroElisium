# bepinex-plugin

Milestone 4A C# BepInEx bridge skeleton for Revachol Ukrainian Companion.

## M3 baseline reuse

M3 scope recovery is tracked in:

```text
docs/m3-bepinex-bridge-scope.md
tests/fixtures/m3_bepinex_bridge_scope.synthetic.json
scripts/check_m3_bepinex_bridge_scope.py
```

The existing package is reused as M3 baseline and should not be recreated. It still does not
complete original M3. The remaining M3 criteria are current-line event emission, line-ID matching,
and a debug console.

The first M3 criterion is scoped by:

```text
docs/m3-current-line-event-contract.md
tests/fixtures/m3_current_line_event_contract.synthetic.json
scripts/check_m3_current_line_event_contract.py
```

The next allowed M3 step is `m3_current_line_event_implementation`. Line-ID matching and debug
console work remain separate criteria.

## Current status

This package is static-reviewable skeleton code. It is not wired into a real game install by the
repo checks, and it is not a production mod.

What exists:

- BepInEx plugin metadata and safe startup logging.
- Config entries for enabling the bridge, companion URL, timeout, and synthetic send-on-start.
- Localhost-only companion `/health` check.
- Manual/synthetic fake-event send to `POST /synthetic/provider-annotate`.
- Disabled-by-default metadata probe snapshot support.
- Metadata-only logs for event id, line id, status, and unavailable companion states.

What does not exist:

- No real dialogue detection.
- No game hooks or Unity object scanning.
- No text extraction, OCR, or decompiled game-code integration.
- No production overlay, keyboard hooks, clipboard behavior, or provider execution.
- No current-line capture, runtime text reads, screenshots, or log parsing.

## Optional build verification

`Revachol.UkrainianCompanion.BepInExBridge.csproj` is intentionally minimal. It expects local
BepInEx assemblies supplied by the user through MSBuild properties:

```text
BepInExCoreDll=<path to BepInEx.Core.dll>
BepInExIL2CPPDll=<path to BepInEx.Unity.IL2CPP.dll>
```

Milestone 4B adds a local-only helper:

```powershell
python scripts/build_bepinex_bridge.py --quiet
```

It skips cleanly if `dotnet` or BepInEx references are missing. When references are supplied, it runs
`dotnet build`, reports total warnings plus `MSB3277` warning count, and writes optional reports only
under `workspace/synthetic-slice/bepinex-bridge/`.

Example:

```powershell
python scripts/build_bepinex_bridge.py `
  --core-dll <path-to-BepInEx.Core.dll> `
  --il2cpp-dll <path-to-BepInEx.Unity.IL2CPP.dll> `
  --output workspace/synthetic-slice/bepinex-bridge/build-report.json
```

The repository checks still do not require a successful C# build, the .NET SDK, or BepInEx binaries.
`check_all` runs the Python safety checker only.

`MSB3277` assembly-version warnings are allowed in 4B when the build succeeds and safety checks pass.
They are not hidden; the helper summarizes them so a later runtime milestone can decide whether to
pin or clean references.

## Manual verification checklist

1. Start the companion server with `python scripts/run_companion_server.py`.
2. Run the optional build helper with user-local BepInEx references.
3. Copy the built DLL into the user-owned `BepInEx/plugins/` folder.
4. Launch the game.
5. Confirm plugin startup logs appear.
6. Confirm the companion `/health` check logs availability or a safe unavailable warning.
7. Optionally enable `SendSyntheticEventOnStart = true` in local config.
8. Confirm the companion receives the invented synthetic provider event.
9. Confirm the game continues if the companion server is unavailable.

Keep this verification synthetic/manual only. Do not capture real dialogue, scan Unity objects, run
OCR, extract data, or commit local install paths.

Milestone 4C keeps the detailed checklist and log contract in:

```text
docs/manual-smoke/bepinex-bridge-runtime-smoke.md
docs/manual-smoke/bepinex-bridge-log-contract.md
docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md
tests/fixtures/bepinex_bridge.log_contract.synthetic.json
tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json
```

The C# bridge logs must remain metadata-only: plugin state, localhost safety state, companion health
status, HTTP status code, synthetic event id, and synthetic line id. Do not log full request
payloads, response bodies, raw source text, private paths, stack traces, or local game data.

## Metadata-only probe skeleton

Milestone 4H adds a disabled metadata probe skeleton. Defaults:

```text
MetadataProbeEnabled = false
MetadataProbeLogOnStart = false
```

When both are manually enabled, the plugin may log one startup snapshot containing only safe
booleans and zero/default counters. The snapshot keeps:

```text
real_text_captured=false
current_line_capture_enabled=false
ui_probe_attempted=false
scene_probe_attempted=false
```

It does not call new companion endpoints, create payloads, read runtime text, inspect game objects,
read files, parse logs, capture screenshots, or enable future text capture.

Milestone 4M extends the snapshot with inert local counters only:

```text
metadata_snapshot_created_count
health_check_observed_count
synthetic_send_configured_count
```

The counters are derived from existing startup booleans, stay in memory only, and are emitted only
inside the manually enabled metadata snapshot log. They do not read game state or send companion
payloads.

Milestone 4N documents how to verify those counters manually and record only redacted values in a
workspace-local report. Do not commit raw logs, screenshots, private paths, payload dumps, or real
metadata probe reports.

Manual metadata probe verification is documented in:

```text
docs/manual-smoke/bepinex-metadata-probe-smoke.md
```

Write a blank redacted metadata probe report template with:

```powershell
python scripts/write_bepinex_metadata_probe_report.py --quiet
```

Validate the completed local report with:

```powershell
python scripts/check_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

Review a completed local report with:

```powershell
python scripts/review_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

For the real local in-game smoke, the helper can prepare the Steam-installed game without launching
it:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --enable-probe
```

For the companion-connected synthetic smoke, start the existing localhost companion server in a
separate terminal, verify health, and temporarily enable the existing synthetic send-on-start flag:

```powershell
python scripts/run_companion_server.py
python scripts/run_companion_client.py health
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --enable-probe `
  --enable-synthetic-send
```

After you manually launch and close the game, it can read only `BepInEx/LogOutput.log` for
allowlisted metadata markers and write the redacted workspace report:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --check-log `
  --write-report
```

Disable the probe flags after the smoke:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --disable-probe `
  --disable-synthetic-send
```

The helper never launches the game, recursively scans drives, prints raw logs, stores raw logs,
parses dialogue, reads arbitrary game files, calls providers, or changes the companion HTTP
contract. It can summarize bridge-owned companion health and synthetic-send markers as redacted
booleans only. Optional local provider-state checks should use
`python scripts/run_companion_client.py latest-provider-context` and
`python scripts/run_companion_client.py latest-provider-annotation`; do not commit or paste those
runtime payloads.

Completed reports must stay local and ignored. Passing validation does not approve current-line
capture or any broader runtime probing. A ready review means only that a later metadata-only
extension can be discussed.

Local redacted runtime smoke reports, if created, must stay under:

```text
workspace/synthetic-slice/bepinex-bridge/runtime-smoke/
```

Validate report summaries with:

```powershell
python scripts/check_bepinex_runtime_smoke_report.py --quiet
```

## Local companion defaults

Default companion URL:

```text
http://127.0.0.1:8765
```

The skeleton skips requests if the configured URL is not localhost. If the companion server is not
available, the plugin logs a concise warning and the game continues without companion data.
