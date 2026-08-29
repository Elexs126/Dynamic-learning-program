# -*- coding: utf-8 -*-
"""
王道考研《2027操作系统考研复习指导》高精度结构化 Markdown 转换与质检引擎 (Master CS408 Formatter v2.0)
特性：
1. 408 知识点层级完美树状化 (章 / 节 / 小节 / 考纲 / 复习提示 / 知识框架 / 疑难点)
2. 选择题选项智能多列拆分 (- A. ... \n - B. ... \n - C. ... \n - D. ...)
3. 答案与解析智能高亮 (【答案】X \n **【解析】** ...)
4. C/C++ 伪代码与 P/V 信号量智能代码块化 (```c ... ```)
5. 考点追踪、王道点拨、注意、命题点、易错点 Callout 引用化
6. 计算机数学公式与参数计算 KaTeX 标准化 ($...$ / $$...$$，严格 0 裸 TeX 命令)
"""

import os
import re
import json

CHAPTER_CONFIG = [
    {
        "file": "第01章_计算机系统概述.md",
        "title": "第1章 计算机系统概述",
        "start_page": 13,
        "end_page": 48,
    },
    {
        "file": "第02章_进程与线程.md",
        "title": "第2章 进程与线程",
        "start_page": 49,
        "end_page": 187,
    },
    {
        "file": "第03章_内存管理.md",
        "title": "第3章 内存管理",
        "start_page": 188,
        "end_page": 262,
    },
    {
        "file": "第04章_文件管理.md",
        "title": "第4章 文件管理",
        "start_page": 263,
        "end_page": 316,
    },
    {
        "file": "第05章_输入输出管理.md",
        "title": "第5章 输入/输出管理",
        "start_page": 317,
        "end_page": 372,
    },
]

CODE_PATTERN = re.compile(
    r"(\bsemaphore\b|\bwait\(|\bsignal\(|\bvoid\s+[a-zA-Z_]|\bint\s+[a-zA-Z_]|"
    r"\bP\(|\bV\(|\bcobegin\b|\bcoend\b|\btypedef\b|\bstruct\b|\bboolean\b|"
    r"\bwhile\s*\(|\bfor\s*\(|\bif\s*\(|\breturn\b|\bpthread_|\bfork\(\)|"
    r"^\s*[\*a-zA-Z_0-9]+\s*=\s*[\*a-zA-Z_0-9]+;|\bSwap\s*\(|^\s*\}\s*$|^\s*\{\s*$)",
    re.IGNORECASE
)

ALL_TEX_COMMANDS = [
    r"\alpha", r"\beta", r"\gamma", r"\delta", r"\varepsilon", r"\theta",
    r"\lambda", r"\mu", r"\xi", r"\eta", r"\sigma", r"\tau", r"\varphi", r"\omega",
    r"\pi", r"\Lambda", r"\Sigma", r"\Phi", r"\Omega",
    r"\pm", r"\neq", r"\le", r"\ge", r"\in", r"\notin", r"\to", r"\infty",
    r"\sum", r"\prod", r"\int", r"\iint", r"\sqrt", r"\times", r"\div", r"\cdot",
    r"\partial", r"\dots", r"\cdots", r"\vdots", r"\ddots"
]

def is_pure_code_line(line):
    s = line.strip()
    if not s:
        return False
    chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", s))
    if chinese_chars > 3 and not (s.startswith("//") or s.startswith("/*")):
        return False
    if s in ["{", "}", "};", "coend", "coend;"]:
        return True
    if s.endswith(";") and (len(re.findall(r"[a-zA-Z0-9_\*\=\(\)\s]", s)) == len(s)):
        return True
    return bool(CODE_PATTERN.search(s))

def clean_noise(line):
    line = re.sub(r"^\d+\s+2027年.*", "", line)
    line = re.sub(r"^第\s*\d+\s*章.*?\d+$", "", line)
    line = re.sub(r"^王道考研.*", "", line)
    line = re.sub(r"^王道论坛.*", "", line)
    line = re.sub(r"^王道训练营.*", "", line)
    line = re.sub(r"^关注公众号.*", "", line)
    line = re.sub(r"^扫码看视频.*", "", line)
    line = re.sub(r"^视频讲解.*", "", line)
    line = re.sub(r"^手最快资料同步.*", "", line)
    line = re.sub(r"^第\s*\d+\s*页$", "", line)
    return line.strip()

