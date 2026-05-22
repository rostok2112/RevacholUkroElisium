# BepInEx Metadata Probe Manual Smoke

Milestone 4I documents how to manually enable the disabled metadata-only probe, observe one safe
startup summary, and record a redacted local report. Milestone 4N aligns that workflow with the 4M
inert metadata counters. This is still a no-capture workflow: it does not approve current-line
detection, UI text reading, game hooks, Unity object scanning, OCR, extraction, provider calls, or
companion HTTP contract changes.

## Prerequisites

- Complete the bridge runtime smoke checklist in
  `docs/manual-smoke/bepinex-bridge-runtime-smoke.md`.
- Build the bridge locally with user-owned BepInEx references if needed:

  ```powershell
  python scripts/build_bepinex_bridge.py --quiet
  ```

- Install the built DLL into the user-owned `BepInEx/plugins/` folder.
- Keep all local logs, screenshots, install paths, and completed reports out of git.

## Enable The Probe Locally

Edit the local BepInEx config for the bridge and set:

```text
MetadataProbeEnabled = true
MetadataProbeLogOnStart = true
```

The defaults in source must remain:

```text
MetadataProbeEnabled = false
MetadataProbeLogOnStart = false
```

## Expected Safe Observation

On startup, when both probe flags are manually enabled, the bridge may log one metadata-only line
with this prefix:

```text
Metadata probe snapshot: synthetic_manual=true
```

The observed summary should include safe metadata keys only:

```text
probe_enabled=true
probe_attempted=true
probe_completed=true
plugin_loaded=true
companion_health_checked=true
companion_available=true|false
synthetic_event_send_configured=true|false
```

The capture flags must remain false:

```text
real_text_captured=false
current_line_capture_enabled=false
ui_probe_attempted=false
scene_probe_attempted=false
```

Safe counters may appear as zero/default values:

```text
counters.safe_status_events=0
counters.synthetic_events=0
```

The 4M inert metadata counters should also be visible in the snapshot:

```text
counters.metadata_snapshot_created_count=1
counters.health_check_observed_count=0|1
counters.synthetic_send_configured_count=0|1
```

Interpret the 4M counters only as startup metadata:

- `metadata_snapshot_created_count=1` means the manually enabled snapshot was built once.
- `health_check_observed_count=1` means the startup health check returned a status result;
  `0` is acceptable when the companion was unavailable before an HTTP status was observed.
- `synthetic_send_configured_count=1` means `SendSyntheticEventOnStart=true` was configured;
  it does not prove a real game event was captured.

Do not paste raw log lines into committed files. A local redacted report should summarize only the
booleans and counters you observed, including the three 4M counters above.

## Report Template

## Local Smoke Helper

For the real local in-game smoke, use the bounded helper:

```text
scripts/run_bepinex_metadata_probe_local_smoke.py
```

It prefers Steam autodiscovery, then bounded common Steam locations, and it never launches the game.
Explicit paths override discovery when needed. Before launching the game manually, prepare the local
install and enable the probe:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --enable-probe
```

Then launch and close the game yourself. After closing the game, read only the discovered
`BepInEx/LogOutput.log` for allowlisted metadata markers and write a redacted workspace report:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --check-log `
  --write-report
```

Validate and review the report:

```powershell
python scripts/check_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet

python scripts/review_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

Disable the probe again after the smoke:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --disable-probe
```

The helper may copy the built bridge DLL only to `BepInEx/plugins/`, edit only the bridge config
under `BepInEx/config/`, and read only `BepInEx/LogOutput.log`. It must not print raw log lines,
store raw logs, recursively scan drives, parse dialogue, read arbitrary game files, inspect
screenshots, run OCR, launch the game, call providers, or change the companion HTTP contract.

## Manual Report Template

Write a blank redacted local template under the ignored workspace report root:

```powershell
python scripts/write_bepinex_metadata_probe_report.py --quiet
```

Or choose an explicit workspace-only path:

```powershell
python scripts/write_bepinex_metadata_probe_report.py `
  --output workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

Validate the completed local report:

```powershell
python scripts/check_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

Review the completed local report:

```powershell
python scripts/review_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

Optional review artifacts must be written only under:

```text
workspace/synthetic-slice/bepinex-bridge/metadata-probe/review/
```

The review summary is redacted. It copies only status booleans, counters, blockers, and readiness
status; it does not copy report notes, raw evidence, logs, screenshots, game files, companion state,
or provider output.

The report must stay redacted and must not include raw logs, screenshots, private paths, stack
traces, request or response dumps, real game text, UI text, OCR output, save data, or asset/audio
references.

## Cleanup

After the manual smoke, restore the local config:

```text
MetadataProbeEnabled = false
MetadataProbeLogOnStart = false
```

Remove or keep local report templates only under:

```text
workspace/synthetic-slice/bepinex-bridge/metadata-probe/
```

Do not commit completed local reports. The committed synthetic fixture remains:

```text
tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json
```

## Boundary

Passing this smoke only confirms that the disabled metadata probe can emit a redacted startup
summary when manually enabled. It does not approve current-line capture, text capture, broader
runtime probing, hooks, OCR, extraction, provider execution, or a new companion contract. A metadata
probe review marked `ready` means only that the redacted report is complete enough to discuss a later
metadata-only extension.
