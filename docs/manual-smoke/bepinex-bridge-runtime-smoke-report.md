# BepInEx Bridge Runtime Smoke Report

Milestone 4D defines a redacted report shape for user-local manual bridge smoke results.

This report is a summary, not a log archive. Do not paste or commit BepInEx logs, game logs,
screenshots, stack traces, full request or response payloads, private paths, secrets, or real game
text.

## Committed Synthetic Fixture

The committed fixture is synthetic and shows the allowed shape:

```text
tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json
```

It is intentionally marked `smoke_status = "not_run"` because it is not evidence from a real local
runtime run.

## Local Report Path

Local manual reports must stay under the ignored workspace root:

```text
workspace/synthetic-slice/bepinex-bridge/runtime-smoke/
```

Validate the committed fixture:

```powershell
python scripts/check_bepinex_runtime_smoke_report.py --quiet
```

Validate a local redacted report:

```powershell
python scripts/check_bepinex_runtime_smoke_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/runtime-smoke/report.json `
  --quiet
```

Optionally write a blank local template:

```powershell
python scripts/write_bepinex_runtime_smoke_report.py --quiet
```

The template writer does not inspect game logs, BepInEx logs, companion responses, private paths, or
runtime files.

Review a completed redacted report:

```powershell
python scripts/review_bepinex_runtime_smoke_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/runtime-smoke/report.json
```

Optionally write redacted review artifacts:

```powershell
python scripts/review_bepinex_runtime_smoke_report.py `
  --report workspace/synthetic-slice/bepinex-bridge/runtime-smoke/report.json `
  --output workspace/synthetic-slice/bepinex-bridge/runtime-smoke/review/summary.json `
  --markdown-output workspace/synthetic-slice/bepinex-bridge/runtime-smoke/review/summary.md
```

The review helper does not read BepInEx logs, game logs, screenshots, game files, companion state,
or provider outputs.

## Allowed Fields

Reports may summarize:

- `smoke_status`: `pass`, `fail`, `partial`, or `not_run`;
- plugin id and bridge version;
- build attempted/succeeded booleans;
- plugin loaded observation;
- companion health observation;
- companion available/unavailable observation;
- synthetic send enabled/observed booleans;
- companion received synthetic event boolean;
- game continued when companion unavailable boolean;
- warning counts and MSB3277 warning counts;
- optional `blockers`;
- optional `next_step_notes`;
- optional `synthetic_send_not_run_reason`;
- optional `unavailable_case_not_run_reason`;
- `evidence_summary_redacted: true`;
- short redacted notes;
- short evidence summary with safe metadata only;
- `created_by_user_manually: true`.

## Review Readiness

`ready_for_next_phase = true` means the redacted report is complete enough to discuss a later
metadata-only probe. It does not approve current-line capture.

Readiness requires:

- report validation passes;
- report status is `pass`;
- plugin load and health check were observed;
- companion available or unavailable behavior was observed;
- unavailable companion behavior either kept the game running or was explicitly not applicable;
- synthetic send was observed or explicitly not run with a safe reason.

`partial`, `fail`, and `not_run` reports are valid report shapes but not ready for next-phase
planning.

## Metadata Probe Gate

After a report review is ready, the next boundary is still a metadata-only gate:

```text
docs/bepinex-metadata-probe-gate.md
```

That gate does not approve current-line capture. It only defines the safe shape for a possible
future disabled-by-default metadata probe report. Real text, hooks, Unity text scanning, OCR,
extraction, raw payloads, screenshots, and committed runtime logs remain forbidden.

## Forbidden Content

Reports must not include:

- raw BepInEx or game logs;
- stack traces;
- full request or response payloads;
- raw source text;
- private absolute paths;
- screenshots, audio, image, asset, or bundle names;
- real game dialogue or proprietary content;
- hook, OCR, extraction, or decompiled-code details;
- provider execution details;
- non-localhost URLs;
- secrets or token-shaped values.

## Review Guidance

A good report says things like:

```text
Plugin startup was observed. Health returned status 200. Synthetic send stayed disabled.
```

It does not paste the runtime log lines themselves. Keep the repo evidence boring and metadata-only;
the real logs stay on the user's machine.
