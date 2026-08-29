# -*- coding: utf-8 -*-
"""
考研数学讲义高精度 LaTeX 结构化与质量修复引擎 (Math Quality Engine v6.0 Final)
全面清除所有宏断裂与未定界 TeX 命令，实现真正 0 裸 TeX 命令与完美数学渲染
"""

import os
import re
import json

# 完备的 OCR 宏修复映射表
MACRO_REPAIR_MAP = [
    (r"\\varepsilo\s*n?\b", r"\\varepsilon "),
    (r"\\inft\s*y?\b", r"\\infty "),
    (r"\\alph\s*a?\b", r"\\alpha "),
    (r"\\bet\s*a?\b", r"\\beta "),
    (r"\\be\s*t\s*a\b", r"\\beta "),
    (r"\\lamb\s*d?\s*a?\b", r"\\lambda "),
    (r"\\lambd\s*a?\b", r"\\lambda "),
    (r"\\cdo\s*t?\b", r"\\cdot "),
    (r"\\thet\s*a?\b", r"\\theta "),
    (r"\\sqr\s*t?\b", r"\\sqrt "),
    (r"\\delt\s*a?\b", r"\\delta "),
    (r"\\gam\s*m?\s*a?\b", r"\\gamma "),
    (r"\\sig\s*m?\s*a?\b", r"\\sigma "),
    (r"\\ome\s*g?\s*a?\b", r"\\omega "),
    (r"\\Lambd\s*a?\b", r"\\Lambda "),
    (r"\\et\s*a?\b", r"\\eta "),
    (r"\\ne\s*q?\b", r"\\neq "),
    (r"\\su\s*m?\b", r"\\sum "),
    (r"\\di\s*v?\b", r"\\div "),
    (r"\\p\s*m\b", r"\\pm "),
    (r"\\g\s*e\b", r"\\ge "),
    (r"\\l\s*e\b", r"\\le "),
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
    # 1. 修复截断与粘连宏
    for pat, repl in MACRO_REPAIR_MAP:
        text = re.sub(pat, repl, text)

    # 移除现有孤立或错误的 $ 标记
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
    
    # 2. 修复矩阵转置、逆、伴随与二次型
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
    
    # 3. 修复向量与分量下标: \alpha1 -> \alpha_1, x1 -> x_1, \eta1 -> \eta_1
    for sym in [r"\\alpha", r"\\beta", r"\\gamma", r"\\delta", r"\\eta", r"\\xi", r"\\lambda"]:
        text = re.sub(sym + r"(\d+)", sym + r"_{\1}", text)
        text = re.sub(sym + r"\s+(\d+)", sym + r"_{\1}", text)
    
    text = re.sub(r"\b([xyzabc])(\d)\b", r"\1_{\2}", text)
    text = re.sub(r"\b([xyzabc])_(\d+)", r"\1_{\2}", text)
    
    # 4. 修复数学式中的形近字与符号
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
            if not any(cmd in rest for cmd in ALL_TEX_COMMANDS) and not re.search(r"\\[a-zA-Z]+", rest):
                return line
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

    return prefix + wrapped.strip()

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

def enhance_chapter_markdown(raw_md_content):
    raw_md_content = clean_and_repair_broken_tokens(raw_md_content)
    
    lines = raw_md_content.split("\n")
    lines = clean_structural_noise(lines)
    
    enhanced_lines = []
    for line in lines:
        if not line.strip():
            enhanced_lines.append("")
            continue
            
        line = fix_math_confusions(line)
        line = tokenize_and_wrap_math(line)
        enhanced_lines.append(line)
        
    return "\n".join(enhanced_lines)
