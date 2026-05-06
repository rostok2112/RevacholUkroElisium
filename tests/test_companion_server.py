from __future__ import annotations

from contextlib import AbstractContextManager
import json
from pathlib import Path
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest

from scripts.companion_server import DEFAULT_HOST, CompanionState, make_server
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
INVALID_EVENT = ROOT / "tests/fixtures/fake_game_event.invalid.synthetic.json"


class CompanionServerTests(unittest.TestCase):
    def test_health_reports_offline_mock_local_contract(self) -> None:
        with ServerHarness() as server:
            status, headers, payload = server.get_json("/health")

        self.assertEqual(200, status)
        self.assertTrue(payload["ok"])
        data = payload["data"]
        self.assertEqual("ok", data["status"])
        self.assertIn("invalid_fake_event", data["stable_error_codes"])
        self.assertIn("method_not_allowed", data["stable_error_codes"])
        self.assertTrue(data["mode"]["offline"])
        self.assertTrue(data["mode"]["mock"])
        self.assertTrue(data["mode"]["synthetic_only"])
        self.assertFalse(data["mode"]["external_services"])
        self.assertEqual(DEFAULT_HOST, data["binding"]["default_host"])
        self.assertFalse(data["latest_state"]["has_latest_context"])
        self.assertIn("GET /health", data["endpoints"])
        self.assertIn("application/json", headers["Content-Type"])

    def test_valid_synthetic_event_returns_slice_outputs(self) -> None:
        event = load_json(VALID_EVENT)

        with ServerHarness() as server:
            status, _headers, payload = server.post_json("/synthetic/event", event)

        self.assertEqual(200, status)
        self.assertTrue(payload["ok"])
        data = payload["data"]
        self.assertEqual(
            event["raw_english_text"], data["context_packet"]["current_line"]["source_text"]
        )
        self.assertEqual(event["raw_english_text"], data["annotation_card"]["original_english"])
        self.assertEqual(
            event["raw_english_text"], data["overlay_demo"]["source"]["original_english"]
        )

    def test_invalid_json_is_clear_error(self) -> None:
        with ServerHarness() as server:
            status, _headers, payload = server.post_raw("/synthetic/event", b"{bad json")

        self.assertEqual(400, status)
        self.assertFalse(payload["ok"])
        self.assertEqual("invalid_json", payload["error"]["code"])
        self.assertIn("Invalid JSON", payload["error"]["message"])

    def test_invalid_fake_event_is_clear_error(self) -> None:
        with ServerHarness() as server:
            status, _headers, payload = server.post_json(
                "/synthetic/event", load_json(INVALID_EVENT)
            )

        self.assertEqual(400, status)
        self.assertFalse(payload["ok"])
        self.assertEqual("invalid_fake_event", payload["error"]["code"])
        self.assertIn("missing required property", payload["error"]["message"])

    def test_latest_context_annotation_and_overlay_after_event(self) -> None:
        event = load_json(VALID_EVENT)

        with ServerHarness() as server:
            server.post_json("/synthetic/event", event)
            context_status, _headers, context = server.get_json("/state/latest-context")
            annotation_status, _headers, annotation = server.get_json("/state/latest-annotation")
            overlay_status, _headers, overlay = server.get_json("/state/latest-overlay-demo")

        self.assertEqual(200, context_status)
        self.assertEqual(event["raw_english_text"], context["data"]["current_line"]["source_text"])
        self.assertEqual(200, annotation_status)
        self.assertEqual(event["raw_english_text"], annotation["data"]["original_english"])
        self.assertEqual(200, overlay_status)
        self.assertEqual(event["raw_english_text"], overlay["data"]["source"]["original_english"])

    def test_latest_state_endpoints_return_null_before_event(self) -> None:
        with ServerHarness() as server:
            context_status, _headers, context = server.get_json("/state/latest-context")
            annotation_status, _headers, annotation = server.get_json("/state/latest-annotation")
            overlay_status, _headers, overlay = server.get_json("/state/latest-overlay-demo")

        self.assertEqual(200, context_status)
        self.assertIsNone(context["data"])
        self.assertEqual(200, annotation_status)
        self.assertIsNone(annotation["data"])
        self.assertEqual(200, overlay_status)
        self.assertIsNone(overlay["data"])

    def test_synthetic_eval_post_and_latest_eval_summary(self) -> None:
        with ServerHarness() as server:
            status, _headers, payload = server.post_json("/synthetic/eval", {})
            latest_status, _headers, latest = server.get_json("/state/latest-eval-summary")

        self.assertEqual(200, status)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["data"]["passed"])
        self.assertGreaterEqual(payload["data"]["case_count"], 6)
        self.assertEqual(200, latest_status)
        self.assertEqual(payload["data"], latest["data"])

    def test_review_latest_returns_json_404_before_event(self) -> None:
        with ServerHarness() as server:
            status, headers, payload = server.get_json("/review/latest.html")

        self.assertEqual(409, status)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertFalse(payload["ok"])
        self.assertEqual("invalid_request", payload["error"]["code"])

    def test_review_latest_returns_html_after_event(self) -> None:
        event = load_json(VALID_EVENT)

        with ServerHarness() as server:
            server.post_json("/synthetic/event", event)
            status, headers, body = server.get_text("/review/latest.html")

        self.assertEqual(200, status)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn("Revachol Synthetic Review", body)
        self.assertIn(event["raw_english_text"], body)
        self.assertIn("Compact Mode", body)

    def test_unknown_route_returns_standard_error_envelope(self) -> None:
        with ServerHarness() as server:
            status, _headers, payload = server.get_json("/missing")

        self.assertEqual(404, status)
        self.assertFalse(payload["ok"])
        self.assertEqual("not_found", payload["error"]["code"])

    def test_method_not_allowed_returns_standard_error_envelope(self) -> None:
        with ServerHarness() as server:
            status, headers, body = server.request("PUT", "/health")

        payload = json.loads(body)
        self.assertEqual(405, status)
        self.assertIn("GET, POST", headers["Allow"])
        self.assertFalse(payload["ok"])
        self.assertEqual("method_not_allowed", payload["error"]["code"])

    def test_tests_bind_only_to_localhost(self) -> None:
        with ServerHarness() as server:
            self.assertEqual(DEFAULT_HOST, server.host)
            status, _headers, payload = server.get_json("/health")

        self.assertEqual(200, status)
        self.assertFalse(payload["data"]["mode"]["external_services"])
        self.assertFalse(payload["data"]["mode"]["requires_api_keys"])


