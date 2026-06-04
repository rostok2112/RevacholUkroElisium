from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_line_index_contract import LINE_INDEX_SCHEMA_VERSION
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_m2_line_index_contract import LINE_INDEX_SCHEMA_VERSION
    from schema_validator import load_json
    from synthetic_slice import ROOT


EVENT_SCHEMA_VERSION = "m3-current-line-event.v1"
SUMMARY_SCHEMA_VERSION = "m3-line-id-match-summary.v1"
EVENT_INPUT_ROOT = "workspace/local-private/bepinex/current-line/"
PRIVATE_LINE_INDEX_ROOT = "workspace/local-private/extraction-indexing/import/line-index/"
MATCH_OUTPUT_ROOT = "workspace/local-private/bepinex/line-id-match/"
MATCH_STATUSES = {"matched", "unmatched", "invalid"}


class M3LineIdMatchError(RuntimeError):
    """Raised when an M3 line-ID match request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Match one redacted M3 current-line event against one ignored private M2 line-index "
            "artifact by exact line_id only."
        )
    )
    parser.add_argument(
        "--event", type=Path, help="Current-line event JSON under bepinex/current-line/."
    )
    parser.add_argument(
        "--line-index",
        type=Path,
        help="Private M2 line-index JSON under extraction-indexing/import/line-index/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional redacted match summary JSON under bepinex/line-id-match/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M3 line-ID match self-test passed.")
            else:
                print(json.dumps({"ok": True, "schema_version": "m3-line-id-match-self-test.v1"}))
            return 0
        if args.event is None or args.line_index is None:
            parser.error("--event and --line-index are required unless --self-test is used.")
        summary = run_m3_line_id_match(args.event, args.line_index, root=ROOT)
        if args.output:
            write_summary(summary, resolve_match_output_path(args.output, root=ROOT))
        if args.quiet:
            print("M3 line-ID match passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (M3LineIdMatchError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def run_m3_line_id_match(
    event_path: Path, line_index_path: Path, *, root: Path = ROOT
) -> dict[str, Any]:
    resolved_event = resolve_event_input_path(event_path, root=root)
    resolved_line_index = resolve_line_index_input_path(line_index_path, root=root)
    summary = _base_summary()
    summary["event_input_exists"] = resolved_event.exists()
    summary["line_index_input_exists"] = resolved_line_index.exists()

    if (
        _raw_path(event_path, root=root).is_symlink()
        or _raw_path(line_index_path, root=root).is_symlink()
    ):
        summary["blocker_categories"].append("symlink_input_rejected")
        return _finalize(summary)
    if not resolved_event.exists() or not resolved_line_index.exists():
        summary["blocker_categories"].append("input_missing")
        return _finalize(summary)
    if not resolved_event.is_file() or not resolved_line_index.is_file():
        summary["blocker_categories"].append("file_input_required")
        return _finalize(summary)

    try:
        event = load_json(resolved_event)
        line_index = load_json(resolved_line_index)
    except Exception:
        summary["match_status"] = "invalid"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    event_errors = collect_event_errors(event)
    index_errors = collect_line_index_errors(line_index)
    if event_errors or index_errors:
        summary["blocker_categories"].extend(event_errors)
        summary["blocker_categories"].extend(index_errors)
        return _finalize(summary)

    summary["event_schema_valid"] = True
    summary["line_index_schema_valid"] = True
    entries = line_index["entries"]
    summary["line_index_entry_count"] = len(entries)
    event_line_id = event.get("line_id")
    summary["event_line_id_present"] = isinstance(event_line_id, str) and bool(event_line_id)
    if not summary["event_line_id_present"]:
        summary["blocker_categories"].append("event_line_id_missing")
        return _finalize(summary)

    line_ids = {entry["line_id"] for entry in entries if isinstance(entry.get("line_id"), str)}
    summary["exact_match_attempted"] = True
    summary["exact_line_id_match"] = event_line_id in line_ids
    summary["matched_entry_count"] = 1 if summary["exact_line_id_match"] else 0
    summary["match_status"] = "matched" if summary["exact_line_id_match"] else "unmatched"
    summary["m3_line_id_matching_done"] = summary["exact_line_id_match"]
    if not summary["exact_line_id_match"]:
        summary["blocker_categories"].append("exact_line_id_not_found")
    return _finalize(summary)


def collect_event_errors(event: Any) -> list[str]:
    if not isinstance(event, dict):
        return ["event_json_object_required"]
    errors: list[str] = []
    if event.get("schema_version") != EVENT_SCHEMA_VERSION:
        errors.append("event_schema_version_mismatch")
    if event.get("event_kind") != "current_line":
        errors.append("event_kind_mismatch")
    if event.get("bridge_source") != "bepinex":
        errors.append("event_bridge_source_mismatch")
    if event.get("source") not in {"synthetic", "runtime_metadata"}:
        errors.append("event_source_mismatch")
    if not isinstance(event.get("emitted_at_unix_ms"), int):
        errors.append("event_timestamp_type_mismatch")
    if event.get("raw_text_included") is not False:
        errors.append("event_raw_text_included")
    if event.get("private_paths_included") is not False:
        errors.append("event_private_paths_included")
    if event.get("provider_called") is not False:
        errors.append("event_provider_called")
    if event.get("line_id") is not None and not isinstance(event.get("line_id"), str):
        errors.append("event_line_id_type_mismatch")
    if event.get("conversation_id") is not None and not isinstance(
        event.get("conversation_id"), str
    ):
        errors.append("event_conversation_id_type_mismatch")
    return errors + _unsafe_value_errors(event, label="event")


def collect_line_index_errors(line_index: Any) -> list[str]:
    if not isinstance(line_index, dict):
        return ["line_index_json_object_required"]
    errors: list[str] = []
    if line_index.get("schema_version") != LINE_INDEX_SCHEMA_VERSION:
        errors.append("line_index_schema_version_mismatch")
    entries = line_index.get("entries")
    if not isinstance(entries, list):
        errors.append("line_index_entries_array_required")
        return errors
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("line_id"), str):
            errors.append("line_index_entry_line_id_required")
            break
    if line_index.get("context_graph_constructed") is not False:
        errors.append("line_index_context_graph_already_constructed")
    return errors


def resolve_event_input_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_private_path(
        path, root=root, allowed_root=EVENT_INPUT_ROOT, label="event input"
    )


def resolve_line_index_input_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_private_path(
        path,
        root=root,
        allowed_root=PRIVATE_LINE_INDEX_ROOT,
        label="line-index input",
    )


def resolve_match_output_path(path: Path, *, root: Path = ROOT) -> Path:
    resolved = _resolve_private_path(
        path,
        root=root,
        allowed_root=MATCH_OUTPUT_ROOT,
        label="match output",
        must_exist=False,
    )
    if resolved.suffix.lower() != ".json":
        raise M3LineIdMatchError("M3 line-ID match output path must use the .json suffix.")
    return resolved


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_marker = "PRIVATE_M3_LINE_MATCH_VALUE_SHOULD_NOT_APPEAR"
        event_path = root / EVENT_INPUT_ROOT / "event.json"
        index_path = root / PRIVATE_LINE_INDEX_ROOT / "line-index.json"
        event_path.parent.mkdir(parents=True)
        index_path.parent.mkdir(parents=True)
        event_path.write_text(json.dumps(_compatible_event(private_marker)), encoding="utf-8")
        index_path.write_text(json.dumps(_compatible_line_index(private_marker)), encoding="utf-8")
        summary = run_m3_line_id_match(
            Path(EVENT_INPUT_ROOT) / "event.json",
            Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json",
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if summary["match_status"] != "matched" or not summary["m3_line_id_matching_done"]:
            raise M3LineIdMatchError("Self-test expected exact line-ID match.")
        if private_marker in rendered or str(root) in rendered:
            raise M3LineIdMatchError("Self-test summary leaked private line IDs or paths.")
        output_path = resolve_match_output_path(Path(MATCH_OUTPUT_ROOT) / "summary.json", root=root)
        write_summary(summary, output_path)
        written = output_path.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M3LineIdMatchError("Self-test output leaked private line IDs or paths.")


def _resolve_private_path(
    path: Path,
    *,
    root: Path,
    allowed_root: str,
    label: str,
    must_exist: bool = True,
) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    base = (root / allowed_root).resolve(strict=False)
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise M3LineIdMatchError(f"Unsafe {label} path. Use {allowed_root}.") from exc
    if must_exist and not resolved.exists():
        raise M3LineIdMatchError(f"M3 {label} path must point to an existing file.")
    if must_exist and not resolved.is_file():
        raise M3LineIdMatchError(f"M3 {label} path must point to a file.")
    if _raw_path(path, root=root).is_symlink():
        raise M3LineIdMatchError(f"M3 {label} path must not be a symlink.")
    return resolved


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise M3LineIdMatchError("Unsafe path traversal is not allowed.")
    for marker in (
        "logoutput.log",
        "player.log",
        "steamapps",
        "screenshot",
        "ocr",
        ".sav",
        "raw-payload",
        "payload-dump",
        "raw payload",
        "raw-log",
        "raw log",
        "decompiled",
    ):
        if marker in normalized:
            raise M3LineIdMatchError("Path uses a forbidden runtime/private marker.")


def _unsafe_value_errors(value: Any, *, label: str) -> list[str]:
    errors: list[str] = []
    for string_value in _iter_string_values(value):
        lowered = string_value.lower()
        if "raw payload" in lowered or "payload dump" in lowered or "raw log" in lowered:
            errors.append(f"{label}_unsafe_marker")
        if "logoutput.log" in lowered or "player.log" in lowered or "screenshot" in lowered:
            errors.append(f"{label}_runtime_marker")
    return errors


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_string_values(nested)


def _raw_path(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute():
        return raw
    return root / raw


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute():
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    summary["blocker_categories"] = list(dict.fromkeys(summary["blocker_categories"]))
    if summary["blocker_categories"] and summary["match_status"] != "invalid":
        summary["match_status"] = "unmatched"
    return summary


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "event_input_exists": False,
        "line_index_input_exists": False,
        "event_schema_valid": False,
        "line_index_schema_valid": False,
        "event_line_id_present": False,
        "line_index_entry_count": 0,
        "exact_match_attempted": False,
        "exact_line_id_match": False,
        "matched_entry_count": 0,
        "match_status": "invalid",
        "blocker_categories": [],
        "m3_current_line_event_done": True,
        "m3_line_id_matching_done": False,
        "m3_debug_console_done": False,
        "fuzzy_matching_used": False,
        "line_ids_included": False,
        "record_ids_included": False,
        "source_text_included": False,
        "private_paths_included": False,
        "hashes_computed": False,
        "provider_called": False,
        "companion_contract_changed": False,
        "game_files_read": False,
        "bepinex_logs_read": False,
        "ui_text_reading_used": False,
        "unity_scanning_used": False,
        "hooks_used": False,
        "ocr_used": False,
    }


def _compatible_event(private_marker: str) -> dict[str, Any]:
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_kind": "current_line",
        "bridge_source": "bepinex",
        "emitted_at_unix_ms": 1,
        "line_id": private_marker,
        "conversation_id": "redacted",
        "source": "synthetic",
        "capture_enabled": False,
        "raw_text_included": False,
        "private_paths_included": False,
        "provider_called": False,
    }


def _compatible_line_index(private_marker: str) -> dict[str, Any]:
    return {
        "schema_version": LINE_INDEX_SCHEMA_VERSION,
        "entries": [
            {
                "record_id": private_marker,
                "line_id": private_marker,
                "conversation_id": private_marker,
                "speaker_id": private_marker,
                "context_placeholder": private_marker,
                "source_text": private_marker,
                "context_tags": [private_marker],
            }
        ],
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
    }


if __name__ == "__main__":
    sys.exit(main())
