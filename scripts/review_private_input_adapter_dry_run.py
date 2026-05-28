from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PRIVATE_OUTPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        build_dry_run_summary,
        write_summary as write_dry_run_summary,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PRIVATE_OUTPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        build_dry_run_summary,
        write_summary as write_dry_run_summary,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_SCHEMA_VERSION = "private-input-adapter-dry-run-review.v1"
SELF_TEST_SCHEMA_VERSION = "private-input-adapter-dry-run-review-self-test.v1"
DECISION_SCHEMA_VERSION = "private-input-dry-run-decision.v1"
MILESTONE = "5A.4"
REVIEW_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/review/"
RECOMMENDED_HASH_NEXT_STEP = "private_input_hash_decision_contract"
RECOMMENDED_REPEAT_NEXT_STEP = "repeat_private_input_adapter_dry_run"
DECISION_FIXTURE_PATH = ROOT / "tests/fixtures/private_input_dry_run_decision.synthetic.json"

FALSE_SAFETY_FIELDS = (
    "real_text_included",
    "raw_payloads_included",
    "raw_logs_included",
    "automatic_game_install_scanning",
    "game_files_read",
    "bepinex_logs_read",
    "game_logs_read",
    "screenshots_read",
    "ocr_used",
    "save_files_read",
    "hooks_used",
    "unity_scanning_used",
    "current_line_capture_used",
    "ui_text_reading_used",
    "decompiled_code_used",
    "companion_contract_changed",
    "provider_called",
    "file_contents_read",
    "hashes_computed",
)
COUNT_FIELDS = (
    "file_count",
    "directory_count",
    "total_size_bytes",
    "traversal_limit",
)
BOOLEAN_FIELDS = (
    "input_exists",
    "dry_run",
    "traversal_truncated",
    "output_written",
    "paths_redacted",
)
ALLOWED_INPUT_KINDS = {"file", "directory", "missing", "unsupported"}
PRIVATE_PATH_KEYS = {"input_path", "allowed_root_path", "output_path"}

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:(?:\\\\|\\)(?:Users|Program Files|Games|Steam|GOG|AppData)(?:\\\\|\\)"
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")
FORBIDDEN_VALUE_MARKERS = (
    "current-line capture approved",
    "current line capture approved",
    "real text capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "harmony patch approved",
    "hook implementation approved",
    "ocr approved",
    "automatic game install scanning approved",
    "real extraction approved",
    "private index construction approved",
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "screen capture",
    "steamapps",
    "bepinex",
    "savegame",
    ".sav",
    "decompiled",
    "dnspy",
    "ilspy",
)
DECISION_FALSE_FIELDS = (
    "private_index_construction_allowed_next",
    "real_extraction_allowed",
    "automatic_game_install_scanning_allowed",
    "real_game_text_commit_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "ocr_allowed",
    "decompiled_code_allowed",
    "companion_contract_change_allowed",
    "provider_execution_allowed",
    "bepinex_log_reads_allowed",
    "screenshots_allowed",
)


