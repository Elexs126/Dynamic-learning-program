#!/usr/bin/env python3
"""Audit canonical question-bank paths and unique-ID inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ID_PATTERN = re.compile(r"【唯一编号】[^`\n]*`([^`]+)`")
QUESTION_HEADING_PATTERN = re.compile(
    r"^#{3,6}\s+【((?:M[123]|408)-\d{2}-[CFA]-T\d{2})】[^\n]*$",
    re.MULTILINE,
)
IMAGE_PATTERN = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
METADATA_FIELDS = ("题型", "科目", "分值", "年份", "考点")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def markdown_inventory(path: Path) -> tuple[list[str], dict[str, int], int]:
    ids: list[str] = []
    field_counts = {field: 0 for field in METADATA_FIELDS}
    files = list(path.rglob("*.md"))
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        ids.extend(ID_PATTERN.findall(text))
        if file_path.name.lower() != "readme.md":
            for field in METADATA_FIELDS:
                field_counts[field] += text.count(f"【{field}】")
    return ids, field_counts, len(files)


def target_block_checks(path: Path) -> dict[str, Any]:
    checked = 0
    missing_body: list[str] = []
    marker_mismatches: list[str] = []
    metadata_issues: list[dict[str, Any]] = []
    missing_images: list[dict[str, str]] = []
    for file_path in sorted(path.rglob("*.md")):
        if file_path.name.lower() == "readme.md":
            continue
        text = file_path.read_text(encoding="utf-8")
        headings = list(QUESTION_HEADING_PATTERN.finditer(text))
        for index, heading in enumerate(headings):
            question_id = heading.group(1)
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            block = text[heading.start() : end]
            checked += 1
            markers = ID_PATTERN.findall(block)
            if markers != [question_id]:
                marker_mismatches.append(question_id)
            marker_position = block.find("【唯一编号】")
            body = block[heading.end() - heading.start() : marker_position].strip()
            if marker_position < 0 or not body:
                missing_body.append(question_id)
            counts = {
                field: block.count(f"【{field}】") for field in METADATA_FIELDS
            }
            bad_counts = {field: count for field, count in counts.items() if count != 1}
            if bad_counts:
                metadata_issues.append(
                    {"question_id": question_id, "field_counts": bad_counts}
                )
            for image_ref in IMAGE_PATTERN.findall(block):
                if re.match(r"^[a-z]+://", image_ref, re.IGNORECASE):
                    continue
                image_path = (file_path.parent / image_ref).resolve()
                if not image_path.is_file():
                    missing_images.append(
                        {
                            "question_id": question_id,
                            "image_ref": image_ref,
                        }
                    )
    return {
        "question_blocks_checked": checked,
        "missing_body_ids": missing_body,
        "marker_mismatch_ids": marker_mismatches,
        "metadata_issues": metadata_issues,
        "missing_image_refs": missing_images,
        "status": "PASS"
        if not (missing_body or marker_mismatches or metadata_issues or missing_images)
        else "FAIL",
    }


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest_map(path: Path) -> dict[str, str]:
    return {
        str(file_path.relative_to(path)): file_digest(file_path)
        for file_path in sorted(value for value in path.rglob("*") if value.is_file())
    }


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    manifest = load_json(args.manifest)
    errors: list[str] = []
    warnings: list[str] = []
    source_reports: list[dict[str, Any]] = []
    all_ids: list[str] = []
    ids_by_source: dict[str, set[str]] = {}

    for source in manifest.get("sources", []):
        source_id = source["source_id"]
        relative_path = source["canonical_path"]
        path = root / relative_path
        if not path.is_dir():
            errors.append(f"{source_id}: missing canonical directory {relative_path}")
            continue
        ids, field_counts, markdown_files = markdown_inventory(path)
        counts = Counter(ids)
        duplicates = sorted(key for key, count in counts.items() if count > 1)
        unique_ids = set(ids)
        expected = int(source["expected_records"])
        if len(ids) != expected:
            errors.append(
                f"{source_id}: found {len(ids)} ID markers, expected {expected}"
            )
        if len(unique_ids) != expected:
            errors.append(
                f"{source_id}: found {len(unique_ids)} unique IDs, expected {expected}"
            )
        if duplicates:
            errors.append(f"{source_id}: duplicate IDs inside canonical source")
        ids_by_source[source_id] = unique_ids
        all_ids.extend(ids)
        target_checks = (
            target_block_checks(path) if source["eligible_for_target_prior"] else None
        )
        if target_checks and target_checks["status"] != "PASS":
            errors.append(f"{source_id}: target question-block structural checks failed")
        source_reports.append(
            {
                "source_id": source_id,
                "canonical_path": relative_path,
                "markdown_files": markdown_files,
                "id_markers": len(ids),
                "unique_ids": len(unique_ids),
                "expected_records": expected,
                "duplicate_ids": duplicates,
                "metadata_field_counts": field_counts,
                "target_question_block_checks": target_checks,
            }
        )

    total_counts = Counter(all_ids)
    cross_source_duplicates = sorted(
        key for key, count in total_counts.items() if count > 1
    )
    unique_total = len(total_counts)
    expected_total = int(manifest["expected_unique_question_records"])
    if unique_total != expected_total:
        errors.append(f"canonical unique total {unique_total}, expected {expected_total}")
    if cross_source_duplicates:
        errors.append(
            f"canonical sources contain {len(cross_source_duplicates)} cross-source duplicate IDs"
        )

    target_prior_sum = sum(
        int(source["expected_records"])
        for source in manifest["sources"]
        if source["eligible_for_target_prior"]
    )
    if target_prior_sum != int(manifest["target_prior_eligible_records"]):
        errors.append("target-prior count derived from sources does not match manifest")
    core_l2_sum = sum(
        int(source["expected_records"])
        for source in manifest["sources"]
        if source["annotation_priority"] == "CORE_L2"
    )
    if core_l2_sum != int(manifest["core_l2_expected_records"]):
        errors.append("core-L2 count derived from sources does not match manifest")

    duplicate_tree_check: dict[str, Any] | None = None
    canonical_classic = root / "配套习题/408/408经典练习题"
    duplicate_classic = root / "delightful-salk/408经典练习题"
    if canonical_classic.is_dir() and duplicate_classic.is_dir():
        canonical_map = tree_digest_map(canonical_classic)
        duplicate_map = tree_digest_map(duplicate_classic)
        duplicate_tree_check = {
            "canonical_path": str(canonical_classic.relative_to(root)),
            "excluded_path": str(duplicate_classic.relative_to(root)),
            "identical": canonical_map == duplicate_map,
            "canonical_files": len(canonical_map),
            "excluded_files": len(duplicate_map),
        }
        if canonical_map != duplicate_map:
            errors.append("configured duplicate 408 classic trees are no longer identical")
    else:
        warnings.append("one of the duplicate 408 classic trees is absent")

    derived_check: dict[str, Any] | None = None
    selected_path = root / "考研数学一真题精选50题_23章节全覆盖.md"
    if selected_path.is_file():
        selected_ids = ID_PATTERN.findall(selected_path.read_text(encoding="utf-8"))
        math1_ids = ids_by_source.get("MATH1_PAST_PAPERS", set())
        extra_ids = sorted(set(selected_ids) - math1_ids)
        derived_check = {
            "path": str(selected_path.relative_to(root)),
            "id_markers": len(selected_ids),
            "unique_ids": len(set(selected_ids)),
            "all_ids_exist_in_math1_canonical": not extra_ids,
            "extra_ids": extra_ids,
        }
        if extra_ids:
            errors.append("50-question derived set contains IDs absent from canonical Math1")

    report = {
        "report_version": "repository-audit-v1.0.0",
        "audit_scope": "canonical ID inventory, per-source counts, duplicate-path identity, and derived-set ID containment",
        "project_root": str(root),
        "manifest": str(args.manifest),
        "canonical_id_markers": len(all_ids),
        "canonical_unique_ids": unique_total,
        "expected_unique_ids": expected_total,
        "cross_source_duplicate_ids": cross_source_duplicates,
        "target_prior_eligible_records": target_prior_sum,
        "core_l2_records": core_l2_sum,
        "sources": source_reports,
        "duplicate_tree_check": duplicate_tree_check,
        "derived_set_check": derived_check,
        "warning_count": len(warnings),
        "warnings": warnings,
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
        "limitations": [
            "PASS不等于题干/OCR/公式/图片/答案或原子化结构均正确。",
            "metadata_field_counts是按canonical文件统计的字段出现次数，不替代逐题语义审核。",
            "1277表示可进入目标统计的候选全集；FIXED_AUDIT/SEALED退役前仍须从Teacher可见TARGET_PRIOR中排除。"
        ],
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
