from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.m2_synthetic_import_validator import load_and_validate_m2_synthetic_import
    from scripts.run_m2_synthetic_context_graph_builder_dry_run import (
        IMPORT_SOURCE_FIXTURE,
        LINE_INDEX_FIXTURE,
        PRIVATE_OUTPUT_ROOT,
        assert_valid_m2_synthetic_context_graph,
        build_m2_synthetic_context_graph,
        write_m2_synthetic_context_graph,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from m2_synthetic_import_validator import load_and_validate_m2_synthetic_import
    from run_m2_synthetic_context_graph_builder_dry_run import (
        IMPORT_SOURCE_FIXTURE,
        LINE_INDEX_FIXTURE,
        PRIVATE_OUTPUT_ROOT,
        assert_valid_m2_synthetic_context_graph,
        build_m2_synthetic_context_graph,
        write_m2_synthetic_context_graph,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_SCHEMA_VERSION = "m2-synthetic-context-graph-builder-review.v1"
SELF_TEST_SCHEMA_VERSION = "m2-synthetic-context-graph-builder-review-self-test.v1"
DECISION_SCHEMA_VERSION = "m2-synthetic-context-graph-builder-review-decision.v1"
REVIEW_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/context-graph-review/"
DECISION_FIXTURE_PATH = (
    ROOT / "tests/fixtures/m2_synthetic_context_graph_builder_review_decision.synthetic.json"
)
RECOMMENDED_LOCAL_IMPORT_ADAPTER_CONTRACT_STEP = "m2_explicit_local_import_adapter_contract"
RECOMMENDED_REPEAT_GRAPH_STEP = "repeat_m2_synthetic_context_graph_builder_dry_run"

DECISION_FALSE_FIELDS = (
    "m2_import_locally_extracted_db_done",
    "m2_line_index_done",
    "m2_context_graph_done",
    "real_db_import_allowed_next",
    "private_input_read_allowed",
    "graph_construction_from_local_export_allowed",
    "local_import_adapter_implementation_allowed_next",
    "automatic_game_install_scanning_allowed",
    "arbitrary_future_branch_traversal_allowed",
    "game_files_read_allowed",
    "bepinex_logs_read_allowed",
    "screenshots_allowed",
    "ocr_allowed",
    "save_files_read_allowed",
    "decompiled_code_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "generated_graph_commit_allowed",
)
FORBIDDEN_VALUE_MARKERS = (
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "screen capture",
    "steamapps",
    "savegame",
    ".sav",
    "ocr",
    "decompiled",
    "dnspy",
    "ilspy",
    "real extraction approved",
    "local import implementation approved",
    "graph construction approved",
    "future branch traversal approved",
    "current-line capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "provider execution approved",
)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:[\\/](?:Users|Program Files|Games|Steam|GOG|AppData)[\\/]",
    re.IGNORECASE,
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")


class M2SyntheticContextGraphBuilderReviewError(RuntimeError):
    """Raised when synthetic context-graph review input or output is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a metadata-only M2 synthetic context-graph builder dry-run."
    )
    parser.add_argument(
        "--graph",
        type=Path,
        help="Generated synthetic context-graph JSON under the ignored private graph root.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional redacted JSON review under the ignored context-graph-review root.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Optional redacted Markdown review under the ignored context-graph-review root.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace synthetic review smoke.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 synthetic context-graph builder review self-test passed.")
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

        if args.graph is None:
            parser.error("--graph is required unless --self-test is used.")
        graph_path = resolve_graph_input_path(args.graph, root=ROOT)
        review = build_review(load_json(graph_path), graph_path=graph_path, root=ROOT)
        if review["graph_valid"]:
            if args.output:
                write_json_review(review, resolve_review_output_path(args.output, root=ROOT))
            if args.markdown_output:
                write_markdown_review(
                    review,
                    resolve_review_output_path(args.markdown_output, root=ROOT),
                )
        if args.quiet:
            print(
                "M2 synthetic context-graph builder review passed."
                if review["graph_valid"]
                else "M2 synthetic context-graph builder review failed."
            )
        else:
            print(json.dumps(review, indent=2, sort_keys=True))
        return 0 if review["graph_valid"] else 1
    except (OSError, ValueError, M2SyntheticContextGraphBuilderReviewError) as exc:
        parser.error(str(exc))
    return 0


def build_review(
    graph: dict[str, Any],
    *,
    graph_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = collect_graph_errors(graph, graph_path=graph_path, root=root)
    blockers = _dedupe([_blocker_for_error(error) for error in errors])
    ready = not errors and not blockers
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "graph_valid": not errors,
        "node_count": _safe_int(graph.get("node_count")),
        "edge_count": _safe_int(graph.get("edge_count")),
        "generated_from_synthetic_fixture": graph.get("generated_from_synthetic_fixture") is True,
        "default_spoiler_budget": (
            graph.get("default_spoiler_budget")
            if graph.get("default_spoiler_budget") == "none"
            else "invalid"
        ),
        "ready_for_local_import_adapter_contract_decision": ready,
        "local_import_adapter_implementation_allowed_next": False,
        "original_m2_import_done": False,
        "original_m2_line_index_done": False,
        "original_m2_context_graph_done": False,
        "real_text_included": False,
        "source_text_included": False,
        "private_paths_included": False,
        "filenames_included": False,
        "hashes_included": False,
        "raw_payloads_included": False,
        "logs_included": False,
        "runtime_evidence_included": False,
        "private_input_read": False,
        "game_files_read": False,
        "arbitrary_future_branch_traversal": False,
        "blockers": blockers,
        "recommended_next_step": (
            RECOMMENDED_LOCAL_IMPORT_ADAPTER_CONTRACT_STEP
            if ready
            else RECOMMENDED_REPEAT_GRAPH_STEP
        ),
        "graph_path_redacted": True,
        "review_output_private_only": True,
    }


def collect_graph_errors(
    graph: Any,
    *,
    graph_path: Path,
    root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    try:
        resolve_graph_input_path(graph_path, root=root)
    except M2SyntheticContextGraphBuilderReviewError as exc:
        errors.append(str(exc))
    if not isinstance(graph, dict):
        return errors + ["Synthetic context graph must be a JSON object."]
    try:
        source = load_and_validate_m2_synthetic_import(IMPORT_SOURCE_FIXTURE)
        line_index = load_json(LINE_INDEX_FIXTURE)
        assert_valid_m2_synthetic_context_graph(graph, source, line_index)
    except Exception as exc:
        errors.append(f"Synthetic context graph is invalid: {exc}")
    errors.extend(_unsafe_value_errors(graph, label="Synthetic context graph"))
    return _dedupe(errors)


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 context-graph review decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 context-graph review decision fixture must be a JSON object."]
    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"Decision fixture schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("roadmap_milestone") != "M2":
        errors.append("Decision fixture roadmap_milestone must be 'M2'.")
    if payload.get("synthetic_context_graph_review_evidence_required") is not True:
        errors.append("Decision fixture must require synthetic context-graph review evidence.")
    if payload.get("local_import_adapter_contract_allowed_next") != "decision_pending":
        errors.append(
            "Decision fixture local_import_adapter_contract_allowed_next must be decision_pending."
        )
    if payload.get("recommended_next_step") != RECOMMENDED_LOCAL_IMPORT_ADAPTER_CONTRACT_STEP:
        errors.append(
            "Decision fixture recommended_next_step must be "
            f"{RECOMMENDED_LOCAL_IMPORT_ADAPTER_CONTRACT_STEP!r}."
        )
    for field in DECISION_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"Decision fixture must keep {field}=false.")
    errors.extend(_unsafe_value_errors(payload, label="Decision fixture"))
    return _dedupe(errors)


def resolve_graph_input_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    graph_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, graph_root):
        raise M2SyntheticContextGraphBuilderReviewError(
            "Unsafe graph path. Use "
            "workspace/local-private/extraction-indexing/import/context-graph/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise M2SyntheticContextGraphBuilderReviewError(
            "Synthetic context-graph path must point to an existing file."
        )
    return resolved


def resolve_review_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    review_root = (root / REVIEW_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, review_root):
        raise M2SyntheticContextGraphBuilderReviewError(
            "Unsafe review output path. Use "
            "workspace/local-private/extraction-indexing/import/context-graph-review/."
        )
    if resolved.exists() and resolved.is_dir():
        raise M2SyntheticContextGraphBuilderReviewError("Review output path must be a file path.")
    return resolved


def write_json_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M2 Synthetic Context-Graph Builder Review",
        "",
        f"- graph_valid: {_yes_no(review['graph_valid'])}",
        f"- node_count: {review['node_count']}",
        f"- edge_count: {review['edge_count']}",
        "- generated_from_synthetic_fixture: yes",
        "- default_spoiler_budget: none",
        "- original_m2_context_graph_done: no",
        "- local_import_adapter_implementation_allowed_next: no",
        (
            "- ready_for_local_import_adapter_contract_decision: "
            f"{_yes_no(review['ready_for_local_import_adapter_contract_decision'])}"
        ),
        "- arbitrary_future_branch_traversal: no",
        "- real_text_included: no",
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
        raise M2SyntheticContextGraphBuilderReviewError("; ".join(decision_errors))
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        source = load_and_validate_m2_synthetic_import(IMPORT_SOURCE_FIXTURE)
        line_index = load_json(LINE_INDEX_FIXTURE)
        graph = build_m2_synthetic_context_graph(source, line_index)
        graph_path = root / PRIVATE_OUTPUT_ROOT / "graph.json"
        write_m2_synthetic_context_graph(graph, graph_path)
        review = build_review(load_json(graph_path), graph_path=graph_path, root=root)
        rendered = json.dumps(review, sort_keys=True)
        if (
            not review["graph_valid"]
            or not review["ready_for_local_import_adapter_contract_decision"]
        ):
            raise M2SyntheticContextGraphBuilderReviewError(
                "Self-test expected ready synthetic review."
            )
        if review["local_import_adapter_implementation_allowed_next"]:
            raise M2SyntheticContextGraphBuilderReviewError(
                "Self-test must not allow local-import adapter implementation."
            )
        if str(root) in rendered or "synthetic_office_entry" in rendered:
            raise M2SyntheticContextGraphBuilderReviewError(
                "Self-test review leaked graph details."
            )
        json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
        markdown_path = root / REVIEW_OUTPUT_ROOT / "review.md"
        write_json_review(review, resolve_review_output_path(json_path, root=root))
        write_markdown_review(review, resolve_review_output_path(markdown_path, root=root))


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
        raise M2SyntheticContextGraphBuilderReviewError("Unsafe path traversal is not allowed.")
    for marker in ("logoutput.log", "player.log", "steamapps", "screenshot", "ocr", ".sav"):
        if marker in normalized:
            raise M2SyntheticContextGraphBuilderReviewError(
                "Path uses a forbidden runtime/private marker."
            )


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute() or WINDOWS_ABSOLUTE_PATH_PATTERN.match(str(raw)):
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _blocker_for_error(error: str) -> str:
    lowered = error.lower()
    if "path" in lowered:
        return "private_path_or_unsafe_path"
    if "marker" in lowered or "payload" in lowered or "log" in lowered:
        return "unsafe_marker_detected"
    if "spoiler" in lowered or "future branch" in lowered:
        return "unsafe_spoiler_scope"
    return "invalid_synthetic_context_graph"


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
    return list(dict.fromkeys(values))


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
