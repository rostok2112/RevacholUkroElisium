from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Iterable, Mapping, Sequence

try:
    from scripts.build_bepinex_bridge import build_bepinex_bridge_report
    from scripts.check_bepinex_metadata_probe_report import (
        REPORT_ROOT,
        canonical_json,
        collect_metadata_probe_report_errors,
        default_metadata_probe_report_template,
        ensure_safe_metadata_probe_report_path,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from build_bepinex_bridge import build_bepinex_bridge_report
    from check_bepinex_metadata_probe_report import (
        REPORT_ROOT,
        canonical_json,
        collect_metadata_probe_report_errors,
        default_metadata_probe_report_template,
        ensure_safe_metadata_probe_report_path,
    )


ROOT = Path(__file__).resolve().parents[1]
REPORT_OUTPUT = REPORT_ROOT / "report.json"
PLUGIN_CONFIG_FILENAME = "local.revachol.ukrainian-companion.bridge.cfg"
BRIDGE_ASSEMBLY_NAME = "Revachol.UkrainianCompanion.BepInExBridge"
LOG_FILENAME = "LogOutput.log"

ENV_CORE_KEYS = ("BEPINEX_CORE_DLL", "BepInExCoreDll")
ENV_IL2CPP_KEYS = ("BEPINEX_IL2CPP_DLL", "BepInExIL2CPPDll")
CORE_DLL_NAMES = ("BepInEx.Core.dll",)
IL2CPP_DLL_NAMES = ("BepInEx.IL2CPP.dll", "BepInEx.Unity.IL2CPP.dll")

GAME_DIR_NAMES = (
    "Disco Elysium",
    "Disco Elysium - The Final Cut",
    "Disco Elysium The Final Cut",
)
COMMON_STEAM_ROOTS = (
    Path(r"C:\Program Files (x86)\Steam"),
    Path(r"C:\Program Files\Steam"),
    Path(r"D:\SteamLibrary"),
    Path(r"E:\SteamLibrary"),
    Path(r"D:\Games\Steam"),
    Path(r"E:\Games\Steam"),
)

PLUGIN_LOADED_MARKERS = (
    "Revachol Ukrainian Companion Bridge",
    "loaded in synthetic/manual bridge mode",
)
METADATA_SNAPSHOT_MARKER = "Metadata probe snapshot: synthetic_manual=true"
TRUE_FALSE_MARKERS = (
    "real_text_captured=false",
    "current_line_capture_enabled=false",
    "ui_probe_attempted=false",
    "scene_probe_attempted=false",
)
COUNTER_PATTERNS = {
    "metadata_snapshot_created_count": re.compile(
        r"counters\.metadata_snapshot_created_count=(\d+)"
    ),
    "health_check_observed_count": re.compile(r"counters\.health_check_observed_count=(\d+)"),
    "synthetic_send_configured_count": re.compile(
        r"counters\.synthetic_send_configured_count=(\d+)"
    ),
}
SNAPSHOT_BOOL_PATTERNS = {
    "companion_health_checked": re.compile(r"companion_health_checked=(true|false)"),
    "companion_available": re.compile(r"companion_available=(true|false)"),
    "synthetic_event_send_configured": re.compile(r"synthetic_event_send_configured=(true|false)"),
}

FORBIDDEN_LOG_PATTERNS = {
    "stack_trace": re.compile(
        r"stack trace|traceback \(most recent call last\)|\bat\s+revachol|\bat\s+il2cpp",
        re.IGNORECASE,
    ),
    "raw_payload": re.compile(
        r"request payload|response payload|raw companion payload|raw_english_text|"
        r'"input_type"\s*:|response\.content|readasstringasync',
        re.IGNORECASE,
    ),
    "screenshot_or_ocr": re.compile(
        r"screenshot|screen capture|\.png\b|\.jpg\b|\.jpeg\b|\bocr\b|tesseract",
        re.IGNORECASE,
    ),
    "runtime_scan_or_hook": re.compile(
        r"harmonypatch|harmony patch|game hook|method hook|findobjectoftype|"
        r"findobjectsoftype|gameobject\.find|resources\.findobjectsoftypeall|scenemanager",
        re.IGNORECASE,
    ),
    "capture_enabled": re.compile(
        r"real_text_captured=true|current_line_capture_enabled=true|captured text|"
        r"dialogue capture|current-line capture|current line capture|ui text captured",
        re.IGNORECASE,
    ),
    "extraction": re.compile(
        r"file extraction|extracted localization|extracted text|save data|save file",
        re.IGNORECASE,
    ),
    "provider_or_contract": re.compile(
        r"provider execution|api\.openai|deepl|anthropic|local_model|"
        r"companion contract change|new companion endpoint",
        re.IGNORECASE,
    ),
}


class LocalSmokeError(RuntimeError):
    """Raised when local smoke preparation cannot continue safely."""


@dataclass(frozen=True)
class GameDiscovery:
    game_dir: Path | None
    source: str


@dataclass(frozen=True)
class BepInExPaths:
    plugins_dir: Path | None
    config_dir: Path | None
    log_file: Path | None


@dataclass(frozen=True)
class ReferenceDiscovery:
    core_dll: Path | None
    il2cpp_dll: Path | None


@dataclass(frozen=True)
class LocalDiscovery:
    game: GameDiscovery
    bepinex: BepInExPaths
    refs: ReferenceDiscovery
    bridge_dll: Path | None

    @property
    def build_refs_ready(self) -> bool:
        return self.refs.core_dll is not None and self.refs.il2cpp_dll is not None


@dataclass(frozen=True)
class LogCheck:
    log_found: bool
    plugin_loaded_observed: bool
    metadata_snapshot_observed: bool
    metadata_snapshot_created_count_observed: bool
    health_check_observed_count_observed: bool
    synthetic_send_configured_count_observed: bool
    real_text_captured_false_observed: bool
    current_line_capture_enabled_false_observed: bool
    ui_probe_attempted_false_observed: bool
    scene_probe_attempted_false_observed: bool
    forbidden_marker_detected: bool
    raw_log_included: bool
    counter_values: dict[str, int]
    companion_health_checked: bool
    companion_available: bool
    synthetic_event_send_configured: bool
    forbidden_marker_categories: tuple[str, ...]

    def redacted_summary(self) -> dict[str, object]:
        return {
            "log_found": self.log_found,
            "plugin_loaded_observed": self.plugin_loaded_observed,
            "metadata_snapshot_observed": self.metadata_snapshot_observed,
            "metadata_snapshot_created_count_observed": (
                self.metadata_snapshot_created_count_observed
            ),
            "health_check_observed_count_observed": self.health_check_observed_count_observed,
            "synthetic_send_configured_count_observed": (
                self.synthetic_send_configured_count_observed
            ),
            "real_text_captured_false_observed": self.real_text_captured_false_observed,
            "current_line_capture_enabled_false_observed": (
                self.current_line_capture_enabled_false_observed
            ),
            "ui_probe_attempted_false_observed": self.ui_probe_attempted_false_observed,
            "scene_probe_attempted_false_observed": self.scene_probe_attempted_false_observed,
            "forbidden_marker_detected": self.forbidden_marker_detected,
            "forbidden_marker_categories": list(self.forbidden_marker_categories),
            "raw_log_included": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        discovery = discover_local_smoke_paths(
            game_dir=args.game_dir,
            core_dll=args.core_dll,
            il2cpp_dll=args.il2cpp_dll,
            configuration=args.configuration,
        )
        result: dict[str, object] = {
            "schema_version": "bepinex-metadata-probe-local-smoke.v1",
            "discovery": discovery_summary(discovery, verbose=args.verbose),
            "actions": {},
            "no_game_launch_performed": True,
            "raw_log_included": False,
        }

        no_action = not any(
            (
                args.enable_probe,
                args.disable_probe,
                args.check_log,
                args.write_report,
                args.print_discovery,
            )
        )

        if args.print_discovery or no_action:
            return _finish(result, quiet=args.quiet)

        if args.enable_probe:
            result["actions"] = _merge_action(
                result["actions"],
                enable_probe_flow(
                    discovery,
                    configuration=args.configuration,
                    skip_build=args.skip_build,
                    skip_install=args.skip_install,
                ),
            )

        if args.disable_probe:
            result["actions"] = _merge_action(
                result["actions"], set_probe_config_action(discovery, enabled=False)
            )

        log_check: LogCheck | None = None
        if args.check_log or args.write_report:
            log_check = check_metadata_probe_log_action(discovery)
            result["log_check"] = log_check.redacted_summary()
            if log_check.forbidden_marker_detected:
                if args.write_report:
                    result["report"] = {"written": False, "blocked_reason": "forbidden_marker"}
                return _finish(result, quiet=args.quiet, exit_code=1)

        if args.write_report:
            if log_check is None:
                log_check = check_metadata_probe_log_action(discovery)
            result["report"] = write_metadata_probe_report(log_check)

        return _finish(result, quiet=args.quiet)
    except LocalSmokeError as exc:
        if args.quiet:
            print(f"BepInEx metadata probe local smoke failed: {exc}")
        else:
            print(
                canonical_json(
                    {
                        "schema_version": "bepinex-metadata-probe-local-smoke.v1",
                        "ok": False,
                        "error": str(exc),
                        "no_game_launch_performed": True,
                        "raw_log_included": False,
                    }
                ),
                end="",
            )
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and review a local metadata-probe BepInEx smoke run without launching "
            "the game or printing raw logs."
        )
    )
    parser.add_argument("--auto-discover", action="store_true", help="Use bounded Steam discovery.")
    parser.add_argument("--game-dir", help="Explicit local game directory override.")
    parser.add_argument("--core-dll", help="Explicit BepInEx.Core.dll override.")
    parser.add_argument("--il2cpp-dll", help="Explicit BepInEx IL2CPP DLL override.")
    parser.add_argument(
        "--configuration",
        choices=("Debug", "Release"),
        default="Debug",
        help="Bridge build configuration.",
    )
    parser.add_argument("--skip-build", action="store_true", help="Do not run the build helper.")
    parser.add_argument("--skip-install", action="store_true", help="Do not copy the bridge DLL.")
    parser.add_argument("--enable-probe", action="store_true", help="Enable metadata probe config.")
    parser.add_argument(
        "--disable-probe", action="store_true", help="Disable metadata probe config."
    )
    parser.add_argument("--check-log", action="store_true", help="Read only BepInEx/LogOutput.log.")
    parser.add_argument("--write-report", action="store_true", help="Write redacted report.json.")
    parser.add_argument("--print-discovery", action="store_true", help="Print safe discovery JSON.")
    parser.add_argument("--quiet", action="store_true", help="Print one short safe status line.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include discovered local paths. Still never prints raw log lines.",
    )
    return parser


