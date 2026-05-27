from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import subprocess
import sys
from typing import Any, Callable, Sequence

try:
    from scripts.companion_client import CompanionClient, CompanionClientError
    from scripts.run_bepinex_metadata_probe_local_smoke import (
        LocalSmokeError,
        discover_local_smoke_paths,
        discovery_summary,
        enable_probe_flow,
        set_synthetic_send_config_action,
    )
    from scripts.run_bridge_to_overlay_synthetic_smoke import (
        BridgeToOverlaySmokeError,
        SmokeOptions as BridgeSmokeOptions,
        run_bridge_to_overlay_smoke,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - direct script execution from scripts/
    from companion_client import CompanionClient, CompanionClientError
    from run_bepinex_metadata_probe_local_smoke import (
        LocalSmokeError,
        discover_local_smoke_paths,
        discovery_summary,
        enable_probe_flow,
        set_synthetic_send_config_action,
    )
    from run_bridge_to_overlay_synthetic_smoke import (
        BridgeToOverlaySmokeError,
        SmokeOptions as BridgeSmokeOptions,
        run_bridge_to_overlay_smoke,
    )
    from synthetic_slice import ROOT


SCHEMA_VERSION = "local-bridge-workflow.v1"
DEFAULT_SERVER_URL = "http://127.0.0.1:8765"
BUILD_HELPER = ROOT / "scripts/build_bepinex_bridge.py"
PHASES = (
    "doctor",
    "prepare-metadata-smoke",
    "prepare-companion-smoke",
    "prepare-bridge-to-overlay-smoke",
    "post-bridge-to-overlay-smoke",
    "cleanup",
)
STAGED_ARTIFACT_SUFFIXES = (
    ".log",
    ".html",
    ".dll",
    ".pdb",
    ".png",
    ".jpg",
    ".jpeg",
)
STAGED_ARTIFACT_NAMES = {
    "logoutput.log",
    "report.json",
    "summary.json",
    "overlay.html",
}


class LocalBridgeWorkflowError(RuntimeError):
    """Raised when a local workflow phase cannot continue safely."""


@dataclass(frozen=True)
class GitCommandResult:
    returncode: int
    stdout: str


GitRunner = Callable[[Sequence[str]], GitCommandResult]


@dataclass(frozen=True)
class WorkflowOptions:
    server_url: str = DEFAULT_SERVER_URL
    game_dir: str | None = None
    core_dll: str | None = None
    il2cpp_dll: str | None = None
    configuration: str = "Debug"
    skip_build: bool = False
    skip_install: bool = False
    write_report: bool = False
    verbose: bool = False


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    options = WorkflowOptions(
        server_url=args.server_url,
        game_dir=args.game_dir,
        core_dll=args.core_dll,
        il2cpp_dll=args.il2cpp_dll,
        configuration=args.configuration,
        skip_build=args.skip_build,
        skip_install=args.skip_install,
        write_report=args.write_report,
        verbose=args.verbose,
    )
    client = CompanionClient(args.server_url)

    try:
        summary, exit_code = run_local_bridge_workflow(
            args.phase,
            options,
            client=client,
        )
    except (LocalBridgeWorkflowError, LocalSmokeError, BridgeToOverlaySmokeError) as exc:
        summary = _base_summary(args.phase)
        summary["ok"] = False
        summary["blockers"] = [_safe_blocker(str(exc))]
        exit_code = 1

    if args.quiet:
        status = "ok" if exit_code == 0 else "not_ready"
        print(f"Local bridge workflow {args.phase}: {status}.")
    else:
        print(canonical_json(summary), end="")
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run redacted local bridge workflow phases without launching the game, printing raw "
            "logs, dumping provider payloads, or changing companion contracts."
        )
    )
    parser.add_argument("--phase", choices=PHASES, default="doctor")
    parser.add_argument("--auto-discover", action="store_true", help="Use bounded discovery.")
    parser.add_argument("--game-dir", help="Explicit local game directory override.")
    parser.add_argument("--core-dll", help="Explicit BepInEx.Core.dll override.")
    parser.add_argument("--il2cpp-dll", help="Explicit BepInEx IL2CPP DLL override.")
    parser.add_argument("--configuration", choices=("Debug", "Release"), default="Debug")
    parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include local paths in discovery output. Still excludes raw logs and payloads.",
    )
    return parser


