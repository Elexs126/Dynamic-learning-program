# -*- coding: utf-8 -*-
"""
全书系高品质数学排版全量重构与生成引擎 (Master Math-Grade Book Generator v3.0 Ultimate)
确保：
1. 0 裸 TeX 命令 (严格 100% 全部包裹在 $...$ 或 $$...$$ 中)
2. 彻底消歧 '入' -> '\lambda'
3. 彻底修复所有破损截断宏 (\lambd a -> \lambda, \cdo t -> \cdot, \sqr t -> \sqrt, \su m -> \sum 等)
4. 彻底规范上下标与转置/逆/伴随/二次型 (\alpha_1, A^T, A^{-1}, A^*, x^TAx, C^TAC)
"""

import os
import re
import json

MACRO_REPAIR_MAP = [
    (r"\\varepsilo\s*n?\b", r"\\varepsilon "),
    (r"\\inft\s*y?\b", r"\\infty "),
    (r"\\alph\s*a\b", r"\\alpha "),
    (r"\\alph\b", r"\\alpha "),
    (r"\\bet\s*a\b", r"\\beta "),
    (r"\\bet\b", r"\\beta "),
    (r"\\be\s*t\s*a\b", r"\\beta "),
    (r"\\be\s*t\b", r"\\beta "),
    (r"\\lamb\s*d\s*a\b", r"\\lambda "),
    (r"\\lambd\s*a\b", r"\\lambda "),
    (r"\\lambd\b", r"\\lambda "),
    (r"\\lamb\b", r"\\lambda "),
    (r"\\cdo\s*t\b", r"\\cdot "),
    (r"\\cdo\b", r"\\cdot "),
    (r"\\thet\s*a\b", r"\\theta "),
    (r"\\thet\b", r"\\theta "),
    (r"\\sqr\s*t\b", r"\\sqrt "),
    (r"\\sqr\b", r"\\sqrt "),
    (r"\\delt\s*a\b", r"\\delta "),
    (r"\\delt\b", r"\\delta "),
    (r"\\gam\s*m?\s*a\b", r"\\gamma "),
    (r"\\gam\b", r"\\gamma "),
    (r"\\sig\s*m?\s*a\b", r"\\sigma "),
    (r"\\sig\b", r"\\sigma "),
    (r"\\ome\s*g?\s*a\b", r"\\omega "),
    (r"\\ome\b", r"\\omega "),
    (r"\\Lambd\s*a\b", r"\\Lambda "),
    (r"\\Lambd\b", r"\\Lambda "),
    (r"\\et\s*a\b", r"\\eta "),
    (r"\\et\b", r"\\eta "),
    (r"\\ne\s*q\b", r"\\neq "),
    (r"\\ne\b", r"\\neq "),
    (r"\\su\s*m\b", r"\\sum "),
    (r"\\su\b", r"\\sum "),
    (r"\\di\s*v\b", r"\\div "),
    (r"\\t\s*o\b", r"\\to "),
    (r"\\p\s*m\b", r"\\pm "),
    (r"\\g\s*e\b", r"\\ge "),
    (r"\\l\s*e\b", r"\\le "),
    (r"\\alphaT\b", r"\\alpha^T "),
    (r"\\betaT\b", r"\\beta^T "),
    (r"\\alphai\b", r"\\alpha_i "),
    (r"\\betax\b", r"\\beta^T "),
]

