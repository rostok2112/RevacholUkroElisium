# BepInEx Bridge Runtime Smoke

Milestone 4C makes manual runtime verification repeatable. This checklist is synthetic/manual only.
It must not be used to capture real game text, scan Unity objects, run OCR, extract data, or commit
local logs.

The machine-readable safe log contract is:

```text
tests/fixtures/bepinex_bridge.log_contract.synthetic.json
```

The redacted smoke report contract is:

```text
tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json
```

Validate the report shape with:

```powershell
python scripts/check_bepinex_runtime_smoke_report.py --quiet
```

The report workflow is documented in:

```text
docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md
```

## Prerequisites

- A user-owned local game install with BepInEx IL2CPP installed.
- Local `.NET` SDK and BepInEx reference DLLs if rebuilding the bridge.
- Revachol Ukrainian Companion repository checkout.
- No real provider credentials or external services.

## Start Companion Server

From the repository root:

```powershell
python scripts/run_companion_server.py
```

The default bridge URL is:

```text
http://127.0.0.1:8765
```

## Optional Build

Build only with user-local BepInEx references:

```powershell
python scripts/build_bepinex_bridge.py `
  --core-dll <path-to-BepInEx.Core.dll> `
  --il2cpp-dll <path-to-BepInEx.Unity.IL2CPP.dll> `
  --output workspace/synthetic-slice/bepinex-bridge/build-report.json
```

`MSB3277` assembly-version warnings may appear. For Milestone 4C they are acceptable when the build
succeeds and `python scripts/check_bepinex_bridge_safety.py --quiet` passes. Do not hide warnings;
keep the local build report under ignored `workspace/`.

## Install DLL

Copy the built DLL from the ignored build output:

```text
packages/bepinex-plugin/bin/Debug/netstandard2.1/Revachol.UkrainianCompanion.BepInExBridge.dll
```

to the user-owned local plugin folder:

```text
BepInEx/plugins/
```

Do not commit the copied DLL, BepInEx logs, game logs, or local install paths.

## Launch And Observe

Launch the game from the user-owned local install.

Expected startup log signal:

```text
loaded in synthetic/manual bridge mode
```

If `Enabled = false`, expected log signal:

```text
Bridge disabled by config. No companion requests will be sent.
```

If companion is available, expected health log signal:

```text
Companion health check passed: status=
```

If companion is unavailable, expected warning signal:

```text
Companion unavailable during bridge startup. Game continues without companion data.
```

The game should continue in both cases.

## Optional Synthetic Send

Synthetic sending is disabled by default:

```text
SendSyntheticEventOnStart = false
```

For a manual smoke only, set it to true in local BepInEx config:

```text
SendSyntheticEventOnStart = true
```

Expected accepted synthetic-send log signal:

```text
Synthetic provider event sent: event_id=synthetic.event.bepinex.4a.001, line_id=synthetic.bepinex.4a.001, status=
```

Expected rejected synthetic-send warning signal:

```text
Synthetic provider event was not accepted: event_id=synthetic.event.bepinex.4a.001, line_id=synthetic.bepinex.4a.001, status=
```

On the companion server, verify that a synthetic provider event was received by checking the server
console or by querying latest provider state with existing local companion client commands. Do not
paste or commit local runtime logs. If you record the result, use only a redacted report under:

```text
workspace/synthetic-slice/bepinex-bridge/runtime-smoke/
```

## Cleanup

1. Set `SendSyntheticEventOnStart = false`.
2. Remove the bridge DLL from the local `BepInEx/plugins/` folder if the smoke is complete.
3. Stop the companion server.
4. Leave generated build reports and outputs under ignored `workspace/`, `bin/`, or `obj/`.
5. Keep any redacted smoke report under ignored `workspace/`; do not commit it.

## Safety Boundaries

This smoke does not validate real current-line detection, game hooks, Unity object scanning, OCR,
extraction, provider execution, overlay shell behavior, keyboard hooks, clipboard writes, or
companion HTTP contract changes.
