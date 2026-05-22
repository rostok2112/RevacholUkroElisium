# BepInEx Metadata-Only Probe Gate

Milestone 4G defines the safety gate for a possible future metadata-only bridge probe. It does not
implement the probe, enable current-line capture, scan Unity objects, patch game methods, run OCR,
extract data, call providers, or change the companion HTTP contract.

## Purpose

The bridge is still synthetic/manual. A later probe may be considered only after a redacted runtime
smoke report has been reviewed and marked ready for next-phase discussion. This gate describes the
small set of safe metadata that a future milestone may report before any text capture is considered.

## Readiness Prerequisites

Probe implementation work must not start until all of the following are true:

- a user-local 4F runtime smoke review exists under the ignored workspace report root;
- the review has `ready_for_next_phase = true`;
- the reviewed report has no forbidden markers;
- companion health behavior was observed;
- companion-unavailable behavior was observed, or explicitly marked not applicable with a safe
  reason;
- synthetic send was observed, or explicitly not run with a safe reason;
- a developer explicitly approves a separate probe implementation milestone.

Readiness for a metadata-only probe is not approval for current-line capture.

## Allowed Future Probe Outputs

A future metadata-only probe may emit only redacted status data such as:

- `plugin_loaded: true|false`;
- `companion_health_checked: true|false`;
- `companion_available: true|false`;
- `synthetic_event_sent: true|false`;
- `scene_probe_attempted: true|false`;
- `ui_probe_attempted: true|false`;
- `current_line_capture_enabled: false`;
- `real_text_captured: false`;
- non-negative counters;
- local timestamps only if redacted and not committed from a real run;
- bridge-generated synthetic ids;
- safe status or error codes.

Committed examples must stay synthetic-only. User-local metadata reports belong only under:

```text
workspace/synthetic-slice/bepinex-bridge/metadata-probe/
```

## Forbidden Probe Outputs

A future probe must not emit or commit:

- real dialogue text;
- UI text strings;
- screenshots;
- OCR output;
- save data;
- audio;
- runtime-sourced asset names;
- decompiled class or method names if legally risky;
- raw companion payloads containing real text;
- private paths;
- stack traces;
- full logs;
- provider request or response payloads.

## Report Contract

The committed synthetic report fixture is:

```text
tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json
```

Validate the fixture:

```powershell
python scripts/check_bepinex_metadata_probe_report.py --quiet
```

Validate an optional local redacted report:

```powershell
python scripts/check_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

The checker validates shape and rejects real text, screenshots, OCR markers, private paths, stack
traces, raw logs, payload dumps, decompiled-code markers, hook or capture claims, external URLs, and
secret-looking values.

Write a blank redacted local template:

```powershell
python scripts/write_bepinex_metadata_probe_report.py --quiet
```

Review a completed redacted local report:

```powershell
python scripts/review_bepinex_metadata_probe_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
  --quiet
```

The review summary uses `schema_version: "bepinex-bridge-metadata-probe-review.v1"` and copies only
status booleans, counters, blockers, readiness status, and no-side-effect flags. It does not copy
report notes, raw evidence, logs, screenshots, game files, companion state, or provider output.

The manual smoke checklist for enabling and disabling the probe locally is:

```text
docs/manual-smoke/bepinex-metadata-probe-smoke.md
```

## Milestone 4H Skeleton Boundary

Milestone 4H adds a disabled-by-default C# metadata probe skeleton. It is not current-line capture
and it does not inspect runtime text or game objects. The skeleton may only build a startup metadata
snapshot with safe booleans and zero/default counters.

The two probe config defaults must remain:

```text
MetadataProbeEnabled = false
MetadataProbeLogOnStart = false
```

When both are manually enabled, the bridge may log one metadata-only startup summary. That summary
must still keep `current_line_capture_enabled = false` and `real_text_captured = false`. Enabling the
probe does not approve future text capture or broader runtime observation.

## Milestone 4I Manual Verification Boundary

Milestone 4I adds only a manual smoke checklist and a workspace-only template writer. It does not add
a metadata report reviewer yet, does not read local logs, does not parse game output, does not call
the companion server, and does not inspect game files or screenshots.

The local workflow is:

1. Enable `MetadataProbeEnabled = true` and `MetadataProbeLogOnStart = true` in the user-local
   BepInEx config.
2. Observe only the safe metadata summary described in
   `docs/manual-smoke/bepinex-metadata-probe-smoke.md`.
3. Record only redacted booleans and counters in a local report under
   `workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.
