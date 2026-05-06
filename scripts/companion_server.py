from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any
from urllib.parse import urlparse

try:
    from scripts.provider_pipeline import ProviderPipelineError, run_provider_pipeline
    from scripts.schema_validator import SchemaValidationError, assert_valid, load_json
    from scripts.synthetic_eval import run_synthetic_eval
    from scripts.synthetic_review_renderer import render_review_html
    from scripts.synthetic_slice import (
        CONTEXT_PACKET_SCHEMA,
        build_context_packet,
        run_synthetic_slice,
    )
except ModuleNotFoundError:  # pragma: no cover - used when run as a script dependency.
    from provider_pipeline import ProviderPipelineError, run_provider_pipeline
    from schema_validator import SchemaValidationError, assert_valid, load_json
    from synthetic_eval import run_synthetic_eval
    from synthetic_review_renderer import render_review_html
    from synthetic_slice import CONTEXT_PACKET_SCHEMA, build_context_packet, run_synthetic_slice


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SERVER_VERSION = "companion-server.synthetic.v1"
MAX_JSON_BODY_BYTES = 1_000_000

ENDPOINTS = [
    "GET /health",
    "GET /state/latest-context",
    "GET /state/latest-annotation",
    "GET /state/latest-overlay-demo",
    "GET /state/latest-eval-summary",
    "GET /state/latest-provider-context",
    "GET /state/latest-provider-annotation",
    "GET /review/latest.html",
    "POST /synthetic/event",
    "POST /synthetic/eval",
    "POST /synthetic/provider-annotate",
]

STABLE_ERROR_CODES = [
    "not_found",
    "invalid_json",
    "invalid_request",
    "invalid_fake_event",
    "method_not_allowed",
    "internal_error",
]


@dataclass
class CompanionState:
    latest_slice_result: dict[str, Any] | None = None
    latest_eval_summary: dict[str, Any] | None = None
    latest_provider_context_packet: dict[str, Any] | None = None
    latest_provider_annotation_card: dict[str, Any] | None = None

    def latest_context_packet(self) -> dict[str, Any] | None:
        if self.latest_slice_result is None:
            return None
        return self.latest_slice_result["context_packet"]

    def latest_annotation_card(self) -> dict[str, Any] | None:
        if self.latest_slice_result is None:
            return None
        return self.latest_slice_result["annotation_card"]

    def latest_overlay_demo(self) -> dict[str, Any] | None:
        if self.latest_slice_result is None:
            return None
        return self.latest_slice_result["overlay_demo"]

    def latest_provider_context(self) -> dict[str, Any] | None:
        return self.latest_provider_context_packet

    def latest_provider_annotation(self) -> dict[str, Any] | None:
        return self.latest_provider_annotation_card


def make_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    state: CompanionState | None = None,
) -> ThreadingHTTPServer:
    companion_state = state or CompanionState()
    server = ThreadingHTTPServer((host, port), make_handler(companion_state))
    server.companion_state = companion_state  # type: ignore[attr-defined]
    return server


