# BepInEx Metadata Probe Manual Smoke

Milestone 4I documents how to manually enable the disabled metadata-only probe, observe one safe
startup summary, and record a redacted local report. This is still a no-capture workflow: it does
not approve current-line detection, UI text reading, game hooks, Unity object scanning, OCR,
extraction, provider calls, or companion HTTP contract changes.

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

Do not paste raw log lines into committed files. A local redacted report should summarize only the
booleans and counters you observed.

## Report Template

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
runtime probing, hooks, OCR, extraction, provider execution, or a new companion contract.
