from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.run_dry_run_summary_hash import (
        FALSE_OUTPUT_FIELDS,
        HASH_ALGORITHM,
        HASH_INPUT_KIND,
        HASH_OUTPUT_ROOT,
        HASH_SCHEMA_VERSION,
        build_hash_summary,
        write_hash_summary,
    )
    from scripts.run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PRIVATE_OUTPUT_ROOT,
        build_dry_run_summary,
        write_summary as write_dry_run_summary,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from run_dry_run_summary_hash import (
        FALSE_OUTPUT_FIELDS,
        HASH_ALGORITHM,
        HASH_INPUT_KIND,
        HASH_OUTPUT_ROOT,
        HASH_SCHEMA_VERSION,
        build_hash_summary,
        write_hash_summary,
    )
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PRIVATE_OUTPUT_ROOT,
        build_dry_run_summary,
        write_summary as write_dry_run_summary,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_SCHEMA_VERSION = "dry-run-summary-hash-review.v1"
SELF_TEST_SCHEMA_VERSION = "dry-run-summary-hash-review-self-test.v1"
DECISION_SCHEMA_VERSION = "dry-run-summary-hash-decision.v1"
MILESTONE = "5A.8"
HASH_REVIEW_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/hash-review/"
DECISION_FIXTURE_PATH = ROOT / "tests/fixtures/dry_run_summary_hash_decision.synthetic.json"
RECOMMENDED_INDEX_CONTRACT_STEP = "private_index_construction_contract"
RECOMMENDED_REPEAT_HASH_STEP = "repeat_dry_run_summary_hash"

HEX_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
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

FORBIDDEN_HASH_VALUE_MARKERS = (
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
    "ocr",
    "decompiled",
    "dnspy",
    "ilspy",
    "file content hashing approved",
    "path string hashing approved",
    "filename hashing approved",
    "private index construction approved",
    "real extraction approved",
    "current-line capture approved",
    "current line capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "hook implementation approved",
    "harmony patch approved",
    "provider execution approved",
    "companion contract change approved",
)

FORBIDDEN_HASH_FIELDS = (
    "source_path",
    "summary_path",
    "input_path",
    "allowed_root_path",
    "output_path",
    "filename",
    "directory_name",
    "canonical_json",
    "source_summary",
    "original_summary",
    "file_contents",
    "raw_payload",
    "raw_log",
    "screenshot",
    "ocr_output",
    "save_file",
    "decompiled_output",
    "provider_payload",
    "generated_index",
    "free_text_evidence",
)

DECISION_FALSE_FIELDS = (
    "private_index_construction_allowed_next",
    "real_extraction_allowed",
    "automatic_game_install_scanning_allowed",
    "real_game_text_commit_allowed",
    "file_content_hashing_allowed",
    "path_string_hashing_allowed",
    "filename_hashing_allowed",
    "raw_payload_hashing_allowed",
    "raw_log_hashing_allowed",
    "generated_index_hashing_allowed",
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
    "save_file_parsing_allowed",
)


