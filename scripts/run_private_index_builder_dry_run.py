from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.review_dry_run_summary_hash import collect_hash_output_errors
    from scripts.review_private_input_adapter_dry_run import collect_summary_errors
    from scripts.run_dry_run_summary_hash import (
        HASH_OUTPUT_ROOT,
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
    from review_dry_run_summary_hash import collect_hash_output_errors
    from review_private_input_adapter_dry_run import collect_summary_errors
    from run_dry_run_summary_hash import (
        HASH_OUTPUT_ROOT,
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


INDEX_DRY_RUN_SCHEMA_VERSION = "private-index-dry-run.v1"
SELF_TEST_SCHEMA_VERSION = "private-index-builder-dry-run-self-test.v1"
PRIVATE_INDEX_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/index/"
PRIVATE_INDEX_CONSTRUCTION_MODE = "dry_run"

FALSE_SAFETY_FIELDS = (
    "real_text_included",
    "file_contents_included",
    "paths_included",
    "filenames_included",
    "raw_payloads_included",
    "logs_included",
    "screenshots_included",
    "ocr_included",
    "save_files_included",
    "decompiled_code_included",
    "provider_payloads_included",
    "companion_runtime_data_included",
    "real_extraction",
    "automatic_game_install_scanning",
    "file_content_hashing",
    "path_string_hashing",
    "filename_hashing",
    "current_line_capture",
    "ui_text_reading",
    "unity_scanning",
    "hooks_used",
    "companion_contract_changed",
    "provider_called",
    "original_private_input_read",
    "file_contents_read",
)

FORBIDDEN_SOURCE_FIELDS = {
    "source_path",
    "summary_path",
    "hash_path",
    "input_path",
    "allowed_root_path",
    "output_path",
    "filename",
    "filenames",
    "directory_name",
    "path",
    "paths",
    "canonical_json",
    "source_summary",
    "original_summary",
    "digest_source_path",
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
}

FORBIDDEN_VALUE_MARKERS = (
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


class PrivateIndexBuilderDryRunError(RuntimeError):
    """Raised when a private index builder dry-run request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a redacted private index dry-run from reviewed metadata evidence."
    )
    parser.add_argument(
        "--dry-run-summary",
        type=Path,
        help="Dry-run summary JSON under workspace/local-private/extraction-indexing/.",
    )
    parser.add_argument(
        "--summary-hash",
        type=Path,
        help="Hash JSON under workspace/local-private/extraction-indexing/hash/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output under workspace/local-private/extraction-indexing/index/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace dry-run smoke that does not need private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Private index builder dry-run self-test passed.")
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

        if args.dry_run_summary is None or args.summary_hash is None:
            parser.error(
                "--dry-run-summary and --summary-hash are required unless --self-test is used."
            )

        summary_path = resolve_summary_input_path(args.dry_run_summary, root=ROOT)
        hash_path = resolve_hash_input_path(args.summary_hash, root=ROOT)
        index = build_private_index_dry_run(
            load_json(summary_path),
            load_json(hash_path),
            summary_path=summary_path,
            hash_path=hash_path,
            root=ROOT,
        )

        if args.output:
            write_private_index_dry_run(index, resolve_output_path(args.output, root=ROOT))

        if args.quiet:
            print("Private index builder dry-run passed.")
        else:
            print(json.dumps(index, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, PrivateIndexBuilderDryRunError) as exc:
        parser.error(str(exc))
    return 0


def build_private_index_dry_run(
    summary: dict[str, Any],
    hash_output: dict[str, Any],
    *,
    summary_path: Path,
    hash_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = collect_index_source_errors(
        summary,
        hash_output,
        summary_path=summary_path,
        hash_path=hash_path,
        root=root,
    )
    if errors:
        raise PrivateIndexBuilderDryRunError("; ".join(errors))

    output: dict[str, Any] = {
        "schema_version": INDEX_DRY_RUN_SCHEMA_VERSION,
        "source_summary_valid": True,
        "source_hash_valid": True,
        "record_count": 1,
        "file_count": _safe_int(summary.get("file_count")),
        "directory_count": _safe_int(summary.get("directory_count")),
        "total_size_bytes": _safe_int(summary.get("total_size_bytes")),
        "summary_digest_present": _digest_present(hash_output),
        "generated_from_redacted_metadata": True,
        "private_index_construction_mode": PRIVATE_INDEX_CONSTRUCTION_MODE,
        "blockers": [],
        "summary_hash_linkage_checked": False,
        "summary_hash_linkage_reason": "no_safe_shared_identifier",
    }
    for field in FALSE_SAFETY_FIELDS:
        output[field] = False
    return output


def collect_index_source_errors(
    summary: Any,
    hash_output: Any,
    *,
    summary_path: Path,
    hash_path: Path,
    root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    try:
        resolve_summary_input_path(summary_path, root=root)
    except PrivateIndexBuilderDryRunError as exc:
        errors.append(str(exc))
    try:
        resolve_hash_input_path(hash_path, root=root)
    except PrivateIndexBuilderDryRunError as exc:
        errors.append(str(exc))

    if not isinstance(summary, dict):
        errors.append("Dry-run summary must be a JSON object.")
    else:
        errors.extend(collect_summary_errors(summary, summary_path=summary_path, root=root))
        if summary.get("input_exists") is not True:
            errors.append(
                "Private index dry-run requires an existing redacted dry-run input summary."
            )
        if summary.get("input_kind") not in {"file", "directory"}:
            errors.append("Private index dry-run requires a file or directory input_kind summary.")
        blockers = summary.get("blocker_categories")
        if blockers:
            errors.append("Private index dry-run requires summary blocker_categories to be empty.")
        errors.extend(_forbidden_field_errors(summary, label="Dry-run summary"))
        errors.extend(_unsafe_value_errors(summary, label="Dry-run summary"))

    if not isinstance(hash_output, dict):
        errors.append("Dry-run summary hash output must be a JSON object.")
    else:
        errors.extend(collect_hash_output_errors(hash_output, hash_path=hash_path, root=root))
        errors.extend(_forbidden_field_errors(hash_output, label="Hash output"))
        errors.extend(_unsafe_value_errors(hash_output, label="Hash output"))

    return _dedupe(errors)


def resolve_summary_input_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise PrivateIndexBuilderDryRunError(
            "Unsafe dry-run summary path. Use workspace/local-private/extraction-indexing/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise PrivateIndexBuilderDryRunError("Dry-run summary path must point to an existing file.")
    return resolved


def resolve_hash_input_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    hash_root = (root / HASH_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, hash_root):
        raise PrivateIndexBuilderDryRunError(
            "Unsafe summary hash path. Use workspace/local-private/extraction-indexing/hash/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise PrivateIndexBuilderDryRunError(
            "Dry-run summary hash path must point to an existing file."
        )
    return resolved


def resolve_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    output_root = (root / PRIVATE_INDEX_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise PrivateIndexBuilderDryRunError(
            "Unsafe private index dry-run output path. Use workspace/local-private/extraction-indexing/index/."
        )
    if resolved.exists() and resolved.is_dir():
        raise PrivateIndexBuilderDryRunError("Private index dry-run output path must be a file.")
    return resolved


def write_private_index_dry_run(index: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
        hash_output = build_hash_summary(
            load_json(summary_path), summary_path=summary_path, root=root
        )
        hash_path = root / HASH_OUTPUT_ROOT / "hash.json"
        write_hash_summary(hash_output, hash_path)

        index = build_private_index_dry_run(
            load_json(summary_path),
            load_json(hash_path),
            summary_path=summary_path,
            hash_path=hash_path,
            root=root,
        )
        rendered = json.dumps(index, sort_keys=True)
        if index["private_index_construction_mode"] != PRIVATE_INDEX_CONSTRUCTION_MODE:
            raise PrivateIndexBuilderDryRunError("Self-test did not produce dry-run mode output.")
        if index["record_count"] != 1 or not index["summary_digest_present"]:
            raise PrivateIndexBuilderDryRunError("Self-test dry-run index summary was incomplete.")
        if private_text in rendered or str(root) in rendered:
            raise PrivateIndexBuilderDryRunError(
                "Self-test private index dry-run leaked private content or paths."
            )
        if any(index[field] for field in FALSE_SAFETY_FIELDS):
            raise PrivateIndexBuilderDryRunError("Self-test enabled a forbidden behavior.")

        output = resolve_output_path(
            Path(PRIVATE_INDEX_OUTPUT_ROOT) / "self-test-index.json",
            root=root,
        )
        write_private_index_dry_run(index, output)
        written = output.read_text(encoding="utf-8")
        if private_text in written or str(root) in written:
            raise PrivateIndexBuilderDryRunError(
                "Self-test written dry-run index leaked private content or paths."
            )


def _forbidden_field_errors(value: Any, *, label: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_SOURCE_FIELDS:
                errors.append(f"{label} must not include private/raw field {key!r}.")
            errors.extend(_forbidden_field_errors(child, label=label))
    elif isinstance(value, list):
        for child in value:
            errors.extend(_forbidden_field_errors(child, label=label))
    return errors


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
        raise PrivateIndexBuilderDryRunError("Unsafe path traversal is not allowed.")
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
            raise PrivateIndexBuilderDryRunError("Path uses a forbidden runtime/private marker.")


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute() or WINDOWS_ABSOLUTE_PATH_PATTERN.match(str(raw)):
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _digest_present(hash_output: Any) -> bool:
    digest = hash_output.get("digest") if isinstance(hash_output, dict) else None
    return isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest))


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


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
