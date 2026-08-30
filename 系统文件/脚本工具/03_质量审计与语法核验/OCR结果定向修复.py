#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既有数学 OCR Markdown 的定向修复器。

它不重跑 OCR，也不更换模型。它只做三件事：

1. 从复查报告中提取“正确式被写成错误式”这类方向明确的勘误，精确替换；
2. 修复少数已确认、且上下文足以唯一判定的线性代数高频错误；
3. 对漏题、整块缺失或无法从错误文本反推出原式的页面，附上源 PDF 原页图，
   并把其他高风险项列入报告，不凭猜测改公式。

默认写到新的“*_已修复”目录，永不覆盖原 Markdown、图片或 PDF。

最常用：

    python OCR结果定向修复.py "数学OCR输出目录" \
      --audit-report "OCR质量复查报告_新版本_线性代数基础篇.md"

若 OCR 输出来自“数学文档OCR_v3.py”，程序会尝试从 ocr_state.json 自动找到源 PDF。
也可手工指定：

    python OCR结果定向修复.py "数学OCR输出目录" \
      --audit-report "复查报告.md" --source-pdf "教材.pdf"

一次处理多份：

    python OCR结果定向修复.py outputs/书1 outputs/书2 outputs/书3

只扫描、不写结果：

    python OCR结果定向修复.py "数学OCR输出目录" --dry-run

生成一份可手工补充的精确勘误配置：

    python OCR结果定向修复.py --write-rules-template OCR定向修复规则.json
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Sequence


SCRIPT_VERSION = "1.0.0"
RULE_SCHEMA_VERSION = 1
STATE_SCHEMA_VERSION = 1

MATH_ENVIRONMENTS = (
    "matrix",
    "pmatrix",
    "bmatrix",
    "Bmatrix",
    "vmatrix",
    "Vmatrix",
    "smallmatrix",
)

EXCLUDED_DIRS = {
    ".git",
    "chunks",
    "chunk_inputs",
    "attempts",
    "repair_assets",
    "repaired",
    "已修复",
}

EXCLUDED_MARKDOWN_NAMES = {
    "quality_report.md",
    "repair_report.md",
    "OCR定向修复报告.md",
}

MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?P<path>[^)\n]+)\)")
HTML_IMAGE_RE = re.compile(r"<img\b[^>]*?\bsrc=[\"'](?P<path>[^\"']+)[\"']", re.I)
CODE_FENCE_RE = re.compile(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$")
BEGIN_END_RE = re.compile(r"\\(?P<kind>begin|end)\{(?P<name>[^{}]+)\}")
PDF_RANGE_RE = re.compile(r"<!--\s*PDF\s+pages?\s+(\d+)\s*[-–—~]\s*(\d+)", re.I)


class RepairError(RuntimeError):
    """可以直接展示的预期错误。"""


@dataclasses.dataclass(frozen=True)
class PatchRule:
    rule_id: str
    pattern: str
    replacement: str
    file_glob: str = "**/*.md"
    action: str = "regex_replace"
    math_only: bool = False
    context_pattern: str | None = None
    document_pattern: str | None = None
    min_matches: int = 0
    max_matches: int | None = 1
    total_guard: bool = False
    source: str = "built-in"
    description: str = ""


@dataclasses.dataclass(frozen=True)
class FallbackRule:
    rule_id: str
    pdf_page: int
    chapter_number: int | None = None
    file_glob: str = "**/*.md"
    reason: str = "复查报告指出该页存在无法安全自动反推的 OCR 错误。"
    crop: tuple[float, float, float, float] | None = None
    source: str = "audit-report"


@dataclasses.dataclass
class Change:
    rule_id: str
    file: str
    line: int
    before: str
    after: str
    source: str


@dataclasses.dataclass
class Finding:
    severity: str
    code: str
    file: str
    line: int | None
    message: str
    excerpt: str = ""
    pdf_range: str | None = None


@dataclasses.dataclass
class FileResult:
    source_path: Path
    target_path: Path
    relative_path: str
    original_text: str
    repaired_text: str
    changes: list[Change]
    findings: list[Finding]
    copied_assets: list[str]


@dataclasses.dataclass
class RunResult:
    source: Path
    output: Path | None
    report_path: Path | None
    files: list[FileResult]
    changes: list[Change]
    findings: list[Finding]
    fallbacks_inserted: int
    status: str


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def sha256_file(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def compact_excerpt(value: str, limit: int = 140) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return bool(backslashes % 2)


def find_code_spans(text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in CODE_FENCE_RE.finditer(text)]


def find_math_body_spans(text: str) -> tuple[list[tuple[int, int]], list[str]]:
    """返回数学定界符内部的范围，以及未闭合问题。"""
    spans: list[tuple[int, int]] = []
    problems: list[str] = []
    code_spans = find_code_spans(text)
    code_index = 0

    def in_code(index: int) -> bool:
        nonlocal code_index
        while code_index < len(code_spans) and code_spans[code_index][1] <= index:
            code_index += 1
        return code_index < len(code_spans) and code_spans[code_index][0] <= index < code_spans[code_index][1]

    index = 0
    length = len(text)
    while index < length:
        if in_code(index):
            index = code_spans[code_index][1]
            continue
        if text.startswith("\\[", index) and not is_escaped(text, index):
            end = text.find("\\]", index + 2)
            if end < 0:
                problems.append(f"第 {line_number(text, index)} 行的 \\[ 未闭合")
                break
            spans.append((index + 2, end))
            index = end + 2
            continue
        if text.startswith("\\(", index) and not is_escaped(text, index):
            end = text.find("\\)", index + 2)
            if end < 0:
                problems.append(f"第 {line_number(text, index)} 行的 \\( 未闭合")
                break
            spans.append((index + 2, end))
            index = end + 2
            continue
        if text.startswith("$$", index) and not is_escaped(text, index):
            end = index + 2
            while True:
                end = text.find("$$", end)
                if end < 0 or not is_escaped(text, end):
                    break
                end += 2
            if end < 0:
                problems.append(f"第 {line_number(text, index)} 行的 $$ 未闭合")
                break
            spans.append((index + 2, end))
            index = end + 2
            continue
        if text[index] == "$" and not is_escaped(text, index):
            end = index + 1
            while True:
                end = text.find("$", end)
                if end < 0 or not is_escaped(text, end):
                    break
                end += 1
            if end < 0:
                problems.append(f"第 {line_number(text, index)} 行的 $ 未闭合")
                break
            spans.append((index + 1, end))
            index = end + 1
            continue
        index += 1
    return spans, problems


def offset_in_spans(start: int, end: int, spans: Sequence[tuple[int, int]]) -> bool:
    return any(left <= start and end <= right for left, right in spans)


def offset_overlaps_spans(start: int, end: int, spans: Sequence[tuple[int, int]]) -> bool:
    return any(start < right and end > left for left, right in spans)


def paragraph_at(text: str, offset: int) -> str:
    start = text.rfind("\n\n", 0, offset)
    start = 0 if start < 0 else start + 2
    end = text.find("\n\n", offset)
    end = len(text) if end < 0 else end
    return text[start:end]


def nearest_pdf_range(text: str, offset: int) -> str | None:
    nearest: re.Match[str] | None = None
    for match in PDF_RANGE_RE.finditer(text, 0, offset):
        nearest = match
    if nearest is None:
        return None
    return f"{nearest.group(1)}-{nearest.group(2)}"


def path_matches(relative_path: str, pattern: str) -> bool:
    path = PurePosixPath(relative_path)
    return path.match(pattern) or fnmatch.fnmatch(relative_path, pattern)


def compile_rule_pattern(rule: PatchRule) -> re.Pattern[str]:
    if rule.action == "replace":
        return re.compile(re.escape(rule.pattern))
    if rule.action == "regex_replace":
        return re.compile(rule.pattern)
    raise RepairError(f"未知补丁动作 {rule.action!r}：{rule.rule_id}")


def find_rule_candidates(
    text: str,
    relative_path: str,
    rule: PatchRule,
) -> list[re.Match[str]]:
    if not path_matches(relative_path, rule.file_glob):
        return []
    if rule.document_pattern and not re.search(rule.document_pattern, text, re.I | re.M):
        return []
    pattern = compile_rule_pattern(rule)
    math_spans, _ = find_math_body_spans(text)
    code_spans = find_code_spans(text)
    candidates: list[re.Match[str]] = []
    for match in pattern.finditer(text):
        if offset_overlaps_spans(match.start(), match.end(), code_spans):
            continue
        if rule.math_only and not offset_in_spans(match.start(), match.end(), math_spans):
            continue
        if rule.context_pattern:
            paragraph = paragraph_at(text, match.start())
            if not re.search(rule.context_pattern, paragraph, re.I | re.M):
                continue
        candidates.append(match)
    return candidates


def apply_patch_rule(
    text: str,
    relative_path: str,
    rule: PatchRule,
) -> tuple[str, list[Change], list[Finding]]:
    candidates = find_rule_candidates(text, relative_path, rule)

    count = len(candidates)
    if count < rule.min_matches or (rule.max_matches is not None and count > rule.max_matches):
        expected = (
            f"{rule.min_matches}～{rule.max_matches}"
            if rule.max_matches is not None
            else f"至少 {rule.min_matches}"
        )
        return text, [], [
            Finding(
                severity="blocker",
                code="PATCH_GUARD_FAILED",
                file=relative_path,
                line=None,
                message=(
                    f"补丁 {rule.rule_id} 预期匹配 {expected} 次，实际 {count} 次；"
                    "为避免误改，整条补丁未执行。"
                ),
            )
        ]
    if not candidates:
        return text, [], []

    changes: list[Change] = []
    output = text
    for match in reversed(candidates):
        replacement = match.expand(rule.replacement)
        before = match.group(0)
        output = output[: match.start()] + replacement + output[match.end() :]
        changes.append(
            Change(
                rule_id=rule.rule_id,
                file=relative_path,
                line=line_number(text, match.start()),
                before=compact_excerpt(before),
                after=compact_excerpt(replacement),
                source=rule.source,
            )
        )
    changes.reverse()
    return output, changes, []


def builtin_linear_algebra_rules() -> list[PatchRule]:
    """只包含报告已确认、且能通过上下文限制避免全局误修的规则。"""
    return [
        PatchRule(
            rule_id="LA_VECTOR_T_GT_S",
            pattern=r"(?<![A-Za-z])t\s*\\gg\s*s(?![A-Za-z])",
            replacement="t>s",
            math_only=True,
            context_pattern=r"向量组|线性相关|线性无关|极大无关|向量个数|个数",
            document_pattern=r"第三章|第\s*3\s*章|向量",
            max_matches=1,
            description="把报告确认的 t\\gg s 恢复为 t>s。",
        ),
        PatchRule(
            rule_id="LA_VECTOR_RANK_I_II",
            pattern=(
                r"r\s*\(\s*\\mathrm\s*\{?\s*I\s*\}?\s*\)\s*"
                r"(?:\\leq?|≤)\s*"
                r"r\s*\(\s*\\mathrm\s*\{?\s*I\s*\}?\s*\)"
            ),
            replacement=r"r(\\mathrm{I})\\le r(\\mathrm{II})",
            math_only=True,
            context_pattern=r"向量组|线性表示|等价|秩|延伸",
            document_pattern=r"第三章|第\s*3\s*章|向量",
            max_matches=1,
            description="把报告确认的 r(I)≤r(I) 恢复为 r(I)≤r(II)。",
        ),
        PatchRule(
            rule_id="LA_ADJUGATE_BULLET",
            pattern=r"A\s*\^\s*(?:\{\s*\\bullet\s*\}|\\bullet|[•·])",
            replacement="A^*",
            math_only=True,
            context_pattern=r"伴随|代数余子式|adjugate",
            max_matches=100,
            description="只在伴随矩阵上下文中把 A 的 bullet 上标恢复为星号。",
        ),
        PatchRule(
            rule_id="LA_ADJUGATE_PRIME",
            pattern=r"A\s*(?:\^\s*\{?\s*\\prime\s*\}?|')",
            replacement="A^*",
            math_only=True,
            context_pattern=r"伴随|代数余子式|adjugate",
            max_matches=100,
            description="只在伴随矩阵上下文中把 A 的 prime 记号恢复为星号。",
        ),
        PatchRule(
            rule_id="LA_LAMBDA_AS_CHINESE_IN_MATH",
            pattern="入",
            replacement=r"\\lambda",
            action="replace",
            math_only=True,
            context_pattern=r"特征值|特征向量|二次型|对角|lambda|\\lambda",
            max_matches=500,
            description="只在特征值/二次型数学上下文中把汉字入恢复为 lambda。",
        ),
    ]


INLINE_TOKEN_RE = re.compile(
    r"\\\((?P<paren>.*?)\\\)|`(?P<code>[^`\n]+)`|(?<!\$)\$(?P<dollar>[^$\n]+)\$(?!\$)"
)


CHAPTER_FILE_GLOBS = {
    1: "**/*行列式*.md",
    2: "**/*矩阵*.md",
    3: "**/*向量*.md",
    4: "**/*方程组*.md",
    5: "**/*特征值*.md",
    6: "**/*二次型*.md",
}


def token_value(match: re.Match[str]) -> str:
    return next(value for value in match.groupdict().values() if value is not None).strip()


def flexible_literal_pattern(value: str) -> str:
    compact = re.sub(r"\s+", "", value)
    normalized = compact.replace("{", "").replace("}", "").replace(r"\leq", r"\le")
    if normalized == r"A^\bullet":
        return r"A\s*\^\s*(?:\{\s*\\bullet\s*\}|\\bullet|[•·])"
    if normalized in {"A'", r"A^\prime"}:
        return r"A\s*(?:\^\s*\{?\s*\\prime\s*\}?|')"
    if normalized == r"r(\mathrmI)\ler(\mathrmI)":
        return (
            r"r\s*\(\s*\\mathrm\s*\{?\s*I\s*\}?\s*\)\s*"
            r"(?:\\leq?|≤)\s*"
            r"r\s*\(\s*\\mathrm\s*\{?\s*I\s*\}?\s*\)"
        )
    pieces = re.split(r"(\s+)", value.strip())
    return "".join(r"\s*" if piece.isspace() else re.escape(piece) for piece in pieces if piece)


def extract_explicit_pairs(line: str) -> list[tuple[str, str]]:
    """提取报告中的“正确式 写成 错误式”或“错误式 应为 正确式”。"""
    tokens = list(INLINE_TOKEN_RE.finditer(line))
    pairs: list[tuple[str, str]] = []
    last_correct: str | None = None
    for left, right in zip(tokens, tokens[1:]):
        between = line[left.end() : right.start()]
        left_value = token_value(left)
        right_value = token_value(right)
        if re.search(r"写成|识成|误成|误作|改成|变成|错成", between):
            correct, wrong = left_value, right_value
            if correct != wrong:
                pairs.append((wrong, correct))
                last_correct = correct
        elif re.search(r"应为|正确(?:式|方程|条件)?为|应改为", between):
            wrong, correct = left_value, right_value
            if correct != wrong:
                pairs.append((wrong, correct))
                last_correct = correct
        elif last_correct and re.fullmatch(r"\s*(?:或|以及|、|和)\s*", between):
            wrong = right_value
            if wrong != last_correct:
                pairs.append((wrong, last_correct))
    return pairs


def parse_audit_report(path: Path) -> tuple[list[PatchRule], list[FallbackRule], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    patches_by_pair: dict[tuple[str, str], PatchRule] = {}
    fallbacks_by_key: dict[tuple[int | None, int], FallbackRule] = {}
    notes: list[str] = []
    chapter_number: int | None = None
    severe_re = re.compile(
        r"整题|整道|题干.*(?:漏|缺)|漏失|缺失|丢失|无法恢复|无法读取|"
        r"改成另一|变成另一|最终(?:式|方程|答案).*(?:错|误)|"
        r"系数、符号和变量|阻断性|不可信|不能直接"
    )

    for line_index, line in enumerate(text.splitlines(), start=1):
        heading = re.match(r"^#{2,4}\s*第\s*([1-6])\s*章", line.strip())
        if heading:
            chapter_number = int(heading.group(1))

        for wrong, correct in extract_explicit_pairs(line):
            if not wrong or not correct or len(wrong) > 300 or len(correct) > 300:
                continue
            file_glob = CHAPTER_FILE_GLOBS.get(chapter_number, "**/*.md")
            rule = PatchRule(
                rule_id=f"AUDIT_L{line_index}_{hashlib.sha1((wrong + correct).encode()).hexdigest()[:8]}",
                pattern=flexible_literal_pattern(wrong),
                replacement=correct.replace("\\", "\\\\"),
                file_glob=file_glob,
                action="regex_replace",
                math_only=True,
                context_pattern=(r"伴随|代数余子式|adjugate" if correct.replace(" ", "") in {"A^*", "A^{*}"} else None),
                min_matches=0,
                max_matches=1,
                total_guard=True,
                source=f"audit:{path.name}:{line_index}",
                description=f"复查报告明确指出 {wrong!r} 应恢复为 {correct!r}。",
            )
            key = (wrong, correct)
            old = patches_by_pair.get(key)
            if old is None or (old.file_glob == "**/*.md" and file_glob != "**/*.md"):
                patches_by_pair[key] = rule

        if not line.lstrip().startswith("-"):
            continue
        page_match = re.search(r"PDF\s*(?:第\s*)?(\d+)\s*(?:页)?", line, re.I)
        if page_match and severe_re.search(line):
            page = int(page_match.group(1))
            key = (chapter_number, page)
            fallbacks_by_key[key] = FallbackRule(
                rule_id=f"AUDIT_P{page}_C{chapter_number or 0}",
                pdf_page=page,
                chapter_number=chapter_number,
                file_glob=CHAPTER_FILE_GLOBS.get(chapter_number, "**/*.md"),
                reason=compact_excerpt(re.sub(r"^\s*-\s*", "", line), 240),
            )

    if not patches_by_pair:
        notes.append("复查报告中没有解析到方向明确的“正确式→错误式”成对勘误。")
    if not fallbacks_by_key:
        notes.append("复查报告中没有解析到带 PDF 页码的严重缺失项。")
    return list(patches_by_pair.values()), list(fallbacks_by_key.values()), notes


def load_rule_file(path: Path) -> tuple[list[PatchRule], list[FallbackRule]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RepairError(f"无法读取规则文件 {path}：{exc}") from exc
    if payload.get("schema_version") != RULE_SCHEMA_VERSION:
        raise RepairError(
            f"规则文件 schema_version 必须为 {RULE_SCHEMA_VERSION}：{path}"
        )
    patches: list[PatchRule] = []
    for index, item in enumerate(payload.get("patches") or [], start=1):
        try:
            patches.append(
                PatchRule(
                    rule_id=str(item["id"]),
                    pattern=str(item.get("find") if item.get("action", "replace") == "replace" else item["pattern"]),
                    replacement=str(item["replace"]),
                    file_glob=str(item.get("file_glob", "**/*.md")),
                    action=str(item.get("action", "replace")),
                    math_only=bool(item.get("math_only", False)),
                    context_pattern=item.get("context_pattern"),
                    document_pattern=item.get("document_pattern"),
                    min_matches=int(item.get("min_matches", 1)),
                    max_matches=(
                        None if item.get("max_matches") is None else int(item.get("max_matches", 1))
                    ),
                    total_guard=bool(item.get("total_guard", False)),
                    source=f"rules:{path.name}:{index}",
                    description=str(item.get("description", "")),
                )
            )
        except Exception as exc:
            raise RepairError(f"规则文件第 {index} 条 patches 无效：{exc}") from exc

    fallbacks: list[FallbackRule] = []
    for index, item in enumerate(payload.get("source_fallbacks") or [], start=1):
        try:
            crop_raw = item.get("crop")
            crop = tuple(float(value) for value in crop_raw) if crop_raw is not None else None
            if crop is not None and len(crop) != 4:
                raise ValueError("crop 必须是 [x0,y0,x1,y1]")
            fallbacks.append(
                FallbackRule(
                    rule_id=str(item["id"]),
                    pdf_page=int(item["pdf_page"]),
                    chapter_number=(
                        int(item["chapter_number"]) if item.get("chapter_number") is not None else None
                    ),
                    file_glob=str(item.get("file_glob", "**/*.md")),
                    reason=str(item.get("reason", "该区域无法从 OCR 文本安全反推。")),
                    crop=crop,
                    source=f"rules:{path.name}:{index}",
                )
            )
        except Exception as exc:
            raise RepairError(f"规则文件第 {index} 条 source_fallbacks 无效：{exc}") from exc
    return patches, fallbacks


def write_rules_template(path: Path) -> None:
    payload = {
        "schema_version": RULE_SCHEMA_VERSION,
        "patches": [
            {
                "id": "BOOK1_FINAL_EQUATION",
                "file_glob": "chapters/*方程组*.md",
                "action": "replace",
                "find": "这里填写 OCR 中完整且唯一的错误原文",
                "replace": "这里填写对照 PDF 后确认的正确原文",
                "math_only": False,
                "min_matches": 1,
                "max_matches": 1,
                "total_guard": True,
                "description": "精确匹配次数不等于 1 时拒绝修改。",
            }
        ],
        "source_fallbacks": [
            {
                "id": "BOOK1_MISSING_QUESTION_P53",
                "file_glob": "chapters/*矩阵*.md",
                "chapter_number": 2,
                "pdf_page": 53,
                "reason": "整道题干缺失，无法从现有 Markdown 反推。",
                "crop": [0.0, 0.0, 1.0, 1.0],
            }
        ],
    }
    atomic_write_json(path, payload)


def discover_markdown_files(source: Path) -> tuple[Path, list[Path]]:
    if source.is_file():
        if source.suffix.lower() != ".md":
            raise RepairError(f"输入文件不是 Markdown：{source}")
        return source.parent, [source]
    if not source.is_dir():
        raise RepairError(f"输入不存在：{source}")
    preferred_chapters = source / "chapters"
    search_root = preferred_chapters if preferred_chapters.is_dir() else source
    files: list[Path] = []
    for path in search_root.rglob("*.md"):
        relative = path.relative_to(source)
        if any(part in EXCLUDED_DIRS or part.endswith("_已修复") for part in relative.parts[:-1]):
            continue
        if path.name in EXCLUDED_MARKDOWN_NAMES:
            continue
        if "OCR质量" in path.name or "复查报告" in path.name:
            continue
        files.append(path)
    files.sort(key=lambda item: item.relative_to(source).as_posix())
    if not files:
        raise RepairError(f"目录中没有找到待修复 Markdown：{source}")
    return source, files


def default_output_path(source: Path) -> Path:
    if source.is_file():
        return source.with_name(f"{source.stem}_已修复{source.suffix}")
    return source.with_name(f"{source.name}_已修复")


def validate_output_target(source: Path, output: Path, source_root: Path) -> None:
    source_resolved = source.resolve()
    output_resolved = output.resolve()
    if source_resolved == output_resolved:
        raise RepairError("输出不能与输入相同；本工具不覆盖原文件。")
    if source.is_dir():
        with contextlib.suppress(ValueError):
            output_resolved.relative_to(source_resolved)
            raise RepairError("输出目录不能位于输入目录内部，避免下一次扫描把结果当原文。")
    else:
        if output_resolved == source_resolved:
            raise RepairError("输出文件不能覆盖输入文件。")
    if output.exists() and output.is_dir():
        state = output / "repair_state.json"
        if not state.is_file():
            if any(output.iterdir()):
                raise RepairError(f"输出目录非空且不是本工具创建的结果：{output}")
            return
        try:
            payload = json.loads(state.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RepairError(f"输出目录状态文件损坏：{state}：{exc}") from exc
        if payload.get("source") != str(source_resolved):
            raise RepairError(f"输出目录属于另一个输入，拒绝混写：{output}")
    elif output.exists() and output.is_file() and source.is_dir():
        raise RepairError(f"目录输入不能写入普通文件：{output}")
    elif output.exists() and output.is_file() and source.is_file():
        state = output.with_name(f"{output.stem}_repair_state.json")
        if not state.is_file():
            raise RepairError(f"输出文件已存在且不是本工具创建的结果：{output}")
        try:
            payload = json.loads(state.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RepairError(f"输出状态文件损坏：{state}：{exc}") from exc
        if payload.get("source") != str(source_resolved):
            raise RepairError(f"输出文件属于另一个输入，拒绝覆盖：{output}")


def discover_audit_report(source: Path) -> Path | None:
    roots = [source if source.is_dir() else source.parent, source.parent]
    candidates: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        candidates.extend(root.glob("*OCR*质量*复查*报告*.md"))
        candidates.extend(root.glob("*OCR*质量*报告*.md"))
    unique = sorted({path.resolve() for path in candidates if path.is_file()})
    if len(unique) == 1:
        return unique[0]
    return None


def discover_source_pdf(source: Path) -> Path | None:
    root = source if source.is_dir() else source.parent
    state_path = root / "ocr_state.json"
    if state_path.is_file():
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            candidate = Path(str((payload.get("source") or {}).get("path", ""))).expanduser()
            if candidate.is_file() and candidate.suffix.lower() == ".pdf":
                return candidate.resolve()
        except Exception:
            pass
    nearby = sorted(root.parent.glob("*.pdf")) + sorted(root.glob("*.pdf"))
    unique = []
    seen: set[Path] = set()
    for item in nearby:
        resolved = item.resolve()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique[0] if len(unique) == 1 else None


def relative_path_for(source_root: Path, path: Path, source_is_file: bool) -> str:
    if source_is_file:
        return path.name
    return path.relative_to(source_root).as_posix()


def scan_environments(text: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []
    code_spans = find_code_spans(text)
    stack: list[tuple[str, int]] = []
    for match in BEGIN_END_RE.finditer(text):
        if offset_overlaps_spans(match.start(), match.end(), code_spans):
            continue
        kind, name = match.group("kind"), match.group("name")
        if kind == "begin":
            stack.append((name, match.start()))
        elif not stack or stack[-1][0] != name:
            findings.append(
                Finding(
                    "blocker",
                    "MATH_ENV_MISMATCH",
                    relative_path,
                    line_number(text, match.start()),
                    f"\\end{{{name}}} 没有对应的最近 \\begin{{{name}}}。",
                    compact_excerpt(paragraph_at(text, match.start())),
                    nearest_pdf_range(text, match.start()),
                )
            )
        else:
            stack.pop()
    for name, offset in stack:
        findings.append(
            Finding(
                "blocker",
                "MATH_ENV_UNCLOSED",
                relative_path,
                line_number(text, offset),
                f"\\begin{{{name}}} 未闭合。",
                compact_excerpt(paragraph_at(text, offset)),
                nearest_pdf_range(text, offset),
            )
        )
    return findings


def split_unescaped_rows(body: str) -> list[str]:
    rows = re.split(r"(?<!\\)\\\\(?:\[[^\]]*\])?", body)
    return [row.strip() for row in rows if row.strip()]


def count_unescaped_ampersands(row: str) -> int:
    return sum(1 for match in re.finditer(r"&", row) if not is_escaped(row, match.start()))


def scan_matrices(text: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []
    env_names = "|".join(re.escape(name) for name in MATH_ENVIRONMENTS)
    pattern = re.compile(
        rf"\\begin\{{(?P<env>{env_names})\}}(?P<body>.*?)\\end\{{(?P=env)\}}",
        re.S,
    )
    for match in pattern.finditer(text):
        body = match.group("body")
        if "\\multicolumn" in body:
            continue
        rows = split_unescaped_rows(body)
        columns = [count_unescaped_ampersands(row) + 1 for row in rows]
        if len(columns) >= 2 and len(set(columns)) > 1:
            findings.append(
                Finding(
                    "blocker",
                    "MATRIX_COLUMN_MISMATCH",
                    relative_path,
                    line_number(text, match.start()),
                    f"{match.group('env')} 各行列数不一致：{columns}。",
                    compact_excerpt(match.group(0)),
                    nearest_pdf_range(text, match.start()),
                )
            )
    return findings


def scan_high_risk_math(text: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []
    math_spans, delimiter_problems = find_math_body_spans(text)
    for problem in delimiter_problems:
        findings.append(Finding("blocker", "MATH_DELIMITER_UNCLOSED", relative_path, None, problem))

    patterns = [
        (
            "warning",
            "DOUBLE_GREATER_REMAINS",
            re.compile(r"\\gg\b"),
            "仍有 \\gg；在线性代数讲义中它可能是把普通大于号识错，需回看 PDF。",
        ),
        (
            "blocker",
            "ADJUGATE_BULLET_REMAINS",
            re.compile(r"[A-Za-z]\s*\^\s*(?:\{\s*\\bullet\s*\}|\\bullet|[•·])"),
            "仍有字母的 bullet 上标；若表示伴随矩阵，通常应为星号。",
        ),
        (
            "warning",
            "CHINESE_LAMBDA_REMAINS",
            re.compile("入"),
            "数学定界符内仍有汉字“入”，疑似 lambda 误识。",
        ),
        (
            "blocker",
            "RANK_SELF_COMPARISON",
            re.compile(
                r"r\s*\(\s*(?P<label>[^()]{1,30})\s*\)\s*"
                r"(?:\\leq?|≤|<|\\geq?|≥|>)\s*"
                r"r\s*\(\s*(?P=label)\s*\)"
            ),
            "秩关系两边标签完全相同，可能是 I/II、1/2 等被合并。",
        ),
    ]
    for left, right in math_spans:
        body = text[left:right]
        for severity, code, pattern, message in patterns:
            for match in pattern.finditer(body):
                offset = left + match.start()
                findings.append(
                    Finding(
                        severity,
                        code,
                        relative_path,
                        line_number(text, offset),
                        message,
                        compact_excerpt(paragraph_at(text, offset)),
                        nearest_pdf_range(text, offset),
                    )
                )

    for match in re.finditer(r"(?:伴随|代数余子式)[^\n]{0,160}", text, re.I):
        paragraph = paragraph_at(text, match.start())
        prime = re.search(r"A\s*(?:\^\s*\{?\s*\\prime\s*\}?|')", paragraph)
        if prime:
            offset = text.find(paragraph, max(0, match.start() - len(paragraph))) + prime.start()
            findings.append(
                Finding(
                    "blocker",
                    "ADJUGATE_PRIME_REMAINS",
                    relative_path,
                    line_number(text, offset),
                    "伴随矩阵上下文中仍有 A 的 prime 记号，疑似 A^* 误识。",
                    compact_excerpt(paragraph),
                    nearest_pdf_range(text, offset),
                )
            )
    return findings


def scan_missing_prompts(text: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []
    pattern = re.compile(
        r"(?m)^(?P<head>\s*(?:例|例题)\s*\d+\s*[^\n]{0,8})\n\s*"
        r"(?P<solution>(?:【解】|\[解\]|解[:：]|【分析】|\[分析\]))"
    )
    for match in pattern.finditer(text):
        findings.append(
            Finding(
                "blocker",
                "QUESTION_PROMPT_MAY_BE_MISSING",
                relative_path,
                line_number(text, match.start()),
                "例题标题后立即进入解答，题干可能整段漏失。",
                compact_excerpt(match.group(0)),
                nearest_pdf_range(text, match.start()),
            )
        )
    return findings


def scan_traceability(text: str, relative_path: str) -> list[Finding]:
    ranges = list(PDF_RANGE_RE.finditer(text))
    if ranges or re.search(r"PDF[_ ]PAGE|原\s*PDF\s*页", text, re.I):
        if ranges and not re.search(r"PDF[_ ]PAGE\s*[:=]?\s*\d+", text, re.I):
            widest = max(int(item.group(2)) - int(item.group(1)) + 1 for item in ranges)
            if widest > 1:
                return [
                    Finding(
                        "warning",
                        "COARSE_PDF_TRACE_ONLY",
                        relative_path,
                        None,
                        f"只有分块页范围标记，最宽覆盖 {widest} 页；尚不能逐页定位。",
                    )
                ]
        return []
    return [
        Finding(
            "warning",
            "NO_PDF_PAGE_TRACE",
            relative_path,
            None,
            "文件中没有 PDF 页码或页范围标记，发现错误后难以回到原页。",
        )
    ]


def local_image_paths(text: str) -> Iterator[str]:
    for regex in (MARKDOWN_IMAGE_RE, HTML_IMAGE_RE):
        for match in regex.finditer(text):
            value = match.group("path").strip().strip("<>")
            if re.match(r"^(?:https?:|data:|#)", value, re.I):
                continue
            yield value.split("#", 1)[0].split("?", 1)[0]


def scan_and_copy_assets(
    text: str,
    source_file: Path,
    target_file: Path | None,
    source_root: Path,
    output_root: Path | None,
    relative_path: str,
    dry_run: bool,
) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    copied: list[str] = []
    for raw in local_image_paths(text):
        source_asset = (source_file.parent / Path(raw)).resolve()
        target_asset = (
            (target_file.parent / Path(raw)).resolve()
            if target_file is not None
            else None
        )
        if not source_asset.is_file():
            # PDF 原页回退图是在输出目录中新生成的，不会存在于原 Markdown 目录。
            if target_asset is not None and target_asset.is_file():
                if output_root is not None:
                    copied.append(target_asset.relative_to(output_root).as_posix())
                continue
            findings.append(
                Finding(
                    "blocker",
                    "MISSING_IMAGE",
                    relative_path,
                    None,
                    f"引用图片不存在：{raw}",
                )
            )
            continue
        if target_file is None or output_root is None:
            continue
        assert target_asset is not None
        try:
            target_asset.relative_to(output_root.resolve())
        except ValueError:
            findings.append(
                Finding(
                    "blocker",
                    "ASSET_PATH_ESCAPES_OUTPUT",
                    relative_path,
                    None,
                    f"图片相对路径会越出修复结果目录：{raw}",
                )
            )
            continue
        if not dry_run:
            target_asset.parent.mkdir(parents=True, exist_ok=True)
            if not target_asset.exists() or sha256_file(target_asset) != sha256_file(source_asset):
                shutil.copy2(source_asset, target_asset)
        copied.append(target_asset.relative_to(output_root).as_posix())
    return findings, copied


def scan_markdown(text: str, source_file: Path, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(scan_environments(text, relative_path))
    findings.extend(scan_matrices(text, relative_path))
    findings.extend(scan_high_risk_math(text, relative_path))
    findings.extend(scan_missing_prompts(text, relative_path))
    findings.extend(scan_traceability(text, relative_path))
    return findings


def choose_fallback_target(
    rule: FallbackRule,
    file_results: Sequence[FileResult],
) -> FileResult | None:
    matches = [item for item in file_results if path_matches(item.relative_path, rule.file_glob)]
    if not matches and rule.chapter_number:
        chapter_word = {
            1: "行列式",
            2: "矩阵",
            3: "向量",
            4: "方程组",
            5: "特征值",
            6: "二次型",
        }[rule.chapter_number]
        matches = [
            item
            for item in file_results
            if chapter_word in item.relative_path or chapter_word in item.repaired_text[:1000]
        ]
    if not matches:
        return None
    matches.sort(
        key=lambda item: (
            0 if "chapters" in PurePosixPath(item.relative_path).parts else 1,
            len(item.repaired_text),
            item.relative_path,
        )
    )
    return matches[0]


def render_pdf_fallback(
    pdf: Path,
    output_root: Path,
    rule: FallbackRule,
    dpi: int,
) -> Path:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RepairError(
            "需要附原 PDF 页图，但当前环境没有 PyMuPDF。请运行：python -m pip install PyMuPDF"
        ) from exc
    document = fitz.open(pdf)
    try:
        if rule.pdf_page < 1 or rule.pdf_page > document.page_count:
            raise RepairError(
                f"规则 {rule.rule_id} 的 PDF 页码 {rule.pdf_page} 超出 1～{document.page_count}。"
            )
        page = document.load_page(rule.pdf_page - 1)
        clip = page.rect
        crop_tag = "full"
        if rule.crop is not None:
            x0, y0, x1, y1 = rule.crop
            if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
                raise RepairError(f"规则 {rule.rule_id} 的 crop 必须是 0～1 归一化坐标。")
            clip = fitz.Rect(
                page.rect.x0 + x0 * page.rect.width,
                page.rect.y0 + y0 * page.rect.height,
                page.rect.x0 + x1 * page.rect.width,
                page.rect.y0 + y1 * page.rect.height,
            )
            crop_tag = hashlib.sha1(repr(rule.crop).encode()).hexdigest()[:8]
        target = output_root / "repair_assets" / f"pdf_p{rule.pdf_page:04d}_{crop_tag}.png"
        if not target.is_file():
            matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
            pixmap = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
            atomic_write_bytes(target, pixmap.tobytes("png"))
        return target
    finally:
        document.close()


def insert_source_fallbacks(
    file_results: list[FileResult],
    fallback_rules: Sequence[FallbackRule],
    source_pdf: Path | None,
    output_root: Path | None,
    dpi: int,
    dry_run: bool,
) -> tuple[int, list[Finding]]:
    findings: list[Finding] = []
    if not fallback_rules:
        return 0, findings
    if source_pdf is None:
        for rule in fallback_rules:
            findings.append(
                Finding(
                    "blocker",
                    "SOURCE_PDF_REQUIRED",
                    rule.file_glob,
                    None,
                    f"PDF 第 {rule.pdf_page} 页需要原页回退，但没有找到源 PDF。",
                    rule.reason,
                )
            )
        return 0, findings
    if not source_pdf.is_file():
        raise RepairError(f"源 PDF 不存在：{source_pdf}")
    if output_root is None and not dry_run:
        raise RepairError("内部错误：插入 PDF 原页时没有输出目录。")

    grouped: dict[int, list[tuple[FallbackRule, Path | None]]] = {}
    targets: dict[int, FileResult] = {}
    for rule in fallback_rules:
        target = choose_fallback_target(rule, file_results)
        if target is None:
            findings.append(
                Finding(
                    "blocker",
                    "FALLBACK_TARGET_NOT_FOUND",
                    rule.file_glob,
                    None,
                    f"找不到承载 PDF 第 {rule.pdf_page} 页原图的章节 Markdown。",
                    rule.reason,
                )
            )
            continue
        image_path = None
        if not dry_run:
            assert output_root is not None
            image_path = render_pdf_fallback(source_pdf, output_root, rule, dpi)
        key = id(target)
        targets[key] = target
        grouped.setdefault(key, []).append((rule, image_path))

    inserted = 0
    for key, entries in grouped.items():
        target = targets[key]
        unique: dict[tuple[int, tuple[float, float, float, float] | None], tuple[FallbackRule, Path | None]] = {}
        for rule, image_path in entries:
            unique[(rule.pdf_page, rule.crop)] = (rule, image_path)
        ordered = sorted(unique.values(), key=lambda pair: (pair[0].pdf_page, pair[0].rule_id))
        pages = "、".join(str(rule.pdf_page) for rule, _ in ordered)
        banner = (
            "\n\n<!-- OCR-REPAIR-SOURCE-FALLBACKS -->\n"
            "> [!WARNING]\n"
            f"> 本章 PDF 第 {pages} 页存在无法从 OCR 文本安全反推的内容；"
            "已在文末附原页图，这些页请以原图为准。\n"
        )
        appendix = ["", "## OCR 定向修复：原 PDF 保真页", ""]
        for rule, image_path in ordered:
            appendix += [
                f"### PDF 第 {rule.pdf_page} 页",
                "",
                f"> 复查原因：{rule.reason}",
                "",
            ]
            if image_path is not None:
                relative_image = os.path.relpath(image_path, target.target_path.parent).replace(os.sep, "/")
                appendix += [f"![原 PDF 第 {rule.pdf_page} 页]({relative_image})", ""]
            else:
                appendix += ["（试运行：此处将插入原 PDF 页图。）", ""]
            inserted += 1
        target.repaired_text = target.repaired_text.rstrip() + banner + "\n".join(appendix).rstrip() + "\n"
    return inserted, findings


def build_report_payload(
    source: Path,
    output: Path | None,
    files: Sequence[FileResult],
    changes: Sequence[Change],
    findings: Sequence[Finding],
    audit_report: Path | None,
    source_pdf: Path | None,
    fallbacks_inserted: int,
    notes: Sequence[str],
    dry_run: bool,
) -> dict[str, Any]:
    counts = {
        "blocker": sum(item.severity == "blocker" for item in findings),
        "warning": sum(item.severity == "warning" for item in findings),
        "info": sum(item.severity == "info" for item in findings),
    }
    status = "blocked" if counts["blocker"] else ("warning" if counts["warning"] else "pass")
    return {
        "generated_at": now_iso(),
        "script_version": SCRIPT_VERSION,
        "dry_run": dry_run,
        "source": str(source),
        "output": str(output) if output else None,
        "audit_report": str(audit_report) if audit_report else None,
        "source_pdf": str(source_pdf) if source_pdf else None,
        "status": status,
        "summary": {
            "markdown_files": len(files),
            "automatic_changes": len(changes),
            "source_page_fallbacks": fallbacks_inserted,
            **counts,
        },
        "notes": list(notes),
        "changes": [dataclasses.asdict(item) for item in changes],
        "findings": [dataclasses.asdict(item) for item in findings],
        "files": [
            {
                "file": item.relative_path,
                "source_sha256": sha256_text(item.original_text),
                "output_sha256": sha256_text(item.repaired_text),
                "changes": len(item.changes),
                "findings": len(item.findings),
                "copied_assets": len(item.copied_assets),
            }
            for item in files
        ],
    }


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def report_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    status_name = {"pass": "通过", "warning": "有待核对项", "blocked": "仍有阻断项"}[
        payload["status"]
    ]
    lines = [
        "# OCR 定向修复报告",
        "",
        f"- 状态：**{status_name}**",
        f"- Markdown 文件：{summary['markdown_files']}",
        f"- 已执行的精确修改：{summary['automatic_changes']}",
        f"- 已附源 PDF 原页/裁图：{summary['source_page_fallbacks']}",
        f"- 阻断项：{summary['blocker']}",
        f"- 警告项：{summary['warning']}",
        "",
        "自动修复只处理方向唯一的勘误；没有唯一答案的式子不会被猜改。",
        "",
    ]
    if payload.get("notes"):
        lines += ["## 运行说明", ""]
        lines.extend(f"- {item}" for item in payload["notes"])
        lines.append("")
    if payload["changes"]:
        lines += [
            "## 已执行修改",
            "",
            "| 文件 | 行 | 规则 | 原文 | 修复后 |",
            "|---|---:|---|---|---|",
        ]
        for item in payload["changes"]:
            lines.append(
                f"| `{markdown_escape(item['file'])}` | {item['line']} | "
                f"`{markdown_escape(item['rule_id'])}` | `{markdown_escape(item['before'])}` | "
                f"`{markdown_escape(item['after'])}` |"
            )
        lines.append("")
    if payload["findings"]:
        lines += [
            "## 尚待处理/核对",
            "",
            "| 级别 | 文件 | 行 | 类型 | 说明 | PDF 页范围 |",
            "|---|---|---:|---|---|---|",
        ]
        for item in payload["findings"]:
            lines.append(
                f"| {item['severity']} | `{markdown_escape(item['file'])}` | "
                f"{item['line'] or ''} | `{item['code']}` | "
                f"{markdown_escape(item['message'])} | {item.get('pdf_range') or ''} |"
            )
        lines.append("")
    lines += [
        "## 判断边界",
        "",
        "- 结构检查通过，不等于每个数学符号都正确。",
        "- 漏掉整块题干、矩阵或推导时，必须以 PDF 原图/裁图回退，不能靠正则重建。",
        "- 报告未抽到的潜在语义错误，不会因为本次修复而自动消失。",
        "",
    ]
    return "\n".join(lines)


def resolve_per_input_path(value: Path | None, input_index: int, input_count: int) -> Path | None:
    if value is None:
        return None
    if input_count == 1:
        return value.resolve()
    if value.is_dir():
        return value.resolve()
    raise RepairError("批量处理多个输入时，--audit-report/--source-pdf 不能共用一个普通文件。")


def process_input(
    source: Path,
    output: Path | None,
    rules: Sequence[PatchRule],
    fallback_rules: Sequence[FallbackRule],
    audit_report: Path | None,
    source_pdf: Path | None,
    dry_run: bool,
    render_dpi: int,
    notes: Sequence[str],
) -> RunResult:
    source = source.resolve()
    source_root, markdown_files = discover_markdown_files(source)
    source_is_file = source.is_file()
    if output is None:
        output = default_output_path(source)
    output = output.resolve()
    if not dry_run:
        validate_output_target(source, output, source_root)

    output_root: Path | None
    if source_is_file:
        output_root = output.parent
    else:
        output_root = output

    if not dry_run and not source_is_file:
        output.mkdir(parents=True, exist_ok=True)
        atomic_write_json(
            output / "repair_state.json",
            {
                "schema_version": STATE_SCHEMA_VERSION,
                "script_version": SCRIPT_VERSION,
                "source": str(source.resolve()),
                "generated_at": now_iso(),
                "status": "in_progress",
            },
        )

    file_results: list[FileResult] = []
    all_changes: list[Change] = []
    all_findings: list[Finding] = []

    for source_file in markdown_files:
        relative = relative_path_for(source_root, source_file, source_is_file)
        target_file = output if source_is_file else output / Path(relative)
        original = source_file.read_text(encoding="utf-8", errors="replace")
        file_result = FileResult(
            source_path=source_file,
            target_path=target_file,
            relative_path=relative,
            original_text=original,
            repaired_text=original,
            changes=[],
            findings=[],
            copied_assets=[],
        )
        file_results.append(file_result)

    # 逐规则、跨文件执行。来自复查报告的规则先在整套章节中做总匹配数门禁，
    # 避免一个合法的 A' 恰好在另一个文件中被逐文件误改。
    for rule in rules:
        if rule.total_guard:
            total = sum(
                len(find_rule_candidates(item.repaired_text, item.relative_path, rule))
                for item in file_results
            )
            if total == 0 and rule.source.startswith("audit:"):
                all_findings.append(
                    Finding(
                        "warning",
                        "AUDIT_PATCH_TEXT_NOT_FOUND",
                        rule.file_glob,
                        None,
                        f"复查报告补丁 {rule.rule_id} 的错误原文未精确命中；可能已修好，也可能排版形式不同，需核对。",
                    )
                )
                continue
            too_few = total < rule.min_matches
            too_many = rule.max_matches is not None and total > rule.max_matches
            if too_few or too_many:
                expected = (
                    f"{rule.min_matches}～{rule.max_matches}"
                    if rule.max_matches is not None
                    else f"至少 {rule.min_matches}"
                )
                all_findings.append(
                    Finding(
                        "blocker",
                        "PATCH_TOTAL_GUARD_FAILED",
                        rule.file_glob,
                        None,
                        f"补丁 {rule.rule_id} 在整套文件中预期匹配 {expected} 次，实际 {total} 次；未执行。",
                    )
                )
                continue
            effective_rule = dataclasses.replace(rule, min_matches=0, max_matches=None)
        else:
            effective_rule = rule
        for item in file_results:
            repaired, changes, findings = apply_patch_rule(
                item.repaired_text, item.relative_path, effective_rule
            )
            item.repaired_text = repaired
            item.changes.extend(changes)
            item.findings.extend(findings)
            all_changes.extend(changes)
            all_findings.extend(findings)

    fallback_count, fallback_findings = insert_source_fallbacks(
        file_results,
        fallback_rules,
        source_pdf,
        output_root if not source_is_file else output.parent,
        render_dpi,
        dry_run,
    )
    all_findings.extend(fallback_findings)

    for item in file_results:
        scan_findings = scan_markdown(item.repaired_text, item.source_path, item.relative_path)
        asset_findings, copied_assets = scan_and_copy_assets(
            item.repaired_text,
            item.source_path,
            item.target_path if not dry_run else None,
            source_root,
            output_root if not source_is_file else output.parent,
            item.relative_path,
            dry_run,
        )
        item.findings.extend(scan_findings)
        item.findings.extend(asset_findings)
        item.copied_assets = copied_assets
        all_findings.extend(scan_findings)
        all_findings.extend(asset_findings)

    if not dry_run:
        if source_is_file:
            atomic_write_text(output, file_results[0].repaired_text)
        else:
            output.mkdir(parents=True, exist_ok=True)
            for item in file_results:
                atomic_write_text(item.target_path, item.repaired_text)

    payload = build_report_payload(
        source,
        None if dry_run else output,
        file_results,
        all_changes,
        all_findings,
        audit_report,
        source_pdf,
        fallback_count,
        notes,
        dry_run,
    )
    report_path: Path | None = None
    if not dry_run:
        if source_is_file:
            report_path = output.with_name(f"{output.stem}_修复报告.md")
            json_path = output.with_name(f"{output.stem}_修复报告.json")
            state_path = output.with_name(f"{output.stem}_repair_state.json")
        else:
            report_path = output / "OCR定向修复报告.md"
            json_path = output / "OCR定向修复报告.json"
            state_path = output / "repair_state.json"
        atomic_write_text(report_path, report_markdown(payload))
        atomic_write_json(json_path, payload)
        atomic_write_json(
            state_path,
            {
                "schema_version": STATE_SCHEMA_VERSION,
                "script_version": SCRIPT_VERSION,
                "source": str(source.resolve()),
                "generated_at": now_iso(),
                "status": payload["status"],
            },
        )

    return RunResult(
        source=source,
        output=None if dry_run else output,
        report_path=report_path,
        files=file_results,
        changes=all_changes,
        findings=all_findings,
        fallbacks_inserted=fallback_count,
        status=payload["status"],
    )


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="ocr_repair_test_") as temp_name:
        root = Path(temp_name) / "book"
        chapters = root / "chapters"
        chapters.mkdir(parents=True)
        vector = chapters / "第03章_向量.md"
        matrix = chapters / "第02章_矩阵.md"
        atomic_write_text(
            vector,
            "# 第三章 向量\n\n"
            "关于向量组线性相关的条件是 $t \\gg s$，且向量组的秩满足 "
            "$r(\\mathrm I)\\le r(\\mathrm I)$。\n\n"
            "另一个不同问题保留 $u\\gg v$。\n\n"
            "$$\\begin{bmatrix}1&0\\\\0&1\\end{bmatrix}$$\n",
        )
        atomic_write_text(
            matrix,
            "# 第二章 矩阵\n\n"
            "伴随矩阵记作 $A^{\\bullet}$，也写成 $A'$。\n\n"
            "转置的旧记法 $B'$ 不应修改。\n\n"
            "无上下文的 $C^{\\bullet}$ 只报警，不猜改。\n",
        )
        source_hashes = {path: sha256_file(path) for path in (vector, matrix)}
        output = Path(temp_name) / "book_已修复"
        result1 = process_input(
            root,
            output,
            builtin_linear_algebra_rules(),
            [],
            None,
            None,
            False,
            144,
            ["self-test"],
        )
        repaired_vector = (output / "chapters" / vector.name).read_text(encoding="utf-8")
        repaired_matrix = (output / "chapters" / matrix.name).read_text(encoding="utf-8")
        assert "$t>s$" in repaired_vector
        assert r"$r(\mathrm{I})\le r(\mathrm{II})$" in repaired_vector
        assert r"$u\gg v$" in repaired_vector
        assert repaired_matrix.count("$A^*$") == 2
        assert "$B'$" in repaired_matrix
        assert r"$C^{\bullet}$" in repaired_matrix
        assert all(sha256_file(path) == digest for path, digest in source_hashes.items())
        assert any(item.code == "DOUBLE_GREATER_REMAINS" for item in result1.findings)
        assert any(item.code == "ADJUGATE_BULLET_REMAINS" for item in result1.findings)

        first_hashes = {
            path.relative_to(output): sha256_file(path)
            for path in output.rglob("*.md")
        }
        result2 = process_input(
            root,
            output,
            builtin_linear_algebra_rules(),
            [],
            None,
            None,
            False,
            144,
            ["self-test"],
        )
        second_hashes = {
            path.relative_to(output): sha256_file(path)
            for path in output.rglob("*.md")
        }
        assert first_hashes == second_hashes
        assert len(result1.changes) == len(result2.changes) == 4

        dry_output = Path(temp_name) / "dry_run_must_not_exist"
        process_input(
            root,
            dry_output,
            builtin_linear_algebra_rules(),
            [],
            None,
            None,
            True,
            144,
            ["self-test-dry-run"],
        )
        assert not dry_output.exists()

        guard_rule = PatchRule(
            rule_id="GUARD_TEST",
            pattern="向量组",
            replacement="SHOULD_NOT_APPLY",
            action="replace",
            min_matches=1,
            max_matches=1,
        )
        unchanged, changes, findings = apply_patch_rule(
            vector.read_text(encoding="utf-8"), "chapters/第03章_向量.md", guard_rule
        )
        assert not changes and findings and "SHOULD_NOT_APPLY" not in unchanged

        audit = Path(temp_name) / "audit.md"
        atomic_write_text(
            audit,
            "# 报告\n\n把 \\(x>y\\) 写成 \\(x\\gg y\\)。\n\n"
            "### 第 2 章 矩阵\n\n- PDF 53：整道题干缺失。\n",
        )
        audit_patches, audit_fallbacks, _ = parse_audit_report(audit)
        assert any("x" in rule.pattern and rule.replacement == "x>y" for rule in audit_patches)
        assert audit_fallbacks and audit_fallbacks[0].pdf_page == 53

        duplicate_root = Path(temp_name) / "duplicate_book"
        (duplicate_root / "chapters").mkdir(parents=True)
        atomic_write_text(duplicate_root / "chapters" / "a.md", "# A\n\n$x\\gg y$\n")
        atomic_write_text(duplicate_root / "chapters" / "b.md", "# B\n\n$x\\gg y$\n")
        duplicate_rule = PatchRule(
            rule_id="TOTAL_GUARD_TEST",
            pattern=r"x\\gg\s*y",
            replacement="x>y",
            math_only=True,
            min_matches=1,
            max_matches=1,
            total_guard=True,
            source="rules:self-test",
        )
        duplicate_result = process_input(
            duplicate_root,
            Path(temp_name) / "duplicate_output",
            [duplicate_rule],
            [],
            None,
            None,
            True,
            144,
            ["self-test-total-guard"],
        )
        assert not duplicate_result.changes
        assert any(item.code == "PATCH_TOTAL_GUARD_FAILED" for item in duplicate_result.findings)

        # 复查报告的全局唯一性门禁与 LaTeX 可选花括号兼容。
        detailed_audit = Path(temp_name) / "detailed_audit.md"
        atomic_write_text(
            detailed_audit,
            "# 报告\n\n"
            "把 \\(t>s\\) 写成 \\(t\\gg s\\)，把 "
            "\\(r(\\mathrm I)\\le r(\\mathrm{II})\\) 写成 "
            "\\(r(\\mathrm I)\\le r(\\mathrm I)\\)，把伴随矩阵 "
            "\\(A^*\\) 识成 \\(A'\\) 或 \\(A^\\bullet\\)。\n",
        )
        report_rules, _, _ = parse_audit_report(detailed_audit)
        output_from_report = Path(temp_name) / "book_报告修复"
        report_result = process_input(
            root,
            output_from_report,
            [*report_rules, *builtin_linear_algebra_rules()],
            [],
            detailed_audit,
            None,
            False,
            144,
            ["self-test-report"],
        )
        assert len(report_result.changes) == 4
        assert not any(item.code == "PATCH_TOTAL_GUARD_FAILED" for item in report_result.findings)

        # 无法反推的漏题使用源 PDF 原页回退，并验证图片链接真实存在。
        try:
            import fitz  # type: ignore
        except ImportError:
            fitz = None
        if fitz is not None:
            pdf = Path(temp_name) / "source.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Authoritative source page")
            document.save(pdf)
            document.close()
            fallback_output = Path(temp_name) / "book_原页回退"
            fallback_result = process_input(
                root,
                fallback_output,
                builtin_linear_algebra_rules(),
                [
                    FallbackRule(
                        rule_id="FALLBACK_TEST",
                        pdf_page=1,
                        chapter_number=2,
                        file_glob="**/*矩阵*.md",
                    )
                ],
                None,
                pdf,
                False,
                96,
                ["self-test-fallback"],
            )
            fallback_md = (fallback_output / "chapters" / matrix.name).read_text(encoding="utf-8")
            assert fallback_result.fallbacks_inserted == 1
            assert "OCR 定向修复：原 PDF 保真页" in fallback_md
            assert list((fallback_output / "repair_assets").glob("*.png"))
            assert not any(item.code == "MISSING_IMAGE" for item in fallback_result.findings)

    print("自检通过：精确修复、上下文防误改、阻断保护、原文件保护、幂等重跑、报告解析均正常。")
    return 0


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="针对既有数学 OCR Markdown 做精确补丁、风险扫描和 PDF 原页回退。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="一个或多个 Markdown 文件/OCR 输出目录")
    parser.add_argument("-o", "--output", type=Path, help="单输入时的输出文件/目录")
    parser.add_argument("--audit-report", type=Path, help="复查报告；未指定时尝试在输入附近自动发现")
    parser.add_argument("--source-pdf", type=Path, help="源 PDF；未指定时尝试从 ocr_state.json 发现")
    parser.add_argument("--rules", type=Path, help="额外的精确 JSON 勘误规则")
    parser.add_argument(
        "--profile",
        choices=["linear-algebra-2026-08-30", "none"],
        default="linear-algebra-2026-08-30",
        help="内置的保守修复规则",
    )
    parser.add_argument("--render-dpi", type=int, default=160, help="PDF 原页回退图分辨率")
    parser.add_argument("--dry-run", action="store_true", help="只扫描并显示计划，不写任何文件")
    parser.add_argument("--write-rules-template", type=Path, help="写出规则模板后退出")
    parser.add_argument("--self-test", action="store_true", help="运行内置回归测试后退出")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    if args.self_test:
        return run_self_test()
    if args.write_rules_template:
        write_rules_template(args.write_rules_template.resolve())
        print(f"已生成规则模板：{args.write_rules_template.resolve()}")
        return 0
    if not args.inputs:
        raise RepairError("请提供至少一个 Markdown 文件或 OCR 输出目录。")
    if args.output and len(args.inputs) != 1:
        raise RepairError("--output 只能与单个输入一起使用。")
    if not (72 <= args.render_dpi <= 600):
        raise RepairError("--render-dpi 必须位于 72～600。")

    base_rules = builtin_linear_algebra_rules() if args.profile != "none" else []
    explicit_patches: list[PatchRule] = []
    explicit_fallbacks: list[FallbackRule] = []
    if args.rules:
        explicit_patches, explicit_fallbacks = load_rule_file(args.rules.resolve())

    results: list[RunResult] = []
    for index, raw_input in enumerate(args.inputs, start=1):
        source = raw_input.expanduser().resolve()
        audit = args.audit_report.expanduser().resolve() if args.audit_report and len(args.inputs) == 1 else None
        if audit is None:
            audit = discover_audit_report(source)
        pdf = args.source_pdf.expanduser().resolve() if args.source_pdf and len(args.inputs) == 1 else None
        if pdf is None:
            pdf = discover_source_pdf(source)

        audit_patches: list[PatchRule] = []
        audit_fallbacks: list[FallbackRule] = []
        notes: list[str] = []
        if audit:
            if not audit.is_file():
                raise RepairError(f"复查报告不存在：{audit}")
            audit_patches, audit_fallbacks, audit_notes = parse_audit_report(audit)
            notes.append(f"已读取复查报告：{audit.name}")
            notes.extend(audit_notes)
        else:
            notes.append("未找到复查报告；只执行内置规则和风险扫描。")
        if pdf:
            notes.append(f"源 PDF：{pdf.name}")
        elif audit_fallbacks or explicit_fallbacks:
            notes.append("存在需原页回退的项目，但未找到源 PDF。")

        output = args.output.expanduser().resolve() if args.output else None
        # 报告中的明确勘误优先；内置规则只补充报告未覆盖的安全上下文修复。
        rules = [*audit_patches, *explicit_patches, *base_rules]
        fallbacks = [*audit_fallbacks, *explicit_fallbacks]
        print(f"[{index}/{len(args.inputs)}] 输入：{source}")
        print(f"  规则：{len(rules)} 条；原页回退：{len(fallbacks)} 页/裁图")
        result = process_input(
            source,
            output,
            rules,
            fallbacks,
            audit,
            pdf,
            args.dry_run,
            args.render_dpi,
            notes,
        )
        results.append(result)
        print(
            f"  修改 {len(result.changes)} 处；原页回退 {result.fallbacks_inserted}；"
            f"blocker {sum(item.severity == 'blocker' for item in result.findings)}；"
            f"warning {sum(item.severity == 'warning' for item in result.findings)}"
        )
        if result.output:
            print(f"  输出：{result.output}")
        if result.report_path:
            print(f"  报告：{result.report_path}")

    blockers = sum(
        item.severity == "blocker" for result in results for item in result.findings
    )
    if args.dry_run:
        print("试运行完成：没有创建或修改任何文件。")
    if blockers:
        print(f"仍有 {blockers} 个阻断项；请查看修复报告，程序没有把它们猜成公式。")
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RepairError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