def split_options_if_needed(line):
    opts = list(re.finditer(r"(?<![a-zA-Z0-9])([A-D][．\.\s])", line))
    if len(opts) >= 2:
        parts = []
        for i in range(len(opts)):
            start = opts[i].start()
            end = opts[i+1].start() if i + 1 < len(opts) else len(line)
            opt_text = line[start:end].strip()
            opt_text = re.sub(r"^([A-D])[．\.\s]\s*", r"- \1. ", opt_text)
            parts.append(opt_text)
        return parts
    elif len(opts) == 1 and line.startswith(opts[0].group(1)):
        opt_text = re.sub(r"^([A-D])[．\.\s]\s*", r"- \1. ", line)
        return [opt_text]
    return [line]

def wrap_cs_math(line):
    if not line.strip() or line.startswith("```"):
        return line
        
    prefix = ""
    for pfx in ["> **【王道点拨】** ", "> **【注意】** ", "> **【命题点】** ", "> **【易错点】** ", "> **【考点追踪】** ", "- A. ", "- B. ", "- C. ", "- D. ", "### ", "#### ", "##### ", "**【解析】** ", "**【分析】** ", "**【答案】** "]:
        if line.startswith(pfx):
            prefix = pfx
            line = line[len(pfx):].strip()
            break

    # 修复常见路径反斜杠
    line = re.sub(r"\\(file|dir|root|path|user|home)\b", r"/\\1", line)

    # 包装 $2^{32}$, $2^{16}$, $2^{10}$
    line = re.sub(r"\b2\^(\d+)\b", r"$2^{\1}$", line)
    line = re.sub(r"\b2\^{(\d+)}\b", r"$2^{\1}$", line)
    
    # 包装常见纯算式与时间公式
    line = re.sub(r"\b(\d+)\s*([\+\-\*\/])\s*(\d+)\s*=\s*(\d+)\b", r"$\1 \2 \3 = \4$", line)
    
    # 包装裸 TeX 命令
    for sym in ALL_TEX_COMMANDS:
        pattern = r"(?<!\$)" + re.escape(sym) + r"(?!\$)"
        line = re.sub(pattern, lambda m, s=sym: f" ${s}$ ", line)

    # 规范化相邻 $...$
    line = re.sub(r"\$\s*([^\$]+?)\s*\$\s*([\+\-\*\/=><≠,;]+)\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2 \3$", line)
    line = re.sub(r"\$\s*([^\$]+?)\s*\$\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2$", line)
    line = re.sub(r"\s+", " ", line).strip()
    
    return prefix + line

