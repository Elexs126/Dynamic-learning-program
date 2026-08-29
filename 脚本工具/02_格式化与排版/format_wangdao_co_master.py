# -*- coding: utf-8 -*-
"""
王道考研《2027计算机组成原理考研复习指导》高精度结构化 Markdown 转换与质检引擎 (Master CO Formatter v5.0 Ultimate)
特性：
1. 408 知识点层级树状化 (章 / 节 / 小节 / 考纲 / 复习提示 / 知识框架 / 常见问题和易混淆知识点 / 疑难点)
2. 选择题选项智能拆分 (- A. ... \n - B. ... \n - C. ... \n - D. ...)
3. 答案与解析智能高亮 (【答案】X \n **【解析】** ...)
4. x86 / MIPS 汇编、RTL 微操作传输 (PC->MAR) 与 C 语言代码智能代码块化 (```assembly / ```c)
5. 纯公式行智能提升为独立公式块 ($$N = (-1)^S \\times M \\times R^E$$)
6. 智能修复十六进制地址 0\\times 404 -> 0x404
7. 智能保护人名中点号 (冯·诺依曼，不被误转为 \\cdot)
8. 严格 0 裸 TeX 命令
"""

import os
import re
import json

CHAPTER_CONFIG = [
    {
        "file": "第01章_计算机系统概述.md",
        "title": "第1章 计算机系统概述",
        "start_page": 13,
        "end_page": 24,
    },
    {
        "file": "第02章_数据的表示和运算.md",
        "title": "第2章 数据的表示和运算",
        "start_page": 25,
        "end_page": 88,
    },
    {
        "file": "第03章_存储系统.md",
        "title": "第3章 存储系统",
        "start_page": 89,
        "end_page": 159,
    },
    {
        "file": "第04章_指令系统.md",
        "title": "第4章 指令系统",
        "start_page": 160,
        "end_page": 206,
    },
    {
        "file": "第05章_中央处理器.md",
        "title": "第5章 中央处理器",
        "start_page": 207,
        "end_page": 285,
    },
    {
        "file": "第06章_总线.md",
        "title": "第6章 总线",
        "start_page": 286,
        "end_page": 302,
    },
    {
        "file": "第07章_输入输出系统.md",
        "title": "第7章 输入/输出系统",
        "start_page": 303,
        "end_page": 340,
    },
]

ASM_KEYWORDS = [
    r"^\s*(mov|add|sub|mul|div|inc|dec|and|or|xor|not|shl|shr|sar|sal|rol|ror)\b",
    r"^\s*(jmp|je|jne|jz|jnz|jg|jge|jl|jle|ja|jae|jb|jbe|call|ret|push|pop)\b",
    r"^\s*(lw|sw|lh|sh|lb|sb|lui|addu|subu|slt|slti|sll|srl|sra|beq|bne|jal|jr)\b",
    r"^\s*(MAR|MDR|PC|IR|ACC|PSW|SP|ALU)\s*[\<\\-]*\\to",
    r"^\s*\(PC\)\s*\\to", r"^\s*\(MAR\)\s*\\to", r"^\s*M\(MAR\)\s*\\to",
    r"\bprintf\s*\(", r"\bscanf\s*\(", r"\bmain\s*\(\)", r"\bsizeof\s*\(",
    r"\btypedef\s+struct\b", r"^\s*int\s+[a-zA-Z_0-9]+;", r"^\s*short\s+[a-zA-Z_0-9]+;",
    r"^\s*float\s+[a-zA-Z_0-9]+;", r"^\s*double\s+[a-zA-Z_0-9]+;",
]

ALL_TEX_COMMANDS = [
    r"\alpha", r"\beta", r"\gamma", r"\delta", r"\varepsilon", r"\theta",
    r"\lambda", r"\mu", r"\xi", r"\eta", r"\sigma", r"\tau", r"\varphi", r"\omega",
    r"\pi", r"\Lambda", r"\Sigma", r"\Phi", r"\Omega", r"\Delta",
    r"\pm", r"\neq", r"\le", r"\ge", r"\in", r"\notin", r"\to", r"\infty",
    r"\sum", r"\prod", r"\int", r"\iint", r"\sqrt", r"\times", r"\div", r"\cdot",
    r"\partial", r"\oplus", r"\dots", r"\cdots", r"\vdots", r"\ddots"
]

def is_asm_or_code_line(line):
    s = line.strip()
    if not s:
        return False
    chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", s))
    if chinese_chars > 3 and not (s.startswith("//") or s.startswith(";")):
        return False
    if any(re.search(kw, s, re.IGNORECASE) for kw in ASM_KEYWORDS):
        return True
    if s in ["{", "}", "};"]:
        return True
    if s.endswith(";") and (len(re.findall(r"[a-zA-Z0-9_\*\=\(\)\s,\$\-\+]", s)) == len(s)):
        return True
    return False

