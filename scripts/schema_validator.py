from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    """Raised when a fixture does not match the supported schema subset."""


def load_json(path: Path | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_errors(instance: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate(instance, schema, schema, "$", errors)
    return errors


def assert_valid(instance: Any, schema: dict[str, Any]) -> None:
    errors = collect_errors(instance, schema)
    if errors:
        raise SchemaValidationError("; ".join(errors))


def _validate(
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root_schema)

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
        return

    if "enum" in schema and instance not in schema["enum"]:
        allowed = ", ".join(repr(item) for item in schema["enum"])
        errors.append(f"{path}: expected one of {allowed}, got {instance!r}")
        return

    if "type" in schema and not _matches_type(instance, schema["type"]):
        errors.append(f"{path}: expected type {schema['type']!r}, got {_json_type(instance)!r}")
        return

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                _validate(value, properties[key], root_schema, f"{path}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property {key!r}")

    if isinstance(instance, list) and "items" in schema:
        for index, value in enumerate(instance):
            _validate(value, schema["items"], root_schema, f"{path}[{index}]", errors)

    if isinstance(instance, str) and "maxLength" in schema:
        if len(instance) > schema["maxLength"]:
            errors.append(f"{path}: length {len(instance)} exceeds maxLength {schema['maxLength']}")

    if _is_number(instance):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: value {instance} is below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: value {instance} is above maximum {schema['maximum']}")


def _resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaValidationError(f"Only local refs are supported, got {ref!r}")

    target: Any = root_schema
    for part in ref[2:].split("/"):
        if not isinstance(target, dict) or part not in target:
            raise SchemaValidationError(f"Unresolvable schema ref {ref!r}")
        target = target[part]
    if not isinstance(target, dict):
        raise SchemaValidationError(f"Schema ref {ref!r} does not point to an object")
    return target


def _matches_type(instance: Any, expected: str | list[str]) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    return any(_matches_single_type(instance, expected_type) for expected_type in expected_types)


def _matches_single_type(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "number":
        return _is_number(instance)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    raise SchemaValidationError(f"Unsupported JSON Schema type {expected!r}")


def _is_number(instance: Any) -> bool:
    return isinstance(instance, (int, float)) and not isinstance(instance, bool)


def _json_type(instance: Any) -> str:
    if instance is None:
        return "null"
    if isinstance(instance, bool):
        return "boolean"
    if isinstance(instance, dict):
        return "object"
    if isinstance(instance, list):
        return "array"
    if isinstance(instance, str):
        return "string"
    if _is_number(instance):
        return "number"
    return type(instance).__name__
