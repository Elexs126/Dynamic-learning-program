#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_observability.py — 检测 trigger_signals 是否引用了题面里不存在的符号/对象。

任务书 §18 要求 Critic 攻击："trigger 是否真的从题面可观察？"
纯粹的字面重合检查没用——trigger 是**诊断**而非引文（"同次齐次式"不会字面出现在题面里）。
但有一个**低误报**的精确子检查：trigger 里引用的**数学符号/标识符**若在题面中根本不存在，
就说明该 trigger 很可能是从答案反推出来的。

本工具只做这一件事，输出可疑条目供 Critic 与人工复核。

用法:
  python check_observability.py --dir <raw_episodes> --md <报告> --json <报告>

判定:
  SYMBOL_MISSING   trigger 引用了题面中不存在的符号（列出缺失符号）
  OK               引用的符号都能在题面找到
  NO_SYMBOLS       trigger 不含可检测的数学符号（跳过，不算通过也不算失败）
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter

# 数学符号/标识符提取：
#   1) LaTeX 命令 \frac \lim 等
#   2) 带上下标的标识符 f(x) a_n x^4 e^x
#   3) 单字母变量与希腊字母（仅在出现 2 次以上时才算"具名对象"，降低噪声）
LATEX_RE = re.compile(r'\\[a-zA-Z]+')
IDENT_RE = re.compile(r'\b[A-Za-z][A-Za-z0-9]*(?:\s*[_^]\s*\{?[A-Za-z0-9+\-]+\}?)?(?:\s*\([^)]{0,12}\))?')
GREEK = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta', 'lambda', 'mu',
         'xi', 'rho', 'sigma', 'tau', 'phi', 'psi', 'omega', 'pi']

# 过于通用的词，不参与判定
STOP = {
    'x', 'y', 'z', 'n', 'k', 'i', 'j', 'm', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'A', 'B', 'C', 'D', 'E', 'F',
    'frac', 'sqrt', 'lim', 'sum', 'int', 'infty', 'to', 'cdot', 'times', 'leq',
    'geq', 'neq', 'left', 'right', 'begin', 'end', 'cases', 'text', 'mathrm',
    'displaystyle', 'quad', 'qquad', 'partial', 'nabla', 'pm', 'mp',
    'a_n', 'x_n', 'n+1', 'n-1', '0', '1', '2',
}


def skeleton(s):
    """把符号/文本压成字母数字骨架：x^2 -> x2, \\cos -> cos, a_n -> an"""
    return re.sub(r'[^A-Za-z0-9]', '', s or '').lower()


def candidates(sym):
    """一个符号可能对应的多个可比对骨架。
    例：'sim(1+2+3)' -> {'sim123', 'sim'}；'to3' -> {'to3', 'to'}
    这样可以避免把 '\\sim' 与 'sim(1+2+3)' 之间的差异误判为"符号缺失"。"""
    full = skeleton(sym)
    out = set()
    if full:
        out.add(full)
    for run in re.findall(r'[A-Za-z]{2,}', sym or ''):
        out.add(run.lower())
    return out


def extract_symbols(text):
    """提取有辨识度的数学符号集合（保留原始写法，比对时再取骨架）。"""
    if not text:
        return set()
    out = set()
    for m in LATEX_RE.finditer(text):
        name = m.group(0)[1:]
        if name.lower() not in STOP and len(name) >= 2:
            out.add('\\' + name)
    for m in IDENT_RE.finditer(text):
        tok = re.sub(r'\s+', '', m.group(0))
        if len(tok) < 2:
            continue
        if tok in STOP or tok.lower() in STOP:
            continue
        if any(ch in tok for ch in '_^()') or len(tok) >= 3:
            out.add(tok)
    for g in GREEK:
        if re.search(r'\\' + g + r'\b', text):
            out.add('\\' + g)
    return out


