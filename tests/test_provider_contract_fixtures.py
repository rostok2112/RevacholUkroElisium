from __future__ import annotations

from contextlib import AbstractContextManager
import json
from pathlib import Path
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest

from scripts.companion_client import CompanionClient
from scripts.companion_server import DEFAULT_HOST, CompanionState, make_server
from scripts.schema_validator import collect_errors, load_json


ROOT = Path(__file__).resolve().parents[1]
FAKE_EVENT_REQUEST = ROOT / "tests/fixtures/provider_annotate.fake_event_request.synthetic.json"
CONTEXT_PACKET_REQUEST = (
    ROOT / "tests/fixtures/provider_annotate.context_packet_request.synthetic.json"
)
SUCCESS_RESPONSE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"
CONTEXT_SCHEMA = ROOT / "specs/context-packet.schema.json"
ANNOTATION_SCHEMA = ROOT / "specs/annotation-card.schema.json"
CONTRACT_DOC = ROOT / "docs/api/companion-server-contract.md"


class ProviderContractFixtureTests(unittest.TestCase):
    def test_fake_event_request_fixture_is_accepted_by_server(self) -> None:
        request = load_json(FAKE_EVENT_REQUEST)
        expected = load_json(SUCCESS_RESPONSE)

        with ServerHarness() as server:
            status, _headers, payload = server.post_json("/synthetic/provider-annotate", request)

        self.assertEqual(200, status)
        self.assertEqual(expected, payload)

    def test_context_packet_request_fixture_is_accepted_by_server(self) -> None:
        request = load_json(CONTEXT_PACKET_REQUEST)
        expected = load_json(SUCCESS_RESPONSE)

        with ServerHarness() as server:
            status, _headers, payload = server.post_json("/synthetic/provider-annotate", request)

        self.assertEqual(200, status)
        self.assertEqual(expected, payload)

    def test_client_unwraps_provider_fixture_response_shape(self) -> None:
        request = load_json(FAKE_EVENT_REQUEST)
        expected = load_json(SUCCESS_RESPONSE)["data"]

        with ServerHarness() as server:
            payload = server.client.provider_annotate_fake_event(request["event"])

        self.assertEqual(expected, payload)
        self.assertIn("context_packet", payload)
        self.assertIn("annotation_card", payload)

    def test_success_response_fixture_validates_nested_schemas(self) -> None:
        fixture = load_json(SUCCESS_RESPONSE)
        self.assertIs(fixture["ok"], True)
        self.assertIn("context_packet", fixture["data"])
        self.assertIn("annotation_card", fixture["data"])

        context_errors = collect_errors(
            fixture["data"]["context_packet"], load_json(CONTEXT_SCHEMA)
        )
        annotation_errors = collect_errors(
            fixture["data"]["annotation_card"],
            load_json(ANNOTATION_SCHEMA),
        )

        self.assertEqual([], context_errors)
        self.assertEqual([], annotation_errors)

    def test_provider_metadata_fields_are_explicit_optional_schema_properties(self) -> None:
        schema = load_json(ANNOTATION_SCHEMA)
        properties = schema["properties"]

        self.assertIn("provider", properties)
        self.assertIn("provider_debug", properties)
        self.assertIn("prompt_pack", properties)
        self.assertNotIn("provider", schema["required"])
        self.assertNotIn("provider_debug", schema["required"])
        self.assertNotIn("prompt_pack", schema["required"])
        self.assertIn("provider_name", properties["provider"]["properties"])
        self.assertIn("prompt_pack_id", properties["provider_debug"]["properties"])
        self.assertIn("pack_id", properties["prompt_pack"]["properties"])

    def test_provider_metadata_fields_are_present_and_public(self) -> None:
        annotation_card = load_json(SUCCESS_RESPONSE)["data"]["annotation_card"]

        self.assertEqual("mock", annotation_card["provider"]["provider_name"])
        self.assertNotIn("future_roles", annotation_card["provider"])
        self.assertEqual("mock", annotation_card["provider_debug"]["provider_name"])
        self.assertEqual("ukrainian_annotation_v1", annotation_card["prompt_pack"]["pack_id"])
        self.assertIn("prompt_pack_guided", annotation_card["risk_flags"])

    def test_provider_fixtures_are_synthetic_and_safe(self) -> None:
        for fixture_path in (FAKE_EVENT_REQUEST, CONTEXT_PACKET_REQUEST, SUCCESS_RESPONSE):
            with self.subTest(fixture=fixture_path.name):
                payload = load_json(fixture_path)
                self.assertIn("synthetic", json.dumps(payload, ensure_ascii=False).lower())
                violations = list(_fixture_safety_violations(payload))
                self.assertEqual([], violations)

    def test_unwrapped_provider_request_fixture_is_rejected(self) -> None:
        request = load_json(FAKE_EVENT_REQUEST)

        with ServerHarness() as server:
            status, _headers, payload = server.post_json(
                "/synthetic/provider-annotate",
                request["event"],
            )

        self.assertEqual(400, status)
        self.assertFalse(payload["ok"])
        self.assertEqual("invalid_request", payload["error"]["code"])
        self.assertIn("input_type", payload["error"]["message"])

    def test_docs_reference_provider_contract_fixtures_and_metadata(self) -> None:
        text = CONTRACT_DOC.read_text(encoding="utf-8")

        self.assertIn("provider_annotate.fake_event_request.synthetic.json", text)
        self.assertIn("provider_annotate.context_packet_request.synthetic.json", text)
        self.assertIn("provider_annotate.success_response.synthetic.json", text)
        self.assertIn("provider_debug", text)
        self.assertIn("prompt_pack", text)
        self.assertIn("explicit optional", text.lower())


