from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = ROOT / "packages/bepinex-plugin/Revachol.UkrainianCompanion.BepInExBridge.csproj"
OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/bepinex-bridge"
ASSEMBLY_NAME = "Revachol.UkrainianCompanion.BepInExBridge"
TARGET_FRAMEWORK = "netstandard2.1"
ENV_CORE_KEYS = ("BEPINEX_CORE_DLL", "BepInExCoreDll")
ENV_IL2CPP_KEYS = ("BEPINEX_IL2CPP_DLL", "BepInExIL2CPPDll")
REPORT_SCHEMA_VERSION = "bepinex-bridge-build-report.v1"

WARNING_LINE_PATTERN = re.compile(r"\bwarning\s+[A-Z]+[0-9]+\s*:", re.IGNORECASE)
WARNING_SUMMARY_PATTERN = re.compile(r"^\s*(\d+)\s+Warning\(s\)\s*$", re.IGNORECASE)
MSB3277_PATTERN = re.compile(r"\bMSB3277\b", re.IGNORECASE)
MSB3277_GROUP_PATTERN = re.compile(r"\bwarning\s+MSB3277\s*:\s*Found conflicts", re.IGNORECASE)


Runner = Callable[..., subprocess.CompletedProcess[str]]


class BepInExBridgeBuildError(RuntimeError):
    """Raised when the optional bridge build helper cannot prepare a safe report."""


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    output_path: Path | None = None
    if args.output:
        try:
            output_path = ensure_safe_output_path(Path(args.output))
        except BepInExBridgeBuildError as exc:
            parser.error(str(exc))

    report = build_bepinex_bridge_report(
        core_dll=args.core_dll,
        il2cpp_dll=args.il2cpp_dll,
        configuration=args.configuration,
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_canonical_json(report), encoding="utf-8")

    if args.quiet:
        print(_quiet_line(report))
    else:
        print(_canonical_json(report), end="")

    if report["build_attempted"] and not report["build_succeeded"]:
        return 1
    return 0