ALL_TEX_COMMANDS = [
    r"\alpha", r"\beta", r"\gamma", r"\delta", r"\varepsilon", r"\theta",
    r"\lambda", r"\mu", r"\xi", r"\eta", r"\sigma", r"\tau", r"\varphi", r"\omega",
    r"\pi", r"\Lambda", r"\Sigma", r"\Phi", r"\Omega",
    r"\pm", r"\neq", r"\le", r"\ge", r"\in", r"\notin", r"\to", r"\infty",
    r"\sum", r"\prod", r"\int", r"\iint", r"\iiint", r"\oint",
    r"\cup", r"\cap", r"\emptyset", r"\subset", r"\subseteq",
    r"\sqrt", r"\times", r"\div", r"\cdot", r"\partial",
    r"\bmatrix", r"\vmatrix", r"\cases", r"\aligned", r"\quad", r"\qquad",
    r"\det", r"\dim", r"\ker", r"\operatorname", r"\dots", r"\cdots", r"\vdots", r"\ddots"
]

def clean_and_repair_broken_tokens(text):
    for pat, repl in MACRO_REPAIR_MAP:
        text = re.sub(pat, repl, text)
    text = text.replace("$$", "\nTEMP_DISPLAY_MATH\n")
    text = text.replace("$", "")
    text = text.replace("TEMP_DISPLAY_MATH", "$$")
    return text

def fix_math_confusions(text):
    # 1. 修复 \lambda 误识为汉字 '入'
    text = re.sub(r"([（\(|\s=><\+\-/,;，。])入([EIAXYZ\d_\\=+\-\s\),;，。])", r"\1\\lambda \2", text)
    text = re.sub(r"入([EIAXYZ]\b)", r"\\lambda \1", text)
    text = re.sub(r"特征值\s*入", r"特征值 \\lambda", text)
    text = re.sub(r"特征多项式.*?[|｜]入", lambda m: m.group(0).replace("入", "\\lambda "), text)
    text = re.sub(r"\|\s*入\s*E\s*-\s*A\s*\|", r"|\\lambda E - A|", text)
    text = re.sub(r"\|\s*入\s*E\s*-\s*B\s*\|", r"|\\lambda E - B|", text)
    text = re.sub(r"\|\s*入\s*E\s*-\s*C\s*\|", r"|\\lambda E - C|", text)
    text = re.sub(r"\(入E\s*-\s*A\)", r"(\\lambda E - A)", text)
    text = re.sub(r"（入E\s*-\s*A）", r"(\\lambda E - A)", text)
    text = re.sub(r"入_(\d+)", r"\\lambda_{\1}", text)
    text = re.sub(r"入(\d)\b", r"\\lambda_{\1}", text)
    text = re.sub(r"当\s*入\s*([=><≠])", r"当 \\lambda \1", text)
    text = re.sub(r"当\s*入\s*(\\le|\\ge|\\neq)", r"当 \\lambda \1", text)
    text = re.sub(r"入取何值", r"\\lambda 取何值", text)
    text = re.sub(r"参数\s*入", r"参数 \\lambda", text)
    text = re.sub(r"入为", r"\\lambda 为", text)
    text = re.sub(r"入是", r"\\lambda 是", text)
    text = re.sub(r"入有", r"\\lambda 有", text)
    text = re.sub(r"入满足", r"\\lambda 满足", text)
    text = re.sub(r"入的", r"\\lambda 的", text)
    text = re.sub(r"入\s*=\s*", r"\\lambda = ", text)
    text = re.sub(r"入\s*\\neq\s*", r"\\lambda \\neq ", text)
    text = re.sub(r"入\s*\\le\s*", r"\\lambda \\le ", text)
    text = re.sub(r"入\s*\\ge\s*", r"\\lambda \\ge ", text)
    
    text = re.sub(r"([A-Z])[\^'’`‘]{1,2}T\b", r"\1^T", text)
    text = re.sub(r"([A-Z])[\^'’`‘]{1,2}\*", r"\1^*", text)
    text = re.sub(r"([A-Z])[\^'’`‘]{1,2}-1\b", r"\1^{-1}", text)
    text = re.sub(r"([A-Z])\s*\*\s*([A-Z])", r"\1^*\2", text)
    text = re.sub(r"\bCAC\s*=\s*B\b", r"C^TAC = B", text)
    text = re.sub(r"\bCAC\s*=\s*\\Lambda\b", r"C^TAC = \\Lambda", text)
    text = re.sub(r"\bC\^TAC\s*=\s*A\b", r"C^TAC = \\Lambda", text)
    text = re.sub(r"\bxAx\b", r"x^TAx", text)
    text = re.sub(r"\bx\s*A\s*x\b", r"x^TAx", text)
    text = re.sub(r"Q-AQ\s*=\s*QAQ", r"Q^{-1}AQ = Q^TAQ", text)
    text = re.sub(r"Q\^TAQ\s*=\s*A\b", r"Q^TAQ = \\Lambda", text)
    text = re.sub(r"Q\^{-1}AQ\s*=\s*A\b", r"Q^{-1}AQ = \\Lambda", text)
    text = re.sub(r"Q\^{-1}AQ\s*=\s*Q\^TAQ\s*=\s*A\b", r"Q^{-1}AQ = Q^TAQ = \\Lambda", text)
    
    for sym in [r"\\alpha", r"\\beta", r"\\gamma", r"\\delta", r"\\eta", r"\\xi", r"\\lambda"]:
        text = re.sub(sym + r"(\d+)", sym + r"_{\1}", text)
        text = re.sub(sym + r"\s+(\d+)", sym + r"_{\1}", text)
    
    text = re.sub(r"\b([xyzabc])(\d)\b", r"\1_{\2}", text)
    text = re.sub(r"\b([xyzabc])_(\d+)", r"\1_{\2}", text)
    
    text = re.sub(r"\(a-6\)\^2", r"(a-b)^2", text)
    text = re.sub(r"\(a\s*-\s*6\)\^2", r"(a-b)^2", text)
    text = re.sub(r"r\s*\(\s*A\s*\)", r"r(A)", text)
    text = re.sub(r"r\s*\(\s*B\s*\)", r"r(B)", text)
    text = re.sub(r"r\s*\(\s*AB\s*\)", r"r(AB)", text)
    text = re.sub(r"r\s*\(\s*A\s*,\s*b\s*\)", r"r(A, b)", text)
    text = re.sub(r"r\s*\(\s*A\s*\|\s*b\s*\)", r"r(A|b)", text)
    text = re.sub(r"\|\s*kA\s*\|\s*=\s*k['’`\"]n\s*\|\s*A\s*\|", r"|kA| = k^n|A|", text)
    text = re.sub(r"\|\s*kA\s*\|\s*=\s*kn\s*\|\s*A\s*\|", r"|kA| = k^n|A|", text)
    
    text = re.sub(r"(\\alpha_{\d+})\s*十\s*", r"\1 + ", text)
    text = re.sub(r"([a-zA-Z\d_])\s*十\s*([a-zA-Z\d_\\])", r"\1 + \2", text)

    return text