def discover_local_smoke_paths(
    *,
    game_dir: str | None,
    core_dll: str | None,
    il2cpp_dll: str | None,
    configuration: str,
    env: Mapping[str, str] | None = None,
    steam_roots: Sequence[Path] | None = None,
    common_roots: Sequence[Path] | None = None,
    toolchain_roots: Sequence[Path] | None = None,
) -> LocalDiscovery:
    env = os.environ if env is None else env
    game = discover_game_dir(
        explicit_game_dir=Path(game_dir) if game_dir else None,
        steam_roots=steam_roots,
        common_roots=common_roots,
    )
    bepinex = discover_bepinex_paths(game.game_dir)
    refs = discover_reference_dlls(
        explicit_core=Path(core_dll) if core_dll else None,
        explicit_il2cpp=Path(il2cpp_dll) if il2cpp_dll else None,
        env=env,
        game_dir=game.game_dir,
        toolchain_roots=toolchain_roots,
    )
    bridge_dll = discover_bridge_dll(configuration)
    return LocalDiscovery(game=game, bepinex=bepinex, refs=refs, bridge_dll=bridge_dll)


def discover_game_dir(
    *,
    explicit_game_dir: Path | None = None,
    steam_roots: Sequence[Path] | None = None,
    common_roots: Sequence[Path] | None = None,
) -> GameDiscovery:
    if explicit_game_dir:
        resolved = explicit_game_dir.expanduser().resolve()
        return GameDiscovery(
            resolved if resolved.exists() else None, "cli" if resolved.exists() else "not_found"
        )

    roots_with_sources: list[tuple[Path, str]] = []
    if steam_roots is None:
        roots_with_sources.extend((path, "steam_registry") for path in read_steam_registry_roots())
    else:
        roots_with_sources.extend((Path(path), "steam_registry") for path in steam_roots)

    seen_roots: set[Path] = set()
    for root, source in roots_with_sources:
        resolved = root.expanduser()
        if resolved in seen_roots:
            continue
        seen_roots.add(resolved)
        found = find_game_in_library_root(resolved)
        if found:
            return GameDiscovery(found.resolve(), source)
        found = find_game_from_libraryfolders(resolved)
        if found:
            return GameDiscovery(found.resolve(), "steam_library")
        found = find_game_from_appmanifests(resolved)
        if found:
            return GameDiscovery(found.resolve(), "steam_manifest")

    for root in common_roots or COMMON_STEAM_ROOTS:
        found = find_game_in_library_root(Path(root))
        if found:
            return GameDiscovery(found.resolve(), "common_path")
        found = find_game_from_libraryfolders(Path(root))
        if found:
            return GameDiscovery(found.resolve(), "steam_library")
        found = find_game_from_appmanifests(Path(root))
        if found:
            return GameDiscovery(found.resolve(), "steam_manifest")

    return GameDiscovery(None, "not_found")


