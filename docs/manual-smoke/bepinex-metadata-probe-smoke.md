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

## Companion-Connected Synthetic Smoke Prep

The same helper can prepare a synthetic/manual companion-connected smoke without launching the game.
This uses only the existing bridge config key `SendSyntheticEventOnStart`; no C# behavior or
companion HTTP contract changes are required.

In terminal A, start the local companion server:

```powershell
python scripts/run_companion_server.py
```

In terminal B, verify health:

```powershell
python scripts/run_companion_client.py health
```

Before manually launching the game, build/install the bridge if possible, enable the metadata
snapshot, and temporarily enable the existing synthetic send-on-start flag:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --enable-probe `
  --enable-synthetic-send
```

Then launch and close the game yourself. After closing the game, read only allowlisted bridge-owned
markers from `BepInEx/LogOutput.log` and write the redacted workspace report:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --check-log `
  --write-report
```

The redacted helper output may report only booleans for companion health and synthetic provider send
markers, including whether the expected synthetic `event_id`, `line_id`, and HTTP status were
present. It must not print raw log lines, payloads, response bodies, private paths, or game text.

If the synthetic send was observed, you may query the running companion server with existing local
client commands:

```powershell
python scripts/run_companion_client.py latest-provider-context
python scripts/run_companion_client.py latest-provider-annotation
```

Do not commit or paste the returned payloads as runtime evidence. Use them only for local
confirmation that the companion received the invented synthetic provider event.

Cleanup must restore both local config switches:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --disable-probe `
  --disable-synthetic-send
```

The helper may copy the built bridge DLL only to `BepInEx/plugins/`, edit only the bridge config
under `BepInEx/config/`, and read only `BepInEx/LogOutput.log`. It must not print raw log lines,
store raw logs, recursively scan drives, parse dialogue, read arbitrary game files, inspect
screenshots, run OCR, launch the game, call providers, or change the companion HTTP contract.

## Bridge-To-Overlay Synthetic Smoke Prep

After the companion-connected synthetic smoke passes, use the redacted wrapper to prove the next
synthetic-only path into the overlay state-source and review renderer:

```text
scripts/run_bridge_to_overlay_synthetic_smoke.py
```

In terminal A, start the local companion server:

```powershell
python scripts/run_companion_server.py
```

Prepare the local bridge config before manually launching the game:

```powershell
python scripts/run_bridge_to_overlay_synthetic_smoke.py `
  --phase prepare `
  --auto-discover
```

Then launch and close the game yourself. After closing the game, run the redacted post-run bridge to
overlay check:

```powershell
python scripts/run_bridge_to_overlay_synthetic_smoke.py `
  --phase post `
  --auto-discover `
  --write-report
```

The post phase reads bridge evidence only through the existing redacted metadata probe helper,
queries only the companion latest provider context/annotation presence, builds the overlay
state-source and view model in memory, renders HTML in memory, and reports booleans/status only.
It must not print raw BepInEx logs, provider payloads, report contents, private paths, screenshots,
or game text.

Cleanup restores all local flags:

```powershell
python scripts/run_bridge_to_overlay_synthetic_smoke.py `
  --phase cleanup `
  --auto-discover
