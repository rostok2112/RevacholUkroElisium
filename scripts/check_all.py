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