def read_steam_registry_roots() -> list[Path]:
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:  # pragma: no cover - Windows-only stdlib module
        return []

    keys = (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Valve\Steam", "InstallPath"),
    )
    roots: list[Path] = []
    for hive, subkey, value_name in keys:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
        except OSError:
            continue
        if isinstance(value, str) and value.strip():
            roots.append(Path(value))
    return _dedupe_paths(roots)


def find_game_in_library_root(library_root: Path) -> Path | None:
    common = library_root / "steamapps" / "common"
    for name in GAME_DIR_NAMES:
        candidate = common / name
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def find_game_from_libraryfolders(steam_root: Path) -> Path | None:
    library_file = steam_root / "steamapps" / "libraryfolders.vdf"
    if not library_file.exists() or not library_file.is_file():
        return None
    try:
        paths = parse_steam_libraryfolders(
            library_file.read_text(encoding="utf-8", errors="replace")
        )
    except OSError:
        return None
    for path in paths:
        found = find_game_in_library_root(path)
        if found:
            return found
    return None


def parse_steam_libraryfolders(text: str) -> list[Path]:
    paths: list[Path] = []
    for match in re.finditer(r'"path"\s+"([^"]+)"', text):
        paths.append(Path(_unescape_vdf_path(match.group(1))))
    for match in re.finditer(r'"\d+"\s+"([^"]+)"', text):
        value = match.group(1)
        if "steamapps" not in value.lower():
            paths.append(Path(_unescape_vdf_path(value)))
    return _dedupe_paths(paths)


