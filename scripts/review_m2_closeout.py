from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.review_m2_context_graph import (
        REVIEW_OUTPUT_ROOT as CONTEXT_GRAPH_REVIEW_ROOT,
        REVIEW_SCHEMA_VERSION as CONTEXT_GRAPH_REVIEW_SCHEMA_VERSION,
        build_review as build_context_graph_review,
    )
    from scripts.review_m2_line_index import (
        REVIEW_OUTPUT_ROOT as LINE_INDEX_REVIEW_ROOT,
        REVIEW_SCHEMA_VERSION as LINE_INDEX_REVIEW_SCHEMA_VERSION,
        build_review as build_line_index_review,
    )
    from scripts.review_m2_local_import import (
        REVIEW_OUTPUT_ROOT as LOCAL_IMPORT_REVIEW_ROOT,
        REVIEW_SCHEMA_VERSION as LOCAL_IMPORT_REVIEW_SCHEMA_VERSION,
        build_review as build_local_import_review,
    )
    from scripts.run_m2_context_graph import (
        LINE_INDEX_REVIEW_ROOT as CONTEXT_GRAPH_LINE_INDEX_REVIEW_ROOT,
        PRIVATE_CONTEXT_GRAPH_ROOT,
        SUMMARY_OUTPUT_ROOT as CONTEXT_GRAPH_SUMMARY_ROOT,
        run_m2_context_graph,
        write_summary as write_context_graph_summary,
    )
    from scripts.run_m2_line_index import (
        LOCAL_IMPORT_REVIEW_ROOT as LINE_INDEX_LOCAL_IMPORT_REVIEW_ROOT,
        PRIVATE_DB_ROOT,
        PRIVATE_LINE_INDEX_ROOT,
        SUMMARY_OUTPUT_ROOT as LINE_INDEX_SUMMARY_ROOT,
        run_m2_line_index,
        write_summary as write_line_index_summary,
    )
    from scripts.run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary as write_import_summary,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from review_m2_context_graph import (
        REVIEW_OUTPUT_ROOT as CONTEXT_GRAPH_REVIEW_ROOT,
        REVIEW_SCHEMA_VERSION as CONTEXT_GRAPH_REVIEW_SCHEMA_VERSION,
        build_review as build_context_graph_review,
    )
    from review_m2_line_index import (
        REVIEW_OUTPUT_ROOT as LINE_INDEX_REVIEW_ROOT,
        REVIEW_SCHEMA_VERSION as LINE_INDEX_REVIEW_SCHEMA_VERSION,
        build_review as build_line_index_review,
    )
    from review_m2_local_import import (
        REVIEW_OUTPUT_ROOT as LOCAL_IMPORT_REVIEW_ROOT,
        REVIEW_SCHEMA_VERSION as LOCAL_IMPORT_REVIEW_SCHEMA_VERSION,
        build_review as build_local_import_review,
    )
    from run_m2_context_graph import (
        LINE_INDEX_REVIEW_ROOT as CONTEXT_GRAPH_LINE_INDEX_REVIEW_ROOT,
        PRIVATE_CONTEXT_GRAPH_ROOT,
        SUMMARY_OUTPUT_ROOT as CONTEXT_GRAPH_SUMMARY_ROOT,
        run_m2_context_graph,
        write_summary as write_context_graph_summary,
    )
    from run_m2_line_index import (
        LOCAL_IMPORT_REVIEW_ROOT as LINE_INDEX_LOCAL_IMPORT_REVIEW_ROOT,
        PRIVATE_DB_ROOT,
        PRIVATE_LINE_INDEX_ROOT,
        SUMMARY_OUTPUT_ROOT as LINE_INDEX_SUMMARY_ROOT,
        run_m2_line_index,
        write_summary as write_line_index_summary,
    )
    from run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary as write_import_summary,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_SCHEMA_VERSION = "m2-closeout-review.v1"
