from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK_ID = "ukrainian_annotation_v1"
DEFAULT_PACKS_ROOT = ROOT / "prompts/packs"

REQUIRED_METADATA_KEYS = (
    "pack_id",
    "version",
    "language",
    "purpose",
    "required_output_fields",
    "quality_priorities",
    "policy_files",
    "synthetic_examples_file",
    "provider_pipeline_compatibility",
)

REQUIRED_POLICY_KEYS = (
    "pack",
    "system",
    "developer",
    "output_contract",
    "style_guide",
    "glossary_policy",
    "uncertainty_policy",
    "spoiler_policy",
    "anti_hallucination_policy",
    "anti_overlocalization_policy",
    "russianism_avoidance",
)


class PromptPackError(ValueError):
    """Raised when a prompt pack is missing or malformed."""


@dataclass(frozen=True)
class PromptPackMetadata:
    pack_id: str
    version: str
    language: str
    purpose: str
    required_output_fields: tuple[str, ...]
    quality_priorities: tuple[str, ...]
    policy_files: dict[str, str]
    synthetic_examples_file: str
    provider_pipeline_compatibility: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_output_fields"] = list(self.required_output_fields)
        data["quality_priorities"] = list(self.quality_priorities)
        return data


@dataclass(frozen=True)
class PromptPack:
    metadata: PromptPackMetadata
    pack_dir: Path
    policy_texts: dict[str, str]
    synthetic_examples: str

    def policy_refs(self) -> tuple[str, ...]:
        return tuple(self.metadata.policy_files[key] for key in sorted(self.metadata.policy_files))

    def sections_for_provider(self) -> dict[str, str]:
        sections = {key: self.policy_texts[key] for key in sorted(self.policy_texts)}
        sections["synthetic_examples"] = self.synthetic_examples
        return sections

    def summary(self) -> dict[str, Any]:
        return {
            "pack_id": self.metadata.pack_id,
            "version": self.metadata.version,
            "language": self.metadata.language,
            "purpose": self.metadata.purpose,
            "required_output_fields": list(self.metadata.required_output_fields),
            "quality_priorities": list(self.metadata.quality_priorities),
            "policy_files": dict(sorted(self.metadata.policy_files.items())),
            "synthetic_examples_file": self.metadata.synthetic_examples_file,
            "provider_pipeline_compatibility": self.metadata.provider_pipeline_compatibility,
        }


def load_prompt_pack(
    pack_id: str = DEFAULT_PACK_ID,
    packs_root: Path | None = None,
) -> PromptPack:
    root = (packs_root or DEFAULT_PACKS_ROOT).resolve(strict=False)
    pack_dir = (root / pack_id).resolve(strict=False)
    metadata_path = pack_dir / "pack.json"
    if not metadata_path.exists():
        raise PromptPackError(f"Prompt pack metadata not found: {metadata_path}")

    try:
        raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PromptPackError(f"Malformed prompt pack metadata JSON: {exc.msg}") from exc

    metadata = _parse_metadata(raw_metadata, pack_id)
    policy_texts = {
        key: _read_pack_file(pack_dir, file_name)
        for key, file_name in sorted(metadata.policy_files.items())
    }
    synthetic_examples = _read_pack_file(pack_dir, metadata.synthetic_examples_file)
    return PromptPack(
        metadata=metadata,
        pack_dir=pack_dir,
        policy_texts=policy_texts,
        synthetic_examples=synthetic_examples,
    )


def _parse_metadata(raw: Any, expected_pack_id: str) -> PromptPackMetadata:
    if not isinstance(raw, dict):
        raise PromptPackError("Prompt pack metadata must be an object.")
    for key in REQUIRED_METADATA_KEYS:
        if key not in raw:
            raise PromptPackError(f"Prompt pack metadata missing required key: {key}")

    pack_id = _required_string(raw, "pack_id")
    if pack_id != expected_pack_id:
        raise PromptPackError(
            f"Prompt pack id mismatch: expected {expected_pack_id}, got {pack_id}"
        )

    policy_files = raw["policy_files"]
    if not isinstance(policy_files, dict):
        raise PromptPackError("policy_files must be an object.")
    for key in REQUIRED_POLICY_KEYS:
        if key not in policy_files:
            raise PromptPackError(f"policy_files missing required key: {key}")
        _validate_relative_markdown(policy_files[key], f"policy_files.{key}")

    synthetic_examples_file = _required_string(raw, "synthetic_examples_file")
    _validate_relative_markdown(synthetic_examples_file, "synthetic_examples_file")

    compatibility = raw["provider_pipeline_compatibility"]
    if not isinstance(compatibility, dict):
        raise PromptPackError("provider_pipeline_compatibility must be an object.")

    return PromptPackMetadata(
        pack_id=pack_id,
        version=_required_string(raw, "version"),
        language=_required_string(raw, "language"),
        purpose=_required_string(raw, "purpose"),
        required_output_fields=_required_string_tuple(raw, "required_output_fields"),
        quality_priorities=_required_string_tuple(raw, "quality_priorities"),
        policy_files={str(key): str(value) for key, value in policy_files.items()},
        synthetic_examples_file=synthetic_examples_file,
        provider_pipeline_compatibility=compatibility,
    )


def _read_pack_file(pack_dir: Path, file_name: str) -> str:
    _validate_relative_markdown(file_name, file_name)
    path = (pack_dir / file_name).resolve(strict=False)
    try:
        path.relative_to(pack_dir.resolve(strict=False))
    except ValueError as exc:
        raise PromptPackError(f"Prompt pack file escapes pack directory: {file_name}") from exc
    if not path.exists():
        raise PromptPackError(f"Prompt pack file not found: {file_name}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise PromptPackError(f"Prompt pack file is empty: {file_name}")
    return text


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise PromptPackError(f"Prompt pack metadata field must be a non-empty string: {key}")
    return value


def _required_string_tuple(raw: dict[str, Any], key: str) -> tuple[str, ...]:
    value = raw.get(key)
    if not isinstance(value, list) or not value:
        raise PromptPackError(f"Prompt pack metadata field must be a non-empty list: {key}")
    if not all(isinstance(item, str) and item for item in value):
        raise PromptPackError(f"Prompt pack metadata list must contain only strings: {key}")
    return tuple(value)


def _validate_relative_markdown(file_name: Any, label: str) -> None:
    if not isinstance(file_name, str) or not file_name:
        raise PromptPackError(f"{label} must be a file name.")
    path = Path(file_name)
    if path.is_absolute() or ".." in path.parts:
        raise PromptPackError(f"{label} must stay inside the prompt pack directory.")
    if path.suffix.lower() != ".md":
        raise PromptPackError(f"{label} must reference a Markdown file.")