def find_game_from_appmanifests(steam_root: Path) -> Path | None:
    steamapps = steam_root / "steamapps"
    if not steamapps.exists() or not steamapps.is_dir():
        return None
    for manifest in steamapps.glob("appmanifest_*.acf"):
        try:
            text = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "disco elysium" not in text.lower():
            continue
        install_dir = _manifest_value(text, "installdir")
        if not install_dir:
            continue
        candidate = steamapps / "common" / install_dir
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _manifest_value(text: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s+"([^"]+)"', text, flags=re.IGNORECASE)
    return _unescape_vdf_path(match.group(1)) if match else None


def _unescape_vdf_path(value: str) -> str:
    return value.replace("\\\\", "\\")


def discover_bepinex_paths(game_dir: Path | None) -> BepInExPaths:
    if game_dir is None:
        return BepInExPaths(None, None, None)
    bepinex = game_dir / "BepInEx"
    plugins = bepinex / "plugins"
    config = bepinex / "config"
    log_file = bepinex / LOG_FILENAME
    return BepInExPaths(
        plugins if plugins.exists() and plugins.is_dir() else None,
        config if config.exists() and config.is_dir() else None,
        log_file if log_file.exists() and log_file.is_file() else None,
    )


def discover_reference_dlls(
    *,
    explicit_core: Path | None,
    explicit_il2cpp: Path | None,
    env: Mapping[str, str],
    game_dir: Path | None,
    toolchain_roots: Sequence[Path] | None = None,
) -> ReferenceDiscovery:
    core = resolve_existing_file(explicit_core)
    il2cpp = resolve_existing_file(explicit_il2cpp)
    if core and il2cpp:
        return ReferenceDiscovery(core, il2cpp)

    if core is None:
        core = resolve_env_file(env, ENV_CORE_KEYS)
    if il2cpp is None:
        il2cpp = resolve_env_file(env, ENV_IL2CPP_KEYS)
    if core and il2cpp:
        return ReferenceDiscovery(core, il2cpp)

    roots = list(toolchain_roots or default_toolchain_roots())
    if game_dir is not None:
        roots.append(game_dir / "BepInEx" / "core")

    if core is None:
        core = find_named_dll(CORE_DLL_NAMES, roots)
    if il2cpp is None:
        il2cpp = find_named_dll(IL2CPP_DLL_NAMES, roots)
    return ReferenceDiscovery(core, il2cpp)


