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
- Checks `GET /health` on the local companion server.
- Can send one invented synthetic fake event to `POST /synthetic/provider-annotate`.
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

## Manual Build Posture

The repository does not currently require C# compilation in `check_all`. This environment does not
include the .NET SDK or BepInEx assemblies, and the repo must not commit proprietary game binaries or
local install files.

The package includes a minimal project file for a later local build:

```text
packages/bepinex-plugin/Revachol.UkrainianCompanion.BepInExBridge.csproj
```

It expects user-local BepInEx references supplied at build time:

```text
BepInExCoreDll=<path to BepInEx.Core.dll>
BepInExIL2CPPDll=<path to BepInEx.Unity.IL2CPP.dll>
```

Build verification is deferred to a later milestone so 4A can stay dependency-light and static.

## Manual Install Shape

When a local build exists, the resulting DLL would be copied into the user-owned BepInEx plugin
folder for their local game install:

```text
BepInEx/plugins/
```

Do not commit built DLLs, game binaries, extracted databases, screenshots, audio, or local install
paths.

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
C# source.

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
