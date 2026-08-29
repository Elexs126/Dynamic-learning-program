#!/usr/bin/env python3
"""Migrate the 50-question l3-v1 prototype without overwriting it.

The migration is deliberately conservative: absent L0/L1 facts are marked as
unknown or needs_review, prototype-only teaching fields are not promoted into
the formal annotation schema, and unresolved subquestion points stay null.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANNOTATION_SCHEMA_VERSION = "question-annotation-v1.0.0"
BUNDLE_SCHEMA_VERSION = "question-annotations-bundle-v1.0.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="legacy l3-v1 JSON")
    parser.add_argument("output", type=Path, help="new migration-candidate bundle")
    parser.add_argument("report", type=Path, help="machine-readable migration report")
    parser.add_argument(
        "--project-root",
        type=Path,
        help="repository root; defaults to the input file's parent",
    )
    parser.add_argument("--force", action="store_true", help="replace generated outputs")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def write_json_atomic(path: Path, value: Any, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to replace existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def flatten_flags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(flatten_flags(item))
        return result
    return [str(value)]


def unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def portable_source_file(raw_path: Any) -> str:
    value = str(raw_path or "考研数学一真题精选50题_23章节全覆盖.md")
    return value.replace("\\", "/").rsplit("/", 1)[-1]


def canonical_math1_source_file(year: int) -> str:
    return f"核心真题/数学一/{year}年全国硕士研究生招生考试数学一真题.md"


def canonical_question_hash(
    project_root: Path, relative_file: str, question_id: str
) -> str:
    source_path = project_root / relative_file
    text = source_path.read_text(encoding="utf-8")
    start_pattern = re.compile(
        rf"^#{{3,6}}\s+【{re.escape(question_id)}】[^\n]*$", re.MULTILINE
    )
    start_match = start_pattern.search(text)
    if start_match is None:
        raise ValueError(f"{question_id}: heading not found in {relative_file}")
    next_pattern = re.compile(
        r"^#{3,6}\s+【(?:M[123]|408)-[^】]+】[^\n]*$", re.MULTILINE
    )
    next_match = next_pattern.search(text, start_match.end())
    end = next_match.start() if next_match else len(text)
    block = text[start_match.start() : end].rstrip() + "\n"
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def subject_area_from_chapter(chapter: str) -> str:
    if "线性代数" in chapter:
        return "linear_algebra"
    if "概率" in chapter or "数理统计" in chapter:
        return "probability"
    if "高等数学" in chapter or "微积分" in chapter:
        return "calculus"
    raise ValueError(f"cannot infer subject_area from chapter: {chapter!r}")


def knowledge_ref(value: dict[str, Any]) -> dict[str, Any]:
    result = {"id": str(value["id"]), "name": str(value["name"])}
    for key in ("definition", "role", "confidence"):
        if value.get(key) not in (None, ""):
            result[key] = value[key]
    return result


def prerequisite_ref(value: dict[str, Any]) -> dict[str, Any]:
    result = {
        "id": str(value["prerequisite_id"]),
        "name": str(value["name"]),
    }
    confidence = value.get("confidence")
    if confidence in {"high", "medium", "low", "unknown"}:
        result["confidence"] = confidence
    return result


def method_ref(value: dict[str, Any]) -> dict[str, Any]:
    result = {"id": str(value["method_id"]), "name": str(value["name"])}
    confidence = value.get("confidence")
    if confidence in {"high", "medium", "low", "unknown"}:
        result["confidence"] = confidence
    return result


def normalized_confidence(value: Any) -> str:
    return value if value in {"high", "medium", "low", "unknown"} else "unknown"


def migrate_item(
    item: dict[str, Any],
    source_schema: str,
    migration_source_file: str,
    project_root: Path,
    migrated_at: str,
) -> tuple[dict[str, Any], dict[str, int]]:
    item_id = str(item["item_id"])
    facts = item["source_facts"]
    content = item["content"]
    methods_group = item["methods"]
    scoring = item["scoring"]
    structure = item["structure"]

    flags = unique_strings(
        flatten_flags(item.get("review_flags"))
        + flatten_flags(content.get("review_flags"))
        + flatten_flags(methods_group.get("review_flags"))
        + flatten_flags(scoring.get("review_flags"))
        + flatten_flags(structure.get("review_flags"))
        + flatten_flags(item.get("teaching_diagnosis", {}).get("review_flags"))
    )
    completeness_keywords = (
        "OCR",
        "排版",
        "公式",
        "符号",
        "题干",
        "选项",
        "配图",
        "图示",
        "图片",
        "缺失",
        "不清",
    )
    completeness_flags = [
        flag for flag in flags if any(keyword in flag for keyword in completeness_keywords)
    ]

    old_scope = content.get("official_scope") or {}
    precise_scope = str(old_scope.get("path") or facts.get("chapter") or "").strip()
    scope_parts = [part.strip() for part in precise_scope.split(">") if part.strip()]
    coarse_scope = " > ".join(scope_parts[:2]) if scope_parts else str(facts["chapter"])

    main_knowledge = knowledge_ref(content["main_knowledge"])
    secondary_knowledge = [
        knowledge_ref(value) for value in content.get("secondary_knowledge", [])
    ]
    secondary_ids = {value["id"] for value in secondary_knowledge}

    legacy_methods = list(methods_group.get("methods", []))
    primary_candidates = [
        value for value in legacy_methods if value.get("role") == "solution_invariant"
    ]
    if not primary_candidates:
        primary_candidates = legacy_methods[:1]
    if not primary_candidates:
        raise ValueError(f"{item_id}: no primary method candidate")
    primary_legacy = primary_candidates[0]
    alternative_legacy = [value for value in legacy_methods if value is not primary_legacy]

    hard_prerequisites: list[dict[str, Any]] = []
    soft_prerequisites: list[dict[str, Any]] = []
    for prerequisite in methods_group.get("prerequisites", []):
        converted = prerequisite_ref(prerequisite)
        if prerequisite.get("necessity") == "hard":
            hard_prerequisites.append(converted)
        elif prerequisite.get("necessity") == "soft":
            soft_prerequisites.append(converted)
        else:
            raise ValueError(
                f"{item_id}: unsupported prerequisite necessity "
                f"{prerequisite.get('necessity')!r}"
            )

    old_difficulty = structure.get("difficulty_band")
    difficulty_band = (
        "very_advanced" if old_difficulty == "highly_integrated" else old_difficulty
    )
    if difficulty_band not in {"basic", "intermediate", "advanced", "very_advanced"}:
        raise ValueError(f"{item_id}: unsupported difficulty {old_difficulty!r}")

    score_units: list[dict[str, Any]] = []
    score_attribution: list[dict[str, Any]] = []
    evidence_steps: list[dict[str, Any]] = []
    for unit in scoring.get("score_units", []):
        unit_id = str(unit["unit_id"])
        point_status = unit.get("point_status")
        if point_status not in {"explicit_total_single_unit", "unresolved", "explicit"}:
            raise ValueError(f"{item_id}: unsupported point_status {point_status!r}")
        target_ids = [str(value) for value in unit.get("target_knowledge_ids", [])]
        target_set = set(target_ids)
        if target_set == {main_knowledge["id"]}:
            category = "main_knowledge"
        elif target_set and target_set.issubset(secondary_ids):
            category = "secondary_knowledge"
        elif main_knowledge["id"] in target_set and len(target_set) > 1:
            category = "integrated_target"
        else:
            category = "undetermined"

        confidence = normalized_confidence(unit.get("confidence"))
        operation = str(unit.get("operation") or "旧记录未提供评分操作摘要")
        evidence_anchor = str(unit.get("evidence_anchor") or "旧记录未提供证据位置")
        score_units.append(
            {
                "unit_id": unit_id,
                "points": unit.get("points"),
                "point_status": point_status,
                "description": operation,
                "source_evidence": evidence_anchor,
                "confidence": confidence,
            }
        )
        score_attribution.append(
            {
                "unit_id": unit_id,
                "category": category,
                "target_knowledge_ids": target_ids,
                "status": "needs_review" if category == "undetermined" else "candidate",
            }
        )
        evidence_steps.append(
            {"unit_id": unit_id, "steps": [operation], "basis": evidence_anchor}
        )

    dependency_note = str(scoring.get("dependency_notes") or "").strip()
    if dependency_note in {"", "无", "none", "None"}:
        dependency_note = ""

    isomorphic_cluster = str(structure.get("isomorphic_cluster") or "").strip()
    isomorphic_relation = None
    if isomorphic_cluster:
        isomorphic_relation = {
            "cluster_id": f"LEGACY::{isomorphic_cluster}",
            "structural_invariant": None,
            "transfer_axis": [],
            "related_question_ids": [],
            "status": "needs_review",
        }

    unresolved = [
        "旧 prototype 未记录真实 L1 候选历史；本记录由 L2 反向回填，仅作迁移候选。",
        "原始题目来源可靠度尚未逐源核对，保持 unknown。",
        "未执行全库 duplicate_candidate 比对。",
        "canonical knowledge dictionary 尚未独立冻结。",
        "旧 isomorphic_cluster 缺 structural_invariant、transfer_axis 和关联题 ID。",
    ]
    if len(score_units) > 1:
        unresolved.append(
            "该题含多个评分单元，仍需结构 QA 决定是否拆成独立 question_id；未知子分值保持 null。"
        )
    if dependency_note:
        unresolved.append(
            "旧 dependency_notes 未提供可靠的 from/to unit ID，原文保留待复核。"
        )
    if flags:
        unresolved.append("旧 QA review_flags 尚未全部人工回看原卷。")

    question_type = str(facts["question_type"])
    year = int(facts["year"])
    canonical_source_file = canonical_math1_source_file(year)
    question_hash = canonical_question_hash(
        project_root, canonical_source_file, item_id
    )
    scope_confidence = normalized_confidence(old_scope.get("confidence"))
    method_confidence = normalized_confidence(primary_legacy.get("confidence"))
    score_confidence_values = {
        normalized_confidence(unit.get("confidence")) for unit in scoring["score_units"]
    }
    score_confidence = (
        next(iter(score_confidence_values))
        if len(score_confidence_values) == 1
        else "unknown"
    )

    record = {
        "schema_version": ANNOTATION_SCHEMA_VERSION,
        "question_id": item_id,
        "annotation_depth": "L3",
        "record_status": "needs_review",
        "l0": {
            "exam_track": "MATH1",
            "subject_area": subject_area_from_chapter(str(facts["chapter"])),
            "question_source": "数学一真题（项目整理版）",
            "source_reliability": "unknown",
            "paper_id": f"M1-{year}",
            "year": year,
            "question_number": int(facts["original_question_number"]),
            "question_type": question_type,
            "original_points": facts.get("points"),
            "original_section": str(facts["chapter"]),
            "source_file": canonical_source_file,
            "source_locator": item_id,
            "question_hash_sha256": question_hash,
            "question_completeness": "needs_review"
            if completeness_flags
            else "complete",
            "locked": True,
            "review_status_by_field": {
                "exam_track": "verified",
                "subject_area": "candidate",
                "question_source": "candidate",
                "source_reliability": "needs_review",
                "paper_id": "verified",
                "year": "verified",
                "question_number": "verified",
                "question_type": "verified",
                "original_points": "verified",
                "original_section": "verified",
                "source_file": "verified",
                "source_locator": "verified",
                "question_hash_sha256": "verified",
                "question_completeness": "needs_review"
                if completeness_flags
                else "candidate",
            },
        },
        "l1": {
            "official_scope_coarse": coarse_scope,
            "official_scope_precise": precise_scope,
            "label_provenance": [
                "question_semantics",
                "ai_inference",
                "legacy_migration",
            ],
            "candidate_main_knowledge": main_knowledge,
            "confidence_by_field": {
                "official_scope_coarse": scope_confidence,
                "official_scope_precise": scope_confidence,
                "label_provenance": "unknown",
                "candidate_main_knowledge": "unknown",
                "duplicate_candidate": "unknown",
            },
            "duplicate_candidate": {
                "is_candidate": None,
                "possible_duplicate_ids": [],
                "basis": None,
                "status": "needs_review",
            },
            "review_status_by_field": {
                "official_scope_coarse": "candidate",
                "official_scope_precise": "candidate",
                "label_provenance": "candidate",
                "candidate_main_knowledge": "candidate",
                "duplicate_candidate": "needs_review",
            },
        },
        "l2": {
            "main_knowledge": main_knowledge,
            "assessed_construct": str(content["assessed_construct"]),
            "secondary_knowledge": secondary_knowledge,
            "primary_method": method_ref(primary_legacy),
            "prerequisites": {
                "hard_prerequisite": hard_prerequisites,
                "soft_prerequisite": soft_prerequisites,
            },
            "difficulty_band": difficulty_band,
            "confidence_by_field": {
                "main_knowledge": "unknown",
                "assessed_construct": "unknown",
                "secondary_knowledge": "unknown",
                "primary_method": method_confidence,
                "prerequisites": "unknown",
                "difficulty_band": "unknown",
            },
            "review_status_by_field": {
                "main_knowledge": "candidate",
                "assessed_construct": "candidate",
                "secondary_knowledge": "candidate",
                "primary_method": "candidate",
                "prerequisites": "candidate",
                "difficulty_band": "candidate",
            },
        },
        "l3": {
            "score_units": score_units,
            "score_attribution": score_attribution,
            "evidence_steps": evidence_steps,
            "alternative_methods": [method_ref(value) for value in alternative_legacy],
            "inter_question_dependency": {
                "relations": [],
                "unresolved_legacy_note": dependency_note or None,
            },
            "isomorphic_relation": isomorphic_relation,
            "confidence_by_field": {
                "score_units": score_confidence,
                "score_attribution": "unknown",
                "evidence_steps": score_confidence,
                "alternative_methods": "unknown",
                "inter_question_dependency": "unknown",
                "isomorphic_relation": "unknown",
            },
            "review_status_by_field": {
                "score_units": "needs_review"
                if any(unit["points"] is None for unit in score_units)
                else "candidate",
                "score_attribution": "candidate",
                "evidence_steps": "candidate",
                "alternative_methods": "candidate",
                "inter_question_dependency": "needs_review"
                if dependency_note
                else "not_applicable",
                "isomorphic_relation": "needs_review"
                if isomorphic_relation
                else "not_applicable",
            },
        },
        "review_flags": flags,
        "migration_metadata": {
            "source_schema_version": source_schema,
            "source_item_id": item_id,
            "migrated_at": migrated_at,
            "transformations": [
                "item_id -> question_id",
                f"迁移输入 {migration_source_file} 重链到 canonical 文件 {canonical_source_file}",
                "official_scope.path -> official_scope_coarse/official_scope_precise",
                "content.main_knowledge -> L1 candidate_main_knowledge + L2 main_knowledge",
                "methods.solution_invariant -> L2 primary_method",
                "methods.valid_method -> L3 alternative_methods",
                "prerequisite necessity hard/soft -> hard_prerequisite/soft_prerequisite",
                "score_units.target_knowledge_ids -> L3 score_attribution",
                "isomorphic_cluster -> needs_review isomorphic_relation candidate",
                "prototype teaching_diagnosis/structure extensions excluded from core schema",
            ]
            + (["difficulty highly_integrated -> very_advanced"] if old_difficulty == "highly_integrated" else []),
            "unresolved": unresolved,
        },
    }

    counters = {
        "multi_score_unit": int(len(score_units) > 1),
        "unresolved_points": int(any(unit["points"] is None for unit in score_units)),
        "difficulty_remap": int(old_difficulty == "highly_integrated"),
        "review_flagged": int(bool(flags)),
        "completeness_flagged": int(bool(completeness_flags)),
        "dependency_note_unresolved": int(bool(dependency_note)),
        "teaching_diagnosis_excluded": int("teaching_diagnosis" in item),
        "canonical_source_relinked": 1,
    }
    return record, counters


def main() -> int:
    args = parse_args()
    legacy = load_json(args.input)
    if legacy.get("schema_version") != "l3-v1":
        raise ValueError(
            f"unsupported legacy schema_version: {legacy.get('schema_version')!r}"
        )
    items = legacy.get("items")
    if not isinstance(items, list):
        raise ValueError("legacy file has no items array")

    migrated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    migration_source_file = portable_source_file(legacy.get("source_file"))
    project_root = (args.project_root or args.input.parent).resolve()
    records: list[dict[str, Any]] = []
    totals = {
        "multi_score_unit": 0,
        "unresolved_points": 0,
        "difficulty_remap": 0,
        "review_flagged": 0,
        "completeness_flagged": 0,
        "dependency_note_unresolved": 0,
        "teaching_diagnosis_excluded": 0,
        "canonical_source_relinked": 0,
    }
    for item in items:
        record, counters = migrate_item(
            item,
            str(legacy["schema_version"]),
            migration_source_file,
            project_root,
            migrated_at,
        )
        records.append(record)
        for key, value in counters.items():
            totals[key] += value

    question_ids = [record["question_id"] for record in records]
    if len(question_ids) != len(set(question_ids)):
        raise ValueError("migration produced duplicate question_id values")

    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "generated_at": migrated_at,
        "source_file": args.input.name,
        "source_schema_version": legacy["schema_version"],
        "record_count": len(records),
        "records": records,
    }
    report = {
        "report_version": "l3-v1-migration-report-v1.0.0",
        "generated_at": migrated_at,
        "input": str(args.input),
        "output": str(args.output),
        "input_schema_version": legacy["schema_version"],
        "output_record_schema_version": ANNOTATION_SCHEMA_VERSION,
        "input_items": len(items),
        "output_records": len(records),
        "unique_question_ids": len(set(question_ids)),
        "counters": totals,
        "global_decisions": [
            "旧文件只读保留，不覆盖。",
            "全部迁移记录保持 needs_review，不把 prototype QA 等同于最新版 schema 审核。",
            "L1 由旧 L2 反向回填并标记 legacy_migration。",
            "未知来源可靠度保持 unknown。",
            "未知子题分值保持 null，不自动拆题或编分。",
            "prototype 教学诊断与扩展结构字段不进入正式核心 annotation。",
            "50题派生精选来源已重链到对应 canonical 年份卷，并保存题块 SHA-256。",
            "只有题干、公式、符号、选项、配图等摄取风险影响 question_completeness；纯评分不确定性不影响。",
        ],
    }

    write_json_atomic(args.output, bundle, args.force)
    write_json_atomic(args.report, report, args.force)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "report": str(args.report),
                "records": len(records),
                "counters": totals,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