def default_toolchain_roots() -> list[Path]:
    base = ROOT / "workspace" / "toolchains"
    return [
        base,
        base / "bepinex-il2cpp-win-x64",
        base / "bepinex-il2cpp-win-x64" / "BepInEx" / "core",
        base / "bepinex-il2cpp-win-x64" / "core",
    ]


def resolve_existing_file(path: Path | None) -> Path | None:
    if path is None:
        return None
    resolved = path.expanduser().resolve()
    if resolved.exists() and resolved.is_file():
        return resolved
    return None


def resolve_env_file(env: Mapping[str, str], keys: Sequence[str]) -> Path | None:
    for key in keys:
        value = env.get(key)
        if not value:
            continue
        resolved = resolve_existing_file(Path(value))
        if resolved:
            return resolved
    return None


def find_named_dll(names: Sequence[str], roots: Iterable[Path]) -> Path | None:
    candidates: list[Path] = []
    suffixes = (
        Path(),
        Path("BepInEx") / "core",
        Path("core"),
        Path("bepinex-il2cpp-win-x64") / "BepInEx" / "core",
        Path("bepinex-il2cpp-win-x64") / "core",
    )
    for root in roots:
        for suffix in suffixes:
            base = root / suffix
            for name in names:
                candidate = base / name
                if candidate.exists() and candidate.is_file():
                    candidates.append(candidate.resolve())
    return (
        sorted(_dedupe_paths(candidates), key=lambda item: str(item).lower())[0]
        if candidates
        else None
    )


def discover_bridge_dll(configuration: str) -> Path | None:
    roots = [
        ROOT / "packages" / "bepinex-plugin" / "bin" / configuration,
        ROOT / "packages" / "bepinex-plugin" / "bin" / "Debug",
        ROOT / "packages" / "bepinex-plugin" / "bin" / "Release",
    ]
    candidates: list[Path] = []
    for root in _dedupe_paths(roots):
        if root.exists() and root.is_dir():
            candidates.extend(root.glob(f"**/{BRIDGE_ASSEMBLY_NAME}.dll"))
    if not candidates:
        return None
    return max((path.resolve() for path in candidates), key=lambda path: path.stat().st_mtime)


def discovery_summary(discovery: LocalDiscovery, *, verbose: bool = False) -> dict[str, object]:
    summary: dict[str, object] = {
        "game_dir_found": discovery.game.game_dir is not None,
        "game_dir_source": discovery.game.source,
        "plugins_dir_found": discovery.bepinex.plugins_dir is not None,
        "config_dir_found": discovery.bepinex.config_dir is not None,
        "log_file_found": discovery.bepinex.log_file is not None,
        "core_dll_found": discovery.refs.core_dll is not None,
        "il2cpp_dll_found": discovery.refs.il2cpp_dll is not None,
        "bridge_dll_found": discovery.bridge_dll is not None,
        "build_refs_ready": discovery.build_refs_ready,
        "private_paths_redacted": not verbose,
    }
    if verbose:
        summary["paths"] = {
            "game_dir": _path_or_none(discovery.game.game_dir),
            "plugins_dir": _path_or_none(discovery.bepinex.plugins_dir),
            "config_dir": _path_or_none(discovery.bepinex.config_dir),
            "log_file": _path_or_none(discovery.bepinex.log_file),
            "core_dll": _path_or_none(discovery.refs.core_dll),
            "il2cpp_dll": _path_or_none(discovery.refs.il2cpp_dll),
            "bridge_dll": _path_or_none(discovery.bridge_dll),
        }
    return summary


