from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

try:
    from scripts.schema_validator import collect_errors, load_json
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import collect_errors, load_json


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "packages/bepinex-plugin"
SOURCE_DIR = PACKAGE_DIR / "src"
PROJECT_FILE = PACKAGE_DIR / "Revachol.UkrainianCompanion.BepInExBridge.csproj"
FIXTURE_PATH = ROOT / "tests/fixtures/bepinex_bridge.provider_annotate_request.synthetic.json"
LOG_CONTRACT_PATH = ROOT / "tests/fixtures/bepinex_bridge.log_contract.synthetic.json"
FAKE_EVENT_SCHEMA = ROOT / "specs/fake-game-event.schema.json"
CHECK_ALL = ROOT / "scripts/check_all.py"
BUILD_HELPER = ROOT / "scripts/build_bepinex_bridge.py"
GITIGNORE = ROOT / ".gitignore"
MANUAL_SMOKE_DIR = ROOT / "docs/manual-smoke"
RUNTIME_SMOKE_DOC = MANUAL_SMOKE_DIR / "bepinex-bridge-runtime-smoke.md"
LOG_CONTRACT_DOC = MANUAL_SMOKE_DIR / "bepinex-bridge-log-contract.md"

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
        FIXTURE_PATH,
        LOG_CONTRACT_PATH,
        BUILD_HELPER,
        RUNTIME_SMOKE_DOC,
        LOG_CONTRACT_DOC,
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

    required_source_markers = (
        'DefaultCompanionServerUrl = "http://127.0.0.1:8765"',
        "DefaultRequestTimeoutMs = 3000",
        "DefaultEnabled = true",
        "DefaultSendSyntheticEventOnStart = false",
        "CheckHealthAsync",
        "PostSyntheticProviderAnnotateAsync",
        "BuildProviderAnnotateRequestJson",
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

    return errors


def _check_text_safety() -> list[str]:
    errors: list[str] = []
    for path in _scanned_files():
        text = _read_text(path)
        relative = path.relative_to(ROOT)
        errors.extend(_check_urls(text, relative))
        errors.extend(_check_secret_values(text, relative))
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
        BUILD_HELPER,
        RUNTIME_SMOKE_DOC,
        LOG_CONTRACT_DOC,
    ]
    files.extend(sorted(SOURCE_DIR.glob("*.cs")))
    return [path for path in files if path.exists()]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