```

Optional redacted summaries belong only under:

```text
workspace/synthetic-slice/bepinex-bridge/bridge-to-overlay-smoke/
```

Optional generated overlay review HTML belongs only under:

```text
workspace/synthetic-slice/overlay-prototype/bridge-to-overlay-smoke/
```

Passing this smoke proves only the invented synthetic bridge event can be observed through companion
latest provider state and transformed into an overlay state-source/view-model/review validation. It
does not prove or approve current-line capture, real text capture, UI text reading, Unity scanning,
hooks, OCR, extraction, real provider execution, production overlay behavior, or companion HTTP
contract changes.

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

## Redacted Local Smoke Result

A local metadata-probe smoke was completed and recorded only as redacted evidence. No raw
`LogOutput.log` lines, report contents, screenshots, private paths, game text, or runtime artifacts
are committed.

Observed redacted result:

- `plugin_loaded_observed`: yes
- `metadata_snapshot_observed`: yes
- `metadata_snapshot_created_count_observed`: yes
- `health_check_observed_count_observed`: yes
- `synthetic_send_configured_count_observed`: yes
- `real_text_captured_false_observed`: yes
- `current_line_capture_enabled_false_observed`: yes
- `ui_probe_attempted_false_observed`: yes
- `scene_probe_attempted_false_observed`: yes
- `forbidden_marker_detected`: no
- report checker: passed
- reviewer: ready
- `MetadataProbeEnabled=false` restored: yes
- `MetadataProbeLogOnStart=false` restored: yes

This proves only that the bridge loaded far enough to emit the metadata-probe startup snapshot and
the safe 4M counters in a local manual run. It does not prove or approve current-line capture, real
text capture, UI text reading, Unity object scanning, hooks, OCR, extraction, provider execution, or
companion HTTP contract changes.

## Redacted Companion-Connected Synthetic Smoke Result

A companion-connected synthetic bridge smoke was completed and recorded only as redacted evidence.
No raw `LogOutput.log` lines, report contents, screenshots, private paths, game text, companion
payloads, logs, or runtime artifacts are committed.

Observed redacted result:

- `plugin_loaded_observed`: yes
- `metadata_snapshot_observed`: yes
- `companion_health_available_observed`: yes
- `synthetic_send_observed`: yes
- `metadata_snapshot_created_count_observed`: yes
- `health_check_observed_count_observed`: yes
- `synthetic_send_configured_count_observed`: yes
- `real_text_captured_false_observed`: yes
- `current_line_capture_enabled_false_observed`: yes
- `ui_probe_attempted_false_observed`: yes
- `scene_probe_attempted_false_observed`: yes
- `forbidden_marker_detected`: no
- report checker: passed
- reviewer: ready
- companion latest synthetic/provider state observed: yes
- `MetadataProbeEnabled=false` restored: yes
- `MetadataProbeLogOnStart=false` restored: yes
- `SendSyntheticEventOnStart=false` restored: yes

This proves only the synthetic/manual bridge-to-companion flow: the bridge loaded, saw localhost
companion health through redacted markers, sent the invented synthetic provider event, and left all
capture flags false. It does not prove or approve current-line capture, real text capture, UI text
reading, Unity object scanning, hooks, OCR, extraction, provider execution with real providers, or
companion HTTP contract changes.

## Redacted Bridge-To-Overlay Synthetic Smoke Result

A bridge-to-overlay synthetic smoke was completed and recorded only as redacted evidence. No raw
`LogOutput.log` lines, provider payload contents, report contents, screenshots, private paths, game
text, generated HTML, logs, or runtime artifacts are committed.

Observed redacted result:

- `plugin_loaded_observed`: yes
- `metadata_snapshot_observed`: yes
- `companion_health_available_observed`: yes
- `synthetic_send_observed`: yes
- provider context exists: yes
- provider annotation exists: yes
- overlay state-source ready: yes
- overlay view model valid: yes
- overlay HTML valid: yes
- accessibility check passed: yes
- `forbidden_marker_detected`: no
- report written: yes, under ignored workspace only
- `MetadataProbeEnabled=false` restored: yes
- `MetadataProbeLogOnStart=false` restored: yes
- `SendSyntheticEventOnStart=false` restored: yes

This proves only the synthetic/manual bridge-to-overlay path:

```text
game/BepInEx/bridge synthetic event -> companion mock provider state -> overlay state/view/review
```

It does not prove or approve current-line capture, real text capture, UI text reading, Unity object
scanning, hooks/Harmony, OCR, extraction, real provider execution, production overlay behavior, or
companion HTTP contract changes.

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