class DryRunSummaryHashReviewError(RuntimeError):
    """Raised when a dry-run summary hash review request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a dry-run summary hash output without reading private inputs."
    )
    parser.add_argument(
        "--hash",
        type=Path,
        help="Hash output JSON under workspace/local-private/extraction-indexing/hash/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional review JSON under workspace/local-private/extraction-indexing/hash-review/.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Optional review Markdown under workspace/local-private/extraction-indexing/hash-review/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace hash review smoke that does not need private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Dry-run summary hash review self-test passed.")
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

        if args.hash is None:
            parser.error("--hash is required unless --self-test is used.")

        hash_path = resolve_hash_input_path(args.hash, root=ROOT)
        payload = load_json(hash_path)
        review = build_review(payload, hash_path=hash_path, root=ROOT)

        if review["hash_output_valid"]:
            if args.output:
                write_json_review(review, resolve_review_output_path(args.output, root=ROOT))
            if args.markdown_output:
                write_markdown_review(
                    review,
                    resolve_review_output_path(args.markdown_output, root=ROOT),
                )

        if args.quiet:
            print(
                "Dry-run summary hash review passed."
                if review["hash_output_valid"]
                else "Dry-run summary hash review failed."
            )
        else:
            print(json.dumps(review, indent=2, sort_keys=True))
        return 0 if review["hash_output_valid"] else 1
    except (OSError, ValueError, DryRunSummaryHashReviewError) as exc:
        parser.error(str(exc))
    return 0


def build_review(
    hash_output: dict[str, Any],
    *,
    hash_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = collect_hash_output_errors(hash_output, hash_path=hash_path, root=root)
    blockers = _dedupe([_blocker_for_error(error) for error in errors])
    ready_for_private_index_decision = not errors and not blockers
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "hash_output_valid": not errors,
        "hash_algorithm": hash_output.get("hash_algorithm")
        if isinstance(hash_output, dict)
        else "",
        "hash_input_kind": (
            hash_output.get("hash_input_kind") if isinstance(hash_output, dict) else ""
        ),
        "digest_present": _digest_present(hash_output),
        "file_content_hashing": False,
        "path_string_hashing": False,
        "filename_hashing": False,
        "raw_payload_hashing": False,
        "private_index_construction": False,
        "real_extraction": False,
        "private_paths_included": False,
        "raw_payloads_included": False,
        "raw_logs_included": False,
        "real_text_included": False,
        "file_contents_read": False,
        "original_private_input_read": False,
        "original_summary_read": False,
        "private_index_construction_allowed_next": False,
        "ready_for_private_index_decision": ready_for_private_index_decision,
        "blockers": blockers,
        "recommended_next_step": (
            RECOMMENDED_INDEX_CONTRACT_STEP
            if ready_for_private_index_decision
            else RECOMMENDED_REPEAT_HASH_STEP
        ),
        "hash_path_redacted": True,
        "review_output_private_only": True,
    }


def collect_hash_output_errors(
    hash_output: Any,
    *,
    hash_path: Path,
    root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    try:
        resolve_hash_input_path(hash_path, root=root)
    except DryRunSummaryHashReviewError as exc:
        errors.append(str(exc))

    if not isinstance(hash_output, dict):
        return errors + ["Dry-run summary hash output must be a JSON object."]

    if hash_output.get("schema_version") != HASH_SCHEMA_VERSION:
        errors.append(f"Hash output schema_version must be {HASH_SCHEMA_VERSION!r}.")
    if hash_output.get("source_summary_valid") is not True:
        errors.append("Hash output must set source_summary_valid=true.")
    if hash_output.get("hash_algorithm") != HASH_ALGORITHM:
        errors.append(f"Hash output hash_algorithm must be {HASH_ALGORITHM!r}.")
    if hash_output.get("hash_input_kind") != HASH_INPUT_KIND:
        errors.append(f"Hash output hash_input_kind must be {HASH_INPUT_KIND!r}.")
    if not _digest_present(hash_output):
        errors.append("Hash output digest must be a lowercase 64-character SHA-256 hex string.")
    if not isinstance(hash_output.get("canonical_field_count"), int):
        errors.append("Hash output canonical_field_count must be an integer.")
    elif hash_output["canonical_field_count"] <= 0:
        errors.append("Hash output canonical_field_count must be positive.")
    if hash_output.get("summary_hash_computed") is not True:
        errors.append("Hash output must set summary_hash_computed=true.")

    for field in FALSE_OUTPUT_FIELDS:
        if not isinstance(hash_output.get(field), bool):
            errors.append(f"Hash output safety field {field!r} must be a boolean.")
        elif hash_output.get(field) is not False:
            errors.append(f"Hash output safety field {field!r} must remain false.")
    for field in FORBIDDEN_HASH_FIELDS:
        if field in hash_output:
            errors.append(f"Hash output must not include private/raw field {field!r}.")

    errors.extend(_unsafe_value_errors(hash_output, label="Hash output"))
    return _dedupe(errors)


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load dry-run summary hash decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["Dry-run summary hash decision fixture must be a JSON object."]

    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"Decision fixture schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("milestone") != MILESTONE:
        errors.append(f"Decision fixture milestone must be {MILESTONE!r}.")
    if payload.get("hash_evidence_required") is not True:
        errors.append("Decision fixture must require hash evidence.")
    if payload.get("private_index_contract_allowed_next") != "decision_pending":
        errors.append(
            "Decision fixture private_index_contract_allowed_next must be decision_pending."
        )
    if payload.get("recommended_next_step") != RECOMMENDED_INDEX_CONTRACT_STEP:
        errors.append(
            f"Decision fixture recommended_next_step must be {RECOMMENDED_INDEX_CONTRACT_STEP!r}."
        )
    for field in DECISION_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"Decision fixture must keep {field}=false.")
    errors.extend(_unsafe_value_errors(payload, label="Decision fixture"))
    return _dedupe(errors)


def resolve_hash_input_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    hash_root = (root / HASH_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, hash_root):
        raise DryRunSummaryHashReviewError(
            "Unsafe hash input path. Use workspace/local-private/extraction-indexing/hash/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise DryRunSummaryHashReviewError(
            "Dry-run summary hash path must point to an existing file."
        )
    return resolved


def resolve_review_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    review_root = (root / HASH_REVIEW_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, review_root):
        raise DryRunSummaryHashReviewError(
            "Unsafe hash review output path. Use workspace/local-private/extraction-indexing/hash-review/."
        )
    if resolved.exists() and resolved.is_dir():
        raise DryRunSummaryHashReviewError("Hash review output path must be a file path.")
    return resolved


def write_json_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dry-Run Summary Hash Review",
        "",
        f"- hash_output_valid: {_yes_no(review['hash_output_valid'])}",
        f"- digest_present: {_yes_no(review['digest_present'])}",
        f"- ready_for_private_index_decision: {_yes_no(review['ready_for_private_index_decision'])}",
        "- private_index_construction_allowed_next: no",
        "- file_content_hashing: no",
        "- path_string_hashing: no",
        "- filename_hashing: no",
        "- raw_payload_hashing: no",
        "- real_extraction: no",
        f"- recommended_next_step: {review['recommended_next_step']}",
    ]
    if review["blockers"]:
        lines.extend(["", "## Blockers"])
        lines.extend(f"- {blocker}" for blocker in review["blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_self_test() -> None:
    decision_errors = collect_decision_fixture_errors()
    if decision_errors:
        raise DryRunSummaryHashReviewError("; ".join(decision_errors))

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        selected = root / PRIVATE_INPUT_ROOT / "selected"
        selected.mkdir(parents=True)
        private_text = "PRIVATE_CONTENT_SHOULD_NOT_APPEAR"
        (selected / "record.txt").write_text(private_text, encoding="utf-8")

        summary = build_dry_run_summary(Path(PRIVATE_INPUT_ROOT) / "selected", root=root)
        summary_path = root / PRIVATE_OUTPUT_ROOT / "summary.json"
        write_dry_run_summary(summary, summary_path)
        hash_output = build_hash_summary(
            load_json(summary_path), summary_path=summary_path, root=root
        )
        hash_path = root / HASH_OUTPUT_ROOT / "hash.json"
        write_hash_summary(hash_output, hash_path)

        review = build_review(load_json(hash_path), hash_path=hash_path, root=root)
        rendered = json.dumps(review, sort_keys=True)
        if not review["hash_output_valid"] or not review["ready_for_private_index_decision"]:
            raise DryRunSummaryHashReviewError("Self-test expected ready redacted hash review.")
        if review["private_index_construction_allowed_next"]:
            raise DryRunSummaryHashReviewError(
                "Self-test must not allow private index construction."
            )
        if private_text in rendered or str(root) in rendered:
            raise DryRunSummaryHashReviewError("Self-test review leaked private content or paths.")

        review_path = root / HASH_REVIEW_OUTPUT_ROOT / "review.json"
        markdown_path = root / HASH_REVIEW_OUTPUT_ROOT / "review.md"
        write_json_review(review, resolve_review_output_path(review_path, root=root))
        write_markdown_review(review, resolve_review_output_path(markdown_path, root=root))
        if private_text in review_path.read_text(encoding="utf-8"):
            raise DryRunSummaryHashReviewError("Self-test JSON review leaked private content.")
        if private_text in markdown_path.read_text(encoding="utf-8"):
            raise DryRunSummaryHashReviewError("Self-test Markdown review leaked private content.")


def _digest_present(hash_output: Any) -> bool:
    return (
        isinstance(hash_output, dict)
        and isinstance(hash_output.get("digest"), str)
        and bool(HEX_DIGEST_PATTERN.fullmatch(hash_output["digest"]))
    )


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
        for marker in FORBIDDEN_HASH_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{label} contains forbidden marker {marker!r}.")
    return errors


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise DryRunSummaryHashReviewError("Unsafe path traversal is not allowed.")
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
        "provider-payload",
        "generated-index",
    ):
        if marker in normalized:
            raise DryRunSummaryHashReviewError("Path uses a forbidden runtime/private marker.")


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute() or WINDOWS_ABSOLUTE_PATH_PATTERN.match(str(raw)):
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _blocker_for_error(error: str) -> str:
    lowered = error.lower()
    if "schema_version" in lowered or "json object" in lowered:
        return "malformed_hash_output"
    if "digest" in lowered or "hash_algorithm" in lowered or "hash_input_kind" in lowered:
        return "invalid_hash_evidence"
    if "path" in lowered:
        return "private_path_or_unsafe_path"
    if "marker" in lowered or "payload" in lowered or "log" in lowered:
        return "unsafe_marker_detected"
    if "remain false" in lowered or "private/raw field" in lowered:
        return "unsafe_hash_flags"
    return "invalid_hash_output"


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