def tokenize_and_wrap_math(line):
    if not line.strip() or line.startswith("<!--"):
        return line

    prefix = ""
    if line.startswith("#"):
        m_head = re.match(r"^(#+\s+)(.*)", line)
        if m_head:
            head_tag = m_head.group(1)
            rest = m_head.group(2)
            prefix = head_tag
            line = rest
            
    if line.startswith("> "):
        prefix += "> "
        line = line[2:]
    elif line.startswith(">"):
        prefix += "> "
        line = line[1:]
        
    if line.startswith("- "):
        prefix += "- "
        line = line[2:]
        
    for tag in ["**【解析】**", "**【解】**", "**【证】**", "**【分析】**", "**【评注】**", "**【编者注】**", "**【注】**", "【例题】", "【解析】", "【解】", "【证】", "【分析】"]:
        if line.startswith(tag):
            prefix += tag + " "
            line = line[len(tag):].strip()
            break

    chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", line))
    has_math_tokens = any(cmd in line for cmd in ALL_TEX_COMMANDS) or bool(re.search(r"[_^=+\-*/|]", line)) or bool(re.search(r"\\[a-zA-Z]+", line))
    
    if chinese_chars == 0 and has_math_tokens and len(line.strip()) > 1:
        clean_inner = line.strip().strip("$")
        return prefix + f"$${clean_inner}$$"

    token_pattern = re.compile(
        r"(\\[a-zA-Z]+(?:_{[^{}\s]+}|_\d+|\^[^{}\s]+|\^\d+)?|"
        r"[a-zA-Z]_\d+|"
        r"[a-zA-Z]\^[a-zA-Z0-9\+\-\*]+|"
        r"r\([A-Z,\|\s]+\)|"
        r"\|\s*[A-Z\d\s\-\\lambda\+\*=]+\s*\||"
        r"[a-zA-Z]\b(?:\s*[=><≠\+\-\*\/]\s*[a-zA-Z0-9\\]+)+|"
        r"\b\d+\s*[=><≠\+\-\*\/]\s*[a-zA-Z\d\\]+)"
    )

    def replace_math(m):
        frag = m.group(0).strip()
        if not frag:
            return ""
        return f" ${frag}$ "

    wrapped = token_pattern.sub(replace_math, line)

    # 兜底：对任何未包裹的 \cmd 强制加上 $...$
    def any_tex_repl(m):
        cmd = m.group(0)
        return f" ${cmd}$ "
        
    wrapped = re.sub(r"(?<!\$)\\[a-zA-Z]+(?:_\{[^{}\s]+\}|_\d+|\^[^{}\s]+|\^\d+)?(?!\$)", any_tex_repl, wrapped)

    # 规范化清理空格与合并相邻的 $...$ 表达
    wrapped = re.sub(r"\$\s*([\+\-\*\/=><≠,;]+)\s*\$", r"\1", wrapped)
    wrapped = re.sub(r"\$\s*([^\$]+?)\s*\$\s*([\+\-\*\/=><≠,;]+)\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2 \3$", wrapped)
    wrapped = re.sub(r"\$\s*([^\$]+?)\s*\$\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2$", wrapped)
    wrapped = re.sub(r"\s+", " ", wrapped)
    
    wrapped = re.sub(r"\s+([，。；：！？、）\)])", r"\1", wrapped)
    wrapped = re.sub(r"([（\(])\s+", r"\1", wrapped)

    # 终极全行安全扫描：确保该行普通文本中 100% 不存在任何裸露反斜杠宏
    parts = []
    last_idx = 0
    # 按照已成型的 $...$ 划分区间
    for match in re.finditer(r"\$[^\$]+?\$", wrapped):
        # 普通文本区间
        plain = wrapped[last_idx:match.start()]
        # 如果普通文本中还有残余的 \cmd
        if "\\" in plain:
            plain = re.sub(r"\\[a-zA-Z]+(?:_\{[^{}\s]+\}|_\d+|\^[^{}\s]+|\^\d+)?", r"$\g<0>$", plain)
        parts.append(plain)
        parts.append(match.group(0))
        last_idx = match.end()
        
    tail = wrapped[last_idx:]
    if "\\" in tail:
        tail = re.sub(r"\\[a-zA-Z]+(?:_\{[^{}\s]+\}|_\d+|\^[^{}\s]+|\^\d+)?", r"$\g<0>$", tail)
    parts.append(tail)
    
    final_line = "".join(parts)
    return prefix + final_line.strip()