def run_local_bridge_workflow(
    phase: str,
    options: WorkflowOptions,
    *,
    client: Any | None = None,
    git_runner: GitRunner | None = None,
) -> tuple[dict[str, object], int]:
    client = client or CompanionClient(options.server_url)
    if phase == "doctor":
        return run_doctor(options, client=client, git_runner=git_runner)
    if phase == "prepare-metadata-smoke":
        return run_prepare_metadata_smoke(options)
    if phase == "prepare-companion-smoke":
        return run_prepare_companion_smoke(options, client=client)
    if phase == "prepare-bridge-to-overlay-smoke":
        return run_delegated_bridge_to_overlay("prepare", options, client=client)
    if phase == "post-bridge-to-overlay-smoke":
        return run_delegated_bridge_to_overlay("post", options, client=client)
    if phase == "cleanup":
        return run_delegated_bridge_to_overlay("cleanup", options, client=client)
    raise LocalBridgeWorkflowError(f"Unsupported workflow phase: {phase}")


def run_doctor(
    options: WorkflowOptions,
    *,
    client: Any,
    git_runner: GitRunner | None = None,
) -> tuple[dict[str, object], int]:
    summary = _base_summary("doctor")
    discovery = _discover(options)
    git_summary = collect_git_summary(git_runner=git_runner)
    health_available = _health_available(client)
    doctor = {
        "git_clean": git_summary["git_clean"],
        "bridge_build_helper_available": BUILD_HELPER.exists(),
        "bepinex_refs_found": discovery.build_refs_ready,
        "steam_game_autodiscovery": discovery.game.game_dir is not None,
        "bepinex_plugins_exists": discovery.bepinex.plugins_dir is not None,
        "companion_health_available": health_available,
        "bridge_dll_built_or_found": discovery.bridge_dll is not None,
        "no_raw_logs_reports_staged": git_summary["no_raw_logs_reports_staged"],
    }
    blockers = [
        name
        for name, ready in (
            ("git_dirty_or_unavailable", git_summary["git_clean"]),
            ("bridge_build_helper_missing", doctor["bridge_build_helper_available"]),
            ("bepinex_refs_missing", doctor["bepinex_refs_found"]),
            ("steam_game_not_discovered", doctor["steam_game_autodiscovery"]),
            ("bepinex_plugins_missing", doctor["bepinex_plugins_exists"]),
            ("companion_health_unavailable", doctor["companion_health_available"]),
            ("bridge_dll_missing", doctor["bridge_dll_built_or_found"]),
            ("raw_logs_reports_staged", doctor["no_raw_logs_reports_staged"]),
        )
        if not ready
    ]
    summary["git"] = git_summary
    summary["discovery"] = discovery_summary(discovery, verbose=options.verbose)
    summary["doctor"] = doctor
    summary["blockers"] = blockers
    summary["ok"] = not blockers
    return summary, 0 if not blockers else 1


def run_prepare_metadata_smoke(options: WorkflowOptions) -> tuple[dict[str, object], int]:
    summary = _base_summary("prepare-metadata-smoke")
    discovery = _discover(options)
    actions = enable_probe_flow(
        discovery,
        configuration=options.configuration,
        skip_build=options.skip_build,
        skip_install=options.skip_install,
    )
    summary["discovery"] = discovery_summary(discovery, verbose=options.verbose)
    summary["prepare_metadata_smoke"] = {
        "bridge_build_attempted": _nested_bool(actions, "build", "attempted"),
        "bridge_build_succeeded": _nested_bool(actions, "build", "succeeded"),
        "bridge_dll_installed": _nested_bool(actions, "install", "installed"),
        "metadata_probe_enabled": _nested_bool(actions, "config", "metadata_probe_enabled"),
        "metadata_probe_log_on_start": _nested_bool(
            actions, "config", "metadata_probe_log_on_start"
        ),
        "send_synthetic_event_on_start": False,
    }
    summary["ok"] = True
    return summary, 0


def run_prepare_companion_smoke(
    options: WorkflowOptions, *, client: Any
) -> tuple[dict[str, object], int]:
    summary = _base_summary("prepare-companion-smoke")
    health_available = _health_available(client)
    summary["companion_health_available"] = health_available
    if not health_available:
        summary["blockers"] = ["companion_health_unavailable"]
        return summary, 1

    discovery = _discover(options)
    actions = enable_probe_flow(
        discovery,
        configuration=options.configuration,
        skip_build=options.skip_build,
        skip_install=options.skip_install,
    )
    synthetic_action = set_synthetic_send_config_action(discovery, enabled=True)
    summary["discovery"] = discovery_summary(discovery, verbose=options.verbose)
    summary["prepare_companion_smoke"] = {
        "bridge_build_attempted": _nested_bool(actions, "build", "attempted"),
        "bridge_build_succeeded": _nested_bool(actions, "build", "succeeded"),
        "bridge_dll_installed": _nested_bool(actions, "install", "installed"),
        "metadata_probe_enabled": _nested_bool(actions, "config", "metadata_probe_enabled"),
        "metadata_probe_log_on_start": _nested_bool(
            actions, "config", "metadata_probe_log_on_start"
        ),
        "send_synthetic_event_on_start": bool(
            synthetic_action.get("send_synthetic_event_on_start")
        ),
    }
    summary["ok"] = True
    return summary, 0


