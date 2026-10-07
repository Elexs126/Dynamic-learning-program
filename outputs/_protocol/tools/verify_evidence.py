#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_evidence.py — 逐条核验 evidence_excerpt 是否真的出自所引用的源文件。

这是本数据集最关键的真实性检查：evidence_excerpt 声称是"从原文摘录"，
若它其实是 worker 自己写的话，则 E2 证据等级是伪造的。

用法:
  python verify_evidence.py --dir <raw_episodes> --src <源仓库根>
      [--json 报告] [--md 报告] [--quiet]

判定（第一层：与所引文件比对）:
  EXACT       规范化后摘录完整出现在所引文件中
  STRONG      摘录前 40 个规范化字符出现在所引文件中（OCR 导致尾部差异）
  WEAK        摘录 ≥60% 的 8-gram 出现在所引文件中
  MIS-CITED   所引文件中找不到，但在 canonical 语料的**别的文件**里找到了
              → 摘录本身是真的，只是 repo_path 写错了
  CONDENSED   摘录含省略号/箭头等连接符，说明 worker 把非连续片段拼接了
              （这违反"原文摘录"要求，但内容是真的）
  NOT_FOUND   canonical 语料里哪里都找不到 → 高度怀疑 worker 自己写的话（伪造）

canonical 语料 = 讲义/ + 核心真题/ + 配套习题/（不含 系统文件/，那是辅助产物）
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter

NOISE_RE = re.compile(r'[\s\$\\\{\}\_\^\[\]\(\)\|,，。．、；;：:！!？?"“”\'’`~—\-＝=<>&#%]+')
# worker 用来拼接非连续片段的连接符
CONDENSE_RE = re.compile(r'(…|\.\.\.|→|—难算→|⋯|···)')


def norm(s):
    if not s:
        return ''
    return NOISE_RE.sub('', s.replace('＊', '*').replace('－', '-'))


def ngrams(s, n=8):
    if len(s) < n:
        return set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


# ---- 题块归属检查 ----------------------------------------------------------
# 混合组 Critic 发现（mixed_m5m6m8c1.md S-1）：C1-004 的 evidence_excerpt
# 逐字为真、却取自**另一道题**的解析（2009 真题 T41 最短路径，L1311–L1313），
# 而该 Episode 是 T42（链表倒数第 k 个，真解析在 L1340–L1362）。
# 旧版 match_in 只问"这个文件里搜不搜得到"，**不问摘录属不属于本题**，故静默判 EXACT。
# 真题文件有稳定的题块标记 `> **【唯一编号】** \`408-09-A-T42\``，可据此定位。
BLOCK_RE = re.compile(r'【唯一编号】\**\s*`?([0-9A-Za-z\-]+)`?')
# 只在该字段里**确实含规范题号**时才做归属比对。
# 实测：不少 worker 把 `example_or_question` 写成人类可读的描述
# （如"用 swap 指令与布尔变量 lock 实现临界区（2023 综合应用题）"），
# 拿它跟题块编号比必然不等 → 会产出大量假阳性（第一版 29 条里只有 1 条是真的）。
ID_FIND = re.compile(r'([A-Za-z0-9][A-Za-z0-9]*-\d{2,4}-[A-Za-z]-[A-Za-z0-9]+)')

# 摘录的最短长度（规范化后，去空白去标点）。低于此值无法承载"这段原文支持了该思路"的信息。
MIN_EXCERPT_CHARS = 20


def norm_with_map(s):
    """规范化并记录每个规范化字符对应的原始下标，用于把摘录位置映射回原文。"""
    out, pos = [], []
    for i, ch in enumerate(s):
        if NOISE_RE.match(ch):
            continue
        out.append(ch)
        pos.append(i)
    return ''.join(out), pos


