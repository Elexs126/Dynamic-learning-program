#!/usr/bin/env python3
"""Validate usage-role bundles, including cross-event isolation rules."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from json_schema_runtime import validate_json_file


HIDDEN_ROLES = {"ADAPTIVE_DIAGNOSTIC", "FIXED_AUDIT", "SEALED"}
VISIBLE_OR_TRAINING_ROLES = {
    "TARGET_PRIOR",
    "STARTUP_TRAINING_ONLY",
    "TRAIN",
    "AUX_OFFPOLICY",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def active_roles_conflicts(
    entity_type: str, entity_id: str, events: list[dict[str, Any]], errors: list[str]
) -> None:
    active = [event for event in events if event["retired_at"] is None]
    roles = {event["role"] for event in active}
    hidden = roles & HIDDEN_ROLES
    visible = roles & VISIBLE_OR_TRAINING_ROLES
    if hidden and visible:
        errors.append(
            f"{entity_type} {entity_id}: active hidden roles {sorted(hidden)} "
            f"conflict with visible/training roles {sorted(visible)}"
        )
    if len(hidden) > 1:
        errors.append(
            f"{entity_type} {entity_id}: multiple active Evaluator roles {sorted(hidden)}"
        )
    if "TARGET_PRIOR" in roles and "AUX_OFFPOLICY" in roles:
        errors.append(
            f"{entity_type} {entity_id}: TARGET_PRIOR conflicts with AUX_OFFPOLICY"
        )
    active_role_counts: dict[str, int] = defaultdict(int)
    for event in active:
        active_role_counts[event["role"]] += 1
    duplicates = sorted(role for role, count in active_role_counts.items() if count > 1)
    if duplicates:
        errors.append(
            f"{entity_type} {entity_id}: duplicate active role events {duplicates}"
        )


def main() -> int:
    args = parse_args()
    schema_errors = validate_json_file(args.bundle, args.schema)
    errors = [f"schema: {message}" for message in schema_errors]
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))

    paper_events = bundle.get("paper_events", []) if isinstance(bundle, dict) else []
    question_events = bundle.get("question_events", []) if isinstance(bundle, dict) else []
    if not schema_errors:
        all_events = list(paper_events) + list(question_events)
        event_ids = [event["event_id"] for event in all_events]
        if len(event_ids) != len(set(event_ids)):
            errors.append("event_id values must be globally unique across paper/question events")
        known_event_ids = set(event_ids)
        for event in all_events:
            assigned = parse_datetime(event["assigned_at"])
            if event["retired_at"] is not None:
                retired = parse_datetime(event["retired_at"])
                if retired < assigned:
                    errors.append(
                        f"event {event['event_id']}: retired_at precedes assigned_at"
                    )
            supersedes = event.get("supersedes_event_id")
            if supersedes is not None:
                if supersedes == event["event_id"]:
                    errors.append(f"event {event['event_id']}: cannot supersede itself")
                elif supersedes not in known_event_ids:
                    errors.append(
                        f"event {event['event_id']}: unknown supersedes_event_id {supersedes}"
                    )

        papers: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in paper_events:
            papers[event["paper_id"]].append(event)
        questions: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in question_events:
            questions[event["question_id"]].append(event)
        for paper_id, events in papers.items():
            active_roles_conflicts("paper", paper_id, events, errors)
        for question_id, events in questions.items():
            active_roles_conflicts("question", question_id, events, errors)

        active_paper_roles = {
            paper_id: {event["role"] for event in events if event["retired_at"] is None}
            for paper_id, events in papers.items()
        }
        for event in question_events:
            if event["retired_at"] is not None:
                continue
            paper_id = event.get("paper_id")
            paper_roles = active_paper_roles.get(paper_id, set()) if paper_id else set()
            if event["role"] == "SEALED" and "SEALED" not in paper_roles:
                errors.append(
                    f"question {event['question_id']}: active SEALED requires active "
                    f"paper-level SEALED for {paper_id!r}"
                )
            if "SEALED" in paper_roles and event["role"] not in {"RAW", "SEALED"}:
                errors.append(
                    f"question {event['question_id']}: active role {event['role']} "
                    f"conflicts with sealed paper {paper_id}"
                )

    report = {
        "validator_version": "usage-role-validator-v1.0.0",
        "bundle": str(args.bundle),
        "schema": str(args.schema),
        "paper_events": len(paper_events),
        "question_events": len(question_events),
        "schema_error_count": len(schema_errors),
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
        "limitations": [
            "整卷SEALED一致性需要bundle包含该卷的全部题目事件；validator不能从角色文件单独证明题目清单完备。"
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