class PrivateInputDryRunReviewError(RuntimeError):
    """Raised when a dry-run summary review request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a private input adapter dry-run summary without reading private input."
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="Dry-run summary JSON under workspace/local-private/extraction-indexing/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional review JSON under workspace/local-private/extraction-indexing/review/.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Optional review Markdown under workspace/local-private/extraction-indexing/review/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace review smoke that does not need real private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Private input adapter dry-run review self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": SELF_TEST_SCHEMA_VERSION,
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0

        if args.summary is None:
            parser.error("--summary is required unless --self-test is used.")

        summary_path = resolve_summary_path(args.summary, root=ROOT)
        payload = load_json(summary_path)
        review = build_review(payload, summary_path=summary_path, root=ROOT)

        if review["dry_run_valid"]:
            if args.output:
                write_json_review(review, resolve_review_output_path(args.output, root=ROOT))
            if args.markdown_output:
                write_markdown_review(
                    review,
                    resolve_review_output_path(args.markdown_output, root=ROOT),
                )

        if args.quiet:
            print(
                "Private input adapter dry-run review passed."
                if review["dry_run_valid"]
                else "Private input adapter dry-run review failed."
            )
        else:
            print(json.dumps(review, indent=2, sort_keys=True))
        return 0 if review["dry_run_valid"] else 1
    except (OSError, ValueError, PrivateInputDryRunReviewError) as exc:
        parser.error(str(exc))
    return 0


def build_review(
    summary: dict[str, Any],
    *,
    summary_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = collect_summary_errors(summary, summary_path=summary_path, root=root)
    blockers = _dedupe([_blocker_for_error(error) for error in errors])
    if not errors:
        blockers.extend(str(item) for item in summary.get("blocker_categories", []))
        blockers = _dedupe(blockers)

    ready_for_hash_decision = not errors and not blockers
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "dry_run_valid": not errors,
        "input_was_under_allowed_root": summary.get("allowed_root") == PRIVATE_INPUT_ROOT,
        "file_count": _safe_int(summary.get("file_count")),
        "directory_count": _safe_int(summary.get("directory_count")),
        "total_size_bytes": _safe_int(summary.get("total_size_bytes")),
        "real_text_included": False,
        "raw_payloads_included": False,
        "hashes_computed": False,
        "private_paths_included": False,
        "raw_logs_included": False,
        "file_contents_read": False,
        "ready_for_hash_decision": ready_for_hash_decision,
        "ready_for_private_index_decision": False,
        "blockers": blockers,
        "recommended_next_step": (
            RECOMMENDED_HASH_NEXT_STEP if ready_for_hash_decision else RECOMMENDED_REPEAT_NEXT_STEP
        ),
        "summary_path_redacted": True,
        "original_private_input_read": False,
        "review_output_private_only": True,
    }


def collect_summary_errors(
    summary: Any,
    *,
    summary_path: Path,
    root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    try:
        resolve_summary_path(summary_path, root=root)
    except PrivateInputDryRunReviewError as exc:
        errors.append(str(exc))

    if not isinstance(summary, dict):
        return errors + ["Dry-run summary must be a JSON object."]

    if summary.get("schema_version") != SUMMARY_SCHEMA_VERSION:
        errors.append(f"Dry-run summary schema_version must be {SUMMARY_SCHEMA_VERSION!r}.")
    if summary.get("allowed_root") != PRIVATE_INPUT_ROOT:
        errors.append(f"Dry-run summary allowed_root must be {PRIVATE_INPUT_ROOT!r}.")
    if summary.get("private_output_root") != PRIVATE_OUTPUT_ROOT:
        errors.append(f"Dry-run summary private_output_root must be {PRIVATE_OUTPUT_ROOT!r}.")
    if summary.get("input_kind") not in ALLOWED_INPUT_KINDS:
        errors.append("Dry-run summary input_kind is not recognized.")

    for field in BOOLEAN_FIELDS:
        if not isinstance(summary.get(field), bool):
            errors.append(f"Dry-run summary field {field!r} must be a boolean.")
    for field in COUNT_FIELDS:
        if not isinstance(summary.get(field), int) or summary.get(field) < 0:
            errors.append(f"Dry-run summary field {field!r} must be a non-negative integer.")
    for field in FALSE_SAFETY_FIELDS:
        if not isinstance(summary.get(field), bool):
            errors.append(f"Dry-run summary safety field {field!r} must be a boolean.")
        elif summary.get(field) is not False:
            errors.append(f"Dry-run summary safety field {field!r} must remain false.")

    blockers = summary.get("blocker_categories")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append("Dry-run summary blocker_categories must be a list of strings.")

    if summary.get("dry_run") is not True:
        errors.append("Dry-run summary must set dry_run=true.")
    if summary.get("paths_redacted") is not True:
        errors.append("Dry-run summary must be produced without verbose/private path fields.")
    for key in PRIVATE_PATH_KEYS:
        if key in summary:
            errors.append(f"Dry-run summary must not include private path field {key!r}.")

    errors.extend(_unsafe_value_errors(summary, label="Dry-run summary"))
    return errors


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load private input dry-run decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["Private input dry-run decision fixture must be a JSON object."]

    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"Decision fixture schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("milestone") != MILESTONE:
        errors.append(f"Decision fixture milestone must be {MILESTONE!r}.")
    if payload.get("dry_run_evidence_required") is not True:
        errors.append("Decision fixture must require dry-run evidence.")
    if payload.get("hashes_allowed_next") != "decision_pending":
        errors.append("Decision fixture hashes_allowed_next must be 'decision_pending'.")
    if payload.get("recommended_next_step") != RECOMMENDED_HASH_NEXT_STEP:
        errors.append(
            f"Decision fixture recommended_next_step must be {RECOMMENDED_HASH_NEXT_STEP!r}."
        )
    for field in DECISION_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"Decision fixture must keep {field}=false.")
    errors.extend(_unsafe_value_errors(payload, label="Decision fixture"))
    return errors


def resolve_summary_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    output_root = _private_output_root(root).resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise PrivateInputDryRunReviewError(
            "Unsafe summary path. Use a summary under workspace/local-private/extraction-indexing/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise PrivateInputDryRunReviewError("Dry-run summary path must point to an existing file.")
    return resolved


def resolve_review_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    review_root = _review_output_root(root).resolve(strict=False)
    if not _is_relative_to(resolved, review_root):
        raise PrivateInputDryRunReviewError(
            "Unsafe review output path. Use workspace/local-private/extraction-indexing/review/."
        )
    if resolved.exists() and resolved.is_dir():
        raise PrivateInputDryRunReviewError("Review output path must be a file path.")
    return resolved


def write_json_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Private Input Adapter Dry-Run Review",
        "",
        f"- dry_run_valid: {_yes_no(review['dry_run_valid'])}",
        f"- ready_for_hash_decision: {_yes_no(review['ready_for_hash_decision'])}",
        "- ready_for_private_index_decision: no",
        f"- file_count: {review['file_count']}",
        f"- directory_count: {review['directory_count']}",
        f"- total_size_bytes: {review['total_size_bytes']}",
        "- real_text_included: no",
        "- raw_payloads_included: no",
        "- hashes_computed: no",
        "- private_paths_included: no",
        f"- recommended_next_step: {review['recommended_next_step']}",
    ]
    if review["blockers"]:
        lines.extend(["", "## Blockers"])
        lines.extend(f"- {blocker}" for blocker in review["blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_self_test() -> None:
    decision_errors = collect_decision_fixture_errors()
    if decision_errors:
        raise PrivateInputDryRunReviewError("; ".join(decision_errors))

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        selected = root / PRIVATE_INPUT_ROOT / "selected"
        selected.mkdir(parents=True)
        private_text = "PRIVATE_CONTENT_SHOULD_NOT_APPEAR"
        (selected / "record.txt").write_text(private_text, encoding="utf-8")

        summary = build_dry_run_summary(Path(PRIVATE_INPUT_ROOT) / "selected", root=root)
        summary_path = root / PRIVATE_OUTPUT_ROOT / "summary.json"
        write_dry_run_summary(summary, summary_path)

        payload = load_json(summary_path)
        review = build_review(payload, summary_path=summary_path, root=root)
        rendered = json.dumps(review, sort_keys=True)
        if not review["dry_run_valid"] or not review["ready_for_hash_decision"]:
            raise PrivateInputDryRunReviewError("Self-test expected ready redacted review.")
        if review["ready_for_private_index_decision"]:
            raise PrivateInputDryRunReviewError("Self-test must not allow private index decision.")
        if private_text in rendered or str(root) in rendered:
            raise PrivateInputDryRunReviewError("Self-test review leaked private content or paths.")

        review_path = root / REVIEW_OUTPUT_ROOT / "review.json"
        markdown_path = root / REVIEW_OUTPUT_ROOT / "review.md"
        write_json_review(review, resolve_review_output_path(review_path, root=root))
        write_markdown_review(review, resolve_review_output_path(markdown_path, root=root))
        if private_text in review_path.read_text(encoding="utf-8"):
            raise PrivateInputDryRunReviewError("Self-test JSON review leaked private content.")
        if private_text in markdown_path.read_text(encoding="utf-8"):
            raise PrivateInputDryRunReviewError("Self-test Markdown review leaked private content.")


def _unsafe_value_errors(value: Any, *, label: str) -> list[str]:
    errors: list[str] = []
    for string_value in _iter_string_values(value):
        for url in URL_PATTERN.findall(string_value):
            errors.append(f"{label} contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(string_value):
            errors.append(f"{label} contains a secret/API-key-looking value.")
        if WINDOWS_PRIVATE_PATH_PATTERN.search(string_value) or POSIX_PRIVATE_PATH_PATTERN.search(
            string_value
        ):
            errors.append(f"{label} contains a private absolute path.")
        lowered = string_value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{label} contains forbidden marker {marker!r}.")
    return errors


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise PrivateInputDryRunReviewError("Unsafe path traversal is not allowed.")
    for marker in (
        "logoutput.log",
        "player.log",
        "steamapps",
        "screenshot",
        "ocr",
        ".sav",
        "savegame",
        "raw-payload",
        "raw payload",
        "raw-log",
        "raw log",
        "decompiled",
    ):
        if marker in normalized:
            raise PrivateInputDryRunReviewError("Path uses a forbidden runtime/private marker.")


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute() or WINDOWS_ABSOLUTE_PATH_PATTERN.match(str(raw)):
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _private_output_root(root: Path) -> Path:
    return root / PRIVATE_OUTPUT_ROOT


def _review_output_root(root: Path) -> Path:
    return root / REVIEW_OUTPUT_ROOT


def _blocker_for_error(error: str) -> str:
    lowered = error.lower()
    if "schema_version" in lowered or "json object" in lowered:
        return "malformed_summary"
    if "hashes_computed" in lowered:
        return "hashes_computed_not_allowed"
    if "path" in lowered:
        return "private_path_or_unsafe_path"
    if "marker" in lowered or "payload" in lowered or "log" in lowered:
        return "unsafe_marker_detected"
    if "remain false" in lowered or "dry_run=true" in lowered:
        return "unsafe_summary_flags"
    return "invalid_dry_run_summary"


def _safe_int(value: Any) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _iter_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(_iter_string_values(item))
        return strings
    if isinstance(value, dict):
        strings = []
        for item in value.values():
            strings.extend(_iter_string_values(item))
        return strings
    return []


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
