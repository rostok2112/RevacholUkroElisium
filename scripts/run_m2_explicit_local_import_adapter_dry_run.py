from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "m2-explicit-local-import-adapter-dry-run-summary.v1"
PRIVATE_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/adapter-dry-run/"


class M2ExplicitLocalImportAdapterDryRunError(RuntimeError):
    """Raised when an M2 explicit local-import dry-run request is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize one explicit workspace-private export file as redacted metadata only. "
            "This M2 dry-run never reads or parses file contents."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Explicit file path under workspace/local-private/extraction-indexing/input/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON output under "
            "workspace/local-private/extraction-indexing/import/adapter-dry-run/."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace smoke without real private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 explicit local-import adapter dry-run self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": (
                                "m2-explicit-local-import-adapter-dry-run-self-test.v1"
                            ),
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0

        if args.input is None:
            parser.error("--input is required unless --self-test is used.")

        summary = build_m2_explicit_local_import_adapter_dry_run(args.input, root=ROOT)
        if args.output:
            output_path = resolve_output_path(args.output, root=ROOT)
            summary["output_written"] = True
            write_summary(summary, output_path)

        if args.quiet:
            print("M2 explicit local-import adapter dry-run passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (
        M2ExplicitLocalImportAdapterDryRunError,
        OSError,
        PrivateInputAdapterDryRunError,
        ValueError,
    ) as exc:
        parser.error(str(exc))
    return 0


def build_m2_explicit_local_import_adapter_dry_run(
    input_path: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    resolved_input = resolve_input_path(input_path, root=root)
    summary = _base_summary()
    summary["input_exists"] = resolved_input.exists()

    if not resolved_input.exists():
        summary["input_kind"] = "missing"
        summary["blocker_categories"].append("input_missing")
    elif resolved_input.is_symlink():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("symlink_input_rejected")
    elif resolved_input.is_file():
        summary["input_kind"] = "file"
        summary["byte_count"] = resolved_input.stat().st_size
    elif resolved_input.is_dir():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("directory_input_rejected")
    else:
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("unsupported_input_kind")
    return summary


def resolve_output_path(output_path: Path, *, root: Path = ROOT) -> Path:
    try:
        resolved = resolve_private_output_path(output_path, root=root)
        output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
        resolved.relative_to(output_root)
    except (PrivateInputAdapterDryRunError, ValueError) as exc:
        raise M2ExplicitLocalImportAdapterDryRunError(
            "Unsafe output path. Use a JSON path under "
            "workspace/local-private/extraction-indexing/import/adapter-dry-run/."
        ) from exc

    if resolved.suffix.lower() != ".json":
        raise M2ExplicitLocalImportAdapterDryRunError("Output path must use the .json suffix.")
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
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        secret_text = "PRIVATE_EXPORT_CONTENT_SHOULD_NOT_APPEAR"
        private_file.write_text(secret_text, encoding="utf-8")

        summary = build_m2_explicit_local_import_adapter_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if summary["input_kind"] != "file" or summary["byte_count"] != len(secret_text):
            raise M2ExplicitLocalImportAdapterDryRunError(
                "Self-test file metadata summary was incorrect."
            )
        if secret_text in rendered or str(root) in rendered:
            raise M2ExplicitLocalImportAdapterDryRunError(
                "Self-test summary leaked private content or paths."
            )

        output = resolve_output_path(
            Path(PRIVATE_OUTPUT_ROOT) / "self-test-summary.json",
            root=root,
        )
        write_summary(summary, output)
        written = output.read_text(encoding="utf-8")
        if secret_text in written or str(root) in written:
            raise M2ExplicitLocalImportAdapterDryRunError(
                "Self-test written summary leaked private data."
            )

        directory = root / PRIVATE_INPUT_ROOT / "directory"
        directory.mkdir()
        blocked = build_m2_explicit_local_import_adapter_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "directory",
            root=root,
        )
        if "directory_input_rejected" not in blocked["blocker_categories"]:
            raise M2ExplicitLocalImportAdapterDryRunError(
                "Self-test failed to reject a directory input."
            )


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "byte_count": 0,
        "schema_status": "deferred",
        "blocker_categories": [],
        "allowed_root": PRIVATE_INPUT_ROOT,
        "private_output_root": PRIVATE_OUTPUT_ROOT,
        "dry_run": True,
        "metadata_only": True,
        "output_written": False,
        "private_paths_included": False,
        "file_contents_read": False,
        "private_content_parsed": False,
        "real_db_imported": False,
        "line_index_constructed": False,
        "context_graph_constructed": False,
        "automatic_game_install_scanning": False,
        "recursive_discovery_used": False,
        "game_files_read": False,
        "bepinex_logs_read": False,
        "screenshots_read": False,
        "ocr_used": False,
        "save_files_read": False,
        "current_line_capture_used": False,
        "ui_text_reading_used": False,
        "unity_scanning_used": False,
        "hooks_used": False,
        "decompiled_code_used": False,
        "provider_called": False,
        "companion_contract_changed": False,
        "real_text_included": False,
        "raw_payloads_included": False,
        "raw_logs_included": False,
    }


if __name__ == "__main__":
    sys.exit(main())
