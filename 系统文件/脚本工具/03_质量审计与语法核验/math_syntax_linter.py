#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学公式与文档排版结构自动化质量审计引擎
支持：
1. 行内/行间数学定界符（$, $$, \\(, \\[）闭合与奇偶平衡性
2. 花括号（{}）嵌套配对与深度平衡
3. LaTeX 常用数学环境（aligned, matrix, array, cases, bmatrix, pmatrix 等）栈式闭合
4. 私有区（PUA）不可见乱码字符与替代字符检测
5. 裸 TeX 语法命令遗漏在公式外部扫描
6. 图片引用（![](assets/...)）本地物理存在性校验
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

LATEX_ENVIRONMENTS = (
    "aligned",
    "align",
    "align*",
    "array",
    "matrix",
    "bmatrix",
    "pmatrix",
    "vmatrix",
    "Vmatrix",
    "cases",
    "gathered",
    "gather",
    "gather*",
    "split",
    "multline",
    "multline*",
)

BEGIN_ENV_RE = re.compile(r"\\begin\{([a-zA-Z0-9*]+)\}")
END_ENV_RE = re.compile(r"\\end\{([a-zA-Z0-9*]+)\}")
BARE_TEX_RE = re.compile(
    r"\\[a-zA-Z]+(?![a-zA-Z])|"
    r"\\(?:alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|"
    r"Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|"
    r"frac|sqrt|sum|prod|int|iint|iiint|oint|lim|infty|partial|nabla|times|div|pm|mp|cdot|circ|cap|cup|subset|subseteq|in|notin|"
    r"leq|geq|neq|approx|equiv|sim|simeq|le|ge|ne|left|right|big|Big|bigg|Bigg|mathbf|mathit|mathrm|mathbb|mathcal|text|operatorname|"
    r"vec|hat|bar|tilde|dot|ddot|overline|underline|begin|end)"
)
IMAGE_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
PRIVATE_USE_RE = re.compile(r"[\uE000-\uF8FF\uFFF0-\uFFFF]")


def strip_fenced_code(text: str) -> str:
    """去除 Markdown 代码块以防止代码被误判为公式。"""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_fence = False
    fence_token = ""
    for line in lines:
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_token = stripped[:3]
                out.append(" " * len(line))
            else:
                out.append(line)
        else:
            if stripped.startswith(fence_token):
                in_fence = False
                out.append(" " * len(line))
            else:
                out.append(" " * len(line))
    return "".join(out)


def extract_math_spans(text: str) -> tuple[list[str], str, list[str]]:
    """提取公式并检测定界符闭合情况。"""
    spans: list[str] = []
    problems: list[str] = []
    chars = list(text)
    index = 0
    length = len(text)

    def escaped(position: int) -> bool:
        count = 0
        cursor = position - 1
        while cursor >= 0 and text[cursor] == "\\":
            count += 1
            cursor -= 1
        return count % 2 == 1

    pairs = {"\\(": "\\)", "\\[": "\\]", "$$": "$$", "$": "$"}
    while index < length:
        opener = None
        for token in ("\\[", "\\(", "$$", "$"):
            if text.startswith(token, index) and not escaped(index):
                opener = token
                break
        if opener is None:
            index += 1
            continue
        closer = pairs[opener]
        search_from = index + len(opener)
        cursor = search_from
        found = -1
        while cursor < length:
            if text.startswith(closer, cursor) and not escaped(cursor):
                if opener == "$" and text.startswith("$$", cursor):
                    cursor += 2
                    continue
                found = cursor
                break
            cursor += 1
        if found < 0:
            problems.append(f"未闭合数学定界符 {opener!r}，字符位置 {index}")
            index += len(opener)
            continue
        spans.append(text[search_from:found])
        for pos in range(index, found + len(closer)):
            chars[pos] = " "
        index = found + len(closer)
    return spans, "".join(chars), problems


def brace_balance_problem(formula: str) -> str | None:
    """检查单个公式内的花括号是否匹配。"""
    depth = 0
    escaped = False
    for char in formula:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return "出现多余的右花括号"
    if depth != 0:
        return f"花括号未配对，净差 {depth}"
    return None


def check_latex_environments(formula: str) -> dict[str, Any] | None:
    """栈式严格检查 LaTeX 数学环境的嵌套与闭合。"""
    tokens: list[tuple[str, str, int]] = []
    for match in BEGIN_ENV_RE.finditer(formula):
        tokens.append(("begin", match.group(1), match.start()))
    for match in END_ENV_RE.finditer(formula):
        tokens.append(("end", match.group(1), match.start()))
    tokens.sort(key=lambda item: item[2])

    stack: list[str] = []
    begins: list[str] = []
    ends: list[str] = []
    error: str | None = None

    for kind, name, _ in tokens:
        if kind == "begin":
            begins.append(name)
            stack.append(name)
        else:
            ends.append(name)
            if not stack:
                error = f"多余的 \\end{{{name}}}"
                break
            top = stack.pop()
            if top != name:
                error = f"环境闭合失配: \\begin{{{top}}} 与 \\end{{{name}}}"
                break
    if not error and stack:
        error = f"未闭合的 LaTeX 环境: {stack}"
    if begins or ends or error:
        return {
            "begin": begins,
            "end": ends,
            "error": error,
        }
    return None


def lint_markdown(text: str, base_dir: Path | None = None) -> dict[str, Any]:
    """对 Markdown 文本进行全量语法与图片审计。"""
    without_code = strip_fenced_code(text)
    formulas, outside_math, delimiter_problems = extract_math_spans(without_code)

    brace_problems: list[dict[str, Any]] = []
    environment_problems: list[dict[str, Any]] = []
    for idx, formula in enumerate(formulas, 1):
        bp = brace_balance_problem(formula)
        if bp:
            brace_problems.append({"formula_index": idx, "problem": bp, "snippet": formula[:60]})
        env_result = check_latex_environments(formula)
        if env_result and env_result.get("error"):
            environment_problems.append({
                "formula_index": idx,
                "error": env_result["error"],
                "begin": env_result["begin"],
                "end": env_result["end"],
            })

    # 扫描公式外残留的裸 TeX 命令
    common_allowlist = {"\\n", "\\t", "\\r", "\\\\", "\\*", "\\_", "\\[", "\\]", "\\(", "\\)", "\\{", "\\}", "\\$"}
    bare_cmds: list[str] = []
    for m in BARE_TEX_RE.finditer(outside_math):
        token = m.group(0)
        if token not in common_allowlist and len(token) > 1:
            bare_cmds.append(token)

    # 扫描私有区乱码
    pua_chars = PRIVATE_USE_RE.findall(text)

    # 扫描图片引用
    missing_images: list[str] = []
    total_images: list[str] = []
    if base_dir:
        for m in IMAGE_REF_RE.finditer(text):
            img_path_str = m.group(2).strip()
            total_images.append(img_path_str)
            img_file = (base_dir / img_path_str).resolve()
            if not img_file.exists():
                missing_images.append(img_path_str)

    has_errors = bool(
        delimiter_problems
        or brace_problems
        or environment_problems
        or bare_cmds
        or pua_chars
        or missing_images
    )

    return {
        "status": "pass" if not has_errors else "failed",
        "formula_count": len(formulas),
        "delimiter_problems": delimiter_problems,
        "brace_problems": brace_problems,
        "environment_problems": environment_problems,
        "bare_tex_commands": sorted(list(set(bare_cmds))),
        "bare_tex_count": len(bare_cmds),
        "private_use_count": len(pua_chars),
        "total_images_referenced": len(total_images),
        "missing_images": missing_images,
    }


def audit_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return lint_markdown(text, base_dir=path.parent)


def audit_directory(dir_path: Path) -> dict[str, Any]:
    md_files = sorted(dir_path.rglob("*.md"))
    results = {}
    total_formulas = 0
    total_images = 0
    passed = 0
    failed = 0
    for p in md_files:
        res = audit_file(p)
        total_formulas += res["formula_count"]
        total_images += res["total_images_referenced"]
        if res["status"] == "pass":
            passed += 1
        else:
            failed += 1
        results[str(p.relative_to(dir_path))] = res

    return {
        "summary": {
            "total_files": len(md_files),
            "passed_files": passed,
            "failed_files": failed,
            "total_formulas": total_formulas,
            "total_images": total_images,
        },
        "details": results,
    }


def main():
    parser = argparse.ArgumentParser(description="数学公式与文档排版语法核验工具")
    parser.add_argument("target", help="要检查的 Markdown 文件或目录路径")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    args = parser.parse_args()

    target_path = Path(args.target)
    if not target_path.exists():
        print(f"错误: 目标路径不存在: {target_path}", file=sys.stderr)
        sys.exit(1)

    if target_path.is_file():
        result = audit_file(target_path)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status_symbol = "✅ PASS" if result["status"] == "pass" else "❌ FAIL"
            print(f"[{status_symbol}] {target_path.name}")
            print(f"  公式数量: {result['formula_count']}")
            print(f"  引用图片: {result['total_images_referenced']}")
            if result["status"] != "pass":
                if result["delimiter_problems"]:
                    print(f"  定界符问题: {result['delimiter_problems']}")
                if result["brace_problems"]:
                    print(f"  花括号问题: {len(result['brace_problems'])} 处")
                if result["environment_problems"]:
                    print(f"  LaTeX 环境问题: {len(result['environment_problems'])} 处")
                if result["bare_tex_commands"]:
                    print(f"  裸 TeX 命令: {result['bare_tex_commands']}")
                if result["missing_images"]:
                    print(f"  缺失图片: {result['missing_images']}")
            sys.exit(0 if result["status"] == "pass" else 1)
    else:
        res = audit_directory(target_path)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            summary = res["summary"]
            print(f"==================================================")
            print(f"目录审计完成: {target_path}")
            print(f"总文件数: {summary['total_files']} | 通过: {summary['passed_files']} | 未通过: {summary['failed_files']}")
            print(f"累计公式: {summary['total_formulas']} | 累计图片引用: {summary['total_images']}")
            print(f"==================================================")
            for file_rel, file_res in res["details"].items():
                mark = "✅ PASS" if file_res["status"] == "pass" else "❌ FAIL"
                print(f"  [{mark}] {file_rel} (公式: {file_res['formula_count']}, 图片: {file_res['total_images_referenced']})")
                if file_res["status"] != "pass":
                    for k in ["delimiter_problems", "brace_problems", "environment_problems", "bare_tex_commands", "missing_images"]:
                        if file_res[k]:
                            print(f"      - {k}: {file_res[k]}")
            sys.exit(0 if summary["failed_files"] == 0 else 1)


if __name__ == "__main__":
    main()
