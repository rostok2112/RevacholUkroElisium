# BepInEx Bridge Skeleton

Milestone 4A adds a safe C# BepInEx bridge skeleton under `packages/bepinex-plugin/`.

This is not production mod behavior. It does not detect real dialogue, scan Unity objects, extract
text, read local game databases, run OCR, call providers, or display an overlay. It only defines a
small localhost bridge shape for future work.

## What The Skeleton Does

- Loads with BepInEx plugin metadata.
- Binds config values:
  - `Enabled = true`
  - `CompanionServerUrl = "http://127.0.0.1:8765"`
  - `RequestTimeoutMs = 3000`
  - `SendSyntheticEventOnStart = false`
  - `MetadataProbeEnabled = false`
  - `MetadataProbeLogOnStart = false`
- Checks `GET /health` on the local companion server.
- Can send one invented synthetic fake event to `POST /synthetic/provider-annotate`.
- Can build one metadata-only startup snapshot when the disabled probe is explicitly enabled.
- Logs only safe metadata such as event id, line id, status, and unavailable companion state.
- Keeps the game running if the companion server is unavailable.

## Running The Companion Server

For local manual testing, start the companion server from the repository root:

```powershell
python scripts/run_companion_server.py
```

The default bridge URL matches the companion default:

```text
http://127.0.0.1:8765
```

The bridge skips requests if a non-localhost URL is configured.

## Optional Build Verification

Milestone 4B adds an optional build helper:

```powershell
python scripts/build_bepinex_bridge.py --quiet
```

The helper is stdlib-only and skips cleanly when `dotnet` or user-local BepInEx IL2CPP references
are missing. It does not download tools, require game files, or run as a required `check_all`
compilation step.

The package includes a minimal project file for a later local build:

```text
packages/bepinex-plugin/Revachol.UkrainianCompanion.BepInExBridge.csproj
```

It expects user-local BepInEx references supplied at build time:

```text
BepInExCoreDll=<path to BepInEx.Core.dll>
BepInExIL2CPPDll=<path to BepInEx.Unity.IL2CPP.dll>
```

You can pass those references directly:

```powershell
python scripts/build_bepinex_bridge.py `
  --core-dll <path-to-BepInEx.Core.dll> `
  --il2cpp-dll <path-to-BepInEx.Unity.IL2CPP.dll> `
  --output workspace/synthetic-slice/bepinex-bridge/build-report.json
```

or provide them through local environment variables:

```text
BEPINEX_CORE_DLL
BEPINEX_IL2CPP_DLL
BepInExCoreDll
BepInExIL2CPPDll
```

Generated reports belong under `workspace/synthetic-slice/bepinex-bridge/`. Built DLLs remain under
ignored `bin/`/`obj/` outputs and must not be committed.

### Warning Policy

Local BepInEx IL2CPP builds may emit `MSB3277` assembly-version conflict warnings from BepInEx/.NET
reference graphs. For Milestone 4B:

- A successful build with `MSB3277` warnings is acceptable if the bridge safety checks pass.
- The helper reports total warning count and `MSB3277` warning count.
- Warnings must stay visible; do not hide or suppress them silently.
- A later milestone may pin or clean references if runtime testing shows those warnings matter.

## Manual Install Shape

When a local build exists, the resulting DLL would be copied into the user-owned BepInEx plugin
folder for their local game install:

```text
BepInEx/plugins/
```

Do not commit built DLLs, game binaries, extracted databases, screenshots, audio, or local install
paths.

## Synthetic Manual Verification Checklist

This checklist is manual and synthetic-only:

1. Start the local companion server:

   ```powershell
   python scripts/run_companion_server.py
   ```

2. Run the optional build helper with local BepInEx references.
3. Copy the built DLL into the user-owned `BepInEx/plugins/` folder.
4. Launch the game from the user-owned local install.
5. Confirm the plugin logs safe startup metadata.
6. Confirm the `/health` check logs companion availability, or a concise unavailable warning.
7. Optionally set `SendSyntheticEventOnStart = true` in the local BepInEx config.
8. Confirm the companion server receives the invented synthetic provider event.
9. Stop the companion server and confirm the game continues after the safe unavailable warning.

Do not use this checklist to capture real dialogue, scan Unity objects, run OCR, or extract game
data.

The dedicated Milestone 4C checklist is:

```text
docs/manual-smoke/bepinex-bridge-runtime-smoke.md
```

The safe log contract is:

```text
docs/manual-smoke/bepinex-bridge-log-contract.md
tests/fixtures/bepinex_bridge.log_contract.synthetic.json
```

The redacted manual smoke report contract is:

```text
docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md
tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json
```

Validate the committed synthetic report fixture or a local workspace report with:

```powershell
python scripts/check_bepinex_runtime_smoke_report.py --quiet
```

Review a completed redacted local report with:

```powershell
python scripts/review_bepinex_runtime_smoke_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/runtime-smoke/report.json
```

Runtime logs may include only safe metadata: enabled/disabled state, localhost skip, companion
health availability, endpoint status, synthetic event id, synthetic line id, and concise unavailable
warnings. Do not commit local BepInEx logs, game logs, full payloads, response bodies, stack traces,
private paths, or smoke reports. Redacted local report summaries belong only under
`workspace/synthetic-slice/bepinex-bridge/runtime-smoke/`.

`ready_for_next_phase = true` in a review summary means the manual smoke evidence is ready for
human discussion of a later metadata-only probe. It is not approval to capture real text, add hooks,
run OCR, scan Unity objects, or change the companion contract.

## Metadata-Only Probe Gate

Milestone 4G defines the future-probe gate in:

```text
docs/bepinex-metadata-probe-gate.md
```

Milestone 4H adds the first disabled-by-default C# probe skeleton. It still does not add current-line
capture, Unity scanning, hooks, OCR, extraction, provider execution, or companion HTTP changes. It
may only log a metadata-only startup summary when both `MetadataProbeEnabled` and
`MetadataProbeLogOnStart` are manually set to true.

Allowed probe output remains limited to booleans, safe counters, synthetic ids, safe status/error
codes, and explicit `current_line_capture_enabled = false` / `real_text_captured = false` markers.

The committed synthetic metadata probe report fixture is:

```text
tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json
```

Validate the fixture or an optional local redacted report with:

```powershell
python scripts/check_bepinex_metadata_probe_report.py --quiet
```

Write a blank local report template with:

```powershell
python scripts/write_bepinex_metadata_probe_report.py --quiet
```

Review a completed redacted local report with:

```powershell
python scripts/review_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json
```

Prepare a real local in-game metadata-probe smoke with the bounded helper:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --enable-probe
```

