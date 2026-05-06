# Companion Server Contract

Milestone 1E defines a small local HTTP contract for synthetic clients. It is intended for future
overlay, BepInEx bridge, and annotation pipeline clients, but it is not production networking.

Default base URL:

```text
http://127.0.0.1:8765
```

The server is offline, mock-only, and synthetic-only in this milestone. It has no auth, TLS,
persistent database, CORS policy, rate limiting, or production security hardening.

## Envelopes

JSON success responses use:

```json
{
  "ok": true,
  "data": {}
}
```

JSON error responses use:

```json
{
  "ok": false,
  "error": {
    "code": "invalid_fake_event",
    "message": "Synthetic event failed validation."
  }
}
```

Stable error codes for Milestone 1E:

- `not_found`
- `invalid_json`
- `invalid_request`
- `invalid_fake_event`
- `method_not_allowed`
- `internal_error`

## Endpoints

| Method | Path | Success | Notes |
| --- | --- | --- | --- |
| GET | `/health` | `200` JSON envelope | Server status, endpoint list, latest-state booleans. |
| GET | `/state/latest-context` | `200` JSON envelope | Latest context packet or `null`. |
| GET | `/state/latest-annotation` | `200` JSON envelope | Latest annotation card or `null`. |
| GET | `/state/latest-overlay-demo` | `200` JSON envelope | Latest overlay demo model or `null`. |
| GET | `/state/latest-eval-summary` | `200` JSON envelope | Latest synthetic eval summary or `null`. |
| GET | `/review/latest.html` | `200` raw HTML | Returns escaped review HTML after an event is posted. |
| POST | `/synthetic/event` | `200` JSON envelope | Accepts a synthetic fake game event. |
| POST | `/synthetic/eval` | `200` JSON envelope | Runs deterministic synthetic structural evals. |

Expected errors:

- Unknown routes return `404 not_found`.
- Unsupported methods return `405 method_not_allowed`.
- Invalid request JSON returns `400 invalid_json`.
- Invalid synthetic fake events return `400 invalid_fake_event`.
- `/review/latest.html` before an event is posted returns `409 invalid_request`.

## Synthetic Examples

Health request:

```text
GET /health
```

Health response shape:

```json
{
  "ok": true,
  "data": {
    "status": "ok",
    "version": "companion-server.synthetic.v1",
    "mode": {
      "offline": true,
      "mock": true,
      "synthetic_only": true
    }
  }
}
```

Synthetic event request:

```text
POST /synthetic/event
Content-Type: application/json
```

```json
{
  "event_id": "synthetic.event.contract.001",
  "synthetic_line_id": "synthetic.contract.001",
  "speaker": "Synthetic Clerk",
  "speaker_type": "npc",
  "raw_english_text": "The committee pinned a medal on the leaking pipe and called it infrastructure.",
  "scene_id": "synthetic.scene.contract-office",
  "conversation_id": "synthetic.conv.contract",
  "nearby_context": [],
  "timestamp": "2026-05-06T10:00:00Z"
}
```

Synthetic event response shape:

```json
{
  "ok": true,
  "data": {
    "context_packet": {},
    "annotation_card": {},
    "overlay_demo": {}
  }
}
```

Review response:

```text
GET /review/latest.html
```

Returns raw escaped HTML, not a JSON envelope, after `POST /synthetic/event` succeeds.

## Stability

Future clients should depend on the envelope shape, endpoint paths, HTTP methods, and stable error
codes above. Any breaking change must update this document and the server/client tests in the same
change.