def enable_probe_flow(
    discovery: LocalDiscovery,
    *,
    configuration: str,
    skip_build: bool,
    skip_install: bool,
) -> dict[str, object]:
    actions: dict[str, object] = {}
    build_report: dict[str, object] | None = None
    if not skip_build:
        build_report = build_bepinex_bridge_report(
            core_dll=str(discovery.refs.core_dll) if discovery.refs.core_dll else None,
            il2cpp_dll=str(discovery.refs.il2cpp_dll) if discovery.refs.il2cpp_dll else None,
            configuration=configuration,
        )
        actions["build"] = {
            "attempted": build_report["build_attempted"],
            "succeeded": build_report["build_succeeded"],
            "skipped_reason": build_report["skipped_reason"],
            "warning_count": build_report["warning_count"],
            "msb3277_warning_count": build_report["msb3277_warning_count"],
        }
        if build_report["build_attempted"] and not build_report["build_succeeded"]:
            raise LocalSmokeError("Bridge build failed; install/config was not changed.")

    bridge_dll = discover_bridge_dll(configuration)
    if not skip_install:
        actions["install"] = install_bridge_dll(
            discovery.game.game_dir, bridge_dll, discovery.bepinex.plugins_dir
        )

    actions["config"] = set_probe_config_action(discovery, enabled=True)
    return actions


def install_bridge_dll(
    game_dir: Path | None, bridge_dll: Path | None, plugins_dir: Path | None
) -> dict[str, object]:
    if game_dir is None:
        raise LocalSmokeError("Game directory was not found. Pass --game-dir <path>.")
    if plugins_dir is None:
        raise LocalSmokeError("BepInEx/plugins was not found. Install BepInEx first.")
    if bridge_dll is None:
        raise LocalSmokeError("Built bridge DLL was not found under package bin outputs.")

    resolved_game = game_dir.resolve()
    expected_plugins = (resolved_game / "BepInEx" / "plugins").resolve()
    resolved_plugins = plugins_dir.resolve()
    if resolved_plugins != expected_plugins:
        raise LocalSmokeError("Install target must be exactly <game-dir>/BepInEx/plugins.")
    if not bridge_dll.resolve().is_relative_to(
        (ROOT / "packages" / "bepinex-plugin" / "bin").resolve()
    ):
        raise LocalSmokeError("Bridge DLL must come from the repository package bin output.")

    destination = resolved_plugins / bridge_dll.name
    shutil.copy2(bridge_dll, destination)
    return {"installed": True, "target": "BepInEx/plugins", "dll": bridge_dll.name}


def set_probe_config_action(discovery: LocalDiscovery, *, enabled: bool) -> dict[str, object]:
    if discovery.game.game_dir is None:
        raise LocalSmokeError("Game directory was not found. Pass --game-dir <path>.")
    config_dir = discovery.bepinex.config_dir or (discovery.game.game_dir / "BepInEx" / "config")
    set_probe_config(config_dir, enabled=enabled)
    return {
        "probe_enabled": enabled,
        "metadata_probe_enabled": enabled,
        "metadata_probe_log_on_start": enabled,
        "config_file": PLUGIN_CONFIG_FILENAME,
    }


def set_probe_config(config_dir: Path, *, enabled: bool) -> Path:
    resolved_config_dir = config_dir.resolve()
    resolved_config_dir.mkdir(parents=True, exist_ok=True)
    config_path = find_bridge_config_file(resolved_config_dir)
    value = "true" if enabled else "false"
    if config_path.exists():
        lines = config_path.read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        lines = []

    lines, seen_enabled = _replace_or_track_config(lines, "MetadataProbeEnabled", value)
    lines, seen_log_on_start = _replace_or_track_config(lines, "MetadataProbeLogOnStart", value)
    if not seen_enabled or not seen_log_on_start:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append("[MetadataProbe]")
        if not seen_enabled:
            lines.append(f"MetadataProbeEnabled = {value}")
        if not seen_log_on_start:
            lines.append(f"MetadataProbeLogOnStart = {value}")
    config_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return config_path


