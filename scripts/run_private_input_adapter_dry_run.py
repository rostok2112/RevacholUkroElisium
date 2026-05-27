from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "private-input-adapter-dry-run-summary.v1"
PRIVATE_INPUT_ROOT = "workspace/local-private/extraction-indexing/input/"
PRIVATE_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/"
DEFAULT_INPUT_ROOT = ROOT / PRIVATE_INPUT_ROOT
DEFAULT_OUTPUT_ROOT = ROOT / PRIVATE_OUTPUT_ROOT
DEFAULT_TRAVERSAL_LIMIT = 1000

FORBIDDEN_PATH_MARKERS = (
    "bepinex",
    "logoutput.log",
    "player.log",
    "steamapps",
    "disco elysium",
    "gameassembly.dll",
    "globalgamemanagers",
    "screenshot",
    "screen capture",
    "ocr",
    ".sav",
    "savegame",
    "save file",
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


class PrivateInputAdapterDryRunError(RuntimeError):
    """Raised when a private input adapter dry-run request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize one explicit private extraction input as redacted metadata only. "
            "This dry-run never reads file contents or scans game installs."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Explicit input path under workspace/local-private/extraction-indexing/input/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output under workspace/local-private/extraction-indexing/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include local resolved paths in the summary. Never includes file contents.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace smoke that does not need real private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Private input adapter dry-run self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": "private-input-adapter-dry-run-self-test.v1",
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0

        if args.input is None:
            parser.error("--input is required unless --self-test is used.")

        summary = build_dry_run_summary(args.input, root=ROOT, verbose=args.verbose)
        if args.output:
            output_path = resolve_output_path(args.output, root=ROOT)
            write_summary(summary, output_path)
            summary["output_written"] = True
            if args.verbose:
                summary["output_path"] = str(output_path)

        if args.quiet:
            print("Private input adapter dry-run passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (OSError, PrivateInputAdapterDryRunError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def build_dry_run_summary(
    input_path: Path,
    *,
    root: Path = ROOT,
    verbose: bool = False,
    traversal_limit: int = DEFAULT_TRAVERSAL_LIMIT,
) -> dict[str, Any]:
    resolved_input = resolve_input_path(input_path, root=root)
    summary = _base_summary(verbose=verbose)
    summary["traversal_limit"] = traversal_limit
    summary["input_exists"] = resolved_input.exists()

    if not resolved_input.exists():
        summary["input_kind"] = "missing"
        summary["blocker_categories"].append("input_missing")
    elif resolved_input.is_symlink():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("symlink_input_rejected")
    elif resolved_input.is_file():
        summary["input_kind"] = "file"
        summary["file_count"] = 1
        summary["total_size_bytes"] = _safe_file_size(resolved_input, summary)
    elif resolved_input.is_dir():
        summary["input_kind"] = "directory"
        _summarize_directory(resolved_input, summary, traversal_limit=traversal_limit)
    else:
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("unsupported_input_kind")

    if verbose:
        summary["input_path"] = str(resolved_input)
        summary["allowed_root_path"] = str(_input_root(root).resolve(strict=False))
    return summary


def resolve_input_path(input_path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(input_path)
    resolved = _resolve_under_root(input_path, root=root)
    input_root = _input_root(root).resolve(strict=False)
    if not _is_relative_to(resolved, input_root):
        raise PrivateInputAdapterDryRunError(
            "Unsafe input path. Copy or place one input under "
            "workspace/local-private/extraction-indexing/input/ first."
        )
    return resolved


def resolve_output_path(output_path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(output_path)
    resolved = _resolve_under_root(output_path, root=root)
    output_root = _output_root(root).resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise PrivateInputAdapterDryRunError(
            "Unsafe output path. Use a path under workspace/local-private/extraction-indexing/."
        )
    if resolved.exists() and resolved.is_dir():
        raise PrivateInputAdapterDryRunError(
            "Output path must be a JSON file path, not a directory."
        )
    return resolved


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        input_dir = root / PRIVATE_INPUT_ROOT / "sample"
        input_dir.mkdir(parents=True)
        secret_text = "PRIVATE_CONTENT_SHOULD_NOT_APPEAR"
        (input_dir / "record.txt").write_text(secret_text, encoding="utf-8")
        (input_dir / "nested").mkdir()
        (input_dir / "nested" / "more.txt").write_text("more private text", encoding="utf-8")

        summary = build_dry_run_summary(
            Path(PRIVATE_INPUT_ROOT) / "sample",
            root=root,
            verbose=False,
            traversal_limit=10,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if summary["input_kind"] != "directory":
            raise PrivateInputAdapterDryRunError("Self-test expected a directory summary.")
        if summary["file_count"] != 2 or summary["directory_count"] != 1:
            raise PrivateInputAdapterDryRunError("Self-test metadata counts were incorrect.")
        if secret_text in rendered or str(root) in rendered:
            raise PrivateInputAdapterDryRunError(
                "Self-test summary leaked private content or paths."
            )

        output = resolve_output_path(
            Path(PRIVATE_OUTPUT_ROOT) / "self-test-summary.json",
            root=root,
        )
        write_summary(summary, output)
        written = output.read_text(encoding="utf-8")
        if secret_text in written or str(root) in written:
            raise PrivateInputAdapterDryRunError("Self-test written summary leaked private data.")

        try:
            resolve_input_path(
                Path("workspace/local-private/extraction-indexing/input/LogOutput.log"),
                root=root,
            )
        except PrivateInputAdapterDryRunError:
            pass
        else:
            raise PrivateInputAdapterDryRunError("Self-test failed to reject a BepInEx log path.")


def _base_summary(*, verbose: bool) -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "file_count": 0,
        "directory_count": 0,
        "total_size_bytes": 0,
        "allowed_root": PRIVATE_INPUT_ROOT,
        "private_output_root": PRIVATE_OUTPUT_ROOT,
        "dry_run": True,
        "hashes_computed": False,
        "traversal_limit": DEFAULT_TRAVERSAL_LIMIT,
        "traversal_truncated": False,
        "blocker_categories": [],
        "output_written": False,
        "paths_redacted": not verbose,
        "file_contents_read": False,
        "real_text_included": False,
        "raw_payloads_included": False,
        "raw_logs_included": False,
        "automatic_game_install_scanning": False,
        "game_files_read": False,
        "bepinex_logs_read": False,
        "game_logs_read": False,
        "screenshots_read": False,
        "ocr_used": False,
        "save_files_read": False,
        "hooks_used": False,
        "unity_scanning_used": False,
        "current_line_capture_used": False,
        "ui_text_reading_used": False,
        "decompiled_code_used": False,
        "companion_contract_changed": False,
        "provider_called": False,
    }


def _summarize_directory(
    directory: Path,
    summary: dict[str, Any],
    *,
    traversal_limit: int,
) -> None:
    stack = [directory]
    visited = 0
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir(), key=lambda child: child.name.lower())
        except OSError:
            _add_blocker(summary, "metadata_unreadable")
            continue

        for child in children:
            visited += 1
            if visited > traversal_limit:
                summary["traversal_truncated"] = True
                _add_blocker(summary, "traversal_limit_reached")
                return
            if child.is_symlink():
                _add_blocker(summary, "symlink_skipped")
                continue
            try:
                if child.is_file():
                    summary["file_count"] += 1
                    summary["total_size_bytes"] += _safe_file_size(child, summary)
                elif child.is_dir():
                    summary["directory_count"] += 1
                    stack.append(child)
                else:
                    _add_blocker(summary, "unsupported_child_kind")
            except OSError:
                _add_blocker(summary, "metadata_unreadable")


def _safe_file_size(path: Path, summary: dict[str, Any]) -> int:
    try:
        return path.stat().st_size
    except OSError:
        _add_blocker(summary, "metadata_unreadable")
        return 0


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise PrivateInputAdapterDryRunError("Unsafe path traversal is not allowed.")
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker in normalized:
            raise PrivateInputAdapterDryRunError(
                "Path uses a forbidden game/log/screenshot/OCR/save/payload marker."
            )


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute() or WINDOWS_ABSOLUTE_PATH_PATTERN.match(str(raw)):
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _input_root(root: Path) -> Path:
    return root / PRIVATE_INPUT_ROOT


def _output_root(root: Path) -> Path:
    return root / PRIVATE_OUTPUT_ROOT


def _add_blocker(summary: dict[str, Any], blocker: str) -> None:
    blockers = summary["blocker_categories"]
    if blocker not in blockers:
        blockers.append(blocker)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
