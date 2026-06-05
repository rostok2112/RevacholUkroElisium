# BepInEx Metadata-Only Extension Scope

Milestone 4L defines the exact scope for a possible Milestone 4M metadata-only C# extension. 4L is
docs/static-contract work only. It does not implement runtime behavior, current-line capture, real
text capture, UI text reading, Unity scanning, hooks, OCR, extraction, companion endpoints, provider
calls, shell work, or new dependencies.

Milestone 4M implements only this inert scope: local in-memory counters and booleans in the disabled
metadata probe snapshot. It does not expand the companion contract, read runtime/game data, capture
text, or enable UI or scene probes.

## Decision

Milestone 4M may be planned without a reviewed local metadata probe report because the allowed
extension is inert, disabled by default, and no-capture. This waiver applies only to the minimal
scope in this document. It does not approve broader probes, UI or scene observation, current-line
capture, text capture, companion contract changes, or provider calls.

4M must still:

- keep implementation disabled by default;
- update bridge safety checks before or with implementation;
- prove capture flags remain false in tests;
- avoid companion HTTP contract changes;
- avoid text capture, hooks, scanning, OCR, extraction, and game-file reads.

## Allowed 4M Behavior

A later 4M implementation may only add inert metadata state inside the existing bridge process:

- increment safe counters;
- record plugin lifecycle booleans;
- record companion health booleans;
- record synthetic event send booleans;
- record metadata probe attempted and completed booleans;
- keep `real_text_captured=false`;
- keep `current_line_capture_enabled=false`;
- keep `ui_probe_attempted=false` unless a later milestone separately approves it;
- keep `scene_probe_attempted=false` unless a later milestone separately approves it;
- optionally write one safe metadata snapshot to logs when manually enabled.

Allowed metadata fields are listed in:

```text
tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json
```

The 4M implementation adds only these inert counter fields to the safe metadata snapshot/report
shape:

- `metadata_snapshot_created_count`;
- `health_check_observed_count`;
- `synthetic_send_configured_count`.

Those counters are derived from existing startup booleans, stay in memory only, and are logged only
when the disabled metadata probe is manually enabled with `MetadataProbeLogOnStart=true`.

Milestone 4N documents the manual verification workflow for those counters. Verification remains
local and redacted: users may summarize the observed counter values in a workspace-only metadata
probe report, but must not commit raw BepInEx logs, game logs, screenshots, private paths, payload
dumps, or real runtime reports.

The local preparation helper for that real in-game smoke is:

```text
scripts/run_bepinex_metadata_probe_local_smoke.py
```

It may discover the user-owned Steam install, copy the built bridge DLL to `BepInEx/plugins/`, set
the two metadata probe config flags, optionally toggle the existing `SendSyntheticEventOnStart`
flag for companion-connected synthetic smoke, and toggle the runtime-first synthetic transport flags
for the capture spike. It may read only `BepInEx/LogOutput.log` after the user manually runs the
game and write a redacted metadata probe report under the ignored workspace. Use
`--enable-synthetic-send`, `--disable-synthetic-send`,
`--enable-runtime-current-line-transport`, `--disable-runtime-current-line-transport`,
`--enable-synthetic-runtime-send`, and `--disable-synthetic-runtime-send` only for invented
synthetic paths. It must not launch the game, recursively scan drives, parse dialogue, store raw
logs, read arbitrary game files, call providers, or add capture hooks.

## Forbidden 4M Behavior

The 4M implementation must not:

- read UI text;
- detect current dialogue or current line;
- scan Unity objects;
- read scene or object names from runtime;
- add Harmony patches;
- add game hooks;
- run OCR;
- capture screenshots;
- extract data;
- read save files;
- parse game logs;
- read game files;
- send metadata probe payloads to the companion;
- add companion endpoints;
- call providers;
- log raw payloads;
- log private paths;
- collect or log real text.

## Required Implementation Tests

Milestone 4M must include tests proving:

- metadata extension defaults are disabled;
- all capture flags remain false;
- UI and scene probe flags remain false;
- counters are safe non-negative integers;
- no companion payload or endpoint is added;
- no provider call path is added;
- C# source remains free of hook, scanning, OCR, extraction, and raw-payload logging markers;
- bridge safety checker validates the new runtime source.

## Boundary

This scope contract allows only a later inert metadata implementation. It does not move the project
to current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction,
provider execution, companion HTTP contract changes, or production overlay work.