def find_bridge_config_file(config_dir: Path) -> Path:
    exact = config_dir / PLUGIN_CONFIG_FILENAME
    if exact.exists():
        return exact
    matches = sorted(config_dir.glob("*revachol*bridge*.cfg"))
    return matches[0] if matches else exact


def _replace_or_track_config(lines: list[str], key: str, value: str) -> tuple[list[str], bool]:
    pattern = re.compile(rf"^(\s*{re.escape(key)}\s*=\s*).*$")
    replaced = False
    updated: list[str] = []
    for line in lines:
        if pattern.match(line):
            updated.append(pattern.sub(rf"\g<1>{value}", line))
            replaced = True
        else:
            updated.append(line)
    return updated, replaced


def check_metadata_probe_log_action(discovery: LocalDiscovery) -> LogCheck:
    if discovery.game.game_dir is None:
        raise LocalSmokeError("Game directory was not found. Pass --game-dir <path>.")
    log_file = discovery.bepinex.log_file or (discovery.game.game_dir / "BepInEx" / LOG_FILENAME)
    return check_metadata_probe_log(log_file)


def check_metadata_probe_log(log_file: Path) -> LogCheck:
    if not log_file.exists() or not log_file.is_file():
        return LogCheck(
            log_found=False,
            plugin_loaded_observed=False,
            metadata_snapshot_observed=False,
            metadata_snapshot_created_count_observed=False,
            health_check_observed_count_observed=False,
            synthetic_send_configured_count_observed=False,
            real_text_captured_false_observed=False,
            current_line_capture_enabled_false_observed=False,
            ui_probe_attempted_false_observed=False,
            scene_probe_attempted_false_observed=False,
            forbidden_marker_detected=False,
            raw_log_included=False,
            counter_values={},
            companion_health_checked=False,
            companion_available=False,
            synthetic_event_send_configured=False,
            forbidden_marker_categories=(),
        )

    text = log_file.read_text(encoding="utf-8", errors="replace")
    forbidden_categories = tuple(
        name for name, pattern in FORBIDDEN_LOG_PATTERNS.items() if pattern.search(text)
    )
    counters = {
        name: int(match.group(1))
        for name, pattern in COUNTER_PATTERNS.items()
        if (match := pattern.search(text)) is not None
    }
    snapshot_bools = {
        name: match.group(1).lower() == "true"
        for name, pattern in SNAPSHOT_BOOL_PATTERNS.items()
        if (match := pattern.search(text)) is not None
    }
    return LogCheck(
        log_found=True,
        plugin_loaded_observed=all(marker in text for marker in PLUGIN_LOADED_MARKERS),
        metadata_snapshot_observed=METADATA_SNAPSHOT_MARKER in text,
        metadata_snapshot_created_count_observed="metadata_snapshot_created_count" in counters,
        health_check_observed_count_observed="health_check_observed_count" in counters,
        synthetic_send_configured_count_observed="synthetic_send_configured_count" in counters,
        real_text_captured_false_observed="real_text_captured=false" in text,
        current_line_capture_enabled_false_observed="current_line_capture_enabled=false" in text,
        ui_probe_attempted_false_observed="ui_probe_attempted=false" in text,
        scene_probe_attempted_false_observed="scene_probe_attempted=false" in text,
        forbidden_marker_detected=bool(forbidden_categories),
        raw_log_included=False,
        counter_values=counters,
        companion_health_checked=snapshot_bools.get(
            "companion_health_checked",
            "Companion health check passed" in text or "Companion health check failed" in text,
        ),
        companion_available=snapshot_bools.get(
            "companion_available", "Companion health check passed" in text
        ),
        synthetic_event_send_configured=snapshot_bools.get(
            "synthetic_event_send_configured",
            counters.get("synthetic_send_configured_count", 0) > 0,
        ),
        forbidden_marker_categories=forbidden_categories,
    )