def run_delegated_bridge_to_overlay(
    delegated_phase: str,
    options: WorkflowOptions,
    *,
    client: Any,
) -> tuple[dict[str, object], int]:
    bridge_options = BridgeSmokeOptions(
        server_url=options.server_url,
        game_dir=options.game_dir,
        core_dll=options.core_dll,
        il2cpp_dll=options.il2cpp_dll,
        configuration=options.configuration,
        skip_build=options.skip_build,
        skip_install=options.skip_install,
        write_report=options.write_report,
        verbose=options.verbose,
    )
    delegated_summary, exit_code = run_bridge_to_overlay_smoke(
        delegated_phase, bridge_options, client=client
    )
    summary = _base_summary(f"{delegated_phase}-bridge-to-overlay-smoke")
    summary["delegated_helper"] = "scripts/run_bridge_to_overlay_synthetic_smoke.py"
    summary["delegated_phase"] = delegated_phase
    summary["bridge_to_overlay"] = delegated_summary
    summary["ok"] = exit_code == 0 and bool(delegated_summary.get("ok"))
    summary["blockers"] = delegated_summary.get("blockers", [])
    return summary, exit_code


def collect_git_summary(*, git_runner: GitRunner | None = None) -> dict[str, object]:
    git_runner = git_runner or _run_git
    status = git_runner(("status", "--porcelain"))
    staged = git_runner(("diff", "--cached", "--name-only"))
    status_lines = _lines(status.stdout) if status.returncode == 0 else []
    staged_lines = _lines(staged.stdout) if staged.returncode == 0 else []
    staged_artifacts = [line for line in staged_lines if is_runtime_artifact_path(line)]
    git_available = status.returncode == 0 and staged.returncode == 0
    return {
        "git_available": git_available,
        "git_clean": git_available and not status_lines,
        "dirty_entry_count": len(status_lines),
        "staged_entry_count": len(staged_lines),
        "staged_artifact_candidate_count": len(staged_artifacts),
        "no_raw_logs_reports_staged": git_available and not staged_artifacts,
        "private_paths_redacted": True,
    }


def is_runtime_artifact_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip().lower()
    if not normalized:
        return False
    parts = normalized.split("/")
    name = parts[-1]
    return (
        normalized.startswith("workspace/")
        or "bin" in parts
        or "obj" in parts
        or name in STAGED_ARTIFACT_NAMES
        or normalized.endswith(STAGED_ARTIFACT_SUFFIXES)
    )


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _discover(options: WorkflowOptions):
    return discover_local_smoke_paths(
        game_dir=options.game_dir,
        core_dll=options.core_dll,
        il2cpp_dll=options.il2cpp_dll,
        configuration=options.configuration,
    )


def _run_git(args: Sequence[str]) -> GitCommandResult:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError:
        return GitCommandResult(returncode=1, stdout="")
    return GitCommandResult(returncode=completed.returncode, stdout=completed.stdout or "")


def _health_available(client: Any) -> bool:
    try:
        health = client.health()
    except (CompanionClientError, OSError, ValueError):
        return False
    return isinstance(health, dict) and health.get("status") == "ok"


def _base_summary(phase: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "phase": phase,
        "ok": False,
        "blockers": [],
        "metadata_only": True,
        "no_game_launch_performed": True,
        "raw_log_included": False,
        "raw_report_included": False,
        "raw_provider_payload_included": False,
        "screenshots_read": False,
        "game_files_read": False,
        "provider_called": False,
        "companion_contract_changed": False,
        "current_line_capture_performed": False,
        "real_text_capture_performed": False,
    }


def _nested_bool(payload: dict[str, object], key: str, nested_key: str) -> bool:
    nested = payload.get(key)
    return bool(nested.get(nested_key)) if isinstance(nested, dict) else False


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _safe_blocker(message: str) -> str:
    lowered = message.lower()
    if "companion" in lowered:
        return "companion_unavailable_or_invalid"
    if "game directory" in lowered:
        return "game_directory_not_found"
    if "bepinex" in lowered:
        return "bepinex_path_unavailable"
    if "unsafe" in lowered:
        return "unsafe_local_workflow_state"
    return "local_bridge_workflow_failed"


if __name__ == "__main__":
    sys.exit(main())