def block_check(raw_text, excerpt):
    """返回 (摘录所处的题块编号, 原始偏移)。找不到则编号为 None。"""
    nex = norm(excerpt)
    if not nex or not raw_text:
        return None, None
    ntext, pos = norm_with_map(raw_text)
    idx = ntext.find(nex)
    if idx < 0:
        probe = nex[:60]
        idx = ntext.find(probe) if len(probe) >= 12 else -1
        if idx < 0:
            return None, None
    raw_off = pos[idx] if idx < len(pos) else len(raw_text)
    best = None
    for m in BLOCK_RE.finditer(raw_text):
        if m.start() <= raw_off:
            best = m.group(1)
        else:
            break
    return best, raw_off


CANON_DIRS = ['讲义', '核心真题', '配套习题']


def build_corpus(src_root):
    """返回 {相对路径: 规范化文本}，仅 canonical 三个目录。"""
    corpus = {}
    for d in CANON_DIRS:
        base = os.path.join(src_root, d)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                p = os.path.join(root, fn)
                rel = os.path.relpath(p, src_root).replace('\\', '/')
                try:
                    with io.open(p, encoding='utf-8', errors='replace') as f:
                        corpus[rel] = norm(f.read())
                except Exception:
                    continue
    return corpus


def match_in(text, nex):
    """返回 (verdict, ratio)。text/nex 均已规范化。"""
    if not nex:
        return 'NO_EXCERPT', 0.0
    if nex in text:
        return 'EXACT', 1.0
    if len(nex) >= 40 and nex[:40] in text:
        return 'STRONG', 1.0
    grams = ngrams(nex)
    if not grams:
        return 'NOT_FOUND', 0.0
    ratio = sum(1 for g in grams if g in text) / len(grams)
    return ('WEAK' if ratio >= 0.6 else 'NOT_FOUND'), round(ratio, 3)

