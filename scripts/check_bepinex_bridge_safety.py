from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

try:
    from scripts.schema_validator import collect_errors, load_json
    from scripts.check_bepinex_runtime_smoke_report import (
        FIXTURE_PATH as RUNTIME_REPORT_FIXTURE_PATH,
        REPORT_ROOT as RUNTIME_REPORT_ROOT,
        collect_runtime_smoke_report_errors,
    )
    from scripts.check_bepinex_metadata_probe_report import (
        FIXTURE_PATH as METADATA_PROBE_FIXTURE_PATH,
        REPORT_ROOT as METADATA_PROBE_REPORT_ROOT,
        collect_metadata_probe_report_errors,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import collect_errors, load_json
    from check_bepinex_runtime_smoke_report import (
        FIXTURE_PATH as RUNTIME_REPORT_FIXTURE_PATH,
        REPORT_ROOT as RUNTIME_REPORT_ROOT,
        collect_runtime_smoke_report_errors,
    )
    from check_bepinex_metadata_probe_report import (
        FIXTURE_PATH as METADATA_PROBE_FIXTURE_PATH,
        REPORT_ROOT as METADATA_PROBE_REPORT_ROOT,
        collect_metadata_probe_report_errors,
    )


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "packages/bepinex-plugin"
SOURCE_DIR = PACKAGE_DIR / "src"
METADATA_PROBE_SOURCE = SOURCE_DIR / "MetadataProbe.cs"
PROJECT_FILE = PACKAGE_DIR / "Revachol.UkrainianCompanion.BepInExBridge.csproj"
FIXTURE_PATH = ROOT / "tests/fixtures/bepinex_bridge.provider_annotate_request.synthetic.json"
LOG_CONTRACT_PATH = ROOT / "tests/fixtures/bepinex_bridge.log_contract.synthetic.json"
FAKE_EVENT_SCHEMA = ROOT / "specs/fake-game-event.schema.json"
CHECK_ALL = ROOT / "scripts/check_all.py"
BUILD_HELPER = ROOT / "scripts/build_bepinex_bridge.py"
GITIGNORE = ROOT / ".gitignore"
CURRENT_LINE_CAPTURE_ADR = ROOT / "docs/adr/0008-current-line-capture-research.md"
METADATA_EXTENSION_GATE_ADR = ROOT / "docs/adr/0009-metadata-only-extension-gate.md"
POST_BRIDGE_TO_OVERLAY_NEXT_STEP_ADR = ROOT / "docs/adr/0010-post-bridge-to-overlay-next-step.md"
METADATA_PROBE_GATE_DOC = ROOT / "docs/bepinex-metadata-probe-gate.md"
METADATA_ONLY_EXTENSION_SCOPE_DOC = ROOT / "docs/bepinex-metadata-only-extension-scope.md"
MANUAL_SMOKE_DIR = ROOT / "docs/manual-smoke"
RUNTIME_SMOKE_DOC = MANUAL_SMOKE_DIR / "bepinex-bridge-runtime-smoke.md"
LOG_CONTRACT_DOC = MANUAL_SMOKE_DIR / "bepinex-bridge-log-contract.md"
RUNTIME_REPORT_DOC = MANUAL_SMOKE_DIR / "bepinex-bridge-runtime-smoke-report.md"
METADATA_PROBE_SMOKE_DOC = MANUAL_SMOKE_DIR / "bepinex-metadata-probe-smoke.md"
LOCAL_WORKFLOW_DOC = ROOT / "docs/local-workflow.md"
RUNTIME_REPORT_CHECKER = ROOT / "scripts/check_bepinex_runtime_smoke_report.py"
RUNTIME_REPORT_WRITER = ROOT / "scripts/write_bepinex_runtime_smoke_report.py"
RUNTIME_REPORT_REVIEWER = ROOT / "scripts/review_bepinex_runtime_smoke_report.py"
METADATA_PROBE_CHECKER = ROOT / "scripts/check_bepinex_metadata_probe_report.py"
METADATA_PROBE_WRITER = ROOT / "scripts/write_bepinex_metadata_probe_report.py"
METADATA_PROBE_REVIEWER = ROOT / "scripts/review_bepinex_metadata_probe_report.py"
METADATA_PROBE_LOCAL_SMOKE_HELPER = ROOT / "scripts/run_bepinex_metadata_probe_local_smoke.py"
BRIDGE_TO_OVERLAY_SMOKE_HELPER = ROOT / "scripts/run_bridge_to_overlay_synthetic_smoke.py"
LOCAL_BRIDGE_WORKFLOW_HELPER = ROOT / "scripts/run_local_bridge_workflow.py"
METADATA_EXTENSION_GATE_FIXTURE = (
    ROOT / "tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json"
)
METADATA_ONLY_EXTENSION_SCOPE_FIXTURE = (
    ROOT / "tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json"
)
POST_BRIDGE_TO_OVERLAY_NEXT_STEP_FIXTURE = (
    ROOT / "tests/fixtures/post_bridge_to_overlay_next_step.synthetic.json"
)

DEFAULT_URL = "http://127.0.0.1:8765"
SYNTHETIC_EVENT_ID = "synthetic.event.bepinex.4a.001"
SYNTHETIC_LINE_ID = "synthetic.bepinex.4a.001"

ALLOWED_URLS = (DEFAULT_URL,)
FORBIDDEN_URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)

FORBIDDEN_EXTERNAL_MARKERS = (
    "api.openai",
    "openai_compatible",
    "deepl",
    "anthropic",
    "local_model",
    "ensemble_reviewer",
    "provider_cache",
)

FORBIDDEN_GAME_CONTENT_MARKERS = (
    "steamapps",
    "gamedata",
    "game-data",
    "database.json",
    ".transl",
    ".assets",
    ".bundle",
    ".wav",
    ".ogg",
    ".mp3",
    ".png",
    ".jpg",
)

FORBIDDEN_HOOK_OR_EXTRACTION_MARKERS = (
    "HarmonyPatch",
    "Input.GetKey",
    "Keyboard.current",
    "Clipboard",
    "GUIUtility.systemCopyBuffer",
    "OnGUI(",
    "Update(",
    "LateUpdate(",
    "FixedUpdate(",
    "FindObjectOfType",
    "FindObjectsOfType",
    "GameObject.Find",
    "Resources.FindObjectsOfTypeAll",
    "SceneManager",
    "OCR",
    "Tesseract",
    "Il2CppDumper",
    "dnSpy",
    "Assembly-CSharp",
)