For the companion-connected synthetic smoke, start the existing localhost companion server in a
separate terminal and temporarily enable the existing synthetic send-on-start config key:

```powershell
python scripts/run_companion_server.py
python scripts/run_companion_client.py health
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --enable-probe `
  --enable-synthetic-send
```

After manually launching and closing the game, check only `BepInEx/LogOutput.log` for allowlisted
metadata markers and write the redacted report:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --check-log `
  --write-report
```

Then disable the local probe flags:

```powershell
python scripts/run_bepinex_metadata_probe_local_smoke.py `
  --auto-discover `
  --disable-probe `
  --disable-synthetic-send
```

If the redacted helper output says the synthetic provider event was observed, optional local
confirmation can use:

```powershell
python scripts/run_companion_client.py latest-provider-context
python scripts/run_companion_client.py latest-provider-annotation
```

Do not commit or paste companion response payloads from a real local run.

The helper is local-test preparation only. It may discover Steam library paths, build/install the
bridge, toggle bridge config flags including `SendSyntheticEventOnStart`, and summarize allowlisted
metadata plus synthetic bridge markers. It never launches the game, recursively scans drives, prints
or stores raw logs, parses dialogue, reads arbitrary game files, calls providers, or changes the
companion HTTP contract.

The manual metadata probe smoke checklist is:

```text
docs/manual-smoke/bepinex-metadata-probe-smoke.md
```

After the companion-connected synthetic smoke passes, the next synthetic/manual wrapper is:

```text
scripts/run_bridge_to_overlay_synthetic_smoke.py
```

It prepares the same bridge config flags, reads only the existing redacted metadata-probe log/report
flow after the user manually closes the game, checks companion latest provider state as booleans,
and validates that the synthetic provider state can build an overlay state-source, view model, and
review HTML in memory.

Manual flow:

```powershell
python scripts/run_companion_server.py
python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase prepare --auto-discover
# manually launch and close the game
python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase post --auto-discover --write-report
python scripts/run_bridge_to_overlay_synthetic_smoke.py --phase cleanup --auto-discover
```

The wrapper must not launch the game, print raw logs, dump provider payloads, call real providers,
change companion endpoints, or commit workspace artifacts. Optional summary output is restricted to
`workspace/synthetic-slice/bepinex-bridge/bridge-to-overlay-smoke/`; optional generated overlay HTML
is restricted to `workspace/synthetic-slice/overlay-prototype/bridge-to-overlay-smoke/`.

Optional local metadata probe reports must remain ignored under:

```text
workspace/synthetic-slice/bepinex-bridge/metadata-probe/
```