def verify_one(rec, src_root, corpus):
    src = rec.get('source') or {}
    rel = src.get('repo_path') or ''
    excerpt = rec.get('evidence_excerpt') or ''
    example = src.get('example_or_question') or ''
    nex = norm(excerpt)

    out = {'file': rel, 'ratio': 0.0, 'example_found': None,
           'actual_file': None, 'excerpt_head': excerpt[:70]}

    if not rel:
        out['verdict'] = 'NO_SOURCE'
        return out

    # ⚠️ 过短摘录闸门。
    # 408 组 Critic（c2c3c4m7.md A-4）发现 `M7-011.evidence_excerpt == "即"`（1 个字符），
    # 却因"逐字命中"被判 EXACT——**1 个字符的串在任何文件里都能命中**，
    # 逐字性检查在这类条目上完全失效。同源问题共 10 条（摘录切在"分析句的引子"上就停了）。
    # 因此：规范化后过短的摘录**一律不判 EXACT**，单列为需人工复核。
    if nex and len(nex) < MIN_EXCERPT_CHARS:
        out['verdict'] = 'EXCERPT_TOO_SHORT'
        out['excerpt_len'] = len(nex)
        out['min_required'] = MIN_EXCERPT_CHARS
        return out
    if not nex:
        out['verdict'] = 'NO_EXCERPT'
        return out

    cited = corpus.get(rel)
    if cited is None:
        # 允许大小写/分隔符差异
        for k in corpus:
            if k.replace('/', '\\') == rel.replace('/', '\\'):
                cited = corpus[k]
                rel = k
                break
    if cited is None:
        out['verdict'] = 'FILE_MISSING'
        return out

    out['example_found'] = (norm(example) in cited) if example and norm(example) else None

    verdict, ratio = match_in(cited, nex)
    out['ratio'] = ratio

    # 关键顺序：只要摘录里出现拼接标记（… / → 等），它就不是连续原文，
    # 必须优先判 CONDENSED —— 即使前缀恰好命中（STRONG）也不能算合格。
    # 只有 EXACT（整段规范化后完整出现）才能豁免。
    if verdict != 'EXACT' and nex and CONDENSE_RE.search(excerpt):
        out['verdict'] = 'CONDENSED'
        return out

    out['verdict'] = verdict

    # ---- 题块归属检查（仅对 EXACT 做，避免噪声）----------------------------
    # "逐字为真"不等于"属于本题"。若所引文件有【唯一编号】题块标记，
    # 且摘录落在**另一个**题块里，则这是"引用错题"，必须显式报出。
    if verdict == 'EXACT' and example:
        m_id = ID_FIND.search(example)
        expected_id = m_id.group(1) if m_id else None
        # 字段里没有规范题号 → 无法做归属比对，跳过（避免假阳性）
        if expected_id:
            raw_path = os.path.join(src_root, rel.replace('/', os.sep))
            try:
                raw = io.open(raw_path, encoding='utf-8', newline='').read()
                raw = raw.replace('\r\n', '\n')
            except Exception:
                raw = None
            if raw:
                blk, _off = block_check(raw, excerpt)
                if blk and blk != expected_id:
                    out['verdict'] = 'WRONG_QUESTION_BLOCK'
                    out['actual_block'] = blk
                    out['expected_block'] = expected_id
                    return out
                out['block'] = blk

    # 所引文件没找到 → 在 canonical 语料全库搜索，区分"误引"与"伪造"
    if verdict == 'NOT_FOUND' and nex:
        probe = nex[:40] if len(nex) >= 40 else nex
        best = None
        grams = ngrams(nex)
        for k, text in corpus.items():
            if k == rel:
                continue
            if probe in text:
                best = (k, 1.0)
                break
            if grams:
                r = sum(1 for x in grams if x in text) / len(grams)
                if r >= 0.6 and (best is None or r > best[1]):
                    best = (k, round(r, 3))
        if best:
            out['verdict'] = 'MIS-CITED'
            out['actual_file'] = best[0]
            out['ratio'] = best[1]
    elif verdict == 'NOT_FOUND' and not nex:
        out['verdict'] = 'NO_EXCERPT'

    return out


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--src', required=True)
    ap.add_argument('--json', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    sys.stderr.reconfigure(encoding='utf-8')
    corpus = build_corpus(args.src)
    print('canonical corpus: %d files' % len(corpus), file=sys.stderr)

    results = []
    for fn in sorted(f for f in os.listdir(args.dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        worker = os.path.splitext(fn)[0]
        with io.open(os.path.join(args.dir, fn), encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                v = verify_one(rec, args.src, corpus)
                v['worker'] = worker
                v['problem_id'] = rec.get('problem_id', '?')
                results.append(v)

    ORDER = ['EXACT', 'STRONG', 'WEAK', 'CONDENSED', 'MIS-CITED',
             'WRONG_QUESTION_BLOCK', 'EXCERPT_TOO_SHORT',
             'NOT_FOUND', 'NO_EXCERPT', 'FILE_MISSING', 'NO_SOURCE']
    verdicts = Counter(r['verdict'] for r in results)
    by_worker = {}
    for r in results:
        by_worker.setdefault(r['worker'], Counter())[r['verdict']] += 1

    forged = [r for r in results if r['verdict'] == 'NOT_FOUND']
    mis = [r for r in results if r['verdict'] == 'MIS-CITED']
    cond = [r for r in results if r['verdict'] == 'CONDENSED']
    weak = [r for r in results if r['verdict'] == 'WEAK']
    wrongblk = [r for r in results if r['verdict'] == 'WRONG_QUESTION_BLOCK']
    tooshort = [r for r in results if r['verdict'] == 'EXCERPT_TOO_SHORT']

    summary = {
        'total': len(results),
        'corpus_files': len(corpus),
        'verdicts': {k: verdicts.get(k, 0) for k in ORDER if verdicts.get(k)},
        'by_worker': {k: dict(v) for k, v in sorted(by_worker.items())},
        'verbatim_ok': verdicts.get('EXACT', 0) + verdicts.get('STRONG', 0),
        'suspect_forged': forged,
        'wrong_question_block': wrongblk,
        'too_short': tooshort,
        'mis_cited': mis,
        'condensed': cond,
        'weak': weak,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    L = ['# evidence_excerpt 真实性核验报告', '']
    L.append('对每条 Episode 的 `evidence_excerpt` 做规范化后与所引源文件比对；')
    L.append('若所引文件找不到，再在 canonical 语料（`讲义/`+`核心真题/`+`配套习题/`，共 %d 文件）全库搜索。' % len(corpus))
    L.append('')
    L.append('- 核验条数：**%d**' % len(results))
    L.append('- 逐字/强匹配通过：**%d**（%.0f%%）' % (
        summary['verbatim_ok'], 100.0 * summary['verbatim_ok'] / max(1, len(results))))
    L.append('')
    LABEL = {
        'EXACT': '逐字一致', 'STRONG': '强匹配（OCR 尾部差异）',
        'WEAK': '弱匹配（OCR 破坏严重）', 'CONDENSED': '拼接摘录（含省略号/箭头，内容真但非连续原文）',
        'MIS-CITED': '误引（内容真但在别的文件里）', 'NOT_FOUND': '⚠️ 全库找不到 —— 疑似伪造',
        'WRONG_QUESTION_BLOCK': '⚠️ 引用错题（摘录逐字为真，但落在**另一道题**的题块里）',
        'EXCERPT_TOO_SHORT': '⚠️ 摘录过短（无法承载"这段原文支持了该思路"的信息）',
        'NO_EXCERPT': '⚠️ 摘录为空', 'FILE_MISSING': '⚠️ 源文件不存在',
        'NO_SOURCE': '⚠️ 缺 source',
    }
    for k in ORDER:
        if verdicts.get(k):
            L.append('- %s：%d —— %s' % (k, verdicts[k], LABEL[k]))
    L.append('')
    L.append('## 各 worker 分布')
    L.append('')
    L.append('| worker | 逐字 | 强 | 弱 | 拼接 | 误引 | 疑似伪造 |')
    L.append('|---|---:|---:|---:|---:|---:|---:|')
    for w in sorted(by_worker):
        d = by_worker[w]
        L.append('| %s | %d | %d | %d | %d | %d | %d |' % (
            w, d.get('EXACT', 0), d.get('STRONG', 0), d.get('WEAK', 0),
            d.get('CONDENSED', 0), d.get('MIS-CITED', 0), d.get('NOT_FOUND', 0)))
    L.append('')

    def table(title, rows, extra_col=None, extra_key=None):
        if not rows:
            return
        L.append('## ' + title)
        L.append('')
        if extra_col:
            L.append('| problem_id | worker | %s | 摘录开头 |' % extra_col)
            L.append('|---|---|---|---|')
            for r in rows:
                L.append('| %s | %s | %s | %s |' % (
                    r['problem_id'], r['worker'], r.get(extra_key) or '',
                    r['excerpt_head'].replace('|', '/').replace('\n', ' ')))
        else:
            L.append('| problem_id | worker | 摘录开头 |')
            L.append('|---|---|---|')
            for r in rows:
                L.append('| %s | %s | %s |' % (
                    r['problem_id'], r['worker'],
                    r['excerpt_head'].replace('|', '/').replace('\n', ' ')))
        L.append('')

    table('⚠️ 疑似伪造（全库找不到，必须人工复核）', forged)
    table('引用错题：摘录逐字为真，但属于另一道题（**旧版会误判为 EXACT**）',
          wrongblk, '应属题号 / 实际所在题号', 'actual_block')
    table('摘录过短：**1 个字符的串在任何文件里都能命中**，逐字检查在这类条目上失效',
          tooshort, '规范化后长度', 'excerpt_len')
    table('误引：内容真但 repo_path 写错', mis, '实际所在文件', 'actual_file')
    table('拼接摘录：把非连续片段用省略号/箭头连起来（内容真，但违反"原文摘录"要求）', cond)
    table('弱匹配：OCR 破坏严重', weak)

    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print(text)
    return 1 if forged or verdicts.get('NO_EXCERPT') else 0


if __name__ == '__main__':
    sys.exit(main())
