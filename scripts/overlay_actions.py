from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MODES = ("compact", "deep", "debug")


@dataclass(frozen=True)
class OverlayActionDefinition:
    action_id: str
    label_uk: str
    hint_uk: str
    allowed_modes: tuple[str, ...]
    player_facing: bool
    debug_only: bool = False

    def to_view_model(self) -> dict[str, Any]:
        return {
            "id": self.action_id,
            "label_uk": self.label_uk,
            "hint_uk": self.hint_uk,
            "allowed_modes": list(self.allowed_modes),
            "player_facing": self.player_facing,
            "debug_only": self.debug_only,
        }


ACTION_DEFINITIONS: tuple[OverlayActionDefinition, ...] = (
    OverlayActionDefinition(
        "switch_compact",
        "Компактний режим",
        "Повернути короткий вигляд.",
        ("deep", "debug"),
        True,
    ),
    OverlayActionDefinition(
        "switch_deep",
        "Глибше пояснення",
        "Відкрити повні нотатки до репліки.",
        ("compact", "debug"),
        True,
    ),
    OverlayActionDefinition(
        "switch_debug",
        "Режим розробника",
        "Показати службові дані для перевірки.",
        ("debug",),
        False,
        True,
    ),
    OverlayActionDefinition(
        "toggle_original",
        "Оригінал",
        "Увімкнути або приховати англійський текст.",
        MODES,
        True,
    ),
    OverlayActionDefinition(
        "toggle_translation",
        "Український варіант",
        "Увімкнути або приховати український текст.",
        MODES,
        True,
    ),
    OverlayActionDefinition(
        "toggle_annotations",
        "Пояснення",
        "Увімкнути або приховати нотатки й глосарій.",
        ("deep", "debug"),
        True,
    ),
    OverlayActionDefinition(
        "next_annotation",
        "Наступна нотатка",
        "Перейти до наступного пояснення.",
        ("deep", "debug"),
        True,
    ),
    OverlayActionDefinition(
        "previous_annotation",
        "Попередня нотатка",
        "Повернутися до попереднього пояснення.",
        ("deep", "debug"),
        True,
    ),
    OverlayActionDefinition(
        "copy_original",
        "Скопіювати оригінал",
        "Підготувати англійський текст до копіювання.",
        MODES,
        True,
    ),
    OverlayActionDefinition(
        "copy_ukrainian_summary",
        "Скопіювати український зміст",
        "Підготувати короткий український зміст до копіювання.",
        MODES,
        True,
    ),
    OverlayActionDefinition(
        "copy_annotation_summary",
        "Скопіювати пояснення",
        "Підготувати стислий підсумок нотаток до копіювання.",
        ("deep", "debug"),
        True,
    ),
    OverlayActionDefinition(
        "hide_overlay",
        "Сховати оверлей",
        "Прибрати підказку з екрана.",
        MODES,
        True,
    ),
)

ACTION_IDS = tuple(action.action_id for action in ACTION_DEFINITIONS)
ACTION_BY_ID = {action.action_id: action for action in ACTION_DEFINITIONS}
DEBUG_ONLY_ACTION_IDS = tuple(
    action.action_id for action in ACTION_DEFINITIONS if action.debug_only
)
PLAYER_FACING_ACTION_IDS = tuple(
    action.action_id for action in ACTION_DEFINITIONS if action.player_facing
)


def build_visibility_state(mode: str) -> dict[str, Any]:
    if mode == "compact":
        return {
            "original_visible": True,
            "translation_visible": True,
            "annotations_visible": False,
            "debug_visible": False,
            "current_mode": "compact",
            "available_modes": ["compact", "deep"],
        }
    if mode == "deep":
        return {
            "original_visible": True,
            "translation_visible": True,
            "annotations_visible": True,
            "debug_visible": False,
            "current_mode": "deep",
            "available_modes": ["compact", "deep"],
        }
    if mode == "debug":
        return {
            "original_visible": True,
            "translation_visible": True,
            "annotations_visible": True,
            "debug_visible": True,
            "current_mode": "debug",
            "available_modes": list(MODES),
        }
    raise ValueError(f"Unsupported overlay mode: {mode}")


def build_overlay_actions(mode: str) -> list[dict[str, Any]]:
    if mode not in MODES:
        raise ValueError(f"Unsupported overlay mode: {mode}")
    if mode == "debug":
        return [action.to_view_model() for action in ACTION_DEFINITIONS]
    return [
        action.to_view_model()
        for action in ACTION_DEFINITIONS
        if mode in action.allowed_modes and action.player_facing and not action.debug_only
    ]
