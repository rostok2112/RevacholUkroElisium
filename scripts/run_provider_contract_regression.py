from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
import json
from pathlib import Path
import sys
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from scripts.companion_server import DEFAULT_HOST, CompanionState, make_server
    from scripts.schema_validator import collect_errors, load_json
    from scripts.synthetic_review_renderer import render_review_html
    from scripts.synthetic_slice import (
        ANNOTATION_CARD_SCHEMA,
        CONTEXT_PACKET_SCHEMA,
        ROOT,
        build_overlay_demo_model,
    )
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from companion_server import DEFAULT_HOST, CompanionState, make_server
    from schema_validator import collect_errors, load_json
    from synthetic_review_renderer import render_review_html
    from synthetic_slice import (
        ANNOTATION_CARD_SCHEMA,
        CONTEXT_PACKET_SCHEMA,
        ROOT,
        build_overlay_demo_model,
    )


SCHEMA_VERSION = "provider-contract-regression.v1"
ENDPOINT = "/synthetic/provider-annotate"
DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/provider-contract"
FAKE_EVENT_REQUEST = ROOT / "tests/fixtures/provider_annotate.fake_event_request.synthetic.json"
CONTEXT_PACKET_REQUEST = (
    ROOT / "tests/fixtures/provider_annotate.context_packet_request.synthetic.json"
)
SUCCESS_RESPONSE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"
REQUIRED_RISK_FLAGS = (
    "synthetic_fixture",
    "mock_provider",
    "deterministic_mock_provider",
    "needs_human_review_before_real_use",
    "prompt_pack_guided",
)
STABLE_JSON_PATHS = (
    ("ok",),
    ("data", "context_packet"),
    ("data", "annotation_card", "line_id"),
    ("data", "annotation_card", "source_text"),
    ("data", "annotation_card", "original_english"),
    ("data", "annotation_card", "glossary_terms"),
    ("data", "annotation_card", "risk_flags"),
    ("data", "annotation_card", "provider"),
    ("data", "annotation_card", "provider_debug"),
    ("data", "annotation_card", "prompt_pack"),
)


class ContractRegressionError(ValueError):
    """Raised when a provider contract regression command cannot run."""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the synthetic provider contract regression check against an in-process "
            "127.0.0.1 companion server. This is offline, deterministic, and mock-only."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON summary output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/provider-contract/; unsafe paths are rejected."
        ),
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        help=(
            "Optional Markdown summary output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/provider-contract/; unsafe paths are rejected."
        ),
    )
    parser.add_argument(
        "--write-review-html",
        action="store_true",
        help=(
            "Write escaped provider review HTML files under "
            "workspace/synthetic-slice/provider-contract/."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress JSON stdout.")
    args = parser.parse_args()

    try:
        output_path = resolve_output_path(args.output) if args.output else None
        markdown_path = resolve_output_path(args.markdown) if args.markdown else None
    except ValueError as exc:
        parser.error(str(exc))

    summary = run_provider_contract_regression(
        review_output_root=DEFAULT_OUTPUT_ROOT if args.write_review_html else None
    )
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    written_paths: list[Path] = []

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        written_paths.append(output_path)

    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown_summary(summary) + "\n", encoding="utf-8")
        written_paths.append(markdown_path)

    for case in summary["cases"]:
        review_path = case.get("artifacts", {}).get("review_html")
        if isinstance(review_path, str):
            written_paths.append((ROOT / review_path).resolve(strict=False))

    if not args.quiet and not written_paths:
        print(rendered)
    elif not args.quiet:
        for path in written_paths:
            print(f"Wrote {_relative_to_root(path)}")
    elif not written_paths:
        status = "passed" if summary["ok"] else "failed"
        print(f"Provider contract regression {status}.")

    return 0 if summary["ok"] else 1


def run_provider_contract_regression(
    *,
    fake_event_request_path: Path = FAKE_EVENT_REQUEST,
    context_packet_request_path: Path = CONTEXT_PACKET_REQUEST,
    success_response_path: Path = SUCCESS_RESPONSE,
    review_output_root: Path | None = None,
) -> dict[str, Any]:
    fixture_errors: list[str] = []
    fake_event_request = _load_fixture(
        fake_event_request_path, "fake_event_request", fixture_errors
    )
    context_packet_request = _load_fixture(
        context_packet_request_path,
        "context_packet_request",
        fixture_errors,
    )
    success_response = _load_fixture(success_response_path, "success_response", fixture_errors)
    expected_validation = _validate_contract_payload(success_response, label="success fixture")
    fixture_errors.extend(expected_validation["errors"])

    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "mode": {
            "offline": True,
            "mock": True,
            "synthetic_only": True,
            "localhost_only": True,
            "external_services": False,
        },
        "fixtures": {
            "fake_event_request": _relative_to_root(fake_event_request_path),
            "context_packet_request": _relative_to_root(context_packet_request_path),
            "success_response": _relative_to_root(success_response_path),
        },
        "endpoint": ENDPOINT,
        "server": {
            "host": DEFAULT_HOST,
            "port": "ephemeral",
            "started": False,
            "shutdown": False,
        },
        "fixture_validation": {
            "ok": not fixture_errors,
            "errors": fixture_errors,
            "success_response_schema": expected_validation["schema_validation"],
        },
        "cases": [],
    }

    harness = _LocalServerHarness()
    try:
        with harness as server:
            for case_id, request_fixture in (
                ("fake_event", fake_event_request),
                ("context_packet", context_packet_request),
            ):
                case_result = _run_case(
                    server=server,
                    case_id=case_id,
                    request_fixture=request_fixture,
                    expected_response=success_response,
                    review_output_root=review_output_root,
                )
                summary["cases"].append(case_result)
    except Exception as exc:  # pragma: no cover - defensive summary for unexpected local failures.
        summary["cases"].append(
            {
                "case_id": "server",
                "ok": False,
                "errors": [f"Unexpected regression runner failure: {exc}"],
                "stable_diffs": [],
            }
        )
    finally:
        summary["server"]["started"] = harness.started
        summary["server"]["shutdown"] = harness.shutdown_complete

    summary["ok"] = (
        summary["fixture_validation"]["ok"]
        and summary["server"]["started"]
        and summary["server"]["shutdown"]
        and all(case.get("ok") is True for case in summary["cases"])
    )
    return summary


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under "
            "workspace/synthetic-slice/provider-contract/ for generated contract artifacts."
        )
    return resolved


