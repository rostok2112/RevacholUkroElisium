from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any

try:
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "runtime-translation-memory-summary.v1"
ENTRY_SCHEMA_VERSION = "runtime-translation-memory-entry.v1"
PRIVATE_EVENT_ROOT = "workspace/local-private/runtime-events/"
PRIVATE_ANNOTATION_ROOT = "workspace/local-private/runtime-annotations/"
PRIVATE_CACHE_ROOT = "workspace/local-private/runtime-cache/translation-memory/"
PRIVATE_SUMMARY_ROOT = "workspace/local-private/runtime-cache/translation-memory-summary/"
MODES = {"lookup", "store", "lookup-or-store"}

FORBIDDEN_PATH_MARKERS = (
    "logoutput.log",
    "player.log",
    "steamapps",
    "gameassembly.dll",
    "globalgamemanagers",
    "screenshot",
    "screen capture",
    "ocr",
    "payload dump",
    "raw payload",
    "raw-payload",
    "raw log",
    "raw-log",
    "dnspy",
    "ilspy",
    "decompiled",
)
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")
SECRET_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|api[_-]?key\s*=|bearer\s+)", re.I)


class RuntimeTranslationMemoryError(RuntimeError):
    """Raised when a runtime translation-memory request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lookup/store local-private runtime translation memory before provider calls."
    )
    parser.add_argument("--event", type=Path, help="Private runtime event JSON.")
    parser.add_argument("--annotation", type=Path, help="Private runtime annotation JSON.")
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=Path(PRIVATE_CACHE_ROOT),
        help="Cache root under workspace/local-private/runtime-cache/translation-memory/.",
    )
    parser.add_argument("--mode", choices=sorted(MODES), default="lookup-or-store")
    parser.add_argument("--summary-output", type=Path, help="Optional redacted summary JSON.")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Runtime translation memory self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": "runtime-translation-memory-self-test.v1",
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0

        if args.event is None:
            parser.error("--event is required unless --self-test is used.")
        if args.annotation is None and args.mode in {"store", "lookup-or-store"}:
            parser.error("--annotation is required for store and lookup-or-store modes.")

        summary = run_translation_memory(
            args.event,
            args.annotation,
            args.cache_root,
            mode=args.mode,
            root=ROOT,
        )
        if args.summary_output:
            write_summary(summary, resolve_summary_output_path(args.summary_output, root=ROOT))
        if args.quiet:
            print("Runtime translation memory passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (OSError, RuntimeTranslationMemoryError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def run_translation_memory(
    event_path: Path,
    annotation_path: Path | None,
    cache_root: Path,
    *,
    mode: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    if mode not in MODES:
        raise RuntimeTranslationMemoryError(f"Unsupported mode: {mode!r}.")
    event_resolved = resolve_private_file_path(event_path, PRIVATE_EVENT_ROOT, "event", root=root)
    annotation_resolved = (
        resolve_private_file_path(annotation_path, PRIVATE_ANNOTATION_ROOT, "annotation", root=root)
        if annotation_path is not None
        else None
    )
    cache_root_resolved = resolve_cache_root(cache_root, root=root)
    summary = _base_summary(mode)
    summary["event_exists"] = event_resolved.exists()
    summary["annotation_provided"] = annotation_resolved is not None

    if _path_without_symlink_resolution(event_path, root=root).is_symlink():
        summary["blocker_categories"].append("event_symlink_rejected")
        return _finalize(summary)
    if not event_resolved.exists() or not event_resolved.is_file():
        summary["blocker_categories"].append("event_missing_or_not_file")
        return _finalize(summary)

    event = _load_json_object(event_resolved, "event", summary)
    if event is None:
        return _finalize(summary)
    key = _cache_key(event)
    summary["key_kind"] = key["kind"]
    entry_path = cache_root_resolved / key["filename"]
    hit = entry_path.exists() and entry_path.is_file() and not entry_path.is_symlink()
    summary["cache_hit"] = hit

    if mode == "lookup":
        return _finalize(summary)

    if hit:
        return _finalize(summary)

    if annotation_resolved is None:
        summary["blocker_categories"].append("annotation_required_for_store")
        return _finalize(summary)
    if _path_without_symlink_resolution(annotation_path, root=root).is_symlink():
        summary["blocker_categories"].append("annotation_symlink_rejected")
        return _finalize(summary)
    if not annotation_resolved.exists() or not annotation_resolved.is_file():
        summary["blocker_categories"].append("annotation_missing_or_not_file")
        return _finalize(summary)
    annotation = _load_json_object(annotation_resolved, "annotation", summary)
    if annotation is None:
        return _finalize(summary)
    _write_cache_entry(entry_path, key["kind"], event, annotation)
    summary["cache_stored"] = True
    summary["cache_entry_count_delta"] = 1
    summary["cache_hit"] = True
    return _finalize(summary)


def build_lookup_summary_for_event(
    event: dict[str, Any],
    cache_root: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    cache_root_resolved = resolve_cache_root(cache_root, root=root)
    summary = _base_summary("lookup")
    summary["event_exists"] = True
    if not isinstance(event, dict):
        summary["blocker_categories"].append("event_json_object_required")
        return _finalize(summary)
    if _contains_unsafe_public_marker(event):
        summary["blocker_categories"].append("event_unsafe_marker_detected")
        return _finalize(summary)
    key = _cache_key(event)
    summary["key_kind"] = key["kind"]
    entry_path = cache_root_resolved / key["filename"]
    summary["cache_hit"] = (
        entry_path.exists() and entry_path.is_file() and not entry_path.is_symlink()
    )
    return _finalize(summary)


def resolve_private_file_path(
    path: Path,
    allowed_root: str,
    label: str,
    *,
    root: Path = ROOT,
) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    allowed = (root / allowed_root).resolve(strict=False)
    if not _is_relative_to(resolved, allowed):
        raise RuntimeTranslationMemoryError(f"Unsafe {label} path. Use {allowed_root}.")
    return resolved


def resolve_cache_root(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    allowed = (root / PRIVATE_CACHE_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, allowed):
        raise RuntimeTranslationMemoryError(f"Unsafe cache root. Use {PRIVATE_CACHE_ROOT}.")
    return resolved


def resolve_summary_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    allowed = (root / PRIVATE_SUMMARY_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, allowed):
        raise RuntimeTranslationMemoryError(f"Unsafe summary output. Use {PRIVATE_SUMMARY_ROOT}.")
    if resolved.suffix.lower() != ".json":
        raise RuntimeTranslationMemoryError("Summary output path must use .json.")
    return resolved


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        event_dir = root / PRIVATE_EVENT_ROOT
        annotation_dir = root / PRIVATE_ANNOTATION_ROOT
        event_dir.mkdir(parents=True)
        annotation_dir.mkdir(parents=True)
        private_source = "PRIVATE_SOURCE_TEXT_SHOULD_NOT_APPEAR"
        private_uk = "PRIVATE_UKRAINIAN_TRANSLATION_SHOULD_NOT_APPEAR"
        event = {
            "schema_version": "runtime-current-line-event.v1",
            "line_id": "runtime.synthetic.001",
            "source_text": private_source,
        }
        annotation = {
            "schema_version": "runtime-annotation.v1",
            "line_id": "runtime.synthetic.001",
            "compact_translation_uk": private_uk,
        }
        event_path = event_dir / "event.json"
        annotation_path = annotation_dir / "annotation.json"
        event_path.write_text(json.dumps(event), encoding="utf-8")
        annotation_path.write_text(json.dumps(annotation), encoding="utf-8")

        lookup = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            None,
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup",
            root=root,
        )
        if lookup["cache_hit"] or not lookup["provider_call_required"]:
            raise RuntimeTranslationMemoryError("Self-test expected first lookup miss.")

        stored = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            Path(PRIVATE_ANNOTATION_ROOT) / "annotation.json",
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup-or-store",
            root=root,
        )
        if not stored["cache_hit"] or stored["provider_call_required"]:
            raise RuntimeTranslationMemoryError("Self-test expected stored cache hit.")

        output = resolve_summary_output_path(
            Path(PRIVATE_SUMMARY_ROOT) / "summary.json",
            root=root,
        )
        write_summary(stored, output)
        rendered = json.dumps(stored, sort_keys=True) + output.read_text(encoding="utf-8")
        for forbidden in (private_source, private_uk, "runtime.synthetic.001", str(root)):
            if forbidden in rendered:
                raise RuntimeTranslationMemoryError("Self-test leaked private cache data.")


def _load_json_object(
    path: Path,
    label: str,
    summary: dict[str, Any],
) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (UnicodeDecodeError, json.JSONDecodeError):
        summary["blocker_categories"].append(f"{label}_json_decode_failed")
        return None
    if not isinstance(payload, dict):
        summary["blocker_categories"].append(f"{label}_json_object_required")
        return None
    if _contains_unsafe_public_marker(payload):
        summary["blocker_categories"].append(f"{label}_unsafe_marker_detected")
        return None
    return payload


def _cache_key(event: dict[str, Any]) -> dict[str, str]:
    line_id = event.get("line_id")
    if isinstance(line_id, str) and line_id.strip():
        material = f"line_id\0{line_id}"
        kind = "line_id"
    else:
        material = "fallback\0" + json.dumps(event, sort_keys=True, ensure_ascii=False)
        kind = "fallback_private_content"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return {"kind": kind, "filename": f"{digest}.json"}


def _write_cache_entry(
    path: Path,
    key_kind: str,
    event: dict[str, Any],
    annotation: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": ENTRY_SCHEMA_VERSION,
        "key_kind": key_kind,
        "stored_from_runtime_private_inputs": True,
        "event": event,
        "annotation": annotation,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_summary(mode: str) -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "mode": mode,
        "event_exists": False,
        "annotation_provided": False,
        "key_kind": "unknown",
        "cache_hit": False,
        "cache_stored": False,
        "cache_entry_count_delta": 0,
        "provider_call_required": True,
        "blocker_categories": [],
        "paths_included": False,
        "filenames_included": False,
        "keys_or_hashes_included": False,
        "source_text_included": False,
        "translated_text_included": False,
        "prompts_included": False,
        "provider_payloads_included": False,
        "raw_logs_included": False,
        "game_file_reads": False,
        "automatic_game_install_scanning": False,
        "provider_execution_performed": False,
        "companion_contract_changed": False,
        "cache_root_allowed": PRIVATE_CACHE_ROOT,
        "recommended_next_step": "runtime_private_hook_descriptor_contract",
    }


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    if summary["blocker_categories"]:
        summary["provider_call_required"] = False
    else:
        summary["provider_call_required"] = not bool(summary["cache_hit"])
    return summary


def _contains_unsafe_public_marker(value: Any) -> bool:
    for text in _iter_string_values(value):
        lowered = text.lower()
        if SECRET_PATTERN.search(text):
            return True
        if "payload dump" in lowered or "raw provider payload" in lowered:
            return True
    return False


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_string_values(nested)


def _reject_unsafe_path_text(path: Path) -> None:
    text = str(path)
    lowered = text.lower()
    if WINDOWS_ABSOLUTE_PATH_PATTERN.match(text) or path.is_absolute():
        raise RuntimeTranslationMemoryError("Use repo-relative workspace paths only.")
    if ".." in Path(text).parts:
        raise RuntimeTranslationMemoryError("Path traversal is not allowed.")
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker in lowered:
            raise RuntimeTranslationMemoryError("Path uses a forbidden runtime/private marker.")


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    if path.is_absolute():
        return path.resolve(strict=False)
    return (root / path).resolve(strict=False)


def _path_without_symlink_resolution(path: Path, *, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