SELF_TEST_SCHEMA_VERSION = "m2-closeout-review-self-test.v1"
DECISION_SCHEMA_VERSION = "m2-closeout-review-decision.v1"
REVIEW_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/m2-closeout-review/"
DECISION_FIXTURE_PATH = ROOT / "tests/fixtures/m2_closeout_review_decision.synthetic.json"
RECOMMENDED_M3_PLANNING_STEP = "m3_bepinex_bridge_planning"
RECOMMENDED_REPEAT_CONTEXT_GRAPH_REVIEW_STEP = "repeat_m2_context_graph_review_gate"
FALSE_REVIEW_FIELDS = (
    "private_paths_included",
    "filenames_included",
    "hashes_computed",
    "raw_payloads_included",
    "logs_included",
    "runtime_evidence_included",
)
DECISION_FALSE_FIELDS = (
    "private_artifact_reopen_allowed_during_review",
    "selected_export_reopen_allowed_during_review",
    "generated_review_commit_allowed",
    "generated_private_db_commit_allowed",
    "generated_line_index_commit_allowed",
    "generated_context_graph_commit_allowed",
    "private_paths_commit_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
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
    "record id",
    "line id",
    "edge id",
    "relation value",
    "source text",
    "provider execution approved",
)


class M2CloseoutReviewError(RuntimeError):
    """Raised when M2 closeout review input or output is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review redacted M2 closeout evidence.")
    parser.add_argument("--local-import-review", type=Path, help="Review JSON under db-review/.")
    parser.add_argument(
        "--line-index-review", type=Path, help="Review JSON under line-index-review/."
    )
    parser.add_argument(
        "--context-graph-review", type=Path, help="Review JSON under context-graph-review/."
    )
    parser.add_argument(
        "--output", type=Path, help="Optional closeout JSON under m2-closeout-review/."
    )
    parser.add_argument(
        "--markdown-output", type=Path, help="Optional closeout Markdown under m2-closeout-review/."
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 closeout review self-test passed.")
            else:
                print(
                    json.dumps(
                        {"ok": True, "schema_version": SELF_TEST_SCHEMA_VERSION},
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0
        if (
            args.local_import_review is None
            or args.line_index_review is None
            or args.context_graph_review is None
        ):
            parser.error(
                "--local-import-review, --line-index-review, and --context-graph-review are required unless --self-test."
            )
        local_path = resolve_review_input_path(
            args.local_import_review,
            root=ROOT,
            allowed_root=LOCAL_IMPORT_REVIEW_ROOT,
            label="local import review",
        )
        line_path = resolve_review_input_path(
            args.line_index_review,
            root=ROOT,
            allowed_root=LINE_INDEX_REVIEW_ROOT,
            label="line-index review",
        )
        graph_path = resolve_review_input_path(
            args.context_graph_review,
            root=ROOT,
            allowed_root=CONTEXT_GRAPH_REVIEW_ROOT,
            label="context-graph review",
        )
        review = build_review(
            load_json(local_path),
            load_json(line_path),
            load_json(graph_path),
            local_import_review_path=local_path,
            line_index_review_path=line_path,
            context_graph_review_path=graph_path,
            root=ROOT,
        )
        if review["closeout_evidence_valid"]:
            if args.output:
                write_json_review(review, resolve_closeout_output_path(args.output, root=ROOT))
            if args.markdown_output:
                write_markdown_review(
                    review, resolve_closeout_output_path(args.markdown_output, root=ROOT)
                )
        if args.quiet:
            print(
                "M2 closeout review passed."
                if review["closeout_evidence_valid"]
                else "M2 closeout review failed."
            )
        else:
            print(json.dumps(review, indent=2, sort_keys=True))
        return 0 if review["closeout_evidence_valid"] else 1
    except (OSError, ValueError, M2CloseoutReviewError) as exc:
        parser.error(str(exc))
    return 0


def build_review(
    local_import_review: Any,
    line_index_review: Any,
    context_graph_review: Any,
    *,
    local_import_review_path: Path,
    line_index_review_path: Path,
    context_graph_review_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = collect_closeout_errors(
        local_import_review,
        line_index_review,
        context_graph_review,
        local_import_review_path=local_import_review_path,
        line_index_review_path=line_index_review_path,
        context_graph_review_path=context_graph_review_path,
        root=root,
    )
    blockers = _dedupe([_blocker_for_error(error) for error in errors])
    if not errors:
        for review in (local_import_review, line_index_review, context_graph_review):
            blockers.extend(str(item) for item in review.get("blockers", []))
        blockers = _dedupe(blockers)
    ready = not errors and not blockers
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "closeout_evidence_valid": not errors,
        "local_import_review_valid": _local_import_review_ready(local_import_review),
        "line_index_review_valid": _line_index_review_ready(line_index_review),
        "context_graph_review_valid": _context_graph_review_ready(context_graph_review),
        "original_m2_import_done": ready,
        "original_m2_line_index_done": ready,
        "original_m2_context_graph_done": ready,
        "original_m2_complete": ready,
        "m2_completed_at_private_implementation_path_level": ready,
        "private_artifacts_reopened_during_closeout_review": False,
        "selected_export_reopened_during_closeout_review": False,
        "generated_private_artifacts_committed": False,
        "generated_reviews_committed": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_ids_included": False,
        "line_ids_included": False,
        "edge_ids_included": False,
        "relation_values_included": False,
        "source_text_included": False,
        "hashes_computed": False,
        "raw_payloads_included": False,
        "logs_included": False,
        "runtime_evidence_included": False,
        "blockers": blockers,
        "recommended_next_step": RECOMMENDED_M3_PLANNING_STEP
        if ready
        else RECOMMENDED_REPEAT_CONTEXT_GRAPH_REVIEW_STEP,
        "review_paths_redacted": True,
        "review_output_private_only": True,
    }


def collect_closeout_errors(
    local_import_review: Any,
    line_index_review: Any,
    context_graph_review: Any,
    *,
    local_import_review_path: Path,
    line_index_review_path: Path,
    context_graph_review_path: Path,
    root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _validate_review_path(
            local_import_review_path,
            root=root,
            allowed_root=LOCAL_IMPORT_REVIEW_ROOT,
            label="local import review",
        )
    )
    errors.extend(
        _validate_review_path(
            line_index_review_path,
            root=root,
            allowed_root=LINE_INDEX_REVIEW_ROOT,
            label="line-index review",
        )
    )
    errors.extend(
        _validate_review_path(
            context_graph_review_path,
            root=root,
            allowed_root=CONTEXT_GRAPH_REVIEW_ROOT,
            label="context-graph review",
        )
    )
    errors.extend(_validate_local_import_review(local_import_review))
    errors.extend(_validate_line_index_review(line_index_review))
    errors.extend(_validate_context_graph_review(context_graph_review))
    errors.extend(_unsafe_value_errors(local_import_review, label="Local import review"))
    errors.extend(_unsafe_value_errors(line_index_review, label="Line-index review"))
    errors.extend(_unsafe_value_errors(context_graph_review, label="Context-graph review"))
    return _dedupe(errors)


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 closeout review decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 closeout review decision fixture must be a JSON object."]
    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"Decision fixture schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("roadmap_milestone") != "M2":
        errors.append("Decision fixture roadmap_milestone must be 'M2'.")
    for field in (
        "m2_closeout_review_evidence_required",
        "local_import_review_required",
        "line_index_review_required",
        "context_graph_review_required",
    ):
        if payload.get(field) is not True:
            errors.append(f"Decision fixture must set {field}=true.")
    if payload.get("m2_completion_allowed_next") != "review_required":
        errors.append("Decision fixture must keep M2 completion review-gated.")
    if payload.get("recommended_next_step") != RECOMMENDED_M3_PLANNING_STEP:
        errors.append("Decision fixture next step must be m3_bepinex_bridge_planning.")
    for field in DECISION_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"Decision fixture must keep {field}=false.")
    errors.extend(_unsafe_value_errors(payload, label="Decision fixture"))
    return _dedupe(errors)


def resolve_review_input_path(
    path: Path, *, root: Path = ROOT, allowed_root: str, label: str
) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    base = (root / allowed_root).resolve(strict=False)
    if not _is_relative_to(resolved, base):
        raise M2CloseoutReviewError(f"Unsafe {label} path. Use {allowed_root}.")
    if not resolved.exists() or not resolved.is_file():
        raise M2CloseoutReviewError(f"M2 {label} path must point to an existing file.")
    return resolved


def resolve_closeout_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    base = (root / REVIEW_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, base):
        raise M2CloseoutReviewError(
            "Unsafe closeout output path. Use workspace/local-private/extraction-indexing/import/m2-closeout-review/."
        )
    if resolved.exists() and resolved.is_dir():
        raise M2CloseoutReviewError("Closeout output path must be a file path.")
    return resolved


def write_json_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M2 Closeout Review",
        "",
        f"- closeout_evidence_valid: {_yes_no(review['closeout_evidence_valid'])}",
        f"- local_import_review_valid: {_yes_no(review['local_import_review_valid'])}",
        f"- line_index_review_valid: {_yes_no(review['line_index_review_valid'])}",
        f"- context_graph_review_valid: {_yes_no(review['context_graph_review_valid'])}",
        f"- original_m2_import_done: {_yes_no(review['original_m2_import_done'])}",
        f"- original_m2_line_index_done: {_yes_no(review['original_m2_line_index_done'])}",
        f"- original_m2_context_graph_done: {_yes_no(review['original_m2_context_graph_done'])}",
        f"- original_m2_complete: {_yes_no(review['original_m2_complete'])}",
        "- private_artifacts_reopened_during_closeout_review: no",
        "- selected_export_reopened_during_closeout_review: no",
        f"- recommended_next_step: {review['recommended_next_step']}",
    ]
    if review["blockers"]:
        lines.extend(["", "## Blockers"])
        lines.extend(f"- {blocker}" for blocker in review["blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_self_test() -> None:
    decision_errors = collect_decision_fixture_errors()
    if decision_errors:
        raise M2CloseoutReviewError("; ".join(decision_errors))
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_marker = "PRIVATE_M2_CLOSEOUT_VALUE_SHOULD_NOT_APPEAR"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_file.write_text(json.dumps(_compatible_export(private_marker)), encoding="utf-8")

        db_path = Path(PRIVATE_DB_ROOT) / "imported-db.json"
        import_summary = run_m2_local_import(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json", db_path, root=root
        )
        import_summary_path = (
            root / "workspace/local-private/extraction-indexing/import/db-summary/summary.json"
        )
        write_import_summary(import_summary, import_summary_path)
        local_review = build_local_import_review(
            import_summary, summary_path=import_summary_path, root=root
        )
        local_review_path = root / LOCAL_IMPORT_REVIEW_ROOT / "review.json"
        write_json_review(local_review, local_review_path)

        line_index_path = Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json"
        line_summary = run_m2_line_index(
            db_path,
            Path(LINE_INDEX_LOCAL_IMPORT_REVIEW_ROOT) / "review.json",
            line_index_path,
            root=root,
        )
        line_summary_path = root / LINE_INDEX_SUMMARY_ROOT / "summary.json"
        write_line_index_summary(line_summary, line_summary_path)
        line_review = build_line_index_review(
            line_summary, summary_path=line_summary_path, root=root
        )
        line_review_path = root / LINE_INDEX_REVIEW_ROOT / "review.json"
        write_json_review(line_review, line_review_path)

        graph_path = Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "graph.json"
        graph_summary = run_m2_context_graph(
            db_path,
            line_index_path,
            Path(CONTEXT_GRAPH_LINE_INDEX_REVIEW_ROOT) / "review.json",
            graph_path,
            root=root,
        )
        graph_summary_path = root / CONTEXT_GRAPH_SUMMARY_ROOT / "summary.json"
        write_context_graph_summary(graph_summary, graph_summary_path)
        graph_review = build_context_graph_review(
            graph_summary, summary_path=graph_summary_path, root=root
        )
        graph_review_path = root / CONTEXT_GRAPH_REVIEW_ROOT / "review.json"
        write_json_review(graph_review, graph_review_path)

        for artifact in (root / graph_path, root / line_index_path, root / db_path, private_file):
            artifact.unlink()

        review = build_review(
            load_json(local_review_path),
            load_json(line_review_path),
            load_json(graph_review_path),
            local_import_review_path=local_review_path,
            line_index_review_path=line_review_path,
            context_graph_review_path=graph_review_path,
            root=root,
        )
        rendered = json.dumps(review, sort_keys=True)
        if not review["closeout_evidence_valid"] or not review["original_m2_complete"]:
            raise M2CloseoutReviewError("Self-test expected ready M2 closeout review.")
        if private_marker in rendered or str(root) in rendered:
            raise M2CloseoutReviewError("Self-test closeout leaked private content or paths.")
        json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
        markdown_path = root / REVIEW_OUTPUT_ROOT / "review.md"
        write_json_review(review, resolve_closeout_output_path(json_path, root=root))
        write_markdown_review(review, resolve_closeout_output_path(markdown_path, root=root))
        written = json_path.read_text(encoding="utf-8") + markdown_path.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2CloseoutReviewError(
                "Self-test closeout output leaked private content or paths."
            )


def _validate_review_path(path: Path, *, root: Path, allowed_root: str, label: str) -> list[str]:
    try:
        resolve_review_input_path(path, root=root, allowed_root=allowed_root, label=label)
    except M2CloseoutReviewError as exc:
        return [str(exc)]
    return []


def _validate_local_import_review(review: Any) -> list[str]:
    errors = _validate_review_common(review, LOCAL_IMPORT_REVIEW_SCHEMA_VERSION, "local import")
    if not errors and not _local_import_review_ready(review):
        errors.append("M2 local import review is not ready for line-index implementation.")
    return errors


def _validate_line_index_review(review: Any) -> list[str]:
    errors = _validate_review_common(review, LINE_INDEX_REVIEW_SCHEMA_VERSION, "line-index")
    if not errors and not _line_index_review_ready(review):
        errors.append("M2 line-index review is not ready for context-graph implementation.")
    return errors


def _validate_context_graph_review(review: Any) -> list[str]:
    errors = _validate_review_common(review, CONTEXT_GRAPH_REVIEW_SCHEMA_VERSION, "context-graph")
    if not errors and not _context_graph_review_ready(review):
        errors.append("M2 context-graph review is not ready for M2 closeout.")
    return errors


def _validate_review_common(review: Any, schema_version: str, label: str) -> list[str]:
    if not isinstance(review, dict):
        return [f"M2 {label} review must be a JSON object."]
    errors: list[str] = []
    if review.get("schema_version") != schema_version:
        errors.append(f"M2 {label} review schema_version must be {schema_version!r}.")
    if review.get("blockers") != []:
        errors.append(f"M2 {label} review blockers must be empty.")
    for field in FALSE_REVIEW_FIELDS:
        if review.get(field) is not False:
            errors.append(f"M2 {label} review must keep {field}=false.")
    return errors


def _local_import_review_ready(review: Any) -> bool:
    return (
        isinstance(review, dict)
        and review.get("schema_version") == LOCAL_IMPORT_REVIEW_SCHEMA_VERSION
        and review.get("summary_valid") is True
        and review.get("ready_for_line_index_implementation") is True
        and review.get("original_m2_import_done") is True
        and review.get("original_m2_line_index_done") is False
        and review.get("original_m2_context_graph_done") is False
        and review.get("blockers") == []
    )


def _line_index_review_ready(review: Any) -> bool:
    return (
        isinstance(review, dict)
        and review.get("schema_version") == LINE_INDEX_REVIEW_SCHEMA_VERSION
        and review.get("summary_valid") is True
        and review.get("ready_for_context_graph_implementation") is True
        and review.get("original_m2_import_done") is True
        and review.get("original_m2_line_index_done") is True
        and review.get("original_m2_context_graph_done") is False
        and review.get("blockers") == []
    )


def _context_graph_review_ready(review: Any) -> bool:
    return (
        isinstance(review, dict)
        and review.get("schema_version") == CONTEXT_GRAPH_REVIEW_SCHEMA_VERSION
        and review.get("summary_valid") is True
        and review.get("ready_for_m2_closeout_review_gate") is True
        and review.get("original_m2_import_done") is True
        and review.get("original_m2_line_index_done") is True
        and review.get("original_m2_context_graph_done") is True
        and review.get("blockers") == []
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
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{label} contains forbidden marker {marker!r}.")
    return errors


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise M2CloseoutReviewError("Unsafe path traversal is not allowed.")
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
            raise M2CloseoutReviewError("Path uses a forbidden runtime/private marker.")


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
    if "schema" in lowered or "json object" in lowered:
        return "malformed_review_evidence"
    return "m2_closeout_evidence_not_ready"


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


def _compatible_export(private_marker: str) -> dict[str, Any]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _compatible_record(f"{private_marker}_A", private_marker),
            _compatible_record(f"{private_marker}_B", private_marker),
        ],
        "context_edges": [
            {
                "from_record_id": f"{private_marker}_A",
                "to_record_id": f"{private_marker}_B",
                "relation": "previous_visible",
            }
        ],
        "metadata": {"nested_marker": private_marker},
    }


def _compatible_record(record_id: str, private_marker: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "line_id": private_marker,
        "conversation_id": private_marker,
        "speaker_id": private_marker,
        "speaker_label": private_marker,
        "context_placeholder": private_marker,
        "source_text": private_marker,
        "context_tags": [private_marker],
        "redacted_metadata": {"nested_marker": private_marker},
    }


if __name__ == "__main__":
    sys.exit(main())