def render_markdown_summary(summary: dict[str, Any]) -> str:
    status = "PASS" if summary.get("ok") else "FAIL"
    lines = [
        "# Provider Contract Regression",
        "",
        f"Status: {status}",
        f"Schema version: {summary.get('schema_version')}",
        "",
        "## Cases",
    ]
    for case in summary.get("cases", []):
        case_status = "PASS" if case.get("ok") else "FAIL"
        lines.append(f"- `{case.get('case_id')}`: {case_status}")
        if case.get("errors"):
            lines.append(f"  - Errors: {'; '.join(case['errors'])}")
        if case.get("stable_diffs"):
            paths = ", ".join(diff["path"] for diff in case["stable_diffs"])
            lines.append(f"  - Stable diffs: {paths}")
    return "\n".join(lines)


def _run_case(
    *,
    server: _LocalServerHarness,
    case_id: str,
    request_fixture: Any,
    expected_response: Any,
    review_output_root: Path | None,
) -> dict[str, Any]:
    status, payload = server.post_json(ENDPOINT, request_fixture)
    validation = _validate_contract_payload(payload, label=case_id)
    stable_diffs = _stable_diffs(payload, expected_response)
    preservation_errors = _source_preservation_errors(payload)
    risk_flag_errors = _risk_flag_errors(payload)
    errors: list[str] = []
    if status != 200:
        errors.append(f"Expected HTTP 200, got {status}.")
    errors.extend(validation["errors"])
    errors.extend(preservation_errors)
    errors.extend(risk_flag_errors)

    result: dict[str, Any] = {
        "case_id": case_id,
        "input_type": _input_type(request_fixture),
        "http_status": status,
        "ok": False,
        "envelope_ok": _envelope_ok(payload),
        "schema_validation": validation["schema_validation"],
        "stable_diffs": stable_diffs,
        "errors": errors,
        "artifacts": {},
    }

    if review_output_root is not None and validation["ok"]:
        review_path = review_output_root / f"review.{case_id}.html"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(_render_review_from_payload(payload) + "\n", encoding="utf-8")
        result["artifacts"]["review_html"] = _relative_to_root(review_path)

    result["ok"] = (
        status == 200
        and validation["ok"]
        and not stable_diffs
        and not preservation_errors
        and not risk_flag_errors
    )
    return result


