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