Passing the checker does not approve text capture. It only verifies that a report is metadata-only
and redacted. A metadata probe review with `readiness_status = "ready"` means only that the redacted
report is complete enough to discuss a later metadata-only extension. It does not approve current-line
capture, UI text reading, real text capture, hooks, OCR, extraction, provider execution, or companion
contract changes.

## Post Bridge-To-Overlay Decision

ADR 0010 records the next decision after the successful redacted bridge-to-overlay synthetic smoke:

```text
docs/adr/0010-post-bridge-to-overlay-next-step.md
tests/fixtures/post_bridge_to_overlay_next_step.synthetic.json
```

The decision keeps the next step limited to `metadata_only_overlay_refresh_readiness_contract` and
supporting packaging/manual workflow polish. It does not approve current-line capture, real text
capture, UI text reading, Unity scanning, hooks/Harmony, OCR, extraction, real provider execution,
production overlay shell behavior, or companion HTTP contract changes.

The metadata-only overlay refresh/readiness contract is:

```text
docs/overlay-refresh-readiness-contract.md
tests/fixtures/overlay_refresh_readiness_contract.synthetic.json
scripts/check_overlay_refresh_readiness_contract.py
```

It maps only redacted readiness metadata across companion health, latest synthetic provider-state
presence, overlay state-source validation, view-model validation, and in-memory HTML/accessibility
checks. It does not approve current-line capture, real text capture, companion contract changes, or
production overlay shell behavior.

## Metadata-Only Extension Decision Gate

Milestone 4K records the extension gate in:

```text
docs/adr/0009-metadata-only-extension-gate.md
```

The current decision is `ready_for_metadata_only_extension_discussion`. That allows only future
scoping and review of a strictly metadata-only extension. It does not allow implementation yet.

The committed gate fixture is:

```text
tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json
```

The gate keeps implementation closed until a ready local metadata probe review exists, or a later
documented decision explicitly explains why implementation may proceed without one. It also keeps
text capture, current-line capture, and companion contract changes disallowed.

## Metadata-Only Extension Scope

Milestone 4L defines the exact scope for a possible inert 4M extension in:

```text
docs/bepinex-metadata-only-extension-scope.md
```

The scope fixture is:

```text
tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json
```

The 4M scope may add only safe counters and booleans, disabled by default. It does not approve
current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction,
provider calls, companion payloads, new companion endpoints, or production overlay behavior.

Milestone 4M implements that inert scope only. The metadata snapshot can now include
`metadata_snapshot_created_count`, `health_check_observed_count`, and
`synthetic_send_configured_count`, all derived from existing startup booleans and held in memory
only. The probe remains disabled by default and still does not read game state, UI text, scene or
object names, files, logs, screenshots, OCR output, or companion payloads.

Milestone 4N documents how to verify those counters manually in a local run. The verification path
uses the existing metadata probe smoke checklist and redacted workspace reports only; raw logs,
screenshots, private paths, payload dumps, and real runtime reports must not be committed.

## Current-Line Capture Research

Milestone 4E records the future capture decision in:

```text
docs/adr/0008-current-line-capture-research.md
```

The decision keeps the bridge synthetic/manual until redacted runtime smoke evidence is reviewed.
Current-line capture is not implemented. Future probes must start as metadata-only local
experiments, emitting booleans, safe counters, synthetic event ids, bridge-generated line ids, or
redacted smoke reports before any real text capture is considered.

Near-term boundaries:

- no OCR;
- no broad Unity object scanning;
- no game method patches;
- no decompiled names or method signatures committed;
- no real text capture by default;
- no committed runtime logs, screenshots, save files, private paths, OCR output, or raw companion
  payloads with real game text.

## Synthetic Event Policy

The built-in event is invented synthetic text only:

```text
The committee pinned a medal on the leaking pipe and called it infrastructure.
```

It is wrapped as:

```json
{
  "input_type": "fake_event",
  "event": {}
}
```

The exact committed safety fixture is:

```text
tests/fixtures/bepinex_bridge.provider_annotate_request.synthetic.json
```

## Safety Check

Run:

```powershell
python scripts/check_bepinex_bridge_safety.py --quiet
```

The check verifies safe defaults, synthetic fixture shape, localhost-only posture, no secret-looking
values, no external service URLs, no raw payload logging, and no hook/extraction/OCR markers in the
C# source. It also verifies local build outputs stay ignored and the optional build helper does not
download tools or become mandatory in `check_all`. Milestone 4C extends it to require the manual
smoke docs and log contract fixture.

## Not Implemented

- Real current-line detection.
- Real game text extraction.
- Decompiled game-code integration.
- OCR.
- Provider execution.
- Production overlay shell.
- Keyboard hooks.
- Clipboard writes.
- Companion HTTP contract changes.