def write_metadata_probe_report(
    log_check: LogCheck, output_path: Path = REPORT_OUTPUT
) -> dict[str, object]:
    if log_check.forbidden_marker_detected:
        raise LocalSmokeError("Forbidden log marker detected; report was not written.")

    report = build_report_from_log_check(log_check)
    safe_output = ensure_safe_metadata_probe_report_path(output_path)
    safe_output.parent.mkdir(parents=True, exist_ok=True)
    safe_output.write_text(canonical_json(report), encoding="utf-8")
    errors = collect_metadata_probe_report_errors(safe_output)
    if errors:
        safe_output.unlink(missing_ok=True)
        raise LocalSmokeError("Generated metadata probe report did not validate.")
    return {
        "written": True,
        "path": str(safe_output.relative_to(ROOT)).replace("\\", "/"),
        "probe_status": report["probe_status"],
    }


def build_report_from_log_check(log_check: LogCheck) -> dict[str, object]:
    report = default_metadata_probe_report_template()
    complete = (
        log_check.log_found
        and log_check.plugin_loaded_observed
        and log_check.metadata_snapshot_observed
        and log_check.metadata_snapshot_created_count_observed
        and log_check.health_check_observed_count_observed
        and log_check.synthetic_send_configured_count_observed
        and log_check.real_text_captured_false_observed
        and log_check.current_line_capture_enabled_false_observed
        and log_check.ui_probe_attempted_false_observed
        and log_check.scene_probe_attempted_false_observed
        and not log_check.forbidden_marker_detected
    )
    status = "pass" if complete else "partial" if log_check.log_found else "not_run"
    metadata_snapshot_count = log_check.counter_values.get("metadata_snapshot_created_count", 0)
    health_count = log_check.counter_values.get("health_check_observed_count", 0)
    synthetic_configured_count = log_check.counter_values.get("synthetic_send_configured_count", 0)
    report.update(
        {
            "probe_status": status,
            "metadata_only": True,
            "probe_enabled": log_check.metadata_snapshot_observed,
            "probe_attempted": log_check.metadata_snapshot_observed,
            "probe_completed": complete,
            "plugin_loaded": log_check.plugin_loaded_observed,
            "companion_health_checked": log_check.companion_health_checked,
            "companion_available": log_check.companion_available,
            "synthetic_event_send_configured": log_check.synthetic_event_send_configured,
            "synthetic_event_sent": False,
            "scene_probe_attempted": False,
            "ui_probe_attempted": False,
            "current_line_capture_enabled": False,
            "real_text_captured": False,
            "counters": {
                "safe_status_events": 1 if log_check.plugin_loaded_observed else 0,
                "synthetic_events": 0,
                "metadata_snapshot_created_count": metadata_snapshot_count,
                "health_check_observed_count": health_count,
                "synthetic_send_configured_count": synthetic_configured_count,
            },
            "blockers": [] if complete else ["metadata_probe_log_incomplete_or_not_run"],
            "next_step_notes": "Review redacted metadata observations only.",
            "not_run_reason": "" if log_check.log_found else "BepInEx log was not found.",
            "evidence_summary_redacted": True,
            "redacted_notes": (
                "Generated from allowlisted metadata probe log markers only. Raw logs were not "
                "included."
            ),
            "created_by_user_manually": True,
        }
    )
    return report


def _merge_action(existing: object, update: dict[str, object]) -> dict[str, object]:
    merged = dict(existing) if isinstance(existing, dict) else {}
    merged.update(update)
    return merged


def _finish(result: dict[str, object], *, quiet: bool, exit_code: int = 0) -> int:
    if quiet:
        status = "failed" if exit_code else "ok"
        details: list[str] = []
        discovery = result.get("discovery")
        if isinstance(discovery, dict):
            details.append(f"game_dir_found={str(discovery.get('game_dir_found')).lower()}")
            details.append(f"bridge_dll_found={str(discovery.get('bridge_dll_found')).lower()}")
        log_check = result.get("log_check")
        if isinstance(log_check, dict):
            details.append(
                "forbidden_marker_detected="
                + str(log_check.get("forbidden_marker_detected")).lower()
            )
        print("BepInEx metadata probe local smoke " + status + " (" + ", ".join(details) + ").")
    else:
        print(canonical_json(result), end="")
    return exit_code


def _path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    deduped: list[Path] = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    return deduped


if __name__ == "__main__":
    sys.exit(main())