def clean_structural_noise(lines):
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if re.search(r"^(学习札记|陈习区域|练习区域|绿习区域|作答区域|草稿纸)$", stripped):
            continue
        if re.search(r"^(扫码看视频|本章测试|作业链接|微信小程序|关注公众号).*", stripped):
            continue
        if re.match(r"^第\s*\d+\s*页$", stripped) or re.match(r"^\d+\s*·\s*\d+$", stripped):
            continue
        cleaned.append(line)
    return cleaned

def format_chapter(title, start_p, end_p, pages_dict, filter_chapter_headers=True):
    md_lines = []
    md_lines.append(f"# {title}\n")
    md_lines.append(f"> **收录范围**：PDF 第 {start_p} 页 至 第 {end_p} 页\n")
    md_lines.append("---\n")
    
    for pno in range(start_p, end_p + 1):
        raw_lines = pages_dict.get(str(pno), pages_dict.get(pno, []))
        if not raw_lines:
            continue
            
        md_lines.append(f"\n<!-- Page {pno} -->\n")
        lines = clean_structural_noise(raw_lines)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 过滤章节重复大标题
            if filter_chapter_headers and pno == start_p:
                if line.startswith("第一章") or line.startswith("第二章") or line.startswith("第三章") or line.startswith("第四章") or line.startswith("第五章") or line.startswith("第六章") or line.startswith("第 1 讲") or line.startswith("第 2 讲") or line.startswith("第 3 讲"):
                    continue
                if line in ["行列式", "矩阵", "n维向量", "向量", "线性方程组", "特征值和特征向量", "二次型", "45分钟水平测试"]:
                    continue

            # 结构化标记处理
            prefix = ""
            if "知识结构网络图" in line or "知识框架" in line:
                prefix = "## 【知识结构框架】 "
                line = line.replace("知识结构网络图", "").replace("知识框架", "").strip()
            elif "基本内容与重要结论" in line or "考点梳理" in line or "基础内容精讲" in line:
                prefix = "## 【基本内容与重要结论】 "
                line = line.replace("基本内容与重要结论", "").replace("考点梳理", "").replace("基础内容精讲", "").strip()
            elif "典型例题分析选讲" in line or "典型例题精解" in line or "例题精解" in line:
                prefix = "## 【典型例题精解】 "
                line = line.replace("典型例题分析选讲", "").replace("典型例题精解", "").replace("例题精解", "").strip()
            elif "练习题严选" in line or "本讲习题" in line:
                prefix = "## 【精选题与测试】 "
                line = line.replace("练习题严选", "").replace("本讲习题", "").strip()
            elif "参考答案与提示" in line or "习题精解" in line:
                prefix = "## 【参考答案与提示】 "
                line = line.replace("参考答案与提示", "").replace("习题精解", "").strip()
            elif re.match(r"^定义\s*\d*\.?\d*", line) or re.match(r"^定理\s*\d*\.?\d*", line) or re.match(r"^推论\s*\d*\.?\d*", line) or re.match(r"^性质\s*\d*", line):
                prefix = "### "
            elif re.match(r"^[一二三四五六七八九十]+、", line):
                prefix = "### "
            elif re.match(r"^[（\(][一二三四五六七八九十]+[）\)]", line):
                prefix = "#### "
            elif re.match(r"^【例(\d+\.\d+|\d+)?】", line) or re.match(r"^【例题】", line) or re.match(r"^例\s*\d+", line):
                prefix = "#### "
            elif "【编者注】" in line or "编者注" in line:
                prefix = "> **【编者注】** "
                line = line.replace("【编者注】", "").replace("编者注", "").strip()
            elif "【评注】" in line or "评注" in line:
                prefix = "> **【评注】** "
                line = line.replace("【评注】", "").replace("评注", "").strip()
            elif "【宇哥点拨】" in line or "宇哥点拨" in line:
                prefix = "> **【宇哥点拨】** "
                line = line.replace("【宇哥点拨】", "").replace("宇哥点拨", "").strip()
            elif "【点拨】" in line or line.startswith("点拨：") or line.startswith("点拨 "):
                prefix = "> **【点拨】** "
                line = line.replace("【点拨】", "").replace("点拨：", "").replace("点拨 ", "").strip()
            elif "【注】" in line or line.startswith("注：") or line.startswith("注 "):
                prefix = "> **【注】** "
                line = line.replace("【注】", "").replace("注：", "").replace("注 ", "").strip()
            elif line.startswith("【解析】") or line.startswith("【解】") or line.startswith("【证】") or line.startswith("【分析】"):
                prefix = f"**{line[:4]}** "
                line = line[4:].strip()
            elif re.match(r"^\([A-D]\)", line) or re.match(r"^（[A-D]）", line):
                prefix = "- "
                
            # 统一执行数学消歧与定界包装
            line = clean_and_repair_broken_tokens(line)
            line = fix_math_confusions(line)
            line = tokenize_and_wrap_math(line)
            
            if prefix and not line.strip():
                md_lines.append(f"\n{prefix}\n")
            elif prefix:
                md_lines.append(f"\n{prefix}{line}\n")
            else:
                md_lines.append(line)
            
    return "\n".join(md_lines)

