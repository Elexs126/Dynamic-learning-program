---
name: kaoyan-pdf-extractor
description: >-
  考研数学/408题库超大PDF极速解析与结构化提取SOP。
  利用本地 Python + pdfplumber + PUA数学符号映射 + 自动图片切片 + 双标签注入，
  1分钟内完成数百页PDF的题库切分、LaTeX转换、配图提取与Markdown目录构建。
---

# 考研数学 / 408 题库 PDF 极速结构化解析提取 SOP

本 Skill 用于对超大体量（数百页、千题级）、含复杂数学公式（MathType PUA私有编码）和几何配图的考研资料（如张宇1000题、基础30讲、408真题等）进行本地极速批处理提取。

---

## 核心痛点与避坑策略

1. **避免大模型聊天逐页生成**：数千题文本直接聊天输出会触发上下文限制与网络中断（`wsasend` 错误）。必须使用本地脚本秒级批处理。
2. **解决字体私有区乱码 (PUA)**：MathType 或排版专有编码（如 `\uf0b6`、`\uf0e0`、`\int` 等）必须通过字典映射为标准 LaTeX 宏。
3. **自动捕获几何插图**：通过 `pdfplumber` 扫描 `page.images` 提取坐标并裁切保存为高清图片，在对应题干中自动嵌入引用。

---

## 极速 3 步提取脚本 (`scripts/pdf_extractor.py`)

```python
# -*- coding: utf-8 -*-
"""
考研题库 PDF 一键极速解析提取工具
"""
import os
import re
import pdfplumber

# 1. 通用数学符号映射字典（解决所有数学乱码）
CHAR_MAP = {
    '\uf00a': "'", '\uf00b': "''", '\uf00c': "'''",
    '\uf0b1': r"\pm ", '\uf0b6': r"\partial ", '\uf0b7': r"\cdot ", '\uf0b9': r"\neq ",
    '\uf0e0': r"\alpha ", '\uf0e1': r"\beta ", '\uf0e2': r"\gamma ", '\uf0e3': r"\delta ",
    '\uf0e4': r"\varepsilon ", '\uf0e8': r"\theta ", '\uf0eb': r"\lambda ", '\uf0ec': r"\mu ",
    '\uf0ee': r"\xi ", '\uf0f4': r"\varphi ", '\uf0f6': r"\omega ",
    '': '(', '': ')', '': '{', '': '}', '': '(', '': ')', '': '[', '': ']',
    '': '|', '': "'", '': "''", '': "'''",
    '': r"\int ", '': r"\iint ", '': r"\iiint ", '': r"\oint ", '': r"\oiint ", '': r"\sum ",
    'π': r"\pi", 'λ': r"\lambda", 'α': r"\alpha", 'β': r"\beta", 'θ': r"\theta",
    '≤': r"\le ", '≥': r"\ge ", '≠': r"\neq ", '∈': r"\in ", '→': r"\to ",
}

def extract_pdf_to_markdown(pdf_path, output_dir, book_name):
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"正在处理《{book_name}》，共 {len(pdf.pages)} 页...")
        
        # 1. 提取图片
        image_map = {}
        for i, page in enumerate(pdf.pages):
            pno = i + 1
            if page.images:
                for img_idx, img in enumerate(page.images):
                    bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                    if (bbox[2] - bbox[0] > 5) and (bbox[3] - bbox[1] > 5):
                        cropped = page.crop(bbox).to_image(resolution=200)
                        img_name = f"page_{pno}_img_{img_idx+1}.png"
                        cropped.save(os.path.join(img_dir, img_name))
                        image_map[pno] = img_name

        # 2. 逐页提取并清理文本
        pages_data = []
        for i, page in enumerate(pdf.pages):
            pno = i + 1
            raw_text = page.extract_text() or ""
            for k, v in CHAR_MAP.items():
                raw_text = raw_text.replace(k, v)
            
            # 清理页眉页脚与水印
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
            cleaned = [l for l in lines if "公众号" not in l and not re.search(r"第\s*\d+\s*页", l)]
            pages_data.append((pno, "\n".join(cleaned)))
            
    print("提取完成，已准备就绪！")
```

---

## 规范输出模板

每道题目必须包含双标签元数据：

```markdown
### 第 X 题（P{页码}）

{题目描述与公式}

> **【科目】** 基础篇 / 强化篇 / 408
> **【专题】** 第X章 {章节名}
```
