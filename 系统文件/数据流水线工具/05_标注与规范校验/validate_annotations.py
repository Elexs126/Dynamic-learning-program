#!/usr/bin/env python3
"""Validate high-value structural and semantic rules for annotation bundles.

This validator uses only the Python standard library so it can run before a
JSON Schema package is installed. The JSON Schema remains the field contract;
this script adds cross-field checks that are easy to audit in code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from json_schema_runtime import validate_json_file


BUNDLE_VERSION = "question-annotations-bundle-v1.0.0"
RECORD_VERSION = "question-annotation-v1.0.0"
DEPTHS = {"L0", "L1", "L2", "L3"}
REVIEW_STATUSES = {"candidate", "verified", "needs_review", "not_applicable"}
CONFIDENCES = {"high", "medium", "low", "unknown"}
DIFFICULTIES = {"basic", "intermediate", "advanced", "very_advanced"}
QUESTION_TYPES = {"choice", "fill", "analytical"}
FORBIDDEN_KEYS = {
    "answer",
    "solution",
    "reference_answer",
    "reference_solution",
    "candidate_main_ability",
    "audited_main_ability",
    "data_role",
    "usage_role",
    "teaching_diagnosis",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        required=True,
        help="question_annotations_bundle.schema.json",
    )
    parser.add_argument("--report", type=Path, help="optional JSON report path")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def walk_keys(value: Any, path: str = "$") -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            findings.append((key, child_path))
            findings.extend(walk_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(walk_keys(child, f"{path}[{index}]"))
    return findings


def validate_field_map(
    value: Any, allowed: set[str], path: str, errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return
    for field, state in value.items():
        if not isinstance(field, str) or not field:
            errors.append(f"{path}: empty/non-string field name")
        if state not in allowed:
            errors.append(f"{path}.{field}: invalid value {state!r}")


def require_keys(value: Any, keys: set[str], path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return False
    missing = sorted(keys - value.keys())
    if missing:
        errors.append(f"{path}: missing keys {missing}")
        return False
    return True


def validate_record(record: Any, index: int, errors: list[str]) -> None:
    path = f"$.records[{index}]"
    required = {
        "schema_version",
        "question_id",
        "annotation_depth",
        "record_status",
        "l0",
        "l1",
        "l2",
        "l3",
        "review_flags",
    }
    if not require_keys(record, required, path, errors):
        return

    if record["schema_version"] != RECORD_VERSION:
        errors.append(f"{path}.schema_version: expected {RECORD_VERSION!r}")
    question_id = record["question_id"]
    if not isinstance(question_id, str) or not question_id:
        errors.append(f"{path}.question_id: expected non-empty string")
    depth = record["annotation_depth"]
    if depth not in DEPTHS:
        errors.append(f"{path}.annotation_depth: invalid {depth!r}")
    if record["record_status"] not in REVIEW_STATUSES:
        errors.append(f"{path}.record_status: invalid {record['record_status']!r}")
    if not isinstance(record["review_flags"], list):
        errors.append(f"{path}.review_flags: expected array")

    level_requirements = {
        "L0": {"l1": False, "l2": False, "l3": False},
        "L1": {"l1": True, "l2": False, "l3": False},
        "L2": {"l1": True, "l2": True, "l3": False},
        "L3": {"l1": True, "l2": True, "l3": True},
    }
    if depth in level_requirements:
        for level, should_exist in level_requirements[depth].items():
            exists = record[level] is not None
            if exists != should_exist:
                errors.append(
                    f"{path}.{level}: depth {depth} requires "
                    f"{'object' if should_exist else 'null'}"
                )

    l0 = record["l0"]
    l0_required = {
        "exam_track",
        "subject_area",
        "question_source",
        "source_reliability",
        "paper_id",
        "year",
        "question_number",
        "question_type",
        "original_points",
        "original_section",
        "source_file",
        "source_locator",
        "question_hash_sha256",
        "question_completeness",
        "locked",
        "review_status_by_field",
    }
    if require_keys(l0, l0_required, f"{path}.l0", errors):
        if l0["question_type"] not in QUESTION_TYPES:
            errors.append(f"{path}.l0.question_type: invalid {l0['question_type']!r}")
        if l0["locked"] is not True:
            errors.append(f"{path}.l0.locked: must be true")
        if Path(str(l0["source_file"])).is_absolute() or "\\" in str(l0["source_file"]):
            errors.append(f"{path}.l0.source_file: must be portable repo-relative path")
        validate_field_map(
            l0["review_status_by_field"],
            REVIEW_STATUSES,
            f"{path}.l0.review_status_by_field",
            errors,
        )

    l1 = record.get("l1")
    if isinstance(l1, dict):
        l1_required = {
            "official_scope_coarse",
            "label_provenance",
            "candidate_main_knowledge",
            "confidence_by_field",
            "duplicate_candidate",
            "review_status_by_field",
        }
        if require_keys(l1, l1_required, f"{path}.l1", errors):
            validate_field_map(
                l1["confidence_by_field"],
                CONFIDENCES,
                f"{path}.l1.confidence_by_field",
                errors,
            )
            validate_field_map(
                l1["review_status_by_field"],
                REVIEW_STATUSES,
                f"{path}.l1.review_status_by_field",
                errors,
            )

    l2 = record.get("l2")
    if isinstance(l2, dict):
        l2_required = {
            "main_knowledge",
            "assessed_construct",
            "secondary_knowledge",
            "primary_method",
            "prerequisites",
            "difficulty_band",
            "confidence_by_field",
            "review_status_by_field",
        }
        if require_keys(l2, l2_required, f"{path}.l2", errors):
            main = l2["main_knowledge"]
            if not isinstance(main, dict) or not main.get("id") or not main.get("name"):
                errors.append(f"{path}.l2.main_knowledge: exactly one id/name object required")
            secondary = l2["secondary_knowledge"]
            if not isinstance(secondary, list):
                errors.append(f"{path}.l2.secondary_knowledge: expected array")
            else:
                limit = 1 if l0.get("question_type") in {"choice", "fill"} else 2
                if len(secondary) > limit:
                    errors.append(
                        f"{path}.l2.secondary_knowledge: {len(secondary)} exceeds {limit}"
                    )
                secondary_ids = [
                    value.get("id") for value in secondary if isinstance(value, dict)
                ]
                if len(secondary_ids) != len(set(secondary_ids)):
                    errors.append(f"{path}.l2.secondary_knowledge: duplicate knowledge id")
                if isinstance(main, dict) and main.get("id") in secondary_ids:
                    errors.append(
                        f"{path}.l2.secondary_knowledge: main knowledge cannot repeat as secondary"
                    )
            if l2["difficulty_band"] not in DIFFICULTIES:
                errors.append(
                    f"{path}.l2.difficulty_band: invalid {l2['difficulty_band']!r}"
                )
            prerequisites = l2["prerequisites"]
            if require_keys(
                prerequisites,
                {"hard_prerequisite", "soft_prerequisite"},
                f"{path}.l2.prerequisites",
                errors,
            ):
                hard_ids = [
                    value.get("id")
                    for value in prerequisites["hard_prerequisite"]
                    if isinstance(value, dict)
                ]
                soft_ids = [
                    value.get("id")
                    for value in prerequisites["soft_prerequisite"]
                    if isinstance(value, dict)
                ]
                if len(hard_ids) != len(set(hard_ids)):
                    errors.append(f"{path}.l2.prerequisites: duplicate hard prerequisite")
                if len(soft_ids) != len(set(soft_ids)):
                    errors.append(f"{path}.l2.prerequisites: duplicate soft prerequisite")
                overlap = sorted(set(hard_ids) & set(soft_ids))
                if overlap:
                    errors.append(
                        f"{path}.l2.prerequisites: hard/soft overlap {overlap}"
                    )
            validate_field_map(
                l2["confidence_by_field"],
                CONFIDENCES,
                f"{path}.l2.confidence_by_field",
                errors,
            )
            validate_field_map(
                l2["review_status_by_field"],
                REVIEW_STATUSES,
                f"{path}.l2.review_status_by_field",
                errors,
            )

    l3 = record.get("l3")
    if isinstance(l3, dict):
        l3_required = {
            "score_units",
            "score_attribution",
            "evidence_steps",
            "alternative_methods",
            "inter_question_dependency",
            "isomorphic_relation",
            "confidence_by_field",
            "review_status_by_field",
        }
        if require_keys(l3, l3_required, f"{path}.l3", errors):
            units = l3["score_units"]
            if not isinstance(units, list) or not units:
                errors.append(f"{path}.l3.score_units: non-empty array required")
                unit_ids: set[str] = set()
            else:
                unit_ids = {str(unit.get("unit_id")) for unit in units if isinstance(unit, dict)}
                if len(unit_ids) != len(units):
                    errors.append(f"{path}.l3.score_units: duplicate/missing unit_id")
                known_points = [unit.get("points") for unit in units if unit.get("points") is not None]
                if any(not isinstance(value, (int, float)) or value < 0 for value in known_points):
                    errors.append(f"{path}.l3.score_units: invalid points")
                original_points = l0.get("original_points")
                if len(known_points) == len(units) and isinstance(original_points, (int, float)):
                    if sum(known_points) > original_points + 1e-9:
                        errors.append(
                            f"{path}.l3.score_units: point sum exceeds original_points"
                        )
            for group_name in ("score_attribution", "evidence_steps"):
                group = l3[group_name]
                if not isinstance(group, list) or not group:
                    errors.append(f"{path}.l3.{group_name}: non-empty array required")
                    continue
                for group_index, entry in enumerate(group):
                    unit_id = entry.get("unit_id") if isinstance(entry, dict) else None
                    if unit_id not in unit_ids:
                        errors.append(
                            f"{path}.l3.{group_name}[{group_index}].unit_id: unknown {unit_id!r}"
                        )
            dependency = l3["inter_question_dependency"]
            if isinstance(dependency, dict):
                for relation_index, relation in enumerate(dependency.get("relations", [])):
                    from_id = relation.get("from_question_id")
                    to_id = relation.get("to_question_id")
                    if from_id == to_id:
                        errors.append(
                            f"{path}.l3.inter_question_dependency.relations"
                            f"[{relation_index}]: endpoints must differ"
                        )
                    if question_id not in {from_id, to_id}:
                        errors.append(
                            f"{path}.l3.inter_question_dependency.relations"
                            f"[{relation_index}]: current question_id must be one endpoint"
                        )
            validate_field_map(
                l3["confidence_by_field"],
                CONFIDENCES,
                f"{path}.l3.confidence_by_field",
                errors,
            )
            validate_field_map(
                l3["review_status_by_field"],
                REVIEW_STATUSES,
                f"{path}.l3.review_status_by_field",
                errors,
            )

    for key, key_path in walk_keys(record, path):
        if key in FORBIDDEN_KEYS:
            errors.append(f"{key_path}: forbidden annotation key")

    if record.get("record_status") == "verified":
        non_verified: list[str] = []
        for level_name in ("l0", "l1", "l2", "l3"):
            level = record.get(level_name)
            if not isinstance(level, dict):
                continue
            for field, status in level.get("review_status_by_field", {}).items():
                if status not in {"verified", "not_applicable"}:
                    non_verified.append(f"{level_name}.{field}={status}")
        if non_verified:
            errors.append(
                f"{path}.record_status: verified conflicts with field states {non_verified}"
            )
        if record.get("review_flags"):
            errors.append(f"{path}.record_status: verified record cannot retain review_flags")
        migration = record.get("migration_metadata")
        if isinstance(migration, dict) and migration.get("unresolved"):
            errors.append(
                f"{path}.record_status: verified record cannot retain unresolved migration issues"
            )


def main() -> int:
    args = parse_args()
    schema_errors = validate_json_file(args.bundle, args.schema)
    errors: list[str] = [f"schema: {message}" for message in schema_errors]

    bundle = load_json(args.bundle)
    if not isinstance(bundle, dict):
        errors.append("$: expected object")
        records: list[Any] = []
    else:
        if bundle.get("schema_version") != BUNDLE_VERSION:
            errors.append(f"$.schema_version: expected {BUNDLE_VERSION!r}")
        records_value = bundle.get("records")
        if not isinstance(records_value, list):
            errors.append("$.records: expected array")
            records = []
        else:
            records = records_value
        if bundle.get("record_count") != len(records):
            errors.append("$.record_count does not equal records length")

    semantic_errors_before = len(errors)
    if not schema_errors:
        for index, record in enumerate(records):
            validate_record(record, index, errors)

    question_ids = [
        record.get("question_id") for record in records if isinstance(record, dict)
    ]
    if not schema_errors and len(question_ids) != len(set(question_ids)):
        errors.append("$.records: duplicate question_id values")

    report = {
        "validator_version": "annotation-validator-v1.1.0",
        "bundle": str(args.bundle),
        "schema": str(args.schema),
        "records": len(records),
        "unique_question_ids": len(set(question_ids)),
        "schema_error_count": len(schema_errors),
        "semantic_error_count": len(errors) - semantic_errors_before,
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
