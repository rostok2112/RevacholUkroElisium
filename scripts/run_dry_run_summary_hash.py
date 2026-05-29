from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_dry_run_summary_hash_contract import (
        ALLOWED_CANONICAL_SUMMARY_FIELDS,
        EXCLUDED_HASH_INPUT_FIELDS,
    )
    from scripts.review_private_input_adapter_dry_run import (
        collect_summary_errors,
        resolve_summary_path as resolve_reviewed_summary_path,
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
    from check_dry_run_summary_hash_contract import (
        ALLOWED_CANONICAL_SUMMARY_FIELDS,
        EXCLUDED_HASH_INPUT_FIELDS,
    )
    from review_private_input_adapter_dry_run import (
        collect_summary_errors,
        resolve_summary_path as resolve_reviewed_summary_path,
    )
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PRIVATE_OUTPUT_ROOT,
        build_dry_run_summary,
        write_summary as write_dry_run_summary,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


HASH_SCHEMA_VERSION = "dry-run-summary-hash.v1"
SELF_TEST_SCHEMA_VERSION = "dry-run-summary-hash-self-test.v1"
HASH_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/hash/"
HASH_ALGORITHM = "sha256"
HASH_INPUT_KIND = "canonical_redacted_dry_run_summary"

FALSE_OUTPUT_FIELDS = (
    "file_content_hashing",
    "path_string_hashing",
    "filename_hashing",
    "raw_payload_hashing",
    "raw_log_hashing",
    "screenshot_hashing",
    "ocr_hashing",
    "save_file_hashing",
    "decompiled_output_hashing",
    "provider_payload_hashing",
    "generated_index_hashing",
    "private_index_construction",
    "real_extraction",
    "raw_paths_included",
    "raw_payloads_included",
    "raw_logs_included",
    "real_text_included",
    "file_contents_read",
    "original_private_input_read",
    "companion_contract_changed",
    "provider_called",
)


class DryRunSummaryHashError(RuntimeError):
    """Raised when a dry-run summary hash request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hash only canonical redacted private-input dry-run summary metadata."
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="Dry-run summary JSON under workspace/local-private/extraction-indexing/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output under workspace/local-private/extraction-indexing/hash/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace hash smoke that does not need real private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Dry-run summary hash self-test passed.")
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
        summary = load_json(summary_path)
        hash_summary = build_hash_summary(summary, summary_path=summary_path, root=ROOT)

        if args.output:
            write_hash_summary(hash_summary, resolve_hash_output_path(args.output, root=ROOT))

        if args.quiet:
            print("Dry-run summary hash passed.")
        else:
            print(json.dumps(hash_summary, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, DryRunSummaryHashError) as exc:
        parser.error(str(exc))
    return 0


def build_hash_summary(
    summary: dict[str, Any],
    *,
    summary_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = collect_hash_source_errors(summary, summary_path=summary_path, root=root)
    if errors:
        raise DryRunSummaryHashError("; ".join(errors))

    canonical = canonicalize_summary(summary)
    canonical_json = canonical_summary_json(canonical)
    digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    output: dict[str, Any] = {
        "schema_version": HASH_SCHEMA_VERSION,
        "source_summary_valid": True,
        "hash_algorithm": HASH_ALGORITHM,
        "hash_input_kind": HASH_INPUT_KIND,
        "digest": digest,
        "canonical_field_count": len(canonical),
        "summary_hash_computed": True,
    }
    for field in FALSE_OUTPUT_FIELDS:
        output[field] = False
    return output


def canonicalize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    canonical: dict[str, Any] = {}
    for field in ALLOWED_CANONICAL_SUMMARY_FIELDS:
        value = summary[field]
        if field == "blocker_categories":
            value = sorted(value)
        canonical[field] = value
    return canonical


def canonical_summary_json(canonical: dict[str, Any]) -> str:
    return json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def collect_hash_source_errors(
    summary: Any,
    *,
    summary_path: Path,
    root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    try:
        resolve_summary_path(summary_path, root=root)
    except DryRunSummaryHashError as exc:
        errors.append(str(exc))

    if not isinstance(summary, dict):
        return errors + ["Dry-run summary hash source must be a JSON object."]

    review_errors = collect_summary_errors(summary, summary_path=summary_path, root=root)
    errors.extend(review_errors)

    summary_keys = set(summary)
    allowed_keys = set(ALLOWED_CANONICAL_SUMMARY_FIELDS)
    excluded_present = sorted(summary_keys & set(EXCLUDED_HASH_INPUT_FIELDS))
    if excluded_present:
        errors.append(
            "Dry-run summary contains fields that are excluded from hashing: "
            + ", ".join(excluded_present)
            + "."
        )
    unknown_present = sorted(summary_keys - allowed_keys - set(EXCLUDED_HASH_INPUT_FIELDS))
    if unknown_present:
        errors.append(
            "Dry-run summary contains unknown fields that are not allowed for hashing: "
            + ", ".join(unknown_present)
            + "."
        )
    missing_allowed = sorted(allowed_keys - summary_keys)
    if missing_allowed:
        errors.append(
            "Dry-run summary is missing canonical hash fields: " + ", ".join(missing_allowed) + "."
        )
    if summary.get("hashes_computed") is not False:
        errors.append("Dry-run summary must keep hashes_computed=false before hashing.")
    return _dedupe(errors)


def resolve_summary_path(path: Path, *, root: Path = ROOT) -> Path:
    try:
        return resolve_reviewed_summary_path(path, root=root)
    except Exception as exc:
        raise DryRunSummaryHashError(str(exc)) from exc


def resolve_hash_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    output_root = (root / HASH_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise DryRunSummaryHashError(
            "Unsafe hash output path. Use workspace/local-private/extraction-indexing/hash/."
        )
    if resolved.exists() and resolved.is_dir():
        raise DryRunSummaryHashError("Hash output path must be a JSON file path.")
    return resolved


def write_hash_summary(hash_summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(hash_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_self_test() -> None:
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
        hash_summary = build_hash_summary(payload, summary_path=summary_path, root=root)
        rendered = json.dumps(hash_summary, sort_keys=True)
        if hash_summary["hash_algorithm"] != HASH_ALGORITHM or not hash_summary["digest"]:
            raise DryRunSummaryHashError("Self-test did not produce a SHA-256 digest.")
        if private_text in rendered or str(root) in rendered:
            raise DryRunSummaryHashError("Self-test hash summary leaked private content or paths.")
        if any(hash_summary[field] for field in FALSE_OUTPUT_FIELDS):
            raise DryRunSummaryHashError("Self-test hash summary enabled a forbidden behavior.")

        output = resolve_hash_output_path(Path(HASH_OUTPUT_ROOT) / "self-test-hash.json", root=root)
        write_hash_summary(hash_summary, output)
        written = output.read_text(encoding="utf-8")
        if private_text in written or str(root) in written:
            raise DryRunSummaryHashError("Self-test written hash leaked private content or paths.")


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise DryRunSummaryHashError("Unsafe path traversal is not allowed.")
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
            raise DryRunSummaryHashError("Path uses a forbidden runtime/private marker.")


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute():
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped


if __name__ == "__main__":
    sys.exit(main())