def make_handler(state: CompanionState) -> type[BaseHTTPRequestHandler]:
    class CompanionRequestHandler(BaseHTTPRequestHandler):
        server_version = "RevacholCompanionSynthetic/0.1"
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            self._dispatch_safely(self._handle_get)

        def do_POST(self) -> None:
            self._dispatch_safely(self._handle_post)

        def do_HEAD(self) -> None:
            self._handle_method_not_allowed()

        def do_PUT(self) -> None:
            self._handle_method_not_allowed()

        def do_PATCH(self) -> None:
            self._handle_method_not_allowed()

        def do_DELETE(self) -> None:
            self._handle_method_not_allowed()

        def do_OPTIONS(self) -> None:
            self._handle_method_not_allowed()

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _handle_get(self) -> None:
            path = urlparse(self.path).path

            if path == "/health":
                self._send_json(200, _ok(_health_payload(state)))
            elif path == "/state/latest-context":
                self._send_json(200, _ok(state.latest_context_packet()))
            elif path == "/state/latest-annotation":
                self._send_json(200, _ok(state.latest_annotation_card()))
            elif path == "/state/latest-overlay-demo":
                self._send_json(200, _ok(state.latest_overlay_demo()))
            elif path == "/state/latest-eval-summary":
                self._send_json(200, _ok(state.latest_eval_summary))
            elif path == "/state/latest-provider-context":
                self._send_json(200, _ok(state.latest_provider_context()))
            elif path == "/state/latest-provider-annotation":
                self._send_json(200, _ok(state.latest_provider_annotation()))
            elif path == "/review/latest.html":
                self._handle_latest_review()
            else:
                self._send_error_json(404, "not_found", f"Unknown endpoint: {path}")

        def _handle_post(self) -> None:
            path = urlparse(self.path).path

            if path == "/synthetic/event":
                self._handle_synthetic_event()
            elif path == "/synthetic/eval":
                self._handle_synthetic_eval()
            elif path == "/synthetic/provider-annotate":
                self._handle_provider_annotate()
            else:
                self._send_error_json(404, "not_found", f"Unknown endpoint: {path}")

        def _handle_synthetic_event(self) -> None:
            try:
                event = self._read_json_body()
            except _InvalidJson as exc:
                self._send_error_json(400, "invalid_json", str(exc))
                return

            if not isinstance(event, dict):
                self._send_error_json(
                    400, "invalid_fake_event", "Synthetic event must be a JSON object."
                )
                return

            try:
                result = run_synthetic_slice(event)
            except SchemaValidationError as exc:
                self._send_error_json(400, "invalid_fake_event", str(exc))
                return

            state.latest_slice_result = result
            self._send_json(
                200,
                _ok(
                    {
                        "context_packet": result["context_packet"],
                        "annotation_card": result["annotation_card"],
                        "overlay_demo": result["overlay_demo"],
                    }
                ),
            )

        def _handle_synthetic_eval(self) -> None:
            summary = run_synthetic_eval()
            state.latest_eval_summary = summary
            self._send_json(200, _ok(summary))

        def _handle_provider_annotate(self) -> None:
            try:
                payload = self._read_json_body()
            except _InvalidJson as exc:
                self._send_error_json(400, "invalid_json", str(exc))
                return

            if not isinstance(payload, dict):
                self._send_error_json(
                    400,
                    "invalid_request",
                    "Provider annotation request must be a JSON object.",
                )
                return

            input_type = payload.get("input_type")
            if input_type is None:
                self._send_error_json(
                    400,
                    "invalid_request",
                    "Provider annotation request requires input_type.",
                )
                return
            if input_type == "fake_event":
                context_packet = self._context_from_fake_event_payload(payload)
            elif input_type == "context_packet":
                context_packet = self._context_from_context_packet_payload(payload)
            else:
                self._send_error_json(
                    400,
                    "invalid_request",
                    "input_type must be 'fake_event' or 'context_packet'.",
                )
                return

            if context_packet is None:
                return

            try:
                annotation_card = run_provider_pipeline(context_packet, provider_name="mock")
            except (ProviderPipelineError, SchemaValidationError) as exc:
                self._send_error_json(400, "invalid_request", str(exc))
                return

            state.latest_provider_context_packet = context_packet
            state.latest_provider_annotation_card = annotation_card
            self._send_json(
                200,
                _ok(
                    {
                        "context_packet": context_packet,
                        "annotation_card": annotation_card,
                    }
                ),
            )

        def _context_from_fake_event_payload(
            self, payload: dict[str, Any]
        ) -> dict[str, Any] | None:
            event = payload.get("event")
            if not isinstance(event, dict):
                self._send_error_json(
                    400,
                    "invalid_request",
                    "event must be a JSON object when input_type is 'fake_event'.",
                )
                return None
            try:
                return build_context_packet(event)
            except SchemaValidationError as exc:
                self._send_error_json(400, "invalid_fake_event", str(exc))
                return None

        def _context_from_context_packet_payload(
            self, payload: dict[str, Any]
        ) -> dict[str, Any] | None:
            context_packet = payload.get("context_packet")
            if not isinstance(context_packet, dict):
                self._send_error_json(
                    400,
                    "invalid_request",
                    "context_packet must be a JSON object when input_type is 'context_packet'.",
                )
                return None
            try:
                assert_valid(context_packet, load_json(CONTEXT_PACKET_SCHEMA))
            except SchemaValidationError as exc:
                self._send_error_json(400, "invalid_request", str(exc))
                return None
            return context_packet

        def _handle_latest_review(self) -> None:
            if state.latest_slice_result is None:
                self._send_error_json(
                    409,
                    "invalid_request",
                    "No latest synthetic overlay demo is available. POST /synthetic/event first.",
                )
                return

            html = render_review_html(state.latest_slice_result)
            self._send_text(200, html, "text/html; charset=utf-8")

        def _handle_method_not_allowed(self) -> None:
            self.send_response(405)
            self.send_header("Allow", "GET, POST")
            payload = json.dumps(
                _error("method_not_allowed", f"Method {self.command} is not allowed."),
                ensure_ascii=False,
                indent=2,
            )
            body = (payload + "\n").encode("utf-8")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _dispatch_safely(self, handler: Any) -> None:
            try:
                handler()
            except Exception:
                self._send_error_json(500, "internal_error", "Internal server error.")

        def _read_json_body(self) -> Any:
            content_length_raw = self.headers.get("Content-Length", "0")
            try:
                content_length = int(content_length_raw)
            except ValueError as exc:
                raise _InvalidJson("Content-Length must be an integer.") from exc

            if content_length < 1:
                raise _InvalidJson("Request body must contain JSON.")
            if content_length > MAX_JSON_BODY_BYTES:
                raise _InvalidJson(f"JSON body exceeds {MAX_JSON_BODY_BYTES} bytes.")

            body = self.rfile.read(content_length)
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise _InvalidJson("Request body must be UTF-8 JSON.") from exc

            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                raise _InvalidJson(
                    f"Invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}."
                ) from exc

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            self._send_text(status, rendered, "application/json; charset=utf-8")

        def _send_error_json(self, status: int, code: str, message: str) -> None:
            self._send_json(status, _error(code, message))

        def _send_text(self, status: int, text: str, content_type: str) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return CompanionRequestHandler


def _health_payload(state: CompanionState) -> dict[str, Any]:
    return {
        "status": "ok",
        "version": SERVER_VERSION,
        "schema_version": "companion-server-health.v1",
        "mode": {
            "offline": True,
            "mock": True,
            "synthetic_only": True,
            "external_services": False,
            "requires_api_keys": False,
        },
        "binding": {
            "default_host": DEFAULT_HOST,
            "localhost_only_by_default": True,
            "note": (
                "Milestone 1D binds to 127.0.0.1 by default; "
                "other hosts require explicit CLI input."
            ),
        },
        "latest_state": {
            "has_latest_context": state.latest_context_packet() is not None,
            "has_latest_annotation": state.latest_annotation_card() is not None,
            "has_latest_overlay_demo": state.latest_overlay_demo() is not None,
            "has_latest_eval_summary": state.latest_eval_summary is not None,
            "has_latest_provider_context": state.latest_provider_context() is not None,
            "has_latest_provider_annotation": state.latest_provider_annotation() is not None,
        },
        "endpoints": ENDPOINTS,
        "stable_error_codes": STABLE_ERROR_CODES,
    }


def _ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _error(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


class _InvalidJson(ValueError):
    pass
