from __future__ import annotations

from contextlib import AbstractContextManager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import subprocess
import sys
import threading
from typing import Any
import unittest

from scripts.companion_client import (
    CompanionClient,
    CompanionConnectionError,
    CompanionProtocolError,
    CompanionServerError,
)
from scripts.companion_server import DEFAULT_HOST, CompanionState, make_server
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
CONTRACT_DOC = ROOT / "docs/api/companion-server-contract.md"


class CompanionClientTests(unittest.TestCase):
    def test_client_health_call(self) -> None:
        with ServerHarness() as server:
            health = server.client.health()

        self.assertEqual("ok", health["status"])
        self.assertTrue(health["mode"]["offline"])
        self.assertTrue(health["mode"]["mock"])

    def test_client_post_synthetic_event_and_latest_state(self) -> None:
        event = load_json(VALID_EVENT)

        with ServerHarness() as server:
            result = server.client.post_synthetic_event(event)
            context = server.client.latest_context()
            annotation = server.client.latest_annotation()
            overlay = server.client.latest_overlay_demo()

        self.assertEqual(
            event["raw_english_text"],
            result["context_packet"]["current_line"]["source_text"],
        )
        self.assertEqual(event["raw_english_text"], context["current_line"]["source_text"])
        self.assertEqual(event["raw_english_text"], annotation["original_english"])
        self.assertEqual(event["raw_english_text"], overlay["source"]["original_english"])

    def test_client_run_synthetic_eval_and_latest_summary(self) -> None:
        with ServerHarness() as server:
            summary = server.client.run_synthetic_eval()
            latest = server.client.latest_eval_summary()

        self.assertTrue(summary["passed"])
        self.assertGreaterEqual(summary["case_count"], 6)
        self.assertEqual(summary, latest)

    def test_client_latest_review_html_is_raw_html(self) -> None:
        with ServerHarness() as server:
            server.client.post_synthetic_event(load_json(VALID_EVENT))
            html = server.client.latest_review_html()

        self.assertIsInstance(html, str)
        self.assertIn("<!doctype html>", html)
        self.assertIn("Revachol Synthetic Review", html)

    def test_client_raises_server_error_envelope(self) -> None:
        with ServerHarness() as server:
            with self.assertRaises(CompanionServerError) as raised:
                server.client.latest_review_html()

        self.assertEqual(409, raised.exception.status)
        self.assertEqual("invalid_request", raised.exception.code)

    def test_client_raises_connection_error_when_server_unavailable(self) -> None:
        port = _unused_local_port()
        client = CompanionClient(f"http://{DEFAULT_HOST}:{port}", timeout=0.2)

        with self.assertRaises(CompanionConnectionError):
            client.health()

    def test_client_raises_protocol_error_for_invalid_json(self) -> None:
        with InvalidJsonHarness() as base_url:
            client = CompanionClient(base_url)

            with self.assertRaises(CompanionProtocolError):
                client.health()

    def test_cli_smoke_test_starts_and_stops_local_server(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_companion_client.py", "smoke-test"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Companion client smoke test passed", completed.stdout)

    def test_api_contract_doc_examples_are_synthetic_only(self) -> None:
        text = CONTRACT_DOC.read_text(encoding="utf-8")
        lowered = text.lower()

        self.assertIn("synthetic.event", text)
        self.assertIn('"ok": true', text)
        self.assertIn("invalid_fake_event", text)
        for forbidden in (
            "data/extracted",
            "data/local",
            "steamapps",
            "http://example",
            "https://",
            "disco dialogue",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lowered)


class ServerHarness(AbstractContextManager["ServerHarness"]):
    def __init__(self) -> None:
        self.state = CompanionState()
        self.server = make_server(DEFAULT_HOST, 0, self.state)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.client = CompanionClient(self.url)

    def __enter__(self) -> "ServerHarness":
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class InvalidJsonHarness(AbstractContextManager[str]):
    def __init__(self) -> None:
        self.server = ThreadingHTTPServer((DEFAULT_HOST, 0), InvalidJsonHandler)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self.thread.start()
        return f"http://{self.host}:{self.port}"

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()


class InvalidJsonHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        body = b"not-json"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _unused_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((DEFAULT_HOST, 0))
        return sock.getsockname()[1]


if __name__ == "__main__":
    unittest.main()
