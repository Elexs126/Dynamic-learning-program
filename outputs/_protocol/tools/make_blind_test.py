#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_blind_test.py — 从核心真题中抽取题目并剥离答案，生成 blind test 题包。

用法:
  python make_blind_test.py inventory <真题文件或目录...>
  python make_blind_test.py extract --out <输出md> <真题文件...> --ids ID1,ID2,...

设计要点:
  * 题目块 = 以含题目唯一编号的标题行开始，到下一个同级/更高级标题为止。
  * 剥离 <details>...</details> 整块（含参考答案与解析）。
  * 额外剥离任何含 参考答案/正确答案/解析 的行，双保险。
  * 保留 题型/科目/分值/年份/考点 元数据（学生本来就能看到考点）。
"""
import re
import sys
import os
import json
import argparse

HEADING_RE = re.compile(r'^(#{2,6})\s*【([^】]+)】')
DETAILS_RE = re.compile(r'<details>.*?</details>', re.S | re.I)
LEAK_RE = re.compile(r'(参考答案|正确答案|【解析】|\*\*解析\*\*|答案[：:])')
ID_RE = re.compile(r'^((?:M1|M2|M3|408|WD|ZY30|ZY1000|408JD)[A-Za-z0-9\-\.]*)$')


def split_blocks(text):
    """把 markdown 按标题切成块，返回 [(heading_level, heading_line, body_lines, start_line)]"""
    lines = text.split('\n')
    marks = []
    for i, ln in enumerate(lines):
        m = HEADING_RE.match(ln)
        if m:
            marks.append((i, len(m.group(1)), ln, m.group(2).strip()))
    blocks = []
    for idx, (i, level, ln, title) in enumerate(marks):
        end = len(lines)
        for j in range(idx + 1, len(marks)):
            if marks[j][1] <= level:
                end = marks[j][0]
                break
        blocks.append({
            'level': level,
            'heading': ln,
            'title': title,
            'body': lines[i + 1:end],
            'start': i + 1,
        })
    return blocks


def parse_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    out = []
    for b in split_blocks(text):
        if not ID_RE.match(b['title']):
            continue
        body = '\n'.join(b['body'])
        meta = {}
        for key in ('唯一编号', '题型', '科目', '分值', '年份', '考点', '课程', '章节'):
            m = re.search(r'【' + key + r'】\*\*\s*`?([^`\n]*)`?', body)
            if m:
                meta[key] = m.group(1).strip()
        out.append({
            'id': b['title'],
            'file': path,
            'heading': b['heading'],
            'body': body,
            'meta': meta,
            'has_answer': bool(DETAILS_RE.search(body)),
            'line': b['start'],
        })
    return out


def sanitize(q):
    body = q['body']
    body = DETAILS_RE.sub('', body)
    kept = []
    for ln in body.split('\n'):
        if LEAK_RE.search(ln):
            continue
        kept.append(ln)
    body = '\n'.join(kept)
    # 收敛连续空行
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    return body


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                for n in sorted(names):
                    if n.lower().endswith('.md'):
                        files.append(os.path.join(root, n))
        else:
            files.append(p)
    qs = []
    for f in files:
        qs.extend(parse_file(f))
    return qs


def cmd_inventory(args):
    qs = collect(args.paths)
    rows = []
    for q in qs:
        rows.append({
            'id': q['id'],
            'year': q['meta'].get('年份', ''),
            'subject': q['meta'].get('科目', q['meta'].get('课程', '')),
            'type': q['meta'].get('题型', ''),
            'kp': q['meta'].get('考点', q['meta'].get('章节', '')),
            'has_answer': q['has_answer'],
            'file': os.path.relpath(q['file']).replace('\\', '/'),
        })
    payload = json.dumps({'count': len(rows), 'questions': rows}, ensure_ascii=False, indent=1)
    if args.out:
        # 直接由 Python 写 UTF-8，避免 PowerShell 管道重编码
        with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(payload)
        print('written %s (%d questions)' % (args.out, len(rows)))
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(payload)


def cmd_extract(args):
    ids = [s.strip() for s in args.ids.split(',') if s.strip()]
    qs = collect(args.paths)
    index = {}
    for q in qs:
        index.setdefault(q['id'], q)
    missing = [i for i in ids if i not in index]
    keep = getattr(args, 'keep_answers', False)
    if keep:
        parts = ['# Blind Test 对照答案（供评分 worker 使用）', '']
        parts.append('> 本文件由 `make_blind_test.py --keep-answers` 生成，**保留参考答案与解析**。')
        parts.append('> 仅供**评分 worker** 把盲测预测与标准解对照使用；')
        parts.append('> **预测 worker 绝不可读本文件**（否则盲测失效）。')
        parts.append('')
    else:
        parts = ['# Blind Test 题包（已剥离答案）', '']
        parts.append('> 本文件由 `make_blind_test.py` 从核心真题自动生成，**所有参考答案与解析块已被移除**。')
        parts.append('> 作答者只能看到题面与元数据，不得检索源仓库中的对应真题文件。')
        if args.src_root:
            parts.append('>')
            parts.append('> **示意图**：题目引用的示意图已复制到本目录 `images/` 下（原始 SVG 及其渲染的 PNG）。')
            parts.append('> 请用 `read_image` 工具读取 **PNG**（SVG 无法直接作为图像读取）。')
            parts.append('> 若某题的图缺失或无法判读，请在 `uncertainty` 中明确说明"无法读取示意图"，')
            parts.append('> **不要凭想象补图**——这会被记为 `UNVERIFIABLE` 而不是你的失误。')
    parts.append('')
    for i in ids:
        q = index.get(i)
        if not q:
            continue
        m = q['meta']
        parts.append('---')
        parts.append('')
        parts.append('## ' + i)
        parts.append('')
        meta_bits = []
        for k in ('年份', '科目', '课程', '题型', '分值', '考点', '章节'):
            if k in m:
                meta_bits.append('**%s** %s' % (k, m[k]))
        if meta_bits:
            parts.append('> ' + ' ｜ '.join(meta_bits))
            parts.append('')
        parts.append(q['body'] if keep else sanitize(q))
        parts.append('')
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(parts))
    report = {
        'out': args.out,
        'requested': len(ids),
        'written': len(ids) - len(missing),
        'missing': missing,
    }
    if args.src_root:
        report['images'] = stage_images(args.out, args.src_root)
    print(json.dumps(report, ensure_ascii=False))


def find_image(src_root, name):
    """在源仓库里按文件名查找示意图。"""
    for base in ('核心真题', '辅助真题'):
        b = os.path.join(src_root, base)
        if not os.path.isdir(b):
            continue
        for root, _dirs, files in os.walk(b):
            if name in files:
                return os.path.join(root, name)
    return None


CHROME_CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
]


def svg_wellformed(svg_path):
    """用 XML 解析器预检 SVG 是否合法。
    ⚠️ 这一步是必需的：源仓库的部分 SVG 是**残缺/畸形**的，Chrome 会把它们
    渲染成**错误页**（粉红横幅 "This page contains the following errors"），
    而不是图。若不预检，产出的 PNG 看着有内容、实际是错误页——
    blind test 的预测者会据此说"图无法判读"，而这其实是我方管线的 bug。
    返回 (是否合法, 错误说明)。"""
    import xml.etree.ElementTree as ET
    try:
        ET.parse(svg_path)
        return True, ''
    except Exception as e:
        return False, str(e)


def looks_like_error_page(png_path):
    """粗检渲染结果是否为浏览器错误页（错误页顶部有大片粉红横幅）。
    这是 svg_wellformed 之后的第二道保险。"""
    try:
        from PIL import Image
    except Exception:
        return None  # 无 Pillow 时跳过
    try:
        im = Image.open(png_path).convert('RGB')
        w, h = im.size
        # 取顶部 12% 区域，统计"粉红"像素比例
        box = im.crop((0, 0, w, max(1, int(h * 0.12))))
        px = list(box.getdata())
        pink = sum(1 for r, g, b in px if r > 200 and 180 < g < 240 and 180 < b < 240)
        return (pink / max(1, len(px))) > 0.30
    except Exception:
        return None


def svg_to_png(svg_path, png_path):
    """用 headless 浏览器把 SVG 渲染成 PNG，使 read_image 能读取。
    先做 XML 合法性预检；渲染后再粗检是否为错误页。"""
    import subprocess
    exe = next((p for p in CHROME_CANDIDATES if os.path.isfile(p)), None)
    if not exe:
        return False
    ok, why = svg_wellformed(svg_path)
    if not ok:
        # 畸形 SVG：不要产出看起来正常的错误页 PNG
        return False
    url = 'file:///' + svg_path.replace('\\', '/').replace(' ', '%20')
    try:
        subprocess.run([exe, '--headless', '--disable-gpu', '--no-sandbox',
                        '--hide-scrollbars', '--window-size=1600,1200',
                        '--screenshot=' + png_path, url],
                       capture_output=True, timeout=120)
    except Exception:
        return False
    if not (os.path.isfile(png_path) and os.path.getsize(png_path) > 0):
        return False
    if looks_like_error_page(png_path) is True:
        try:
            os.remove(png_path)
        except Exception:
            pass
        return False
    return True


IMG_RE = re.compile(r'!\[([^\]]*)\]\(images/([^)]+)\)')


def stage_images(md_path, src_root):
    """把题包引用的示意图复制到 <md 目录>/images/ 并把 SVG 渲染为 PNG、改写引用。"""
    out_dir = os.path.dirname(os.path.abspath(md_path))
    img_dir = os.path.join(out_dir, 'images')
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    staged, rendered, missing, render_failed, no_text = [], [], [], [], []
    for m in IMG_RE.finditer(text):
        name = m.group(2)
        if name in staged:
            continue
        src = find_image(src_root, name)
        if not src:
            missing.append(name)
            continue
        os.makedirs(img_dir, exist_ok=True)
        dst = os.path.join(img_dir, name)
        if not os.path.isfile(dst):
            import shutil
            shutil.copy2(src, dst)
        staged.append(name)
        if name.lower().endswith('.svg'):
            # 检查是否有真正的文字标注（<text> 节点且非水印）
            try:
                import re as _re
                t = open(dst, encoding='utf-8', errors='replace').read()
                texts = [x for x in _re.findall(r'<text[^>]*>(.*?)</text>', t, _re.S)]
                cleaned = [_re.sub(r'<[^>]+>', '', x).strip() for x in texts]
                cleaned = [x for x in cleaned if x]
                # 水印判定：所有文字都是同一句且很短
                if not cleaned or (len(set(cleaned)) == 1 and len(cleaned[0]) <= 12):
                    no_text.append(name)
            except Exception:
                pass
            png = os.path.splitext(dst)[0] + '.png'
            ok, why = svg_wellformed(dst)
            if svg_to_png(dst, png):
                rendered.append(os.path.basename(png))
                text = text.replace('(images/%s)' % name,
                                    '(images/%s)' % os.path.basename(png))
            else:
                render_failed.append({
                    'svg': name,
                    'wellformed': ok,
                    'reason': ('SVG 畸形，XML 解析失败：%s' % why[:160]) if not ok
                              else '渲染结果疑似浏览器错误页，已丢弃',
                })
    if staged:
        with open(md_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    return {'staged': staged, 'rendered': rendered, 'missing': missing,
            'render_failed': render_failed, 'svg_without_text_labels': no_text}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    pi = sub.add_parser('inventory')
    pi.add_argument('paths', nargs='+')
    pi.add_argument('--out', default=None)
    pe = sub.add_parser('extract')
    pe.add_argument('paths', nargs='+')
    pe.add_argument('--ids', required=True)
    pe.add_argument('--out', required=True)
    pe.add_argument('--src-root', default=None,
                    help='源仓库根，用于复制示意图；省略则跳过图片暂存')
    pe.add_argument('--keep-answers', action='store_true',
                    help='保留参考答案与解析（仅评分 worker 用；预测 worker 绝不可读）')
    args = ap.parse_args()
    if args.cmd == 'inventory':
        cmd_inventory(args)
    else:
        cmd_extract(args)


if __name__ == '__main__':
    main()
