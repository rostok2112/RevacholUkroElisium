from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.m2_synthetic_import_validator import (
        ALLOWED_RELATIONS,
        load_and_validate_m2_synthetic_import,
    )
    from scripts.run_m2_synthetic_context_graph_builder_dry_run import (
        RELATION_TO_BUCKET,
        build_m2_synthetic_context_graph,
    )
    from scripts.schema_validator import collect_errors, load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from m2_synthetic_import_validator import (
        ALLOWED_RELATIONS,
        load_and_validate_m2_synthetic_import,
    )
    from run_m2_synthetic_context_graph_builder_dry_run import (
        RELATION_TO_BUCKET,
        build_m2_synthetic_context_graph,
    )
    from schema_validator import collect_errors, load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_context_graph.synthetic.json"
IMPORT_FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_import_db.synthetic.json"
LINE_INDEX_FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_line_index.synthetic.json"
SCHEMA_PATH = ROOT / "specs/m2-synthetic-context-graph.schema.json"
DOC_PATH = ROOT / "docs/m2-synthetic-context-graph-contract.md"
ADR_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
IMPORT_DOC_PATH = ROOT / "docs/m2-synthetic-import-format-contract.md"
LINE_INDEX_DOC_PATH = ROOT / "docs/m2-synthetic-line-index-contract.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
SCHEMA_VERSION = "m2-synthetic-context-graph.v1"
RECOMMENDED_NEXT_STEP = "m2_synthetic_context_graph_builder_review_gate"
SAFETY_FLAG_FIELDS = (
    "real_game_text_included",
    "source_text_included",
    "file_contents_included",
    "paths_included",
    "filenames_included",
    "hashes_included",
    "raw_payloads_included",
    "logs_included",
    "runtime_evidence_included",
    "private_input_read",
    "graph_constructed",
    "arbitrary_future_branch_traversal",
    "automatic_game_install_scanning",
    "game_files_read",
    "bepinex_logs_read",
    "screenshots_read",
    "ocr_used",
    "save_files_read",
    "decompiled_code_used",
    "current_line_capture_used",
    "ui_text_reading_used",
    "unity_scanning_used",
    "hooks_used",
    "provider_called",
    "companion_contract_changed",
    "generated_graph_committed",
)
FORBIDDEN_FIELD_NAMES = (
    "source_text",
    "filename",
    "path",
    "digest",
    "hash",
    "raw_payload",
    "log",
    "runtime_evidence",
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
    "decompiled",
    "dnspy",
    "ilspy",
    "real extraction approved",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the M2 synthetic context-graph contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m2_synthetic_context_graph_contract_errors()
    if errors:
        if args.quiet:
            print("M2 synthetic context-graph contract check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M2 synthetic context-graph contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-synthetic-context-graph-contract-check.v1",
                    "fixture_schema_version": SCHEMA_VERSION,
                    "builder_added": True,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_synthetic_context_graph_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 synthetic context-graph fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 synthetic context-graph fixture must be an object."]

    errors = collect_errors(payload, load_json(SCHEMA_PATH))
    try:
        source = load_and_validate_m2_synthetic_import(IMPORT_FIXTURE_PATH)
        line_index = load_json(LINE_INDEX_FIXTURE_PATH)
    except Exception as exc:
        errors.append(f"Could not load M2 synthetic context-graph sources: {exc}")
    else:
        errors.extend(_node_errors(payload, line_index))
        errors.extend(_edge_errors(payload, source))
        if payload != build_m2_synthetic_context_graph(source, line_index):
            errors.append("$: must match deterministic synthetic context-graph builder output.")
    errors.extend(_safety_errors(payload))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return _dedupe(errors)


def _node_errors(payload: dict[str, Any], line_index: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    nodes = payload.get("nodes")
    if not isinstance(nodes, list):
        return errors
    expected = line_index.get("entries")
    if payload.get("node_count") != len(nodes):
        errors.append("$.node_count: must match nodes length.")
    if nodes != expected:
        errors.append("$.nodes: must match the synthetic line-index metadata entries exactly.")
    line_ids = [node.get("line_id") for node in nodes if isinstance(node, dict)]
    if line_ids != sorted(line_ids):
        errors.append("$.nodes: must be sorted by line_id.")
    if len(line_ids) != len(set(line_ids)):
        errors.append("$.nodes: must not contain duplicate line ids.")
    return errors


def _edge_errors(payload: dict[str, Any], source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    edges = payload.get("edges")
    nodes = payload.get("nodes")
    if not isinstance(edges, list) or not isinstance(nodes, list):
        return errors
    if payload.get("edge_count") != len(edges):
        errors.append("$.edge_count: must match edges length.")
    node_ids = {node.get("line_id") for node in nodes if isinstance(node, dict)}
    expected = sorted(
        (
            {
                "from_line_id": edge["from_record_id"],
                "to_line_id": edge["to_record_id"],
                "relation": edge["relation"],
                "retrieval_bucket": RELATION_TO_BUCKET[edge["relation"]],
            }
            for edge in source["context_edges"]
        ),
        key=_edge_sort_key,
    )
    if edges != expected:
        errors.append("$.edges: must match invented import relations exactly in stable order.")
    seen: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue
        from_id = edge.get("from_line_id")
        to_id = edge.get("to_line_id")
        relation = edge.get("relation")
        identity = (str(from_id), str(to_id), str(relation))
        if from_id not in node_ids or to_id not in node_ids:
            errors.append(f"$.edges[{index}]: must reference existing synthetic nodes.")
        if from_id == to_id:
            errors.append(f"$.edges[{index}]: must not reference itself.")
        if identity in seen:
            errors.append(f"$.edges[{index}]: duplicates an earlier edge.")
        seen.add(identity)
        if relation not in ALLOWED_RELATIONS:
            errors.append(f"$.edges[{index}].relation: uses an unknown relation.")
        elif edge.get("retrieval_bucket") != RELATION_TO_BUCKET[relation]:
            errors.append(f"$.edges[{index}].retrieval_bucket: does not match relation.")
    if edges != sorted(edges, key=_edge_sort_key):
        errors.append("$.edges: must use stable ordering.")
    return errors


def _safety_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("default_spoiler_budget") != "none":
        errors.append("$.default_spoiler_budget: must remain 'none'.")
    flags = payload.get("safety_flags")
    if isinstance(flags, dict):
        for field in SAFETY_FLAG_FIELDS:
            if flags.get(field) is not False:
                errors.append(f"$.safety_flags.{field}: must remain false.")
    for field in _iter_field_names(payload):
        if field in FORBIDDEN_FIELD_NAMES:
            errors.append(f"$: contains forbidden field {field!r}.")
    for value in _iter_string_values(payload):
        for url in URL_PATTERN.findall(value):
            errors.append(f"$: contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append("$: contains a secret/API-key-looking value.")
        if WINDOWS_PRIVATE_PATH_PATTERN.search(value) or POSIX_PRIVATE_PATH_PATTERN.search(value):
            errors.append("$: contains a private absolute path.")
        lowered = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"$: contains forbidden marker {marker!r}.")
    return errors


def _doc_errors() -> list[str]:
    required_refs = (
        "docs/m2-synthetic-context-graph-contract.md",
        "specs/m2-synthetic-context-graph.schema.json",
        "tests/fixtures/m2_synthetic_context_graph.synthetic.json",
        "scripts/check_m2_synthetic_context_graph_contract.py",
    )
    errors: list[str] = []
    for path in (
        DOC_PATH,
        ADR_PATH,
        IMPORT_DOC_PATH,
        LINE_INDEX_DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
    ):
        if not path.exists():
            errors.append(f"Missing M2 context-graph contract doc: {_display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for required in required_refs:
            if required not in text:
                errors.append(f"{_display_path(path)} must point to {required}.")
    return errors


def _edge_sort_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (str(edge.get("from_line_id")), str(edge.get("to_line_id")), str(edge.get("relation")))


def _iter_field_names(value: Any):
    if isinstance(value, dict):
        for field, nested in value.items():
            yield field
            yield from _iter_field_names(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_field_names(nested)


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_string_values(nested)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(ROOT.resolve(strict=False))).replace(
            "\\", "/"
        )
    except ValueError:
        return path.name


if __name__ == "__main__":
    raise SystemExit(main())