def clean_noise(line):
    # 保护中文人名中的点号
    line = re.sub(r"([\u4e00-\u9fa5])\s*\\cdot\s*([\u4e00-\u9fa5])", r"\1·\2", line)
    
    # 修复十六进制地址 0\times 404 -> 0x404
    line = re.sub(r"\b0\s*\\times\s*([0-9a-fA-F]{2,8})\b", r"0x\1", line)
    
    line = re.sub(r"^\d+\s+2027年.*", "", line)
    line = re.sub(r"^第\s*\d+\s*章.*?\d+$", "", line)
    line = re.sub(r"^王道考研.*", "", line)
    line = re.sub(r"^王道论坛.*", "", line)
    line = re.sub(r"^王道训练营.*", "", line)
    line = re.sub(r"^关注公众号.*", "", line)
    line = re.sub(r"^扫码看视频.*", "", line)
    line = re.sub(r"^视频讲解.*", "", line)
    line = re.sub(r"^手最快资料同步.*", "", line)
    line = re.sub(r"^官方开源.*", "", line)
    line = re.sub(r"^最新配套视频请上.*", "", line)
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

    # 保护中文人名中的点号
    line = re.sub(r"([\u4e00-\u9fa5])\s*\\cdot\s*([\u4e00-\u9fa5])", r"\1·\2", line)

    # 纯数学公式推导行识别 (0 汉字且包含算式)
    chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", line))
    has_math_ops = bool(re.search(r"(=|\\times|\\div|\+|\-|\*|/|\^|_)", line))
    if chinese_chars == 0 and has_math_ops and len(line) > 2 and not line.endswith(";") and not line.startswith("//"):
        clean_inner = line.replace("$", "").strip()
        return prefix + f"$${clean_inner}$$"

    # 包装补码与原码表示 [X]补 -> $[X]_{\text{补}}$
    line = re.sub(r"\[([a-zA-Z0-9_\+\-]+)\]\s*(原|补|反|移)", r"$[\1]_{\\text{\2}}$", line)
    
    # 修复常见路径反斜杠
    line = re.sub(r"\\(file|dir|root|path|user|home)\b", r"/\\1", line)

    # 包装 $2^{32}$, $2^{16}$, $2^{10}$
    line = re.sub(r"\b2\^(\d+)\b", r"$2^{\1}$", line)
    line = re.sub(r"\b2\^{(\d+)}\b", r"$2^{\1}$", line)
    
    # 包装纯算式与时间公式
    line = re.sub(r"\b(\d+)\s*([\+\-\*\/])\s*(\d+)\s*=\s*(\d+)\b", r"$\1 \2 \3 = \4$", line)
    
    # 包装裸 TeX 命令
    for sym in ALL_TEX_COMMANDS:
        pattern = r"(?<!\$)" + re.escape(sym) + r"(?!\$)"
        line = re.sub(pattern, lambda m, s=sym: f" ${s}$ ", line)

    line = re.sub(r"\$\s*([^\$]+?)\s*\$\s*([\+\-\*\/=><≠,;]+)\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2 \3$", line)
    line = re.sub(r"\$\s*([^\$]+?)\s*\$\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2$", line)
    line = re.sub(r"\s+", " ", line).strip()

    # 全行扫描兜底：确保普通文本区间不存在残余裸 TeX
    parts = []
    last_idx = 0
    for match in re.finditer(r"\$[^\$]+?\$", line):
        plain = line[last_idx:match.start()]
        if "\\" in plain:
            plain = re.sub(r"\\[a-zA-Z]+(?:_\{[^{}\s]+\}|_\d+|\^[^{}\s]+|\^\d+)?", r"$\g<0>$", plain)
        parts.append(plain)
        parts.append(match.group(0))
        last_idx = match.end()
        
    tail = line[last_idx:]
    if "\\" in tail:
        tail = re.sub(r"\\[a-zA-Z]+(?:_\{[^{}\s]+\}|_\d+|\^[^{}\s]+|\^\d+)?", r"$\g<0>$", tail)
    parts.append(tail)
    
    final_line = "".join(parts)
    return prefix + final_line.strip()

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
            if pno == start_p and (line.startswith("第1章") or line.startswith("第2章") or line.startswith("第3章") or line.startswith("第4章") or line.startswith("第5章") or line.startswith("第6章") or line.startswith("第7章")):
                continue
            if pno == start_p and line in ["计算机系统概述", "数据的表示和运算", "存储系统", "指令系统", "中央处理器", "总线", "输入/输出系统", "输入输出系统"]:
                continue

            # 智能汇编与代码块识别
            if is_asm_or_code_line(line):
                if not in_code_block:
                    md_lines.append("\n```assembly")
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
            if "本章小结" in line or line.endswith("本章小结"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = False
                continue
            if "常见问题和易混淆知识点" in line or line.endswith("常见问题和易混淆知识点"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = False
                continue

            # 识别二级节标题 (如 1.1 计算机发展历程)
            if re.match(r"^\*?\d+\.\d+\s+[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n### {line}\n")
                in_answers_section = False
                continue
                
            # 识别三级小节标题 (如 1.1.1 计算机硬件的发展)
            if re.match(r"^\*?\d+\.\d+\.\d+\s+[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 识别四级标题 (如 1．硬件系统, 1. 概念)
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

            # 识别选择题题干编号 (如 01．计算机硬件能够直接执行... 或 11．【2012统考真题】...)
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
    base_dir = r"d:\考研动态学习项目\配套讲义\王道2027计算机组成原理考研复习指导"
    cache_file = os.path.join(base_dir, "ocr_cache.json")
    
    if not os.path.exists(cache_file):
        print(f"错误：未找到 OCR 缓存文件: {cache_file}")
        return
        
    print(f"正在从高精度缓存 {cache_file} 全量格式化生成 7 大章节 Markdown 讲义...")
    with open(cache_file, "r", encoding="utf-8") as f:
        pages_dict = json.load(f)
        
    for cfg in CHAPTER_CONFIG:
        print(f" -> 正在生成: {cfg['title']} (P{cfg['start_page']}~P{cfg['end_page']})...")
        md_text = format_chapter(cfg, pages_dict)
        out_path = os.path.join(base_dir, cfg["file"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_text)
            
    print("\n恭喜！《王道2027计算机组成原理考研复习指导》全书 7 大章节已全部高质量重构生成完成！")

if __name__ == "__main__":
    main()