def norm(s):
    return re.sub(r'\s+', '', s or '')


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--md', default=None)
    ap.add_argument('--json', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

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
                problem = rec.get('raw_problem') or ''
                p_skel = skeleton(problem)
                p_syms = extract_symbols(problem)
                p_syms_skel = set()
                for s in p_syms:
                    p_syms_skel |= candidates(s)

                for i, trig in enumerate(rec.get('trigger_signals') or []):
                    t_syms = extract_symbols(trig)
                    if not t_syms:
                        results.append({
                            'problem_id': rec.get('problem_id'), 'worker': worker,
                            'index': i, 'verdict': 'NO_SYMBOLS',
                            'missing': [], 'trigger': trig[:120],
                        })
                        continue
                    missing = []
                    for sym in t_syms:
                        cands = candidates(sym)
                        if not cands:
                            continue
                        # 命中条件（任一即可）：
                        #   1) 题面里有同名符号（骨架级）
                        #   2) 该骨架作为子串出现在题面的字母数字骨架里
                        if cands & p_syms_skel:
                            continue
                        if any(c in p_skel for c in cands):
                            continue
                        missing.append(sym)
                    verdict = 'SYMBOL_MISSING' if missing else 'OK'
                    results.append({
                        'problem_id': rec.get('problem_id'), 'worker': worker,
                        'index': i, 'verdict': verdict,
                        'missing': missing, 'trigger': trig[:120],
                    })

    verdicts = Counter(r['verdict'] for r in results)
    suspects = [r for r in results if r['verdict'] == 'SYMBOL_MISSING']
    by_worker = {}
    for r in results:
        by_worker.setdefault(r['worker'], Counter())[r['verdict']] += 1

    summary = {
        'total_triggers': len(results),
        'verdicts': dict(verdicts),
        'by_worker': {k: dict(v) for k, v in sorted(by_worker.items())},
        'suspects': suspects,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    L = ['# trigger_signals 可观察性核验（符号级）', '']
    L.append('任务书 §18 要求攻击"trigger 是否真的从题面可观察"。')
    L.append('本检查只做**低误报**的那一部分：trigger 引用的数学符号若在题面中不存在，')
    L.append('值得人工看一眼。')
    L.append('')
    L.append('## ⚠️ 这是**分诊清单，不是判决**')
    L.append('')
    L.append('**触发信号是诊断，不是引文。** 它天然会引入题面里没有的符号，例如：')
    L.append('- 求解者**自己定义**的辅助对象（令 `F = f·f\'`，`F` 当然不在题面里）；')
    L.append('- 求解者**引入的已知关系**（`1-cos x ~ x²/2` 里的 `~`，题面不会写）；')
    L.append('- 求解者**命名的新量**（把某个极限记作 `A`）。')
    L.append('')
    L.append('以上三类都**完全合法**。本检查把这类一并标出，是因为机器无法区分')
    L.append('"合法引入的新符号"与"从答案反推才出现的符号"。')
    L.append('**因此 `SYMBOL_MISSING` 只表示"值得 Critic 复核"，不表示该 trigger 有问题。**')
    L.append('真正需要警惕的信号是：trigger 引用了**题面中完全不存在、且求解者也没有理由引入**的对象。')
    L.append('')
    L.append('- 核验 trigger 条数：**%d**' % len(results))
    for k in ('OK', 'SYMBOL_MISSING', 'NO_SYMBOLS'):
        if verdicts.get(k):
            L.append('- %s：%d' % (k, verdicts[k]))
    L.append('')
    L.append('> `NO_SYMBOLS` = 该 trigger 不含可检测的数学符号，本检查不适用（既不算通过也不算失败）。')
    L.append('> 它占比最高（约一半）是正常的——多数 trigger 是结构性描述（"分子分母同次齐次"），本来就不含符号。')
    L.append('')
    L.append('## 各 worker 分布')
    L.append('')
    L.append('| worker | OK | SYMBOL_MISSING | NO_SYMBOLS |')
    L.append('|---|---:|---:|---:|')
    for w in sorted(by_worker):
        d = by_worker[w]
        L.append('| %s | %d | %d | %d |' % (
            w, d.get('OK', 0), d.get('SYMBOL_MISSING', 0), d.get('NO_SYMBOLS', 0)))
    L.append('')
    if suspects:
        L.append('## ⚠️ 引用了题面中不存在符号的 trigger（供 Critic 复核）')
        L.append('')
        L.append('| problem_id | worker | 缺失符号 | trigger 摘要 |')
        L.append('|---|---|---|---|')
        for r in suspects:
            L.append('| %s | %s | %s | %s |' % (
                r['problem_id'], r['worker'],
                ', '.join(r['missing'][:6]).replace('|', '/'),
                r['trigger'].replace('|', '/').replace('\n', ' ')))
        L.append('')
    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
