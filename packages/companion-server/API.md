# Companion Server API

## WebSocket: `/ws/game-events`

Receives events from game bridge.

```json
{
  "type": "DialogueLineSeen",
  "line_id": "local-line-id",
  "source_text": "Current English line",
  "speaker": "Speaker",
  "conversation_id": "conversation",
  "location": "location",
  "timestamp_ms": 123456
}
```

## HTTP: `POST /v1/annotate-current-line`

Input: `ContextPacket`

Output: `AnnotationCard`

## HTTP: `GET /v1/line/:line_id`

Returns local metadata for a line if imported.

## HTTP: `POST /v1/review`

Stores human correction, rating, or glossary update.

## HTTP: `POST /runtime/current-line`

Receives one local/private runtime current-line event from the BepInEx bridge or a manual synthetic
smoke helper.

```json
{
  "schema_version": "runtime-current-line-event.v1",
  "event_kind": "current_line",
  "line_id": "optional-stable-id",
  "source_text": "private runtime text",
  "speaker": "optional speaker",
  "conversation_id": "optional conversation",
  "source": "bepinex_runtime"
}
```

The server stores the latest event in memory only, checks runtime translation memory, and returns a
receipt with redacted cache status. It does not call providers.

## HTTP: `GET /state/latest-runtime-current-line`

Returns the latest in-memory runtime current-line event for local smoke tests and runtime debugging.
This endpoint is local/private and must not be used to create tracked reports containing runtime
text.
