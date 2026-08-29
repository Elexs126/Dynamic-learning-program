#!/usr/bin/env python3
"""Small dependency-free validator for the JSON Schema features used here.

It is intentionally scoped to the project's checked-in schemas. Unsupported
keywords are ignored only when they are annotations (title/description/$id);
all assertion keywords currently used by the schemas are implemented.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _pointer(document: Any, fragment: str) -> Any:
    if fragment in {"", "#"}:
        return document
    if fragment.startswith("#"):
        fragment = fragment[1:]
    if not fragment.startswith("/"):
        raise ValueError(f"unsupported JSON pointer fragment: {fragment!r}")
    value = document
    for raw_part in fragment[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    return value


class SchemaRuntime:
    def __init__(self, root_schema_path: Path):
        self.root_schema_path = root_schema_path.resolve()
        self._documents: dict[Path, Any] = {}

    def _load(self, path: Path) -> Any:
        path = path.resolve()
        if path not in self._documents:
            with path.open("r", encoding="utf-8") as handle:
                self._documents[path] = json.load(handle)
        return self._documents[path]

    def _resolve_ref(
        self, ref: str, current_document: Any, current_schema_path: Path
    ) -> tuple[Any, Any, Path]:
        if ref.startswith("#"):
            return _pointer(current_document, ref), current_document, current_schema_path
        file_part, separator, fragment = ref.partition("#")
        target_path = (current_schema_path.parent / file_part).resolve()
        target_document = self._load(target_path)
        target_schema = _pointer(target_document, f"#{fragment}" if separator else "#")
        return target_schema, target_document, target_path

    def validate(self, instance: Any) -> list[str]:
        document = self._load(self.root_schema_path)
        return self._validate(
            instance,
            document,
            "$",
            document,
            self.root_schema_path,
        )

    def _validate(
        self,
        instance: Any,
        schema: Any,
        instance_path: str,
        current_document: Any,
        current_schema_path: Path,
    ) -> list[str]:
        if schema is True:
            return []
        if schema is False:
            return [f"{instance_path}: rejected by false schema"]
        if not isinstance(schema, dict):
            return [f"{instance_path}: invalid schema node {schema!r}"]

        if "$ref" in schema:
            target, target_document, target_path = self._resolve_ref(
                schema["$ref"], current_document, current_schema_path
            )
            return self._validate(
                instance,
                target,
                instance_path,
                target_document,
                target_path,
            )

        errors: list[str] = []

        if "const" in schema and instance != schema["const"]:
            errors.append(
                f"{instance_path}: expected const {schema['const']!r}, got {instance!r}"
            )
        if "enum" in schema and instance not in schema["enum"]:
            errors.append(f"{instance_path}: {instance!r} not in enum")

        expected_type = schema.get("type")
        if expected_type is not None:
            expected_types = (
                expected_type if isinstance(expected_type, list) else [expected_type]
            )
            if not any(_json_type_matches(instance, value) for value in expected_types):
                errors.append(
                    f"{instance_path}: expected type {expected_type!r}, "
                    f"got {type(instance).__name__}"
                )
                return errors

        if "oneOf" in schema:
            branch_errors = [
                self._validate(
                    instance,
                    branch,
                    instance_path,
                    current_document,
                    current_schema_path,
                )
                for branch in schema["oneOf"]
            ]
            passing = sum(not value for value in branch_errors)
            if passing != 1:
                errors.append(
                    f"{instance_path}: oneOf matched {passing} branches, expected exactly 1"
                )
                if passing == 0:
                    for branch_index, branch_result in enumerate(branch_errors):
                        errors.extend(
                            f"{instance_path}: oneOf[{branch_index}] {message}"
                            for message in branch_result[:3]
                        )

        for sub_schema in schema.get("allOf", []):
            errors.extend(
                self._validate(
                    instance,
                    sub_schema,
                    instance_path,
                    current_document,
                    current_schema_path,
                )
            )

        if "if" in schema:
            condition_errors = self._validate(
                instance,
                schema["if"],
                instance_path,
                current_document,
                current_schema_path,
            )
            branch_name = "then" if not condition_errors else "else"
            if branch_name in schema:
                errors.extend(
                    self._validate(
                        instance,
                        schema[branch_name],
                        instance_path,
                        current_document,
                        current_schema_path,
                    )
                )

        if isinstance(instance, dict):
            required = schema.get("required", [])
            for key in required:
                if key not in instance:
                    errors.append(f"{instance_path}: missing required property {key!r}")

            properties = schema.get("properties", {})
            for key, property_schema in properties.items():
                if key in instance:
                    errors.extend(
                        self._validate(
                            instance[key],
                            property_schema,
                            f"{instance_path}.{key}",
                            current_document,
                            current_schema_path,
                        )
                    )

            if "additionalProperties" in schema:
                additional_schema = schema["additionalProperties"]
                for key in instance.keys() - properties.keys():
                    if additional_schema is False:
                        errors.append(
                            f"{instance_path}.{key}: additional property is not allowed"
                        )
                    elif additional_schema is not True:
                        errors.extend(
                            self._validate(
                                instance[key],
                                additional_schema,
                                f"{instance_path}.{key}",
                                current_document,
                                current_schema_path,
                            )
                        )

        if isinstance(instance, list):
            if "minItems" in schema and len(instance) < schema["minItems"]:
                errors.append(
                    f"{instance_path}: {len(instance)} items below minItems {schema['minItems']}"
                )
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                errors.append(
                    f"{instance_path}: {len(instance)} items above maxItems {schema['maxItems']}"
                )
            if schema.get("uniqueItems"):
                canonical = [
                    json.dumps(value, ensure_ascii=False, sort_keys=True) for value in instance
                ]
                if len(canonical) != len(set(canonical)):
                    errors.append(f"{instance_path}: array items are not unique")
            if "items" in schema:
                for index, value in enumerate(instance):
                    errors.extend(
                        self._validate(
                            value,
                            schema["items"],
                            f"{instance_path}[{index}]",
                            current_document,
                            current_schema_path,
                        )
                    )

        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < schema["minLength"]:
                errors.append(
                    f"{instance_path}: string shorter than minLength {schema['minLength']}"
                )
            if "pattern" in schema and re.search(schema["pattern"], instance) is None:
                errors.append(f"{instance_path}: string does not match pattern")
            if schema.get("format") == "date-time":
                try:
                    datetime.fromisoformat(instance.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{instance_path}: invalid date-time")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"{instance_path}: below minimum {schema['minimum']}")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"{instance_path}: above maximum {schema['maximum']}")
            if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
                errors.append(
                    f"{instance_path}: not above exclusiveMinimum {schema['exclusiveMinimum']}"
                )

        return errors


def validate_json_file(instance_path: Path, schema_path: Path) -> list[str]:
    with instance_path.open("r", encoding="utf-8") as handle:
        instance = json.load(handle)
    return SchemaRuntime(schema_path).validate(instance)