class ServerHarness(AbstractContextManager["ServerHarness"]):
    def __init__(self) -> None:
        self.state = CompanionState()
        self.server = make_server(DEFAULT_HOST, 0, self.state)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.client = CompanionClient(self.url)

    def __enter__(self) -> ServerHarness:
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def post_json(
        self, path: str, payload: dict[str, Any]
    ) -> tuple[int, dict[str, str], dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.url + path,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=5) as response:
                text = response.read().decode("utf-8")
                return response.status, dict(response.headers), json.loads(text)
        except HTTPError as exc:
            try:
                text = exc.read().decode("utf-8")
                return exc.code, dict(exc.headers), json.loads(text)
            finally:
                exc.close()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


def _fixture_safety_violations(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            violations.extend(_string_safety_violations(str(key), (*path, str(key), "<key>")))
            violations.extend(_fixture_safety_violations(child, (*path, str(key))))
        return violations
    if isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(_fixture_safety_violations(child, (*path, str(index))))
        return violations
    if not isinstance(value, str):
        return violations

    violations.extend(_string_safety_violations(value, path))
    if "disco elysium" in value.lower() and path not in (
        ("context_packet", "game", "title"),
        ("data", "context_packet", "game", "title"),
    ):
        violations.append(f"{'.'.join(path)} contains real game title outside game.title")
    return violations


def _string_safety_violations(value: str, path: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    lowered = value.lower()
    forbidden_markers = (
        "http://",
        "https://",
        "data/extracted",
        "data/local",
        "workspace/",
        "llm-cache",
        "vector-store",
        "translation-memory/private",
        "audio-index/private",
        "screenshots/private",
        ".cache",
        "steamapps",
        "openai",
        "deepl",
        "anthropic",
        "api_key",
        "api-key",
        "secret",
        "token",
        "password",
    )
    for marker in forbidden_markers:
        if marker in lowered:
            violations.append(f"{'.'.join(path)} contains forbidden marker {marker!r}")
    return violations


if __name__ == "__main__":
    unittest.main()