4. Validate the report with `scripts/check_bepinex_metadata_probe_report.py`.
5. Restore both metadata probe config flags to false.

The template writer is `scripts/write_bepinex_metadata_probe_report.py`. Passing the checker still
does not approve current-line capture, text capture, hooks, OCR, extraction, provider execution, or
new companion endpoints.

## Milestone 4J Review Boundary

Milestone 4J adds `scripts/review_bepinex_metadata_probe_report.py`, a redacted readiness helper for
local metadata probe reports. `readiness_status = "ready"` means only that the report is complete
enough to discuss a later metadata-only extension. It does not approve current-line capture, UI text
reading, real text capture, hooks, OCR, extraction, provider execution, or companion contract
changes.

The reviewer is deterministic:

- `pass` report status is required;
- metadata-only and capture-disabled flags must remain safe;
- the probe must be enabled, attempted, and completed;
- `ui_probe_attempted` and `scene_probe_attempted` must remain false;
- unsafe markers fail during report validation before review output is generated.

Review artifacts, if written, belong only under:

```text
workspace/synthetic-slice/bepinex-bridge/metadata-probe/review/
```

## Milestone 4K Extension Decision Gate

Milestone 4K records the metadata-only extension decision in:

```text
docs/adr/0009-metadata-only-extension-gate.md
```

The current decision is `ready_for_metadata_only_extension_discussion`, not implementation. A later
extension may be scoped in docs, but runtime expansion remains blocked until a ready local metadata
probe review exists or a documented no-review exception is explicitly approved.

The committed gate fixture is:

```text
tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json
```

The fixture keeps:

```text
implementation_allowed=false
text_capture_allowed=false
current_line_capture_allowed=false
companion_contract_change_allowed=false
```

Even a future `ready_for_metadata_only_extension_implementation` state must not approve current-line
capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider
execution, companion HTTP contract changes, or production overlay work.

## Milestone 4L Metadata-Only Extension Scope

Milestone 4L defines the exact allowed scope for a possible 4M implementation in:

```text
docs/bepinex-metadata-only-extension-scope.md
```

The committed scope fixture is:

```text
tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json
```

4L does not implement runtime behavior. It allows planning 4M without a reviewed local metadata
probe report only because the allowed 4M scope is inert, disabled by default, and limited to safe
counters and booleans. The fixture may set `implementation_allowed_next=true`, but it must keep text
capture, current-line capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider
calls, and companion contract changes false.

## Milestone 4M Inert Metadata Extension

Milestone 4M implements only the 4L-approved inert metadata snapshot fields. The disabled probe can
now include local in-memory counters for `metadata_snapshot_created_count`,
`health_check_observed_count`, and `synthetic_send_configured_count` when a user manually enables
metadata probe logging.

The 4M extension still does not read runtime text, inspect game or UI state, call companion
endpoints, create metadata payloads, add hooks, run OCR, extract data, or approve current-line
capture. The defaults remain:

```text
MetadataProbeEnabled = false
MetadataProbeLogOnStart = false
```

## Milestone 4N Manual Counter Verification

Milestone 4N aligns the manual metadata probe smoke workflow with the 4M counters. A local user may
enable the disabled probe, observe a single safe startup snapshot, and summarize only these counter
values in a redacted workspace report:

```text
metadata_snapshot_created_count
health_check_observed_count
synthetic_send_configured_count
```

The report checker and reviewer keep those counters as metadata-only evidence. They still reject
capture flags set to true, raw logs, screenshots, private paths, stack traces, payload dumps, real
game text, OCR output, hooks, extraction markers, provider calls, and companion contract changes.

## Companion-Connected Synthetic Smoke Prep

After the redacted local metadata-probe smoke, the next local preparation step may run the existing
localhost companion server and use the same helper to toggle the already-defined
`SendSyntheticEventOnStart` config key. This is still synthetic/manual only.

Use:

```text
scripts/run_bepinex_metadata_probe_local_smoke.py
--enable-synthetic-send
--disable-synthetic-send
```

The helper may summarize only bridge-owned companion health and synthetic provider send markers as
redacted booleans. It must not add C# behavior, call real providers, change companion endpoints,
print raw logs, parse dialogue, or treat synthetic send success as current-line capture.
