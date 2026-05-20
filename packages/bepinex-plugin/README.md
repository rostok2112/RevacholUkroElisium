# bepinex-plugin

Milestone 4A C# BepInEx bridge skeleton for Revachol Ukrainian Companion.

## Current status

This package is static-reviewable skeleton code. It is not wired into a real game install by the
repo checks, and it is not a production mod.

What exists:

- BepInEx plugin metadata and safe startup logging.
- Config entries for enabling the bridge, companion URL, timeout, and synthetic send-on-start.
- Localhost-only companion `/health` check.
- Manual/synthetic fake-event send to `POST /synthetic/provider-annotate`.
- Metadata-only logs for event id, line id, status, and unavailable companion states.

What does not exist:

- No real dialogue detection.
- No game hooks or Unity object scanning.
- No text extraction, OCR, or decompiled game-code integration.
- No production overlay, keyboard hooks, clipboard behavior, or provider execution.

## Manual build posture

`Revachol.UkrainianCompanion.BepInExBridge.csproj` is intentionally minimal. It expects local
BepInEx assemblies supplied by the user through MSBuild properties:

```text
BepInExCoreDll=<path to BepInEx.Core.dll>
BepInExIL2CPPDll=<path to BepInEx.Unity.IL2CPP.dll>
```

The repository checks do not require `dotnet build`, the .NET SDK, or BepInEx binaries. Milestone 4A
is covered by Python static safety checks until a later milestone adds build verification.

## Local companion defaults

Default companion URL:

```text
http://127.0.0.1:8765
```

The skeleton skips requests if the configured URL is not localhost. If the companion server is not
available, the plugin logs a concise warning and the game continues without companion data.