RAW_PAYLOAD_LOG_PATTERNS = (
    r"Log(?:Info|Warning|Error|Debug)\s*\(\s*payload",
    r"Log(?:Info|Warning|Error|Debug)\s*\(\s*jsonPayload",
    r"Log(?:Info|Warning|Error|Debug)\s*\(\s*request",
    r"Log(?:Info|Warning|Error|Debug)\s*\(\s*RawEnglishText",
    r"Log(?:Info|Warning|Error|Debug).*ReadAsStringAsync",
    r"Log(?:Info|Warning|Error|Debug).*response\.Content",
    r"Log(?:Info|Warning|Error|Debug).*StackTrace",
)

FORBIDDEN_DOWNLOAD_OR_INSTALL_MARKERS = (
    "Invoke-WebRequest",
    "Start-BitsTransfer",
    "WebClient",
    "urllib.request",
    "requests.",
    "curl ",
    "wget ",
    "winget ",
    "choco ",
    "scoop ",
    "dotnet add package",
    "dotnet restore",
)


class BepInExBridgeSafetyError(RuntimeError):
    """Raised when the BepInEx bridge skeleton violates the 4A safety boundary."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the synthetic/manual BepInEx bridge skeleton safety contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_bepinex_bridge_safety_errors()
    if errors:
        if args.quiet:
            print("BepInEx bridge safety check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("BepInEx bridge safety check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "bepinex-bridge-safety.v1",
                    "package": str(PACKAGE_DIR.relative_to(ROOT)),
                    "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
                    "dotnet_build_required": False,
                    "bepinex_binaries_required": False,
                    "synthetic_only": True,
                    "localhost_only_by_default": True,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


def assert_bepinex_bridge_safe() -> None:
    errors = collect_bepinex_bridge_safety_errors()
    if errors:
        raise BepInExBridgeSafetyError("; ".join(errors))


def collect_bepinex_bridge_safety_errors() -> list[str]:
    errors: list[str] = []
    errors.extend(_check_required_files())
    errors.extend(_check_fixture())
    errors.extend(_check_log_contract())
    errors.extend(_check_runtime_report_contract())
    errors.extend(_check_metadata_probe_contract())
    errors.extend(_check_metadata_extension_gate_contract())
    errors.extend(_check_metadata_only_extension_scope_contract())
    errors.extend(_check_post_bridge_to_overlay_next_step_contract())
    errors.extend(_check_local_metadata_probe_smoke_helper())
    errors.extend(_check_bridge_to_overlay_smoke_helper())
    errors.extend(_check_local_bridge_workflow_helper())
    errors.extend(_check_source_contract())
    errors.extend(_check_text_safety())
    errors.extend(_check_ignored_output_roots())
    errors.extend(_check_check_all_smoke())
    return errors


def _check_required_files() -> list[str]:
    required = [
        PACKAGE_DIR / "README.md",
        PACKAGE_DIR / "DESIGN.md",
        PROJECT_FILE,
        SOURCE_DIR / "RevacholCompanionBridgePlugin.cs",
        SOURCE_DIR / "CompanionHttpClient.cs",
        SOURCE_DIR / "SyntheticEventFactory.cs",
        METADATA_PROBE_SOURCE,
        FIXTURE_PATH,
        LOG_CONTRACT_PATH,
        BUILD_HELPER,
        CURRENT_LINE_CAPTURE_ADR,
        METADATA_EXTENSION_GATE_ADR,
        POST_BRIDGE_TO_OVERLAY_NEXT_STEP_ADR,
        METADATA_PROBE_GATE_DOC,
        METADATA_ONLY_EXTENSION_SCOPE_DOC,
        RUNTIME_SMOKE_DOC,
        LOG_CONTRACT_DOC,
        RUNTIME_REPORT_DOC,
        METADATA_PROBE_SMOKE_DOC,
        LOCAL_WORKFLOW_DOC,
        RUNTIME_REPORT_FIXTURE_PATH,
        RUNTIME_REPORT_CHECKER,
        RUNTIME_REPORT_WRITER,
        RUNTIME_REPORT_REVIEWER,
        METADATA_PROBE_FIXTURE_PATH,
        METADATA_PROBE_CHECKER,
        METADATA_PROBE_WRITER,
        METADATA_PROBE_REVIEWER,
        METADATA_PROBE_LOCAL_SMOKE_HELPER,
        BRIDGE_TO_OVERLAY_SMOKE_HELPER,
        LOCAL_BRIDGE_WORKFLOW_HELPER,
        METADATA_EXTENSION_GATE_FIXTURE,
        METADATA_ONLY_EXTENSION_SCOPE_FIXTURE,
        POST_BRIDGE_TO_OVERLAY_NEXT_STEP_FIXTURE,
    ]
    return [
        f"Missing required bridge file: {path.relative_to(ROOT)}"
        for path in required
        if not path.exists()
    ]


def _check_fixture() -> list[str]:
    errors: list[str] = []
    try:
        fixture = load_json(FIXTURE_PATH)
        fake_event_schema = load_json(FAKE_EVENT_SCHEMA)
    except Exception as exc:
        return [f"Could not load bridge fixture/schema: {exc}"]

    if not isinstance(fixture, dict):
        return ["Bridge provider request fixture must be a JSON object."]
    if fixture.get("input_type") != "fake_event":
        errors.append("Bridge provider request fixture must use input_type='fake_event'.")

    event = fixture.get("event")
    if not isinstance(event, dict):
        errors.append("Bridge provider request fixture must include an event object.")
        event = {}

    schema_errors = collect_errors(event, fake_event_schema)
    if schema_errors:
        errors.append(
            f"Bridge synthetic event does not match fake-game-event schema: {schema_errors}"
        )

    if event.get("event_id") != SYNTHETIC_EVENT_ID:
        errors.append("Bridge fixture event_id does not match the C# synthetic event id.")
    if event.get("synthetic_line_id") != SYNTHETIC_LINE_ID:
        errors.append("Bridge fixture synthetic_line_id does not match the C# synthetic line id.")
    if "synthetic" not in json.dumps(fixture, ensure_ascii=False).lower():
        errors.append("Bridge provider request fixture must be clearly synthetic.")
    return errors


def _check_runtime_report_contract() -> list[str]:
    errors = collect_runtime_smoke_report_errors(RUNTIME_REPORT_FIXTURE_PATH)
    for doc_path in (RUNTIME_SMOKE_DOC, RUNTIME_REPORT_DOC):
        if not doc_path.exists():
            continue
        text = _read_text(doc_path).replace("\\", "/")
        fixture_ref = str(RUNTIME_REPORT_FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/")
        checker_ref = str(RUNTIME_REPORT_CHECKER.relative_to(ROOT)).replace("\\", "/")
        reviewer_ref = str(RUNTIME_REPORT_REVIEWER.relative_to(ROOT)).replace("\\", "/")
        if fixture_ref not in text:
            errors.append(f"{doc_path.relative_to(ROOT)} must point to the runtime report fixture.")
        if checker_ref not in text:
            errors.append(f"{doc_path.relative_to(ROOT)} must point to the runtime report checker.")
        if reviewer_ref not in text:
            errors.append(
                f"{doc_path.relative_to(ROOT)} must point to the runtime report reviewer."
            )

    gitignore_text = _read_text(GITIGNORE) if GITIGNORE.exists() else ""
    report_root = str(RUNTIME_REPORT_ROOT.relative_to(ROOT)).replace("\\", "/")
    if "workspace/" not in gitignore_text:
        errors.append(f"Runtime report root {report_root} must stay under ignored workspace/.")
    return errors


def _check_metadata_probe_contract() -> list[str]:
    errors = collect_metadata_probe_report_errors(METADATA_PROBE_FIXTURE_PATH)
    if not METADATA_PROBE_GATE_DOC.exists():
        return errors

    text = _read_text(METADATA_PROBE_GATE_DOC).replace("\\", "/")
    fixture_ref = str(METADATA_PROBE_FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/")
    checker_ref = str(METADATA_PROBE_CHECKER.relative_to(ROOT)).replace("\\", "/")
    writer_ref = str(METADATA_PROBE_WRITER.relative_to(ROOT)).replace("\\", "/")
    reviewer_ref = str(METADATA_PROBE_REVIEWER.relative_to(ROOT)).replace("\\", "/")
    smoke_ref = str(METADATA_PROBE_SMOKE_DOC.relative_to(ROOT)).replace("\\", "/")
    report_root = str(METADATA_PROBE_REPORT_ROOT.relative_to(ROOT)).replace("\\", "/")
    for ref in (fixture_ref, checker_ref, writer_ref, reviewer_ref, smoke_ref, report_root):
        if ref not in text:
            errors.append(f"{METADATA_PROBE_GATE_DOC.relative_to(ROOT)} must point to {ref}.")

    if METADATA_PROBE_SMOKE_DOC.exists():
        smoke_text = _read_text(METADATA_PROBE_SMOKE_DOC).replace("\\", "/")
        for marker in (
            "MetadataProbeEnabled = true",
            "MetadataProbeLogOnStart = true",
            "MetadataProbeEnabled = false",
            "MetadataProbeLogOnStart = false",
            "Metadata probe snapshot: synthetic_manual=true",
            "real_text_captured=false",
            "current_line_capture_enabled=false",
            "ui_probe_attempted=false",
            "scene_probe_attempted=false",
            "counters.metadata_snapshot_created_count=1",
            "counters.health_check_observed_count=0|1",
            "counters.synthetic_send_configured_count=0|1",
            writer_ref,
            checker_ref,
            reviewer_ref,
            report_root,
        ):
            if marker not in smoke_text:
                errors.append(
                    f"{METADATA_PROBE_SMOKE_DOC.relative_to(ROOT)} must document {marker}."
                )

    bridge_doc = ROOT / "docs/bepinex-bridge.md"
    if bridge_doc.exists():
        bridge_text = _read_text(bridge_doc).replace("\\", "/")
        if "docs/bepinex-metadata-probe-gate.md" not in bridge_text:
            errors.append("docs/bepinex-bridge.md must point to the metadata probe gate.")
        if smoke_ref not in bridge_text:
            errors.append("docs/bepinex-bridge.md must point to the metadata probe smoke doc.")
        if reviewer_ref not in bridge_text:
            errors.append("docs/bepinex-bridge.md must point to the metadata probe reviewer.")

    gitignore_text = _read_text(GITIGNORE) if GITIGNORE.exists() else ""
    if "workspace/" not in gitignore_text:
        errors.append(
            f"Metadata probe report root {report_root} must stay under ignored workspace/."
        )
    return errors


def _check_local_metadata_probe_smoke_helper() -> list[str]:
    errors: list[str] = []
    if not METADATA_PROBE_LOCAL_SMOKE_HELPER.exists():
        return [
            f"Missing required local smoke helper: "
            f"{METADATA_PROBE_LOCAL_SMOKE_HELPER.relative_to(ROOT)}"
        ]

    text = _read_text(METADATA_PROBE_LOCAL_SMOKE_HELPER)
    relative = METADATA_PROBE_LOCAL_SMOKE_HELPER.relative_to(ROOT)
    required_markers = (
        "--auto-discover",
        "--enable-probe",
        "--disable-probe",
        "--enable-synthetic-send",
        "--disable-synthetic-send",
        "--check-log",
        "--write-report",
        "libraryfolders.vdf",
        "appmanifest_*.acf",
        "COMMON_STEAM_ROOTS",
        "BepInEx",
        "plugins",
        "config",
        "LogOutput.log",
        "MetadataProbeEnabled",
        "MetadataProbeLogOnStart",
        "SendSyntheticEventOnStart",
        "Companion health check passed",
        "Synthetic provider event sent:",
        "Synthetic provider event was not accepted:",
        "synthetic_provider_event_sent_observed",
        "build_bepinex_bridge_report",
        "default_metadata_probe_report_template",
        "collect_metadata_probe_report_errors",
        "no_game_launch_performed",
        "raw_log_included",
        "private_paths_redacted",
        "forbidden_marker_detected",
    )
    for marker in required_markers:
        if marker not in text:
            errors.append(f"{relative}: local smoke helper missing marker {marker!r}.")

    forbidden_runtime_markers = (
        "subprocess.Popen",
        "os.system",
        "Start-Process",
        "ShellExecute",
        "CreateProcess",
        "steam://",
        "rungameid",
        "os.walk",
        "shutil.rmtree",
        "webbrowser",
        "requests.",
        "urllib.request",
    )
    for marker in forbidden_runtime_markers:
        if marker in text:
            errors.append(f"{relative}: local smoke helper contains forbidden marker {marker!r}.")

    helper_ref = str(METADATA_PROBE_LOCAL_SMOKE_HELPER.relative_to(ROOT)).replace("\\", "/")
    docs_to_link = (
        METADATA_PROBE_SMOKE_DOC,
        ROOT / "docs/bepinex-bridge.md",
        METADATA_ONLY_EXTENSION_SCOPE_DOC,
        PACKAGE_DIR / "README.md",
        PACKAGE_DIR / "DESIGN.md",
    )
    for doc_path in docs_to_link:
        if not doc_path.exists():
            continue
        doc_text = _read_text(doc_path).replace("\\", "/")
        if helper_ref not in doc_text:
            errors.append(f"{doc_path.relative_to(ROOT)} must point to {helper_ref}.")
        for marker in ("--enable-synthetic-send", "--disable-synthetic-send"):
            if marker not in doc_text:
                errors.append(
                    f"{doc_path.relative_to(ROOT)} must document local helper flag {marker}."
                )
    return errors


def _check_bridge_to_overlay_smoke_helper() -> list[str]:
    errors: list[str] = []
    if not BRIDGE_TO_OVERLAY_SMOKE_HELPER.exists():
        return [
            f"Missing required bridge-to-overlay smoke helper: "
            f"{BRIDGE_TO_OVERLAY_SMOKE_HELPER.relative_to(ROOT)}"
        ]

    text = _read_text(BRIDGE_TO_OVERLAY_SMOKE_HELPER)
    relative = BRIDGE_TO_OVERLAY_SMOKE_HELPER.relative_to(ROOT)
    required_markers = (
        "--phase",
        "prepare",
        "post",
        "cleanup",
        "CompanionClient",
        "latest_provider_context",
        "latest_provider_annotation",
        "build_overlay_state_source",
        "build_overlay_view_model",
        "render_overlay_html",
        "collect_overlay_review_accessibility_errors",
        "check_metadata_probe_log_action",
        "write_metadata_probe_report",
        "set_probe_config_action",
        "set_synthetic_send_config_action",
        "workspace/synthetic-slice/bepinex-bridge/bridge-to-overlay-smoke",
        "workspace/synthetic-slice/overlay-prototype/bridge-to-overlay-smoke",
        "no_game_launch_performed",
        "raw_log_included",
        "raw_provider_payload_included",
        "provider_called",
        "companion_contract_changed",
    )
    for marker in required_markers:
        if marker not in text:
            errors.append(f"{relative}: bridge-to-overlay helper missing marker {marker!r}.")

    forbidden_runtime_markers = (
        "subprocess.Popen",
        "subprocess.run",
        "os.system",
        "Start-Process",
        "ShellExecute",
        "CreateProcess",
        "steam://",
        "rungameid",
        "os.walk",
        "shutil.rmtree",
        "provider_annotate",
        "post_synthetic_event",
        "run_companion_client",
        "LogOutput.log",
        "ReadAllText",
    )
    for marker in forbidden_runtime_markers:
        if marker in text:
            errors.append(
                f"{relative}: bridge-to-overlay helper contains forbidden marker {marker!r}."
            )

    helper_ref = str(BRIDGE_TO_OVERLAY_SMOKE_HELPER.relative_to(ROOT)).replace("\\", "/")
    docs_to_link = (
        METADATA_PROBE_SMOKE_DOC,
        ROOT / "docs/bepinex-bridge.md",
        ROOT / "docs/overlay-prototype.md",
    )
    for doc_path in docs_to_link:
        if not doc_path.exists():
            continue
        doc_text = _read_text(doc_path).replace("\\", "/")
        if helper_ref not in doc_text:
            errors.append(f"{doc_path.relative_to(ROOT)} must point to {helper_ref}.")
        for marker in ("--phase prepare", "--phase post", "--phase cleanup"):
            if marker not in doc_text:
                errors.append(
                    f"{doc_path.relative_to(ROOT)} must document bridge-to-overlay flag {marker}."
                )
    return errors


def _check_local_bridge_workflow_helper() -> list[str]:
    errors: list[str] = []
    if not LOCAL_BRIDGE_WORKFLOW_HELPER.exists():
        return [
            f"Missing required local bridge workflow helper: "
            f"{LOCAL_BRIDGE_WORKFLOW_HELPER.relative_to(ROOT)}"
        ]

    text = _read_text(LOCAL_BRIDGE_WORKFLOW_HELPER)
    relative = LOCAL_BRIDGE_WORKFLOW_HELPER.relative_to(ROOT)
    required_markers = (
        "doctor",
        "prepare-metadata-smoke",
        "prepare-companion-smoke",
        "prepare-bridge-to-overlay-smoke",
        "post-bridge-to-overlay-smoke",
        "cleanup",
        "CompanionClient",
        "discover_local_smoke_paths",
        "discovery_summary",
        "enable_probe_flow",
        "set_synthetic_send_config_action",
        "run_bridge_to_overlay_smoke",
        "git",
        "no_raw_logs_reports_staged",
        "no_game_launch_performed",
        "raw_log_included",
        "raw_provider_payload_included",
        "companion_contract_changed",
    )
    for marker in required_markers:
        if marker not in text:
            errors.append(f"{relative}: local workflow helper missing marker {marker!r}.")

    forbidden_runtime_markers = (
        "subprocess.Popen",
        "os.system",
        "Start-Process",
        "ShellExecute",
        "CreateProcess",
        "steam://",
        "rungameid",
        "os.walk",
        "shutil.rmtree",
        "provider_annotate",
        "post_synthetic_event",
        "run_companion_client",
    )
    for marker in forbidden_runtime_markers:
        if marker in text:
            errors.append(
                f"{relative}: local workflow helper contains forbidden marker {marker!r}."
            )

    helper_ref = str(LOCAL_BRIDGE_WORKFLOW_HELPER.relative_to(ROOT)).replace("\\", "/")
    docs_to_link = (
        LOCAL_WORKFLOW_DOC,
        METADATA_PROBE_SMOKE_DOC,
        ROOT / "docs/bepinex-bridge.md",
    )
    for doc_path in docs_to_link:
        if not doc_path.exists():
            continue
        doc_text = _read_text(doc_path).replace("\\", "/")
        if helper_ref not in doc_text:
            errors.append(f"{doc_path.relative_to(ROOT)} must point to {helper_ref}.")
        for marker in (
            "--phase doctor",
            "--phase prepare-bridge-to-overlay-smoke",
            "--phase post-bridge-to-overlay-smoke",
            "--phase cleanup",
        ):
            if marker not in doc_text:
                errors.append(f"{doc_path.relative_to(ROOT)} must document {marker}.")
    return errors


def collect_metadata_extension_gate_errors(
    path: Path = METADATA_EXTENSION_GATE_FIXTURE,
) -> list[str]:
    errors: list[str] = []
    try:
        gate = load_json(path)
    except Exception as exc:
        return [f"Could not load metadata extension gate fixture: {exc}"]

    if not isinstance(gate, dict):
        return ["Metadata extension gate fixture must be a JSON object."]

    allowed_statuses = (
        "not_ready",
        "ready_for_metadata_only_extension_discussion",
        "ready_for_metadata_only_extension_implementation",
    )
    if gate.get("schema_version") != "bepinex-bridge-metadata-extension-gate.v1":
        errors.append("Metadata extension gate fixture has the wrong schema_version.")
    if gate.get("decision_status") not in allowed_statuses:
        errors.append("Metadata extension gate decision_status is not a known readiness state.")

    for field in (
        "reviewed_metadata_report_available",
        "review_ready",
        "implementation_allowed",
        "text_capture_allowed",
        "current_line_capture_allowed",
        "companion_contract_change_allowed",
    ):
        if not isinstance(gate.get(field), bool):
            errors.append(f"Metadata extension gate field {field!r} must be a boolean.")

    if gate.get("text_capture_allowed") is not False:
        errors.append("Metadata extension gate must keep text_capture_allowed=false.")
    if gate.get("current_line_capture_allowed") is not False:
        errors.append("Metadata extension gate must keep current_line_capture_allowed=false.")
    if gate.get("companion_contract_change_allowed") is not False:
        errors.append("Metadata extension gate must keep companion_contract_change_allowed=false.")
    if (
        gate.get("decision_status") == "ready_for_metadata_only_extension_discussion"
        and gate.get("implementation_allowed") is not False
    ):
        errors.append(
            "Metadata extension gate discussion status must keep implementation_allowed=false."
        )
    if gate.get("implementation_allowed") and (
        gate.get("text_capture_allowed")
        or gate.get("current_line_capture_allowed")
        or gate.get("companion_contract_change_allowed")
    ):
        errors.append("Metadata extension implementation cannot imply capture or contract changes.")

    if not isinstance(gate.get("required_next_milestone"), str) or not gate.get(
        "required_next_milestone"
    ):
        errors.append("Metadata extension gate must include a required_next_milestone string.")
    blockers = gate.get("blockers")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append("Metadata extension gate blockers must be a list of strings.")

    rendered = json.dumps(gate, ensure_ascii=False, sort_keys=True)
    errors.extend(_check_urls(rendered, path.relative_to(ROOT)))
    errors.extend(_check_secret_values(rendered, path.relative_to(ROOT)))
    errors.extend(
        _check_forbidden_markers(rendered, path.relative_to(ROOT), FORBIDDEN_EXTERNAL_MARKERS)
    )
    errors.extend(
        _check_forbidden_markers(rendered, path.relative_to(ROOT), FORBIDDEN_GAME_CONTENT_MARKERS)
    )
    return errors


def _check_metadata_extension_gate_contract() -> list[str]:
    errors = collect_metadata_extension_gate_errors(METADATA_EXTENSION_GATE_FIXTURE)

    if METADATA_EXTENSION_GATE_ADR.exists():
        adr_text = _read_text(METADATA_EXTENSION_GATE_ADR).replace("\\", "/")
        fixture_ref = str(METADATA_EXTENSION_GATE_FIXTURE.relative_to(ROOT)).replace("\\", "/")
        for marker in (
            "ready_for_metadata_only_extension_discussion",
            "ready_for_metadata_only_extension_implementation",
            "not_ready",
            fixture_ref,
            "does not approve current-line capture",
        ):
            if marker not in adr_text:
                errors.append(
                    f"{METADATA_EXTENSION_GATE_ADR.relative_to(ROOT)} must mention {marker}."
                )

    if METADATA_PROBE_GATE_DOC.exists():
        gate_text = _read_text(METADATA_PROBE_GATE_DOC).replace("\\", "/")
        adr_ref = str(METADATA_EXTENSION_GATE_ADR.relative_to(ROOT)).replace("\\", "/")
        fixture_ref = str(METADATA_EXTENSION_GATE_FIXTURE.relative_to(ROOT)).replace("\\", "/")
        for ref in (adr_ref, fixture_ref):
            if ref not in gate_text:
                errors.append(f"{METADATA_PROBE_GATE_DOC.relative_to(ROOT)} must point to {ref}.")

    bridge_doc = ROOT / "docs/bepinex-bridge.md"
    if bridge_doc.exists():
        bridge_text = _read_text(bridge_doc).replace("\\", "/")
        adr_ref = str(METADATA_EXTENSION_GATE_ADR.relative_to(ROOT)).replace("\\", "/")
        if adr_ref not in bridge_text:
            errors.append("docs/bepinex-bridge.md must point to ADR 0009.")
    return errors


def collect_metadata_only_extension_scope_errors(
    path: Path = METADATA_ONLY_EXTENSION_SCOPE_FIXTURE,
) -> list[str]:
    errors: list[str] = []
    try:
        scope = load_json(path)
    except Exception as exc:
        return [f"Could not load metadata-only extension scope fixture: {exc}"]

    if not isinstance(scope, dict):
        return ["Metadata-only extension scope fixture must be a JSON object."]

    if scope.get("schema_version") != "bepinex-bridge-metadata-only-extension-scope.v1":
        errors.append("Metadata-only extension scope fixture has the wrong schema_version.")
    if scope.get("scope_status") != "planned_not_implemented":
        errors.append("Metadata-only extension scope_status must be planned_not_implemented.")
    if scope.get("required_next_milestone") != "4M":
        errors.append("Metadata-only extension scope required_next_milestone must be 4M.")

    required_bool_fields = (
        "implementation_allowed_next",
        "requires_reviewed_runtime_report",
        "text_capture_allowed",
        "current_line_capture_allowed",
        "ui_text_reading_allowed",
        "unity_scanning_allowed",
        "hooks_allowed",
        "ocr_allowed",
        "extraction_allowed",
        "companion_contract_change_allowed",
        "provider_calls_allowed",
    )
    for field in required_bool_fields:
        if not isinstance(scope.get(field), bool):
            errors.append(f"Metadata-only extension scope field {field!r} must be a boolean.")

    if scope.get("implementation_allowed_next") is not True:
        errors.append("Metadata-only extension scope must set implementation_allowed_next=true.")
    if scope.get("requires_reviewed_runtime_report") is not False:
        errors.append(
            "Metadata-only extension scope must set requires_reviewed_runtime_report=false."
        )

    forbidden_permissions = (
        "text_capture_allowed",
        "current_line_capture_allowed",
        "ui_text_reading_allowed",
        "unity_scanning_allowed",
        "hooks_allowed",
        "ocr_allowed",
        "extraction_allowed",
        "companion_contract_change_allowed",
        "provider_calls_allowed",
    )
    for field in forbidden_permissions:
        if scope.get(field) is not False:
            errors.append(f"Metadata-only extension scope must keep {field}=false.")

    if scope.get("implementation_allowed_next") and any(
        scope.get(field) for field in forbidden_permissions
    ):
        errors.append(
            "Metadata-only extension implementation cannot imply capture, provider calls, "
            "or companion contract changes."
        )

    for field in ("allowed_future_fields", "forbidden_future_fields"):
        value = scope.get(field)
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item for item in value)
        ):
            errors.append(
                f"Metadata-only extension scope field {field!r} must be a non-empty list of strings."
            )

    required_allowed = (
        "probe_execution_count",
        "plugin_loaded",
        "plugin_enabled",
        "companion_health_checked",
        "companion_available",
        "synthetic_event_send_configured",
        "synthetic_event_sent",
        "probe_attempted",
        "probe_completed",
        "metadata_snapshot_created_count",
        "health_check_observed_count",
        "synthetic_send_configured_count",
        "safe_status_events",
        "synthetic_events",
        "real_text_captured_false",
        "current_line_capture_enabled_false",
    )
    allowed_fields = set(scope.get("allowed_future_fields", []))
    for field in required_allowed:
        if field not in allowed_fields:
            errors.append(f"Metadata-only extension scope allowed fields must include {field!r}.")

    rendered = json.dumps(scope, ensure_ascii=False, sort_keys=True)
    errors.extend(_check_urls(rendered, path.relative_to(ROOT)))
    errors.extend(_check_secret_values(rendered, path.relative_to(ROOT)))
    return errors


def _check_metadata_only_extension_scope_contract() -> list[str]:
    errors = collect_metadata_only_extension_scope_errors(METADATA_ONLY_EXTENSION_SCOPE_FIXTURE)

    if METADATA_ONLY_EXTENSION_SCOPE_DOC.exists():
        scope_text = _read_text(METADATA_ONLY_EXTENSION_SCOPE_DOC).replace("\\", "/")
        fixture_ref = str(METADATA_ONLY_EXTENSION_SCOPE_FIXTURE.relative_to(ROOT)).replace(
            "\\", "/"
        )
        for marker in (
            fixture_ref,
            "Milestone 4L defines",
            "docs/static-contract work only",
            "Milestone 4M may be planned without a reviewed local metadata probe report",
            "does not implement runtime behavior",
            "must not",
        ):
            if marker not in scope_text:
                errors.append(
                    f"{METADATA_ONLY_EXTENSION_SCOPE_DOC.relative_to(ROOT)} must mention {marker}."
                )

    docs_to_link = (
        METADATA_PROBE_GATE_DOC,
        ROOT / "docs/bepinex-bridge.md",
        METADATA_EXTENSION_GATE_ADR,
        PACKAGE_DIR / "DESIGN.md",
    )
    scope_ref = str(METADATA_ONLY_EXTENSION_SCOPE_DOC.relative_to(ROOT)).replace("\\", "/")
    fixture_ref = str(METADATA_ONLY_EXTENSION_SCOPE_FIXTURE.relative_to(ROOT)).replace("\\", "/")
    for doc_path in docs_to_link:
        if not doc_path.exists():
            continue
        text = _read_text(doc_path).replace("\\", "/")
        for ref in (scope_ref, fixture_ref):
            if ref not in text:
                errors.append(f"{doc_path.relative_to(ROOT)} must point to {ref}.")
    return errors


def collect_post_bridge_to_overlay_next_step_errors(
    path: Path = POST_BRIDGE_TO_OVERLAY_NEXT_STEP_FIXTURE,
) -> list[str]:
    errors: list[str] = []
    try:
        decision = load_json(path)
    except Exception as exc:
        return [f"Could not load post bridge-to-overlay next-step fixture: {exc}"]

    if not isinstance(decision, dict):
        return ["Post bridge-to-overlay next-step fixture must be a JSON object."]

    if decision.get("schema_version") != "post-bridge-to-overlay-next-step.v1":
        errors.append("Post bridge-to-overlay next-step fixture has the wrong schema_version.")
    if decision.get("bridge_to_overlay_smoke_passed") is not True:
        errors.append("Post bridge-to-overlay next-step fixture must record smoke passed=true.")
    if decision.get("recommended_next_step") != "metadata_only_overlay_refresh_readiness_contract":
        errors.append(
            "Post bridge-to-overlay next-step fixture must recommend the metadata-only "
            "overlay refresh/readiness contract."
        )

    required_bool_fields = (
        "bridge_to_overlay_smoke_passed",
        "implementation_allowed_next",
        "docs_static_contract_work_allowed",
        "packaging_manual_workflow_polish_allowed",
        "current_line_capture_allowed",
        "real_text_capture_allowed",
        "ui_text_reading_allowed",
        "unity_scanning_allowed",
        "hooks_allowed",
        "ocr_allowed",
        "extraction_allowed",
        "real_provider_execution_allowed",
        "companion_contract_change_allowed",
        "production_overlay_shell_allowed",
    )
    for field in required_bool_fields:
        if not isinstance(decision.get(field), bool):
            errors.append(f"Post bridge-to-overlay next-step field {field!r} must be a boolean.")

    if decision.get("implementation_allowed_next") is not False:
        errors.append(
            "Post bridge-to-overlay next-step fixture must keep implementation_allowed_next=false."
        )
    if decision.get("docs_static_contract_work_allowed") is not True:
        errors.append(
            "Post bridge-to-overlay next-step fixture must allow docs/static-contract work."
        )

    forbidden_permissions = (
        "current_line_capture_allowed",
        "real_text_capture_allowed",
        "ui_text_reading_allowed",
        "unity_scanning_allowed",
        "hooks_allowed",
        "ocr_allowed",
        "extraction_allowed",
        "real_provider_execution_allowed",
        "companion_contract_change_allowed",
        "production_overlay_shell_allowed",
    )
    for field in forbidden_permissions:
        if decision.get(field) is not False:
            errors.append(f"Post bridge-to-overlay next-step fixture must keep {field}=false.")

    if decision.get("bridge_to_overlay_smoke_passed") and any(
        decision.get(field) for field in forbidden_permissions
    ):
        errors.append(
            "Bridge-to-overlay smoke success cannot imply capture, provider execution, "
            "production shell, or companion contract permission."
        )
    if decision.get("implementation_allowed_next") and any(
        decision.get(field) for field in forbidden_permissions
    ):
        errors.append(
            "Post bridge-to-overlay implementation permission cannot imply forbidden scope."
        )

    if not isinstance(decision.get("required_next_step"), str) or not decision.get(
        "required_next_step"
    ):
        errors.append("Post bridge-to-overlay next-step fixture must include required_next_step.")
    blockers = decision.get("blockers")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append("Post bridge-to-overlay next-step blockers must be a list of strings.")

    rendered = json.dumps(decision, ensure_ascii=False, sort_keys=True)
    errors.extend(_check_urls(rendered, path.relative_to(ROOT)))
    errors.extend(_check_secret_values(rendered, path.relative_to(ROOT)))
    errors.extend(
        _check_forbidden_markers(rendered, path.relative_to(ROOT), FORBIDDEN_GAME_CONTENT_MARKERS)
    )
    return errors


def _check_post_bridge_to_overlay_next_step_contract() -> list[str]:
    errors = collect_post_bridge_to_overlay_next_step_errors(
        POST_BRIDGE_TO_OVERLAY_NEXT_STEP_FIXTURE
    )

    if POST_BRIDGE_TO_OVERLAY_NEXT_STEP_ADR.exists():
        adr_text = _read_text(POST_BRIDGE_TO_OVERLAY_NEXT_STEP_ADR).replace("\\", "/")
        fixture_ref = str(POST_BRIDGE_TO_OVERLAY_NEXT_STEP_FIXTURE.relative_to(ROOT)).replace(
            "\\", "/"
        )
        for marker in (
            "metadata_only_overlay_refresh_readiness_contract",
            "Current-line capture implementation",
            "disallowed",
            "does not approve current-line capture",
            fixture_ref,
        ):
            if marker not in adr_text:
                errors.append(
                    f"{POST_BRIDGE_TO_OVERLAY_NEXT_STEP_ADR.relative_to(ROOT)} "
                    f"must mention {marker}."
                )

    docs_to_link = (
        ROOT / "docs/bepinex-bridge.md",
        ROOT / "docs/overlay-prototype.md",
        ROOT / "docs/devlog/NEXT_ACTIONS.md",
    )
    adr_ref = str(POST_BRIDGE_TO_OVERLAY_NEXT_STEP_ADR.relative_to(ROOT)).replace("\\", "/")
    fixture_ref = str(POST_BRIDGE_TO_OVERLAY_NEXT_STEP_FIXTURE.relative_to(ROOT)).replace("\\", "/")
    for doc_path in docs_to_link:
        if not doc_path.exists():
            continue
        text = _read_text(doc_path).replace("\\", "/")
        if adr_ref not in text:
            errors.append(f"{doc_path.relative_to(ROOT)} must point to ADR 0010.")
        if fixture_ref not in text:
            errors.append(f"{doc_path.relative_to(ROOT)} must point to the ADR 0010 fixture.")
    return errors


def _check_log_contract() -> list[str]:
    errors: list[str] = []
    try:
        contract = load_json(LOG_CONTRACT_PATH)
    except Exception as exc:
        return [f"Could not load bridge log contract fixture: {exc}"]

    if not isinstance(contract, dict):
        return ["Bridge log contract fixture must be a JSON object."]
    if contract.get("schema_version") != "bepinex-bridge-log-contract.v1":
        errors.append("Bridge log contract fixture has the wrong schema_version.")
    if contract.get("synthetic_only") is not True:
        errors.append("Bridge log contract fixture must set synthetic_only=true.")

    expected = contract.get("expected_safe_log_snippets")
    if not isinstance(expected, list) or not all(isinstance(item, str) for item in expected):
        errors.append(
            "Bridge log contract fixture must include expected_safe_log_snippets strings."
        )
        expected = []
    forbidden = contract.get("forbidden_log_content")
    if not isinstance(forbidden, list) or not all(isinstance(item, str) for item in forbidden):
        errors.append("Bridge log contract fixture must include forbidden_log_content strings.")

    source = _read_source_text()
    for snippet in expected:
        if snippet not in source:
            errors.append(f"Bridge source missing safe log contract snippet: {snippet!r}")

    metadata_tokens = contract.get("required_metadata_tokens")
    if not isinstance(metadata_tokens, list) or not all(
        isinstance(item, str) for item in metadata_tokens
    ):
        errors.append("Bridge log contract fixture must include required_metadata_tokens strings.")

    runtime_policy = contract.get("runtime_report_policy")
    if not isinstance(runtime_policy, dict):
        errors.append("Bridge log contract fixture must include runtime_report_policy.")
    else:
        for key in (
            "commit_runtime_logs",
            "commit_bepinex_logs",
            "commit_game_logs",
            "commit_smoke_reports",
        ):
            if runtime_policy.get(key) is not False:
                errors.append(f"Bridge log contract runtime_report_policy.{key} must be false.")

    for doc_path in (RUNTIME_SMOKE_DOC, LOG_CONTRACT_DOC):
        fixture_ref = str(LOG_CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/")
        if doc_path.exists() and fixture_ref not in _read_text(doc_path).replace("\\", "/"):
            errors.append(
                f"{doc_path.relative_to(ROOT)} must point to the committed log contract fixture."
            )

    return errors


def _check_ignored_output_roots() -> list[str]:
    if not GITIGNORE.exists():
        return [".gitignore is missing; bridge build outputs must stay ignored."]
    text = _read_text(GITIGNORE)
    errors: list[str] = []
    for marker in ("bin/", "obj/", "workspace/"):
        if marker not in text:
            errors.append(f".gitignore must keep {marker!r} ignored for local bridge outputs.")
    return errors


def _check_source_contract() -> list[str]:
    errors: list[str] = []
    source = _read_source_text()
    plugin_source = _read_text(SOURCE_DIR / "RevacholCompanionBridgePlugin.cs")
    client_source = _read_text(SOURCE_DIR / "CompanionHttpClient.cs")
    event_source = _read_text(SOURCE_DIR / "SyntheticEventFactory.cs")
    metadata_probe_source = _read_text(METADATA_PROBE_SOURCE)

    required_source_markers = (
        'DefaultCompanionServerUrl = "http://127.0.0.1:8765"',
        "DefaultRequestTimeoutMs = 3000",
        "DefaultEnabled = true",
        "DefaultSendSyntheticEventOnStart = false",
        "DefaultMetadataProbeEnabled = false",
        "DefaultMetadataProbeLogOnStart = false",
        "CheckHealthAsync",
        "PostSyntheticProviderAnnotateAsync",
        "BuildProviderAnnotateRequestJson",
        "MetadataProbe.BuildSnapshot",
        "Metadata probe snapshot: synthetic_manual=true",
        "input_type",
        "fake_event",
        "synthetic/provider-annotate",
    )
    for marker in required_source_markers:
        if marker not in source:
            errors.append(f"Bridge source missing required marker: {marker}")

    if "IsLocalhost" not in client_source or "IsLoopbackHost" not in client_source:
        errors.append("Companion client must keep an explicit localhost guard.")
    if "Config.Bind" not in plugin_source:
        errors.append("Bridge plugin must bind BepInEx config entries.")
    if "raw_english_text" not in event_source:
        errors.append("Synthetic event builder must include the fake-event raw_english_text field.")
    for marker in (
        "RealTextCaptured = false",
        "CurrentLineCaptureEnabled = false",
        "UiProbeAttempted = false",
        "SceneProbeAttempted = false",
        "DefaultSafeStatusEvents = 0",
        "DefaultSyntheticEvents = 0",
        "DefaultMetadataSnapshotCreatedCount = 1",
        "real_text_captured=",
        "current_line_capture_enabled=",
        "ui_probe_attempted=",
        "scene_probe_attempted=",
        "metadata_snapshot_created_count=",
        "health_check_observed_count=",
        "synthetic_send_configured_count=",
    ):
        if marker not in metadata_probe_source:
            errors.append(f"Metadata probe source missing required safe marker: {marker}")

    return errors


def _check_text_safety() -> list[str]:
    errors: list[str] = []
    for path in _scanned_files():
        text = _read_text(path)
        relative = path.relative_to(ROOT)
        errors.extend(_check_urls(text, relative))
        errors.extend(_check_secret_values(text, relative))
        if path != RUNTIME_REPORT_CHECKER:
            errors.extend(_check_forbidden_markers(text, relative, FORBIDDEN_EXTERNAL_MARKERS))
            errors.extend(_check_forbidden_markers(text, relative, FORBIDDEN_GAME_CONTENT_MARKERS))

        if path.suffix.lower() == ".cs":
            errors.extend(
                _check_forbidden_markers(text, relative, FORBIDDEN_HOOK_OR_EXTRACTION_MARKERS)
            )
            for pattern in RAW_PAYLOAD_LOG_PATTERNS:
                if re.search(pattern, text):
                    errors.append(f"{relative}: appears to log a raw request payload.")
        if path == BUILD_HELPER:
            errors.extend(
                _check_forbidden_markers(text, relative, FORBIDDEN_DOWNLOAD_OR_INSTALL_MARKERS)
            )

    return errors


def _check_check_all_smoke() -> list[str]:
    if not CHECK_ALL.exists():
        return ["scripts/check_all.py is missing."]
    text = _read_text(CHECK_ALL)
    if "scripts/check_bepinex_bridge_safety.py" not in text:
        return ["scripts/check_all.py must include the BepInEx bridge safety smoke."]
    if "scripts/build_bepinex_bridge.py" in text:
        return ["scripts/check_all.py must not require the optional BepInEx bridge build helper."]
    if "scripts/run_bepinex_metadata_probe_local_smoke.py" in text:
        return ["scripts/check_all.py must not require the local metadata probe smoke helper."]
    if "scripts/run_bridge_to_overlay_synthetic_smoke.py" in text:
        return ["scripts/check_all.py must not require the bridge-to-overlay smoke helper."]
    if "scripts/run_local_bridge_workflow.py" in text:
        return ["scripts/check_all.py must not require the local bridge workflow helper."]
    return []


def _check_urls(text: str, relative: Path) -> list[str]:
    errors: list[str] = []
    for match in FORBIDDEN_URL_PATTERN.findall(text):
        if match.rstrip(".,)") not in ALLOWED_URLS:
            errors.append(f"{relative}: contains non-localhost URL {match!r}")
    return errors


def _check_secret_values(text: str, relative: Path) -> list[str]:
    if SECRET_VALUE_PATTERN.search(text):
        return [f"{relative}: contains a secret/API-key-looking value."]
    return []


def _check_forbidden_markers(text: str, relative: Path, markers: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    lowered = text.lower()
    for marker in markers:
        if marker.lower() in lowered:
            errors.append(f"{relative}: contains forbidden marker {marker!r}")
    return errors


def _read_source_text() -> str:
    return "\n".join(_read_text(path) for path in sorted(SOURCE_DIR.glob("*.cs")))


def _scanned_files() -> list[Path]:
    files = [
        PACKAGE_DIR / "README.md",
        PACKAGE_DIR / "DESIGN.md",
        PROJECT_FILE,
        FIXTURE_PATH,
        LOG_CONTRACT_PATH,
        RUNTIME_REPORT_FIXTURE_PATH,
        BUILD_HELPER,
        RUNTIME_REPORT_CHECKER,
        RUNTIME_REPORT_WRITER,
        RUNTIME_REPORT_REVIEWER,
        METADATA_PROBE_WRITER,
        METADATA_PROBE_REVIEWER,
        RUNTIME_SMOKE_DOC,
        LOG_CONTRACT_DOC,
        RUNTIME_REPORT_DOC,
        METADATA_PROBE_SMOKE_DOC,
    ]
    files.extend(sorted(SOURCE_DIR.glob("*.cs")))
    return [path for path in files if path.exists()]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