class ServerHarness(AbstractContextManager["ServerHarness"]):
    def __init__(self) -> None:
        self.state = CompanionState()
        self.server = make_server(DEFAULT_HOST, 0, self.state)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "ServerHarness":
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def get_json(self, path: str) -> tuple[int, dict[str, str], dict[str, Any]]:
        status, headers, text = self.get_text(path)
        return status, headers, json.loads(text)

    def get_text(self, path: str) -> tuple[int, dict[str, str], str]:
        return self._request(path, method="GET")

    def request(self, method: str, path: str) -> tuple[int, dict[str, str], str]:
        return self._request(path, method=method)

    def post_json(
        self, path: str, payload: dict[str, Any]
    ) -> tuple[int, dict[str, str], dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8")
        status, headers, text = self._request(path, method="POST", body=body)
        return status, headers, json.loads(text)

    def post_raw(self, path: str, body: bytes) -> tuple[int, dict[str, str], dict[str, Any]]:
        status, headers, text = self._request(path, method="POST", body=body)
        return status, headers, json.loads(text)

    def _request(
        self,
        path: str,
        *,
        method: str,
        body: bytes | None = None,
    ) -> tuple[int, dict[str, str], str]:
        headers = {"Content-Type": "application/json"} if body is not None else {}
        request = Request(self.url + path, data=body, method=method, headers=headers)
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, dict(response.headers), response.read().decode("utf-8")
        except HTTPError as exc:
            try:
                body = exc.read().decode("utf-8")
                return exc.code, dict(exc.headers), body
            finally:
                exc.close()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


if __name__ == "__main__":
    unittest.main()
