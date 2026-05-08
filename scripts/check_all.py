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
