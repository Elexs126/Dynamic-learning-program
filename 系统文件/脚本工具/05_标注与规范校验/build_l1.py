#!/usr/bin/env python3
"""Build and verify a conservative, offline L0/L1 annotation snapshot.

Only canonical sources are scanned. No model/API calls, answer export, role
assignment, atomic-question splitting, or promotion of legacy tags to L2.
Unchanged inputs reuse a verified snapshot; changed inputs require a new path.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

VERSION = "l1-builder-v1.0.0"
MANIFEST = "系统文件/系统配置/canonical_sources_v1.json"
SCOPE_FILE = "系统文件/考纲与教材映射/大纲范围/json/syllabus_scope_v0.json"
TOOL_DIR = "系统文件/脚本工具/05_标注与规范校验"
SCHEMA = "系统文件/数据规范/question_annotations_bundle.schema.json"
RULE_FILE = Path(__file__).with_name("l1_scope_rules_v1.json")
MARKER = re.compile(r"【唯一编号】[^`\n]*`([^`]+)`")
HEADING = re.compile(r"^#{3,6}\s+【([^】\n]+)】[^\n]*$", re.M)
METADATA = re.compile(r"^>\s*\*\*【([^】\n]+)】\*\*\s*(.*)$", re.M)
ALLOWED_META = {"题型", "科目", "课程", "专题", "章节", "知识点", "分值", "年份", "考点"}
EXAM_ID = re.compile(r"^(M[123]|408)-(\d{2})-([CFA])-T(\d+)$")
SUBJECTS = {
    "calculus": "高等数学", "linear_algebra": "线性代数",
    "probability": "概率论与数理统计", "data_structure": "数据结构",
    "computer_organization": "计算机组成原理", "operating_system": "操作系统",
    "computer_network": "计算机网络",
}
TRACKS = {"MATH1": "数学一", "MATH2": "数学二", "MATH3": "数学三", "CS408": "408"}
SUBJECT_CODES = {"GS": "calculus", "XD": "linear_algebra", "GL": "probability",
                 "DS": "data_structure", "CO": "computer_organization",
                 "OS": "operating_system", "CN": "computer_network"}
TYPES = {"C": "choice", "F": "fill", "A": "analytical"}
TYPE_NAMES = {"选择题": "choice", "填空题": "fill", "解答题": "analytical", "综合题": "analytical", "综合应用题": "analytical"}
L1_FIELDS = ("official_scope_coarse", "label_provenance", "candidate_main_knowledge", "duplicate_candidate")
LIMITATIONS = [
    "全量L1指候选元数据视图，不表示语义审核、OCR校对或L2完成；本次未调用外部API。",
    "沿用整题ID，不自动拆分小问；原题未提供的分值保持null。",
    "CANDIDATE_前缀只是可复用候选引用，不是正式知识词典；章节代理候选不等于细知识点。",
    "未命中指纹时重复状态为null；未进行近似改写或同构分析，不证明没有重复。",
    "图片只能机械核对文件存在性和内容哈希；PASS不等于公式、图示、答案正确。",
    "未产生角色历史、作答、能力认证或正式考频；隐藏测评继续受既有隔离规则约束。",
    "MATH2/MATH3借用数学一课程骨架作路由，不表示它们与数学一考纲相同或可用于目标考频。",
]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    return digest(Path(path).read_bytes())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fail(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, relative):
    p = Path(relative)
    fail(not p.is_absolute() and ".." not in p.parts and "\\" not in relative, "Non-portable source path")
    resolved = (root / p).resolve()
    fail(resolved.is_relative_to(root), "Source path escapes project")
    return resolved


def canonical_files(root, manifest):
    result = []
    seen = set()
    for source in manifest["sources"]:
        folder = inside(root, source["canonical_path"])
        fail(folder.is_dir(), f"Missing source directory: {source['source_id']}")
        for path in sorted(folder.rglob("*.md")):
            fail(path.resolve().is_relative_to(root), "Canonical symlink escapes project")
            rel = path.relative_to(root).as_posix()
            fail(rel not in seen, "Overlapping canonical source directories")
            seen.add(rel)
            result.append((source, path))
    return result


def input_hashes(root, files):
    required = [MANIFEST, SCOPE_FILE, SCHEMA, "系统文件/数据规范/question_annotation.schema.json",
                "系统文件/数据规范/标签说明.md", "系统文件/数据规范/README.md", "完整执行协议.md", "启动合同.md",
                f"{TOOL_DIR}/validate_annotations.py", f"{TOOL_DIR}/json_schema_runtime.py"]
    result = {r: file_hash(inside(root, r)) for r in required}
    result.update({p.relative_to(root).as_posix(): file_hash(p) for _, p in files})
    result["@builder"] = file_hash(Path(__file__))
    result["@rules"] = file_hash(RULE_FILE)
    return dict(sorted(result.items()))


def parse_file(text, source_file):
    """Use the same next-question boundary and rstrip+LF hash as migrate_l3_v1."""
    markers = MARKER.findall(text)
    fail(len(markers) == len(set(markers)), f"Repeated ID marker in {source_file}")
    marker_ids = set(markers)
    headings = [h for h in HEADING.finditer(text) if h.group(1) in marker_ids]
    fail(len(headings) == len(markers), f"Unmatched ID or heading in {source_file}")
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), "")
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[heading.start():end].rstrip() + "\n"
        qid = heading.group(1)
        fail(MARKER.findall(block) == [qid], f"Heading/marker mismatch in {source_file}")
        marker_start = MARKER.search(block).start()
        body_end = block.rfind("\n", 0, marker_start) + 1
        # A metadata line starts after the statement. Never inspect or copy answer sections.
        body = block[heading.end() - heading.start():body_end].strip()
        body = re.split(r"\*\*【(?:参考答案|答案|解析|解答)】", body, maxsplit=1)[0].strip()
        meta = {}
        for m in METADATA.finditer(block):
            key = m.group(1)
            if key in ALLOWED_META:
                fail(key not in meta, f"Repeated metadata field {key} in {source_file}")
                meta[key] = m.group(2).strip()
        yield {"question_id": qid, "block_hash": digest(block.encode()), "body": body,
               "metadata": meta, "heading": heading.group(0), "title": title,
               "line_start": text.count("\n", 0, heading.start()) + 1,
               "line_end": text.count("\n", 0, end) + (not text[:end].endswith("\n"))}


def subject_for(qid, meta, source_file):
    """Prefer explicit course metadata; reject conflicting course/ID evidence."""
    evidence = []
    for key in ("课程", "科目"):
        value = meta.get(key, "").replace("微积分", "高等数学")
        hits = [s for s, name in SUBJECTS.items() if name in value]
        evidence.extend(hits)
    code = re.search(r"-(GS|XD|GL|DS|CO|OS|CN)(?=\d|-)" , qid)
    if code:
        evidence.append(SUBJECT_CODES[code.group(1)])
    if not evidence:
        evidence = [s for s, name in SUBJECTS.items() if name in source_file]
    fail(len(set(evidence)) == 1, f"Missing/conflicting subject metadata in {source_file}")
    return evidence[0]


def infer_type(qid, meta, body, title):
    explicit = meta.get("题型")
    by_meta = TYPE_NAMES.get(explicit)
    exam = EXAM_ID.fullmatch(qid)
    code = exam.group(3) if exam else None
    wd = re.match(r"WD-[A-Z]+-([CA])-", qid)
    if wd:
        code = wd.group(1)
    by_id = TYPES.get(code)
    fail(not explicit or by_meta is not None, "Unknown explicit question type")
    if by_meta and by_id and by_meta != by_id:
        return by_id, "needs_review", "id_metadata_conflict_id_candidate_retained"
    if by_meta or by_id:
        return by_meta or by_id, "verified", "explicit_metadata_or_id"
    if "选择题" in title and "解答" not in title:
        return "choice", "verified", "source_title"
    options = [bool(re.search(rf"(?:[（(]{c}[）)]|(?<![A-Za-z]){c}[.．、:：)）])", body)) for c in "ABCD"]
    if all(options):
        return "choice", "verified", "four_option_markers"
    if re.search(r"填空|_{3,}|\\(?:underline|underbrace)\s*\{\s*\}|[＿]{2,}", body):
        return "fill", "verified", "blank_marker"
    return "analytical", "verified", "no_explicit_type_structural_fallback"


def route_scope(subject, label, scopes, rules):
    if re.match(r"第\d+[章讲]", label) and " · " in label:
        # A book's chapter is stronger coarse-routing evidence than incidental
        # terms in a subsection such as '主存储器与CPU的连接'.
        chapter = label.split(" · ", 1)[0]
        chapter_route = route_scope(subject, chapter, scopes, rules)
        if chapter_route[3] == "candidate":
            return chapter_route
    hits = [sid for sid, pattern in rules["rules"][subject] if re.search(pattern, label, re.I)]
    hits = sorted(set(hits))
    for sid in hits:
        fail(sid in scopes and scopes[sid]["subject_area"] == subject, "Invalid routing rule scope")
    # Broad compound index heading can be followed by an explicit narrower topic.
    if label.startswith("参数估计与假设检验、"):
        tail = label.split("、", 1)[1]
        hits = sorted({sid for sid, pattern in rules["rules"][subject] if re.search(pattern, tail, re.I)})
    if subject == "linear_algebra" and len(hits) > 1 and hits == ["SCOPE_M1_LA_02", "SCOPE_M1_LA_05"]:
        # Feature values/vectors are a designated syllabus chapter, although also matrices.
        hits = ["SCOPE_M1_LA_05"]
    if subject == "data_structure" and re.search("二叉排序树|平衡二叉树", label):
        hits = [sid for sid in hits if sid != "SCOPE_408_DS_04"]
    if subject == "probability" and re.search("多维|二维", label) and "SCOPE_M1_PROB_03" in hits:
        hits = [sid for sid in hits if sid != "SCOPE_M1_PROB_02"]
    prefix = ("数学一" if subject in {"calculus", "linear_algebra", "probability"} else "408") + " > " + SUBJECTS[subject]
    if len(hits) == 1:
        return prefix + " > " + scopes[hits[0]]["scope_name"], hits, "medium", "candidate"
    return prefix, hits, "low" if hits else "unknown", "needs_review"


def image_fingerprint(root, source_file, body, assets):
    """Keep formulas/data; replace only image references with content digests."""
    issues = []
    image_count = 0
    def replace(match):
        nonlocal image_count
        image_count += 1
        ref = match.group(1).strip().strip("<>")
        parsed = urlsplit(ref)
        if parsed.scheme or parsed.netloc:
            issues.append("REMOTE_IMAGE_UNVERIFIED")
            return "[unresolved image]"
        # An optional Markdown title is not part of the image's filename.
        ref = re.split(r'\s+["\']', unquote(parsed.path), maxsplit=1)[0]
        path = (root / source_file).parent / ref
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            issues.append("IMAGE_OUTSIDE_PROJECT")
            return "[unresolved image]"
        key = resolved.relative_to(root).as_posix()
        value = file_hash(resolved) if resolved.is_file() else None
        assets[key] = value
        if value is None:
            issues.append("MISSING_IMAGE")
            return "[unresolved image]"
        return f"[image sha256:{value}]"
    normalized = re.sub(r"!\[[^\]\n]*\]\(([^)\n]+)\)", replace, body)
    # Unsupported HTML/reference images should never create false duplicate candidates.
    if re.search(r"<img\b|!\[[^\]]*\]\[", normalized, re.I):
        issues.append("UNSUPPORTED_IMAGE_REFERENCE")
    normalized = re.sub(r"^\s*---+\s*$", "", normalized, flags=re.M).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    if not normalized or len(normalized) < 24:
        issues.append("SHORT_OR_EMPTY_STEM")
    if "\ufffd" in body or re.search(r"[\ue000-\uf8ff]", body):
        issues.append("OCR_SUSPICIOUS_CHARACTERS")
    # Do not normalize mathematical symbols, case, numbers, or variable names.
    fp = digest(normalized.encode()) if not issues else None
    return fp, sorted(set(issues)), image_count


def make_record(root, source, path, item, scopes, rules, assets):
    rel = path.relative_to(root).as_posix()
    qid, meta = item["question_id"], item["metadata"]
    subject = subject_for(qid, meta, rel)
    track = source["exam_track"]
    exam = EXAM_ID.fullmatch(qid)
    qtype, type_status, type_basis = infer_type(qid, meta, item["body"], item["title"])
    year = 2000 + int(exam.group(2)) if exam else "not_applicable"
    if exam:
        expected_track = {"M1": "MATH1", "M2": "MATH2", "M3": "MATH3", "408": "CS408"}[exam.group(1)]
        fail(track == expected_track, "Track/ID conflict")
        fail(meta.get("年份") == f"{year}年" and str(year) in path.name, "Year metadata/ID/file conflict")
    points = None
    if "分值" in meta:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*分(?:\s*\(各小问:\s*([\d, ]+)分\))?", meta["分值"])
        fail(m is not None and float(m.group(1)) > 0, "Invalid source points")
        points = float(m.group(1))
        if m.group(2):
            fail(sum(int(x.strip()) for x in m.group(2).split(",")) == points, "Subquestion points disagree with source total")
        if points.is_integer():
            points = int(points)
    number = "T" + exam.group(4) if exam else qid.rsplit("-", 1)[-1]
    section = meta.get("章节") or meta.get("专题") or meta.get("知识点") or meta.get("题型") or ""
    original_section = item["title"] + (" > " + section if section else "")
    paper_id = f"{exam.group(1)}-{year}" if exam else "SOURCE-" + source["source_id"] + "-" + digest(rel.encode())[:16]
    fp, quality_flags, image_count = image_fingerprint(root, rel, item["body"], assets)
    completeness = "incomplete" if not item["body"] or "MISSING_IMAGE" in quality_flags else "needs_review"
    l0 = {"exam_track": track, "subject_area": subject, "question_source": item["title"],
          "source_reliability": "unknown", "paper_id": paper_id, "year": year,
          "question_number": number, "question_type": qtype, "original_points": points,
          "original_section": original_section, "source_file": rel,
          "source_locator": qid, "question_hash_sha256": item["block_hash"],
          "question_completeness": completeness, "locked": True}
    statuses = {key: "verified" for key in l0 if key != "locked"}
    statuses.update(source_reliability="needs_review", question_completeness="needs_review", question_type=type_status)
    if not exam:
        statuses["year"] = "not_applicable"
        statuses["original_points"] = "not_applicable"
    elif points is None:
        statuses["original_points"] = "needs_review"
    l0["review_status_by_field"] = statuses
    label_key = next((k for k in ("考点", "知识点", "章节", "专题") if meta.get(k)), None)
    # Retain actual source evidence; do not fill the schema with invented knowledge.
    fail(label_key is not None, f"No candidate-label evidence in {rel}; cannot claim L1")
    label = meta[label_key]
    generic_label = label in {"考点综合", "综合", "暂无", "未知", "待补充"}
    scope_path, scope_ids, scope_confidence, scope_status = route_scope(subject, label, scopes, rules)
    proxy = label_key in {"章节", "专题"}
    role = "unresolved_source_label" if generic_label else "chapter_proxy" if proxy else "unreviewed_source_label"
    knowledge_confidence = "unknown" if generic_label else "low" if proxy else "medium"
    candidate_id = "CANDIDATE_" + subject.upper() + "_" + digest((subject + "\0" + label).encode())[:16]
    flags = ["SEMANTIC_COMPLETENESS_UNREVIEWED", "SOURCE_RELIABILITY_UNREVIEWED", "LEGACY_LABEL_UNVERIFIED"]
    if proxy:
        flags.append("CHAPTER_PROXY_NOT_FINE_KNOWLEDGE")
    if scope_status == "needs_review":
        flags.append("SCOPE_AMBIGUOUS" if scope_ids else "SCOPE_UNMAPPED")
    if track in {"MATH2", "MATH3"}:
        flags.append("AUX_TRACK_ROUTED_TO_MATH1_SKELETON_ONLY")
    if qtype == "analytical":
        flags.append("ATOMIZATION_NOT_REVIEWED")
    if type_status != "verified":
        flags.append("QUESTION_TYPE_INFERRED")
    if type_basis == "id_metadata_conflict_id_candidate_retained":
        flags.append("QUESTION_TYPE_METADATA_CONFLICT")
    if exam and points is None:
        flags.append("ORIGINAL_POINTS_UNKNOWN")
    flags.extend(quality_flags)
    if generic_label:
        flags.append("GENERIC_LABEL_NOT_KNOWLEDGE")
    l1 = {"official_scope_coarse": scope_path,
          "label_provenance": ["unofficial_index"] + (["official_syllabus"] if scope_ids else []),
          "candidate_main_knowledge": {"id": candidate_id, "name": label, "role": role,
              "confidence": knowledge_confidence},
          "confidence_by_field": {"official_scope_coarse": scope_confidence,
              "label_provenance": "high", "candidate_main_knowledge": knowledge_confidence,
              "duplicate_candidate": "unknown"},
          "duplicate_candidate": {"is_candidate": None, "possible_duplicate_ids": [],
              "basis": "当前题干指纹未命中或不可用；尚未审核近似改写，不据此认定无重复。", "status": "needs_review"},
          "review_status_by_field": {"official_scope_coarse": scope_status, "label_provenance": "verified",
              "candidate_main_knowledge": "needs_review" if proxy or generic_label else "candidate", "duplicate_candidate": "needs_review"}}
    record = {"schema_version": "question-annotation-v1.0.0", "question_id": qid,
              "annotation_depth": "L1", "record_status": "needs_review", "l0": l0, "l1": l1,
              "l2": None, "l3": None, "review_flags": sorted(set(flags))}
    evidence = {"question_id": qid, "source_id": source["source_id"], "source_file": rel,
                "line_start": item["line_start"], "line_end": item["line_end"],
                "source_metadata": meta, "label_field": label_key, "scope_ids": scope_ids,
                "scope_route_status": scope_status, "type_basis": type_basis,
                "statement_fingerprint_sha256": fp, "statement_image_count": image_count,
                "structural_flags": quality_flags}
    return record, evidence


def attach_duplicates(records, evidence):
    groups = collections.defaultdict(list)
    by_id = {r["question_id"]: r for r in records}
    for e in evidence:
        if e["statement_fingerprint_sha256"]:
            r = by_id[e["question_id"]]
            groups[(r["l0"]["subject_area"], r["l0"]["question_type"], e["statement_fingerprint_sha256"])].append(e["question_id"])
    found = []
    for key, ids in sorted(groups.items()):
        if len(ids) < 2:
            continue
        ids.sort()
        found.append({"fingerprint_sha256": key[2], "question_ids": ids, "status": "candidate"})
        for qid in ids:
            l1 = by_id[qid]["l1"]
            l1["duplicate_candidate"] = {"is_candidate": True, "possible_duplicate_ids": [x for x in ids if x != qid],
                "basis": "同课程同题型的题干、选项及图片内容指纹相同；只合并空白，保留数据、符号和变量，仍需审核。",
                "status": "candidate"}
            l1["confidence_by_field"]["duplicate_candidate"] = "medium"
            l1["review_status_by_field"]["duplicate_candidate"] = "candidate"
    return found


def validate_bundle(root, bundle_path):
    sys.path.insert(0, str(root / TOOL_DIR))
    from json_schema_runtime import validate_json_file
    from validate_annotations import validate_record
    errors = validate_json_file(bundle_path, root / SCHEMA)
    bundle = load_json(bundle_path)
    if not errors:
        for i, record in enumerate(bundle["records"]):
            validate_record(record, i, errors)
    ids = [r["question_id"] for r in bundle["records"]]
    if len(ids) != len(set(ids)) or len(ids) != bundle["record_count"]:
        errors.append("Bundle count/ID uniqueness mismatch")
    fail(not errors, "Annotation validation failed: " + str(errors[:5]))
    return {"status": "PASS", "records": len(ids), "schema_and_semantic_errors": 0}


def verify(root, output):
    """Independently re-read source blocks; never trust locked:true alone."""
    run = load_json(output / "run_manifest.json")
    fail(run["builder_version"] == VERSION, "Builder version changed; use a new snapshot")
    manifest = load_json(root / MANIFEST)
    files = canonical_files(root, manifest)
    fail(input_hashes(root, files) == run["input_sha256"], "Inputs changed; create a new output snapshot")
    for rel, expected in run["asset_sha256"].items():
        p = inside(root, rel)
        actual = file_hash(p) if p.is_file() else None
        fail(actual == expected, "Source image changed; create a new snapshot")
    for name, expected in run["output_sha256"].items():
        fail(Path(name).name == name, "Invalid output filename in manifest")
        fail(file_hash(output / name) == expected, f"Output changed: {name}")
    result = validate_bundle(root, output / "question_annotations_l1_v1.json")
    bundle = load_json(output / "question_annotations_l1_v1.json")
    evidence = [json.loads(line) for line in (output / "l1_evidence_v1.jsonl").read_text().splitlines()]
    evidence_by_id = {e["question_id"]: e for e in evidence}
    records = {r["question_id"]: r for r in bundle["records"]}
    fail(set(evidence_by_id) == set(records) and len(evidence) == len(records), "Evidence ID mismatch")
    counts = collections.Counter()
    fresh = {}
    for source, path in files:
        rel = path.relative_to(root).as_posix()
        for item in parse_file(path.read_text(encoding="utf-8"), rel):
            qid = item["question_id"]
            fail(qid not in fresh, "Repeated canonical ID")
            fresh[qid] = (rel, item["block_hash"])
            counts[source["source_id"]] += 1
    fail(set(fresh) == set(records), "Source/output ID coverage mismatch")
    fail(len(records) == manifest["expected_unique_question_records"], "Source baseline count mismatch")
    for source in manifest["sources"]:
        fail(counts[source["source_id"]] == source["expected_records"], "Per-source baseline mismatch")
    for qid, record in records.items():
        l0, l1 = record["l0"], record["l1"]
        fail(fresh[qid] == (l0["source_file"], l0["question_hash_sha256"]), "Source hash/reference mismatch")
        fail(l0["source_locator"] == qid, "Unstable source locator")
        fail(record["annotation_depth"] == "L1" and record["l2"] is None and record["l3"] is None, "Depth was promoted")
        e = evidence_by_id[qid]
        fail(l1["candidate_main_knowledge"]["name"] == e["source_metadata"][e["label_field"]], "Label evidence mismatch")
        dup = l1["duplicate_candidate"]
        neighbors = dup["possible_duplicate_ids"]
        fail((dup["is_candidate"] is True) == bool(neighbors), "Duplicate boolean/links conflict")
        for other in neighbors:
            fail(other != qid and other in records, "Duplicate dangling/self reference")
            fail(qid in records[other]["l1"]["duplicate_candidate"]["possible_duplicate_ids"], "Asymmetric duplicate relation")
            fail(e["statement_fingerprint_sha256"] is not None and e["statement_fingerprint_sha256"] == evidence_by_id[other]["statement_fingerprint_sha256"], "Duplicate fingerprint mismatch")
    result.update(source_hashes_checked=len(records), evidence_records=len(evidence), unique_ids=len(records),
                  per_source=dict(sorted(counts.items())), output_integrity="PASS", input_integrity="PASS")
    return result


def build(root, output):
    if (output / "run_manifest.json").exists():
        result = verify(root, output)
        return {"status": "REUSED", **result, "action": "reused_verified_snapshot"}
    fail(not output.exists() or not any(output.iterdir()), "Output is nonempty; choose a new snapshot path")
    manifest = load_json(root / MANIFEST)
    files = canonical_files(root, manifest)
    before = input_hashes(root, files)
    rules = load_json(RULE_FILE)
    scopes = {s["scope_id"]: s for s in load_json(root / SCOPE_FILE)}
    records, evidence, assets = [], [], {}
    counts = collections.Counter()
    for source, path in files:
        rel = path.relative_to(root).as_posix()
        for item in parse_file(path.read_text(encoding="utf-8"), rel):
            record, ev = make_record(root, source, path, item, scopes, rules, assets)
            records.append(record)
            evidence.append(ev)
            counts[source["source_id"]] += 1
    fail(len(records) == len({r["question_id"] for r in records}), "Duplicate canonical IDs")
    fail(len(records) == manifest["expected_unique_question_records"], "Canonical total differs from baseline")
    for source in manifest["sources"]:
        fail(counts[source["source_id"]] == source["expected_records"], f"Count mismatch: {source['source_id']}")
    records.sort(key=lambda r: r["question_id"])
    evidence.sort(key=lambda e: e["question_id"])
    duplicate_groups = attach_duplicates(records, evidence)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    bundle = {"schema_version": "question-annotations-bundle-v1.0.0", "generated_at": generated_at,
              "source_file": MANIFEST, "source_schema_version": manifest["manifest_version"],
              "record_count": len(records), "records": records}
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".l1-build-", dir=output.parent))
    try:
        write_json(temp / "question_annotations_l1_v1.json", bundle)
        (temp / "l1_evidence_v1.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in evidence), encoding="utf-8")
        write_json(temp / "duplicate_candidates_v1.json", {"status": "candidate", "groups": duplicate_groups})
        validation = validate_bundle(root, temp / "question_annotations_l1_v1.json")
        flags = collections.Counter(f for r in records for f in r["review_flags"])
        summary = {"status": "PASS", "builder_version": VERSION, "generated_at": generated_at,
                   "records": len(records), "unique_ids": len(records), "sources": dict(sorted(counts.items())),
                   "subject_areas": dict(sorted(collections.Counter(r["l0"]["subject_area"] for r in records).items())),
                   "chapter_scope_candidates": sum(e["scope_route_status"] == "candidate" for e in evidence),
                   "course_only_scope_candidates": sum(e["scope_route_status"] != "candidate" for e in evidence),
                   "legacy_topic_candidates": sum(e["label_field"] in {"考点", "知识点"} for e in evidence),
                   "chapter_proxy_candidates": sum(e["label_field"] in {"章节", "专题"} for e in evidence),
                   "duplicate_groups": len(duplicate_groups), "duplicate_candidate_records": sum(len(g["question_ids"]) for g in duplicate_groups),
                   "unknown_original_points": sum(r["l0"]["original_points"] is None for r in records),
                   "inferred_question_types": flags["QUESTION_TYPE_INFERRED"], "flags": dict(sorted(flags.items())),
                   "external_api_calls": 0, "source_markdown_files": len(files), "referenced_images": len(assets),
                   "validation": validation, "limitations": LIMITATIONS}
        write_json(temp / "l1_build_report.json", summary)
        lines = ["# L1 候选粗标执行报告", "", f"生成时间：{generated_at}", "", "结构与可追溯性校验：**PASS**。", "",
                 f"共生成 {len(records)} 条 L1 累积标注，全部保留 L0；L2/L3 均为 null，审核状态为 needs_review。", "",
                 "| 题源 | 记录数 |", "|---|---:|"]
        lines.extend(f"| {source['canonical_path']} | {counts[source['source_id']]} |" for source in manifest["sources"])
        lines += ["", f"章级 Scope 候选：{summary['chapter_scope_candidates']}；仅课程级路由：{summary['course_only_scope_candidates']}。",
                  f"旧考点/知识点候选：{summary['legacy_topic_candidates']}；原章节代理候选：{summary['chapter_proxy_candidates']}。",
                  f"重复候选：{len(duplicate_groups)} 组、{summary['duplicate_candidate_records']} 条；只是指纹匹配，尚未人工确认。",
                  f"未知分值：{summary['unknown_original_points']} 条；推断题型：{summary['inferred_question_types']} 条。", "",
                  "## 交付文件", "", "- `question_annotations_l1_v1.json`：唯一正式候选集合，符合既有 schema。",
                  "- `l1_evidence_v1.jsonl`：逐条元数据、来源行号、路由候选与指纹证据；不保存题干或答案。",
                  "- `duplicate_candidates_v1.json`：重复候选组；原题不删除、不合并。",
                  "- `run_manifest.json`：输入、图片、程序、规则、输出哈希，支持复跑与防覆盖。", "",
                  "## 检测范围与未决项", ""]
        lines.extend("- " + s for s in LIMITATIONS)
        lines += ["", "| 待审核标记 | 条数 |", "|---|---:|"]
        lines.extend(f"| {flag} | {count} |" for flag, count in sorted(flags.items()))
        (temp / "L1执行报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        fail(before == input_hashes(root, canonical_files(root, manifest)), "Inputs changed during execution")
        run = {"builder_version": VERSION, "rules_version": rules["version"], "generated_at": generated_at,
               "input_sha256": before, "asset_sha256": dict(sorted(assets.items())),
               "output_sha256": {p.name: file_hash(p) for p in sorted(temp.iterdir())}, "api_calls": 0}
        write_json(temp / "run_manifest.json", run)
        verification = verify(root, temp)
        if output.exists():
            output.rmdir()  # Only the empty destination allowed above.
        os.rename(temp, output)
        return {"action": "built_new_snapshot", **summary, "verification": verification}
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "check"])
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-dir", type=Path, help="default: PROJECT/系统文件/题目标注/L1")
    parser.add_argument("--report", type=Path, help="Optional additional check report (outside the snapshot)")
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = (args.output_dir or root / "系统文件/题目标注/L1").resolve()
    try:
        if args.report:
            fail(not args.report.resolve().is_relative_to(output), "Additional report must be outside immutable snapshot")
        result = build(root, output) if args.command == "build" else verify(root, output)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            write_json(args.report, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