def _validate_contract_payload(payload: Any, *, label: str) -> dict[str, Any]:
    schema_validation = {
        "context_packet": {"ok": False, "errors": []},
        "annotation_card": {"ok": False, "errors": []},
    }
    errors = _envelope_errors(payload)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return {"ok": False, "errors": errors, "schema_validation": schema_validation}

    context_packet = data.get("context_packet")
    annotation_card = data.get("annotation_card")
    context_errors = collect_errors(context_packet, load_json(CONTEXT_PACKET_SCHEMA))
    annotation_errors = collect_errors(annotation_card, load_json(ANNOTATION_CARD_SCHEMA))
    schema_validation = {
        "context_packet": {"ok": not context_errors, "errors": context_errors},
        "annotation_card": {"ok": not annotation_errors, "errors": annotation_errors},
    }
    if context_errors:
        errors.append(f"{label} context_packet schema errors: {context_errors}")
    if annotation_errors:
        errors.append(f"{label} annotation_card schema errors: {annotation_errors}")
    return {"ok": not errors, "errors": errors, "schema_validation": schema_validation}


def _stable_diffs(actual: Any, expected: Any) -> list[dict[str, Any]]:
    diffs = []
    for path in STABLE_JSON_PATHS:
        actual_value = _get_path(actual, path)
        expected_value = _get_path(expected, path)
        if actual_value != expected_value:
            diffs.append(
                {
                    "path": ".".join(path),
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )
    return diffs


def _source_preservation_errors(payload: Any) -> list[str]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return []
    context_packet = data.get("context_packet")
    annotation_card = data.get("annotation_card")
    if not isinstance(context_packet, dict) or not isinstance(annotation_card, dict):
        return []
    current_line = context_packet.get("current_line")
    if not isinstance(current_line, dict):
        return []
    source_text = current_line.get("source_text")
    errors = []
    if annotation_card.get("source_text") != source_text:
        errors.append("annotation_card.source_text does not preserve context source_text.")
    if annotation_card.get("original_english") != source_text:
        errors.append("annotation_card.original_english does not preserve context source_text.")
    return errors


def _risk_flag_errors(payload: Any) -> list[str]:
    risk_flags = _get_path(payload, ("data", "annotation_card", "risk_flags"))
    if not isinstance(risk_flags, list):
        return ["annotation_card.risk_flags must be a list."]
    missing = [flag for flag in REQUIRED_RISK_FLAGS if flag not in risk_flags]
    if missing:
        return [f"annotation_card.risk_flags missing required flags: {', '.join(missing)}"]
    return []


def _envelope_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["Response must be a JSON object."]
    errors = []
    if payload.get("ok") is not True:
        errors.append("Response envelope must contain ok=true.")
    data = payload.get("data")
    if not isinstance(data, dict):
        errors.append("Response envelope must contain a data object.")
        return errors
    if not isinstance(data.get("context_packet"), dict):
        errors.append("Response data must contain a context_packet object.")
    if not isinstance(data.get("annotation_card"), dict):
        errors.append("Response data must contain an annotation_card object.")
    return errors


def _envelope_ok(payload: Any) -> bool:
    return not _envelope_errors(payload)


def _render_review_from_payload(payload: dict[str, Any]) -> str:
    data = payload["data"]
    context_packet = data["context_packet"]
    annotation_card = data["annotation_card"]
    overlay_demo = build_overlay_demo_model(context_packet, annotation_card)
    return render_review_html(
        {
            "context_packet": context_packet,
            "annotation_card": annotation_card,
            "overlay_demo": overlay_demo,
        }
    )


def _load_fixture(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return load_json(path)
    except Exception as exc:
        errors.append(f"Could not load {label} fixture {path}: {exc}")
        return {}


def _input_type(request_fixture: Any) -> str | None:
    if not isinstance(request_fixture, dict):
        return None
    input_type = request_fixture.get("input_type")
    return input_type if isinstance(input_type, str) else None


def _get_path(value: Any, path: tuple[str, ...]) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return "<missing>"
        current = current[key]
    return current


def _relative_to_root(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT.resolve(strict=False))).replace("\\", "/")
    except ValueError:
        return str(path)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


class _LocalServerHarness(AbstractContextManager["_LocalServerHarness"]):
    def __init__(self) -> None:
        self.state = CompanionState()
        self.server = make_server(DEFAULT_HOST, 0, self.state)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.started = False
        self.shutdown_complete = False

    def __enter__(self) -> "_LocalServerHarness":
        self.thread.start()
        self.started = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.shutdown_complete = not self.thread.is_alive()

    def post_json(self, path: str, payload: Any) -> tuple[int, Any]:
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
                return response.status, json.loads(text)
        except HTTPError as exc:
            try:
                text = exc.read().decode("utf-8")
                return exc.code, json.loads(text)
            finally:
                exc.close()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


if __name__ == "__main__":
    sys.exit(main())