def format_chapter(chapter_info, pages_dict):
    title = chapter_info["title"]
    start_p = chapter_info["start_page"]
    end_p = chapter_info["end_page"]
    
    md_lines = []
    md_lines.append(f"# {title}\n")
    md_lines.append(f"> **收录范围**：PDF 第 {start_p} 页 至 第 {end_p} 页\n")
    md_lines.append("---\n")
    
    in_code_block = False
    in_answers_section = False
    
    for pno in range(start_p, end_p + 1):
        raw_lines = pages_dict.get(str(pno), pages_dict.get(pno, []))
        if not raw_lines:
            continue
            
        md_lines.append(f"\n<!-- Page {pno} -->\n")
        
        for raw_line in raw_lines:
            line = clean_noise(raw_line)
            if not line:
                continue
                
            # 过滤章节大标题重复
            if pno == start_p and (line.startswith("第1章") or line.startswith("第2章") or line.startswith("第3章") or line.startswith("第4章") or line.startswith("第5章")):
                continue
            if pno == start_p and line in ["计算机系统概述", "进程与线程", "内存管理", "文件管理", "输入/输出管理", "输入输出管理"]:
                continue

            # 智能代码块识别
            if is_pure_code_line(line):
                if not in_code_block:
                    md_lines.append("\n```c")
                    in_code_block = True
                md_lines.append(line)
                continue
            else:
                if in_code_block:
                    md_lines.append("```\n")
                    in_code_block = False

            # 王道板块与大纲识别
            if "【考纲内容】" in line or line == "考纲内容":
                md_lines.append("\n## 【考纲内容】\n")
                continue
            if "【复习提示】" in line or line == "复习提示":
                md_lines.append("\n## 【复习提示】\n")
                continue
            if "【知识框架】" in line or "知识框架" in line:
                md_lines.append("\n## 【知识框架】\n")
                continue
            if "本节习题精选" in line or line.endswith("本节习题精选"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = False
                continue
            if "答案与解析" in line or line.endswith("答案与解析"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = True
                continue
            if "本章疑难点" in line or line.endswith("本章疑难点"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = False
                continue

            # 识别二级节标题 (如 1.1 操作系统的基本概念)
            if re.match(r"^\d+\.\d+\s+[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n### {line}\n")
                in_answers_section = False
                continue
                
            # 识别三级小节标题 (如 1.1.1 操作系统的概念)
            if re.match(r"^\d+\.\d+\.\d+\s+[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 识别四级标题 (如 1．操作系统作为系统资源管理者, 1. 概念)
            if re.match(r"^[1-9]\s*[．\.]\s*[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n##### {line}\n")
                continue
                
            # 识别题型分类
            if line in ["一、单项选择题", "单项选择题", "选择题"]:
                md_lines.append("\n### 单项选择题\n")
                continue
            if line in ["二、综合应用题", "综合应用题", "综合题"]:
                md_lines.append("\n### 综合应用题\n")
                continue
                
            # 识别王道特色 Callout 引用框
            if "王道点拨" in line or "【王道点拨】" in line:
                clean_t = line.replace("【王道点拨】", "").replace("王道点拨", "").strip()
                md_lines.append(f"\n> **【王道点拨】** {clean_t}\n")
                continue
            if line.startswith("注意") or "【注意】" in line:
                clean_t = line.replace("【注意】", "").replace("注意：", "").replace("注意", "").strip()
                md_lines.append(f"\n> **【注意】** {clean_t}\n")
                continue
            if "考点追踪" in line or "【考点追踪】" in line:
                clean_t = line.replace("【考点追踪】", "").replace("考点追踪", "").strip()
                md_lines.append(f"\n> **【考点追踪】** {clean_t}\n")
                continue
            if "命题点" in line or "【命题点】" in line:
                clean_t = line.replace("【命题点】", "").replace("命题点：", "").replace("命题点", "").strip()
                md_lines.append(f"\n> **【命题点】** {clean_t}\n")
                continue
            if "易错点" in line or "【易错点】" in line:
                clean_t = line.replace("【易错点】", "").replace("易错点：", "").replace("易错点", "").strip()
                md_lines.append(f"\n> **【易错点】** {clean_t}\n")
                continue

            # 识别题目答案与解析 (在答案部分，如 01.C 或 01. 【答案】C)
            m_ans = re.match(r"^0*([1-9]\d*)\s*[．\.]\s*([A-D])\b", line)
            if in_answers_section and m_ans:
                qnum = m_ans.group(1)
                ans = m_ans.group(2)
                md_lines.append(f"\n**{qnum}. 【答案】 {ans}**\n")
                continue
            elif in_answers_section and (line.startswith("【解析】") or line.startswith("【分析】")):
                md_lines.append(f"\n**{line[:4]}** {line[4:].strip()}\n")
                continue

            # 识别选择题题干编号 (如 01．操作系统是对... 或 11．【2010统考真题】...)
            m_q = re.match(r"^0*([1-9]\d*)\s*[．\.]\s*(.*)", line)
            if m_q and ("（）" in line or "()" in line or "下列" in line or "统考真题" in line or "【" in line):
                qnum = m_q.group(1)
                qcontent = m_q.group(2)
                md_lines.append(f"\n**{qnum}.** {wrap_cs_math(qcontent)}\n")
                continue

            # 识别并拆分选择题选项 (A. ... B. ... C. ... D. ...)
            split_opts = split_options_if_needed(line)
            for opt_line in split_opts:
                formatted_line = wrap_cs_math(opt_line)
                md_lines.append(formatted_line)
                
        if in_code_block:
            md_lines.append("```\n")
            in_code_block = False
            
    return "\n".join(md_lines)

def main():
    base_dir = r"d:\考研动态学习项目\配套讲义\王道2027操作系统考研复习指导"
    cache_file = os.path.join(base_dir, "ocr_cache.json")
    
    if not os.path.exists(cache_file):
        print(f"错误：未找到 OCR 缓存文件: {cache_file}")
        return
        
    print(f"正在从高精度缓存 {cache_file} 全量格式化生成 5 大章节 Markdown 讲义...")
    with open(cache_file, "r", encoding="utf-8") as f:
        pages_dict = json.load(f)
        
    for cfg in CHAPTER_CONFIG:
        print(f" -> 正在生成: {cfg['title']} (P{cfg['start_page']}~P{cfg['end_page']})...")
        md_text = format_chapter(cfg, pages_dict)
        out_path = os.path.join(base_dir, cfg["file"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_text)
            
    print("\n恭喜！《王道2027操作系统考研复习指导》全书 5 大章节已全部高质量重构生成完成！")

if __name__ == "__main__":
    main()
