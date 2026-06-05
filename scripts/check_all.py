from __future__ import annotations

from pathlib import Path
import compileall
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    steps = [
        ("repository safety", [sys.executable, "scripts/check_repo.py"]),
        ("schema and fixture validation", [sys.executable, "scripts/validate_schemas.py"]),
        (
            "example config validation",
            [
                sys.executable,
                "scripts/validate_config.py",
                "--example",
                "config/revachol.example.toml",
            ],
        ),
        (
            "synthetic slice CLI smoke",
            [
                sys.executable,
                "scripts/run_synthetic_slice.py",
                "--output",
                "workspace/synthetic-slice/check-output.json",
                "--quiet",
            ],
        ),
        (
            "synthetic review renderer smoke",
            [
                sys.executable,
                "scripts/run_synthetic_slice.py",
                "--render-review",
                "--output",
                "workspace/synthetic-slice/review.html",
                "--quiet",
            ],
        ),
        (
            "synthetic eval smoke",
            [
                sys.executable,
                "scripts/run_synthetic_eval.py",
                "--output",
                "workspace/synthetic-slice/eval-summary.json",
                "--write-reviews",
                "--quiet",
            ],
        ),
        (
            "companion server smoke",
            [sys.executable, "scripts/run_companion_server.py", "--smoke-test"],
        ),
        (
            "companion client smoke",
            [sys.executable, "scripts/run_companion_client.py", "smoke-test"],
        ),
        (
            "provider pipeline smoke",
            [
                sys.executable,
                "scripts/run_provider_pipeline.py",
                "--output",
                "workspace/synthetic-slice/provider-output.json",
                "--quiet",
            ],
        ),
        (
            "provider registry smoke",
            [sys.executable, "scripts/run_provider_registry.py", "--summary", "--quiet"],
        ),
        (
            "provider preflight smoke",
            [sys.executable, "scripts/run_provider_preflight.py", "--quiet"],
        ),
        (
            "provider privacy smoke",
            [sys.executable, "scripts/run_provider_privacy_check.py", "--quiet"],
        ),
        (
            "provider contract regression smoke",
            [
                sys.executable,
                "scripts/run_provider_contract_regression.py",
                "--quiet",
            ],
        ),
        (
            "runtime translation memory contract",
            [
                sys.executable,
                "scripts/check_runtime_translation_memory_contract.py",
                "--quiet",
            ],
        ),
        (
            "runtime translation memory smoke",
            [
                sys.executable,
                "scripts/run_runtime_translation_memory.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "runtime current-line transport smoke",
            [
                sys.executable,
                "scripts/run_runtime_current_line_smoke.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "runtime current-line capture spike report",
            [
                sys.executable,
                "scripts/check_runtime_current_line_capture_spike_report.py",
                "--quiet",
            ],
        ),
        (
            "runtime current-line capture spike review smoke",
            [
                sys.executable,
                "scripts/review_runtime_current_line_capture_spike.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "runtime current-line capture strategy decision",
            [
                sys.executable,
                "scripts/check_runtime_current_line_capture_strategy_decision.py",
                "--quiet",
            ],
        ),
        (
            "runtime targeted hook candidate research contract",
            [
                sys.executable,
                "scripts/check_runtime_targeted_hook_candidate_research_contract.py",
                "--quiet",
            ],
        ),
        (
            "runtime targeted hook candidate research report",
            [
                sys.executable,
                "scripts/check_runtime_targeted_hook_candidate_research_report.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "runtime targeted hook candidate research review",
            [
                sys.executable,
                "scripts/review_runtime_targeted_hook_candidate_research_report.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "runtime targeted hook candidate decision contract",
            [
                sys.executable,
                "scripts/check_runtime_targeted_hook_candidate_decision_contract.py",
                "--quiet",
            ],
        ),
        (
            "runtime private hook descriptor contract",
            [
                sys.executable,
                "scripts/check_runtime_private_hook_descriptor_contract.py",
                "--quiet",
            ],
        ),
        (
            "local overlay prototype smoke",
            [
                sys.executable,
                "scripts/run_local_overlay_prototype.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "overlay view-model fixture regression",
            [
                sys.executable,
                "scripts/check_overlay_viewmodel_fixtures.py",
                "--quiet",
            ],
        ),
        (
            "overlay review HTML render smoke",
            [
                sys.executable,
                "scripts/render_overlay_review.py",
                "--quiet",
            ],
        ),
        (
            "overlay review accessibility smoke",
            [
                sys.executable,
                "scripts/check_overlay_review_accessibility.py",
                "--quiet",
            ],
        ),
        (
            "overlay state transition simulator smoke",
            [
                sys.executable,
                "scripts/run_overlay_state_simulator.py",
                "--fixture",
                "compact",
                "--action",
                "switch_deep",
                "--quiet",
            ],
        ),
        (
            "overlay state source smoke",
            [
                sys.executable,
                "scripts/run_overlay_state_source.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "overlay state-source fixture regression",
            [
                sys.executable,
                "scripts/check_overlay_state_source_fixtures.py",
                "--quiet",
            ],
        ),
        (
            "overlay refresh readiness contract",
            [
                sys.executable,
                "scripts/check_overlay_refresh_readiness_contract.py",
                "--quiet",
            ],
        ),
        (
            "overlay refresh readiness helper smoke",
            [
                sys.executable,
                "scripts/run_overlay_refresh_readiness.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "extraction/indexing scope contract",
            [
                sys.executable,
                "scripts/check_extraction_indexing_scope.py",
                "--quiet",
            ],
        ),
        (
            "synthetic extraction index contract",
            [
                sys.executable,
                "scripts/check_extraction_index_contract.py",
                "--quiet",
            ],
        ),
        (
            "extraction private input adapter contract",
            [
                sys.executable,
                "scripts/check_extraction_private_input_adapter_contract.py",
                "--quiet",
            ],
        ),
        (
            "private input adapter dry-run smoke",
            [
                sys.executable,
                "scripts/run_private_input_adapter_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "private input adapter dry-run review smoke",
            [
                sys.executable,
                "scripts/review_private_input_adapter_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "private input hash decision contract",
            [
                sys.executable,
                "scripts/check_private_input_hash_decision_contract.py",
                "--quiet",
            ],
        ),
        (
            "dry-run summary hash contract",
            [
                sys.executable,
                "scripts/check_dry_run_summary_hash_contract.py",
                "--quiet",
            ],
        ),
        (
            "private index construction contract",
            [
                sys.executable,
                "scripts/check_private_index_construction_contract.py",
                "--quiet",
            ],
        ),
        (
            "dry-run summary hash smoke",
            [
                sys.executable,
                "scripts/run_dry_run_summary_hash.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "dry-run summary hash review smoke",
            [
                sys.executable,
                "scripts/review_dry_run_summary_hash.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "private index builder dry-run smoke",
            [
                sys.executable,
                "scripts/run_private_index_builder_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "extraction/indexing Milestone 5A closeout",
            [
                sys.executable,
                "scripts/check_extraction_indexing_5a_closeout.py",
                "--quiet",
            ],
        ),
        (
            "M0 strict closeout",
            [
                sys.executable,
                "scripts/check_m0_closeout.py",
                "--quiet",
            ],
        ),
        (
            "roadmap governance review",
            [
                sys.executable,
                "scripts/check_roadmap_governance_review.py",
                "--quiet",
            ],
        ),
        (
            "M0 manual verification review smoke",
            [
                sys.executable,
                "scripts/review_m0_manual_verification.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M1 strict closeout",
            [
                sys.executable,
                "scripts/check_m1_closeout.py",
                "--quiet",
            ],
        ),
        (
            "M1 manual synthetic slice review smoke",
            [
                sys.executable,
                "scripts/review_m1_manual_synthetic_slice.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "original M2 local extraction import scope",
            [
                sys.executable,
                "scripts/check_m2_local_extraction_import_scope.py",
                "--quiet",
            ],
        ),
        (
            "M2 synthetic import format contract",
            [
                sys.executable,
                "scripts/check_m2_synthetic_import_format.py",
                "--quiet",
            ],
        ),
        (
            "M2 synthetic line-index contract",
            [
                sys.executable,
                "scripts/check_m2_synthetic_line_index_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 synthetic line-index builder dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_synthetic_line_index_builder_dry_run.py",
                "--check-fixture",
                "--quiet",
            ],
        ),
        (
            "M2 synthetic line-index builder review smoke",
            [
                sys.executable,
                "scripts/review_m2_synthetic_line_index_builder_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 synthetic context-graph contract",
            [
                sys.executable,
                "scripts/check_m2_synthetic_context_graph_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 synthetic context-graph builder dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_synthetic_context_graph_builder_dry_run.py",
                "--check-fixture",
                "--quiet",
            ],
        ),
        (
            "M2 synthetic context-graph builder review smoke",
            [
                sys.executable,
                "scripts/review_m2_synthetic_context_graph_builder_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import adapter contract",
            [
                sys.executable,
                "scripts/check_m2_explicit_local_import_adapter_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import adapter dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_adapter_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import adapter dry-run review smoke",
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_adapter_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import schema-compatibility contract",
            [
                sys.executable,
                "scripts/check_m2_explicit_local_import_schema_compatibility_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import schema-compatibility dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import schema-compatibility dry-run review smoke",
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_schema_compatibility_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import record-shape contract",
            [
                sys.executable,
                "scripts/check_m2_explicit_local_import_record_shape_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import record-shape dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_record_shape_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import record-shape dry-run review smoke",
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_record_shape_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge shape contract",
            [
                sys.executable,
                "scripts/check_m2_explicit_local_import_context_edge_shape_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge shape dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_context_edge_shape_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge shape dry-run review smoke",
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_context_edge_shape_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge reference contract",
            [
                sys.executable,
                "scripts/check_m2_explicit_local_import_context_edge_reference_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge reference dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge reference dry-run review smoke",
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge integrity contract",
            [
                sys.executable,
                "scripts/check_m2_explicit_local_import_context_edge_integrity_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge integrity dry-run smoke",
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_context_edge_integrity_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 explicit local-import context-edge integrity dry-run review smoke",
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_context_edge_integrity_dry_run.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 local import final approval contract",
            [
                sys.executable,
                "scripts/check_m2_local_import_final_approval_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 local import implementation smoke",
            [
                sys.executable,
                "scripts/run_m2_local_import.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 local import review smoke",
            [
                sys.executable,
                "scripts/review_m2_local_import.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 line-index contract",
            [
                sys.executable,
                "scripts/check_m2_line_index_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 line-index implementation smoke",
            [
                sys.executable,
                "scripts/run_m2_line_index.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 line-index review smoke",
            [
                sys.executable,
                "scripts/review_m2_line_index.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 context-graph contract",
            [
                sys.executable,
                "scripts/check_m2_context_graph_contract.py",
                "--quiet",
            ],
        ),
        (
            "M2 context-graph implementation smoke",
            [
                sys.executable,
                "scripts/run_m2_context_graph.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 context-graph review smoke",
            [
                sys.executable,
                "scripts/review_m2_context_graph.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 closeout review smoke",
            [
                sys.executable,
                "scripts/review_m2_closeout.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M2 manual private-export verification smoke",
            [
                sys.executable,
                "scripts/review_m2_manual_private_export_verification.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M3 BepInEx bridge scope",
            [
                sys.executable,
                "scripts/check_m3_bepinex_bridge_scope.py",
                "--quiet",
            ],
        ),
        (
            "M3 current-line event contract",
            [
                sys.executable,
                "scripts/check_m3_current_line_event_contract.py",
                "--quiet",
            ],
        ),
        (
            "M3 current-line event implementation",
            [
                sys.executable,
                "scripts/check_m3_current_line_event_implementation.py",
                "--quiet",
            ],
        ),
        (
            "M3 line-ID match smoke",
            [
                sys.executable,
                "scripts/run_m3_line_id_match.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M3 debug console",
            [
                sys.executable,
                "scripts/check_m3_debug_console.py",
                "--quiet",
            ],
        ),
        (
            "M3 closeout",
            [
                sys.executable,
                "scripts/check_m3_closeout.py",
                "--quiet",
            ],
        ),
        (
            "M4 real overlay scope",
            [
                sys.executable,
                "scripts/check_m4_real_overlay_scope.py",
                "--quiet",
            ],
        ),
        (
            "M4 overlay shell contract",
            [
                sys.executable,
                "scripts/check_m4_overlay_shell_contract.py",
                "--quiet",
            ],
        ),
        (
            "M4 compact overlay shell smoke",
            [
                sys.executable,
                "scripts/run_m4_overlay_shell.py",
                "--self-test",
                "--quiet",
            ],
        ),
        (
            "M4 closeout",
            [
                sys.executable,
                "scripts/check_m4_closeout.py",
                "--quiet",
            ],
        ),
        (
            "M0-M4 strict completion status",
            [
                sys.executable,
                "scripts/check_milestone_completion_status.py",
                "--quiet",
            ],
        ),
        (
            "BepInEx bridge safety smoke",
            [
                sys.executable,
                "scripts/check_bepinex_bridge_safety.py",
                "--quiet",
            ],
        ),
        (
            "prompt pack smoke",
            [sys.executable, "scripts/run_prompt_pack.py", "--summary"],
        ),
    ]

    for label, command in steps:
        if _run(label, command) != 0:
            return 1

    if not compileall.compile_dir(ROOT / "scripts", quiet=1):
        print("Python compile check failed for scripts/")
        return 1
    print("OK Python compile check", flush=True)

    unit_command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    if _run("unit tests", unit_command) != 0:
        return 1

    ruff = shutil.which("ruff")
    if ruff:
        if _run("ruff check", [ruff, "check", "."]) != 0:
            return 1
        if _run("ruff format check", [ruff, "format", "--check", "."]) != 0:
            return 1
    else:
        print("SKIP ruff: not installed", flush=True)

    print("All checks passed.", flush=True)
    return 0


def _run(label: str, command: list[str]) -> int:
    print(f"\n== {label} ==", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False, stderr=subprocess.STDOUT)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
