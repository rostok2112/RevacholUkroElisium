from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class CompanionClientError(RuntimeError):
    """Base error for local companion client failures."""


class CompanionServerError(CompanionClientError):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message


class CompanionConnectionError(CompanionClientError):
    """Raised when the local companion server cannot be reached."""


class CompanionProtocolError(CompanionClientError):
    """Raised when a response does not match the expected local contract."""


class CompanionClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8765", timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        return self._request_json("GET", "/health")

    def latest_context(self) -> dict[str, Any] | None:
        return self._request_json("GET", "/state/latest-context")

    def latest_annotation(self) -> dict[str, Any] | None:
        return self._request_json("GET", "/state/latest-annotation")

    def latest_overlay_demo(self) -> dict[str, Any] | None:
        return self._request_json("GET", "/state/latest-overlay-demo")

    def latest_eval_summary(self) -> dict[str, Any] | None:
        return self._request_json("GET", "/state/latest-eval-summary")

    def latest_review_html(self) -> str:
        return self._request_text("GET", "/review/latest.html")

    def post_synthetic_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", "/synthetic/event", event)

    def run_synthetic_eval(self) -> dict[str, Any]:
        return self._request_json("POST", "/synthetic/eval", {})

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        status, body = self._request(method, path, payload)
        try:
            envelope = json.loads(body)
        except json.JSONDecodeError as exc:
            raise CompanionProtocolError(f"Invalid JSON response from {path}: {exc.msg}") from exc
        return _unwrap_json_envelope(status, path, envelope)

    def _request_text(self, method: str, path: str) -> str:
        _status, body = self._request(method, path, None)
        return body

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
    ) -> tuple[int, str]:
        body: bytes | None = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            try:
                error_body = exc.read().decode("utf-8")
                _raise_server_error(exc.code, path, error_body)
            finally:
                exc.close()
        except (OSError, URLError) as exc:
            raise CompanionConnectionError(f"Could not reach companion server: {exc}") from exc

        raise CompanionProtocolError(f"No response received from {path}")


def _raise_server_error(status: int, path: str, body: str) -> None:
    try:
        envelope = json.loads(body)
    except json.JSONDecodeError as exc:
        raise CompanionProtocolError(
            f"HTTP {status} from {path} did not include a JSON error envelope."
        ) from exc
    _unwrap_json_envelope(status, path, envelope)
    raise CompanionProtocolError(f"HTTP {status} from {path} did not raise an error.")


def _unwrap_json_envelope(status: int, path: str, envelope: Any) -> Any:
    if not isinstance(envelope, dict) or "ok" not in envelope:
        raise CompanionProtocolError(f"Response from {path} is not a companion envelope.")

    if envelope["ok"] is True:
        if "data" not in envelope:
            raise CompanionProtocolError(f"Success envelope from {path} is missing data.")
        return envelope["data"]

    if envelope["ok"] is False:
        error = envelope.get("error")
        if not isinstance(error, dict):
            raise CompanionProtocolError(f"Error envelope from {path} is missing error details.")
        code = error.get("code")
        message = error.get("message")
        if not isinstance(code, str) or not isinstance(message, str):
            raise CompanionProtocolError(f"Error envelope from {path} has invalid error details.")
        raise CompanionServerError(status, code, message)

    raise CompanionProtocolError(f"Envelope from {path} has non-boolean ok field.")