def build_bepinex_bridge_report(
    *,
    core_dll: str | None = None,
    il2cpp_dll: str | None = None,
    configuration: str = "Debug",
    env: Mapping[str, str] | None = None,
    runner: Runner = subprocess.run,
    dotnet_path: str | None = None,
) -> dict[str, object]:
    """Return a JSON-safe optional build report.

    The build is attempted only when `dotnet` and both user-local BepInEx reference DLLs are
    available. The helper never downloads references or requires game files.
    """

    env = os.environ if env is None else env
    dotnet = dotnet_path if dotnet_path is not None else shutil.which("dotnet")
    core_ref = resolve_reference_path(core_dll, ENV_CORE_KEYS, env)
    il2cpp_ref = resolve_reference_path(il2cpp_dll, ENV_IL2CPP_KEYS, env)
    references_supplied = bool(core_ref and il2cpp_ref)

    report = _base_report(
        configuration=configuration,
        dotnet_found=bool(dotnet),
        references_supplied=references_supplied,
        core_ref=core_ref,
        il2cpp_ref=il2cpp_ref,
    )

    if not dotnet:
        report["skipped_reason"] = "dotnet_not_found"
        return report
    if not references_supplied:
        report["skipped_reason"] = "bepinex_references_missing"
        return report

    assert core_ref is not None
    assert il2cpp_ref is not None
    command = build_dotnet_command(dotnet, core_ref, il2cpp_ref, configuration)
    report["build_attempted"] = True
    report["command"] = redact_command(command)

    completed = runner(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = completed.stdout or ""
    warning_count, msb3277_count = parse_warning_counts(output)
    report["warning_count"] = warning_count
    report["msb3277_warning_count"] = msb3277_count
    report["build_succeeded"] = completed.returncode == 0
    report["dotnet_exit_code"] = completed.returncode
    if completed.returncode != 0:
        report["skipped_reason"] = None
        report["failure_summary"] = summarize_build_failure(output)
        return report

    dll_path = expected_output_dll_path(configuration)
    report["output_dll_path"] = safe_path_for_report(dll_path) if dll_path.exists() else None
    report["skipped_reason"] = None
    return report


def resolve_reference_path(
    explicit_value: str | None, env_keys: Sequence[str], env: Mapping[str, str]
) -> Path | None:
    candidates = [explicit_value] if explicit_value else []
    candidates.extend(env.get(key) for key in env_keys if env.get(key))
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.exists() and path.is_file():
            return path.resolve()
    return None


def build_dotnet_command(
    dotnet: str, core_dll: Path, il2cpp_dll: Path, configuration: str
) -> list[str]:
    return [
        dotnet,
        "build",
        str(PROJECT_FILE),
        "--configuration",
        configuration,
        "/nologo",
        f"-p:BepInExCoreDll={core_dll}",
        f"-p:BepInExIL2CPPDll={il2cpp_dll}",
    ]


def redact_command(command: Sequence[str]) -> list[str]:
    redacted: list[str] = []
    for part in command:
        if part.startswith("-p:BepInExCoreDll="):
            redacted.append("-p:BepInExCoreDll=<local:BepInEx.Core.dll>")
        elif part.startswith("-p:BepInExIL2CPPDll="):
            redacted.append("-p:BepInExIL2CPPDll=<local:BepInEx.Unity.IL2CPP.dll>")
        elif part.startswith("/") and "/" not in part[1:]:
            redacted.append(part)
        else:
            redacted.append(safe_path_string_for_report(part))
    return redacted


def parse_warning_counts(output: str) -> tuple[int, int]:
    lines = output.splitlines()
    summary_counts = [
        int(match.group(1))
        for line in lines
        if (match := WARNING_SUMMARY_PATTERN.match(line)) is not None
    ]
    msb3277_count = sum(1 for line in lines if MSB3277_GROUP_PATTERN.search(line))
    counted_warning_lines: list[str] = []
    for line in lines:
        if MSB3277_PATTERN.search(line):
            if MSB3277_GROUP_PATTERN.search(line):
                counted_warning_lines.append(line)
            continue
        if WARNING_LINE_PATTERN.search(line):
            counted_warning_lines.append(line)
    if summary_counts:
        warning_count = max(summary_counts)
    else:
        warning_count = len(counted_warning_lines)
    if msb3277_count == 0:
        msb3277_count = sum(
            1
            for line in lines
            if WARNING_LINE_PATTERN.search(line) and MSB3277_PATTERN.search(line)
        )
    msb3277_count = min(msb3277_count, warning_count)
    return warning_count, msb3277_count


def summarize_build_failure(output: str) -> str:
    for line in output.splitlines():
        lowered = line.lower()
        if "error " in lowered or "failed" in lowered:
            return safe_path_string_for_report(line.strip())[:300]
    return "dotnet build failed"


def expected_output_dll_path(configuration: str) -> Path:
    return (
        ROOT
        / "packages/bepinex-plugin/bin"
        / configuration
        / TARGET_FRAMEWORK
        / f"{ASSEMBLY_NAME}.dll"
    )


def ensure_safe_output_path(path: Path) -> Path:
    resolved_root = OUTPUT_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise BepInExBridgeBuildError(
            f"Output path must stay under {OUTPUT_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise BepInExBridgeBuildError("Output report path must end in .json")
    return resolved


def safe_path_for_report(path: Path | None) -> str | None:
    if path is None:
        return None
    return safe_path_string_for_report(str(path))


def safe_path_string_for_report(value: str) -> str:
    normalized = value.replace("\\", "/")
    root_normalized = str(ROOT).replace("\\", "/")
    if root_normalized in normalized:
        normalized = normalized.replace(root_normalized, ".")
        if normalized.startswith("./"):
            return normalized[2:]
        return normalized
    if normalized.startswith(root_normalized + "/"):
        return normalized[len(root_normalized) + 1 :]
    if normalized.startswith("/") and "/" not in normalized[1:]:
        return normalized
    if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("/"):
        return f"<local:{Path(value).name}>"
    return value


def _base_report(
    *,
    configuration: str,
    dotnet_found: bool,
    references_supplied: bool,
    core_ref: Path | None,
    il2cpp_ref: Path | None,
) -> dict[str, object]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "project": str(PROJECT_FILE.relative_to(ROOT)),
        "configuration": configuration,
        "dotnet_found": dotnet_found,
        "references_supplied": references_supplied,
        "reference_filenames": {
            "core": core_ref.name if core_ref else None,
            "il2cpp": il2cpp_ref.name if il2cpp_ref else None,
        },
        "build_attempted": False,
        "build_succeeded": False,
        "warning_count": 0,
        "msb3277_warning_count": 0,
        "output_dll_path": None,
        "skipped_reason": None,
        "dotnet_exit_code": None,
        "failure_summary": None,
        "command": None,
        "no_game_files_required": True,
        "no_downloads_performed": True,
        "no_companion_contract_change": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Optionally build the synthetic/manual BepInEx bridge when local refs exist."
    )
    parser.add_argument("--core-dll", help="Path to user-local BepInEx.Core.dll.")
    parser.add_argument("--il2cpp-dll", help="Path to user-local BepInEx.Unity.IL2CPP.dll.")
    parser.add_argument(
        "--configuration",
        choices=("Debug", "Release"),
        default="Debug",
        help="MSBuild configuration to compile when refs are supplied.",
    )
    parser.add_argument(
        "--output", help="Optional JSON report under workspace/synthetic-slice/bepinex-bridge/."
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short skip/pass/fail line.")
    return parser


def _quiet_line(report: Mapping[str, object]) -> str:
    if not report["build_attempted"]:
        return f"BepInEx bridge build skipped: {report['skipped_reason']}"
    if report["build_succeeded"]:
        return (
            "BepInEx bridge build passed "
            f"({report['warning_count']} warnings, "
            f"{report['msb3277_warning_count']} MSB3277)."
        )
    return "BepInEx bridge build failed."


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


if __name__ == "__main__":
    sys.exit(main())
