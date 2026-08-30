#!/usr/bin/env python3
"""Validate append-only attempts JSONL and minimum protocol semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from json_schema_runtime import SchemaRuntime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"line {line_number}: record must be an object")
            continue
        value["__line_number"] = line_number
        records.append(value)
    return records, errors


def validate_record(record: dict[str, Any], errors: list[str]) -> None:
    line_number = record["__line_number"]
    prefix = f"line {line_number} {record['attempt_id']}"
    attempted = parse_datetime(record["attempted_at"])
    verified = parse_datetime(record["verified_at"])
    if verified < attempted:
        errors.append(f"{prefix}: verified_at precedes attempted_at")
    if parse_datetime(record["next_review_at"]) <= attempted:
        errors.append(f"{prefix}: next_review_at must be later than attempted_at")
    if record["is_mixed"] and record["batch_id"] is None:
        errors.append(f"{prefix}: mixed attempt requires batch_id")
    if record["usage_role"] in {"FIXED_AUDIT", "SEALED"} and record["batch_id"] is None:
        errors.append(f"{prefix}: audit/sealed attempt requires batch_id")
    if record["attempt_kind"] == "fixed_audit" and record["usage_role"] != "FIXED_AUDIT":
        errors.append(f"{prefix}: fixed_audit kind requires FIXED_AUDIT role")
    if record["attempt_kind"] == "sealed_exam" and record["usage_role"] != "SEALED":
        errors.append(f"{prefix}: sealed_exam kind requires SEALED role")
    if not record["is_timed"] and record["dimensions"]["timed_fluency"] is not None:
        errors.append(f"{prefix}: untimed attempt cannot update timed_fluency")
    if record["dimensions"]["delayed_retention"] is not None and record["interval_hours"] is None:
        errors.append(f"{prefix}: delayed_retention requires interval_hours")
    if record["attempt_kind"] == "cold_test":
        if record["interval_hours"] is None or record["interval_hours"] < 48:
            errors.append(f"{prefix}: cold_test requires at least 48 hours interval")
        if record["highest_hint_level_used"] != "L0":
            errors.append(f"{prefix}: cold_test requires L0")
        if not record["is_unseen"]:
            errors.append(f"{prefix}: cold_test requires an unseen question")
        if not record["is_timed"]:
            errors.append(f"{prefix}: cold_test must be timed")
        if not record["is_mixed"]:
            errors.append(f"{prefix}: cold_test must be mixed")


def main() -> int:
    args = parse_args()
    records, errors = read_jsonl(args.log)
    runtime = SchemaRuntime(args.schema)
    schema_error_count = 0
    valid_records: list[dict[str, Any]] = []
    for record in records:
        line_number = record.pop("__line_number")
        schema_errors = runtime.validate(record)
        record["__line_number"] = line_number
        if schema_errors:
            schema_error_count += len(schema_errors)
            errors.extend(f"line {line_number}: schema: {message}" for message in schema_errors)
        else:
            valid_records.append(record)

    attempt_ids = [record["attempt_id"] for record in valid_records]
    if len(attempt_ids) != len(set(attempt_ids)):
        errors.append("attempt_id values must be unique")

    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in valid_records:
        validate_record(record, errors)
        by_question[record["question_id"]].append(record)
    for question_id, question_records in by_question.items():
        ordered = sorted(question_records, key=lambda item: parse_datetime(item["attempted_at"]))
        for repeated in ordered[1:]:
            if repeated["is_unseen"]:
                errors.append(
                    f"line {repeated['__line_number']} {repeated['attempt_id']}: "
                    f"repeated question {question_id} cannot remain unseen"
                )

    mixed_batches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in valid_records:
        if record["is_mixed"] and record["batch_id"] is not None:
            mixed_batches[record["batch_id"]].append(record)
    for batch_id, batch_records in mixed_batches.items():
        question_ids = {record["question_id"] for record in batch_records}
        ability_ids = {
            record["target_ability_id"]
            for record in batch_records
            if record["target_ability_id"] is not None
        }
        if len(question_ids) < 2:
            errors.append(f"mixed batch {batch_id}: requires at least two question_ids")
        if len(ability_ids) < 2:
            errors.append(f"mixed batch {batch_id}: requires at least two target_ability_ids")

    for record in valid_records:
        record.pop("__line_number", None)
    report = {
        "validator_version": "attempt-log-validator-v1.0.0",
        "log": str(args.log),
        "log_sha256": sha256_file(args.log),
        "schema": str(args.schema),
        "schema_sha256": sha256_file(args.schema),
        "record_count": len(records),
        "schema_error_count": schema_error_count,
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
        "derived_initial_state": "未接触" if not records else None
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