def process_book(book_name, base_dir, chapter_configs):
    cache_path = os.path.join(base_dir, "ocr_cache.json")
    if not os.path.exists(cache_path):
        print(f"跳过：未找到 {book_name} 的缓存文件: {cache_path}")
        return
        
    print(f"\n>>> 正在重构并高精度生成: 《{book_name}》...")
    with open(cache_path, "r", encoding="utf-8") as f:
        pages_dict = json.load(f)
        
    for cfg in chapter_configs:
        md_content = format_chapter(cfg["title"], cfg["start_page"], cfg["end_page"], pages_dict)
        out_file = os.path.join(base_dir, cfg["file"])
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(md_content)
            
    print(f" -> 《{book_name}》已全部高品质重构完成！")

def main():
    # 1. 李永乐复习全书基础篇-线代学习册
    process_book(
        "2027李永乐复习全书基础篇-线代学习册",
        r"d:\考研动态学习项目\配套讲义\李永乐复习全书基础篇-线代学习册",
        [
            {"file": "第01章_行列式.md", "title": "第一章 行列式", "start_page": 16, "end_page": 36},
            {"file": "第02章_矩阵.md", "title": "第二章 矩阵", "start_page": 37, "end_page": 69},
            {"file": "第03章_向量.md", "title": "第三章 向量", "start_page": 70, "end_page": 98},
            {"file": "第04章_线性方程组.md", "title": "第四章 线性方程组", "start_page": 99, "end_page": 119},
            {"file": "第05章_特征值和特征向量.md", "title": "第五章 特征值和特征向量", "start_page": 120, "end_page": 144},
            {"file": "第06章_二次型.md", "title": "第六章 二次型", "start_page": 145, "end_page": 170},
        ]
    )

    # 2. 李永乐线性代数辅导讲义【强化】
    process_book(
        "2027李永乐线性代数辅导讲义【强化】",
        r"d:\考研动态学习项目\配套讲义\李永乐线性代数辅导讲义【强化】",
        [
            {"file": "第01章_行列式.md", "title": "第一章 行列式 —— 每一章都有应用", "start_page": 14, "end_page": 43},
            {"file": "第02章_矩阵.md", "title": "第二章 矩阵 —— 基础，防混淆", "start_page": 44, "end_page": 79},
            {"file": "第03章_n维向量.md", "title": "第三章 n维向量 —— 难点，加油", "start_page": 80, "end_page": 109},
            {"file": "第04章_线性方程组.md", "title": "第四章 线性方程组 —— 重点，别马虎大意", "start_page": 110, "end_page": 142},
            {"file": "第05章_特征值和特征向量.md", "title": "第五章 特征值和特征向量 —— 重点，综合性强", "start_page": 143, "end_page": 174},
            {"file": "第06章_二次型.md", "title": "第六章 二次型 —— 重点，注意和特征值、特征向量的联系", "start_page": 175, "end_page": 205},
            {"file": "附录_45分钟水平测试.md", "title": "附录 45分钟水平测试", "start_page": 206, "end_page": 211},
        ]
    )

    # 3. 李良概率论与数理统计辅导讲义
    base_ll = r"d:\考研动态学习项目\配套讲义\李良概率论与数理统计辅导讲义"
    if os.path.exists(os.path.join(base_ll, "ocr_cache.json")):
        with open(os.path.join(base_ll, "ocr_cache.json"), "r", encoding="utf-8") as f:
            ll_cache = json.load(f)
            
        print("\n>>> 正在重构并高精度生成: 《李良概率论与数理统计辅导讲义》...")
        jichu_cfgs = [
            {"file": "第01章_随机事件和概率.md", "title": "第01章 随机事件和概率【基础篇】", "start_page": 12, "end_page": 30},
            {"file": "第02章_一维随机变量及其分布.md", "title": "第02章 一维随机变量及其分布【基础篇】", "start_page": 31, "end_page": 44},
            {"file": "第03章_多维随机变量及其分布.md", "title": "第03章 多维随机变量及其分布【基础篇】", "start_page": 45, "end_page": 63},
            {"file": "第04章_随机变量的数字特征.md", "title": "第04章 随机变量的数字特征【基础篇】", "start_page": 64, "end_page": 80},
            {"file": "第05章_大数定律和中心极限定理.md", "title": "第05章 大数定律和中心极限定理【基础篇】", "start_page": 81, "end_page": 87},
            {"file": "第06章_数理统计的基本概念.md", "title": "第06章 数理统计的基本概念【基础篇】", "start_page": 88, "end_page": 101},
            {"file": "第07章_参数估计.md", "title": "第07章 参数估计【基础篇】", "start_page": 102, "end_page": 116},
        ]
        os.makedirs(os.path.join(base_ll, "01_基础篇"), exist_ok=True)
        for cfg in jichu_cfgs:
            md = format_chapter(cfg["title"], cfg["start_page"], cfg["end_page"], ll_cache)
            with open(os.path.join(base_ll, "01_基础篇", cfg["file"]), "w", encoding="utf-8") as f:
                f.write(md)
                
        qianghua_cfgs = [
            {"file": "第01章_随机事件和概率.md", "title": "第01章 随机事件和概率【强化篇】", "start_page": 117, "end_page": 139},
            {"file": "第02章_一维随机变量及其分布.md", "title": "第02章 一维随机变量及其分布【强化篇】", "start_page": 140, "end_page": 160},
            {"file": "第03章_多维随机变量及其分布.md", "title": "第03章 多维随机变量及其分布【强化篇】", "start_page": 161, "end_page": 188},
            {"file": "第04章_随机变量的数字特征.md", "title": "第04章 随机变量的数字特征【强化篇】", "start_page": 189, "end_page": 211},
            {"file": "第05章_大数定律和中心极限定理.md", "title": "第05章 大数定律和中心极限定理【强化篇】", "start_page": 212, "end_page": 219},
            {"file": "第06章_数理统计的基本概念.md", "title": "第06章 数理统计的基本概念【强化篇】", "start_page": 220, "end_page": 234},
            {"file": "第07章_参数估计.md", "title": "第07章 参数估计【强化篇】", "start_page": 235, "end_page": 249},
        ]
        os.makedirs(os.path.join(base_ll, "02_强化篇"), exist_ok=True)
        for cfg in qianghua_cfgs:
            md = format_chapter(cfg["title"], cfg["start_page"], cfg["end_page"], ll_cache)
            with open(os.path.join(base_ll, "02_强化篇", cfg["file"]), "w", encoding="utf-8") as f:
                f.write(md)
        print(" -> 《李良概率论与数理统计辅导讲义》已全部高品质重构完成！")

    # 4. 张宇高等数学18讲
    process_book(
        "张宇高等数学18讲",
        r"d:\考研动态学习项目\配套讲义\张宇高等数学18讲",
        [
            {"file": "第01讲_函数极限与连续.md", "title": "第 1 讲 函数极限与连续", "start_page": 7, "end_page": 81},
            {"file": "第02讲_数列极限.md", "title": "第 2 讲 数列极限", "start_page": 82, "end_page": 104},
            {"file": "第03讲_一元函数微分学的概念.md", "title": "第 3 讲 一元函数微分学的概念", "start_page": 105, "end_page": 124},
            {"file": "第04讲_一元函数微分学的计算.md", "title": "第 4 讲 一元函数微分学的计算", "start_page": 125, "end_page": 144},
            {"file": "第05讲_一元函数微分学的应用_一__几何应用.md", "title": "第 5 讲 一元函数微分学的应用（一）——几何应用", "start_page": 145, "end_page": 169},
            {"file": "第06讲_一元函数微分学的应用_二__中值定理_微分等式与微分不等式.md", "title": "第 6 讲 一元函数微分学的应用（二）——中值定理、微分等式与微分不等式", "start_page": 170, "end_page": 191},
            {"file": "第07讲_一元函数微分学的应用_三__物理应用与经济应用.md", "title": "第 7 讲 一元函数微分学的应用（三）——物理应用与经济应用", "start_page": 192, "end_page": 200},
            {"file": "第08讲_一元函数积分学的概念与性质.md", "title": "第 8 讲 一元函数积分学的概念与性质", "start_page": 201, "end_page": 235},
            {"file": "第09讲_一元函数积分学的计算.md", "title": "第 9 讲 一元函数积分学的计算", "start_page": 236, "end_page": 268},
            {"file": "第10讲_一元函数积分学的应用_一__几何应用.md", "title": "第 10 讲 一元函数积分学的应用（一）——几何应用", "start_page": 269, "end_page": 287},
            {"file": "第11讲_一元函数积分学的应用_二__积分等式与积分不等式.md", "title": "第 11 讲 一元函数积分学的应用（二）——积分等式与积分不等式", "start_page": 288, "end_page": 299},
            {"file": "第12讲_一元函数积分学的应用_三__物理应用与经济应用.md", "title": "第 12 讲 一元函数积分学的应用（三）——物理应用与经济应用", "start_page": 300, "end_page": 309},
            {"file": "第13讲_多元函数微分学.md", "title": "第 13 讲 多元函数微分学", "start_page": 310, "end_page": 343},
            {"file": "第14讲_二重积分.md", "title": "第 14 讲 二重积分", "start_page": 344, "end_page": 382},
            {"file": "第15讲_微分方程.md", "title": "第 15 讲 微分方程", "start_page": 383, "end_page": 414},
            {"file": "第16讲_无穷级数.md", "title": "第 16 讲 无穷级数", "start_page": 415, "end_page": 469},
            {"file": "第17讲_多元函数积分学的预备知识.md", "title": "第 17 讲 多元函数积分学的预备知识", "start_page": 470, "end_page": 493},
            {"file": "第18讲_多元函数积分学.md", "title": "第 18 讲 多元函数积分学", "start_page": 494, "end_page": 551},
            {"file": "附录_1_图像变换.md", "title": "附录 1 图像变换", "start_page": 552, "end_page": 554},
            {"file": "附录_2_常用平面图形.md", "title": "附录 2 常用平面图形", "start_page": 555, "end_page": 557},
            {"file": "附录_3_常用空间图形.md", "title": "附录 3 常用空间图形", "start_page": 558, "end_page": 560},
            {"file": "附录_4_重要公式.md", "title": "附录 4 重要公式", "start_page": 561, "end_page": 563},
            {"file": "附录_5_从指数函数到双曲函数.md", "title": "附录 5 从指数函数到双曲函数", "start_page": 564, "end_page": 568},
            {"file": "附录_6_变形技巧.md", "title": "附录 6 变形技巧", "start_page": 569, "end_page": 586},
        ]
    )

if __name__ == "__main__":
    main()
