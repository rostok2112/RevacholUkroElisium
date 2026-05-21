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
