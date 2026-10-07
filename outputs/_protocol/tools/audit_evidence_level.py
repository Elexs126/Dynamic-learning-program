#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_evidence_level.py — 审计 evidence_level 的**低估**风险。

背景：EPISODE_SPEC §6.1 最初把两件事混为一谈——
  * `evidence_excerpt` 必须出自 `source.repo_path`（可核验性要求）
  * `evidence_level` 应依据**整个仓库的材料**判断（材料是否明说）
后果：worker 因为"讲义原话不在所引文件里"就把 E2 降成 E1，
      把"材料明说"错记成"我自己推断"——**系统性低估证据强度**。
M6 实测提出该问题（M6-002/004/006/007 四条），规则已修正。

本工具机械地找出**可能被低估**的 E1 条目：
  若某条 evidence_level=E1，但它的 notes 里存在 `additional_evidence` 段，
  且该段包含**推理层标记词**（分析/方法总结/注/良哥解读/展示新知/学习札记/考点及方法小结…），
  则该条可能是"跨文件 E2"，值得复核。

⚠️ 这是**分诊**，不是判决：标记词出现不等于原文真的陈述了该思路。
   必须回到源文件读那句话，才能定 E1 还是 E2。

用法:
  python audit_evidence_level.py --dir <raw_episodes> --md <报告> --json <报告>
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

# 各科推理层标记词（来自 discover_markers.py 的发现式统计）
REASONING_MARKERS = [
    '分析', '方法总结', '良哥解读', '展示新知', '学习札记',
    '考点及方法小结', '注意', '技巧', '评注', '本题代码如下',
]

LEVEL_RE = re.compile(r'evidence_level\s*[:：]\s*(E\d)')
ADD_EV_RE = re.compile(r'additional_evidence', re.I)


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--md', default=None)
    ap.add_argument('--json', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    total = 0
    level_dist = Counter()
    by_worker = defaultdict(Counter)
    suspects = []

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
                total += 1
                notes = rec.get('notes') or ''
                m = LEVEL_RE.search(notes)
                lvl = m.group(1) if m else 'none'
                level_dist[lvl] += 1
                by_worker[worker][lvl] += 1

                if lvl != 'E1':
                    continue
                # E1 但 notes 里有 additional_evidence 且含推理标记词 → 可能是跨文件 E2
                if not ADD_EV_RE.search(notes):
                    continue
                hits = [k for k in REASONING_MARKERS if k in notes]
                if hits:
                    suspects.append({
                        'problem_id': rec.get('problem_id'),
                        'worker': worker,
                        'domain': rec.get('domain', ''),
                        'markers_in_notes': hits,
                        'confidence': rec.get('confidence', ''),
                        'repo_path': (rec.get('source') or {}).get('repo_path', ''),
                        'notes_excerpt': notes[:260].replace('\n', ' '),
                    })

    e1 = level_dist.get('E1', 0)
    summary = {
        'total_episodes': total,
        'evidence_level_distribution': dict(level_dist),
        'by_worker': {k: dict(v) for k, v in sorted(by_worker.items())},
        'e1_total': e1,
        'e1_with_cross_file_candidate': len(suspects),
        'suspects': suspects,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    L = ['# evidence_level 低估审计（跨文件 E2 候选）', '']
    L.append('由 `audit_evidence_level.py` 生成。')
    L.append('')
    L.append('## 为什么做这个审计')
    L.append('')
    L.append('SPEC §6.1 最初把两件事混为一谈：')
    L.append('')
    L.append('| | 应有约束 | 为什么 |')
    L.append('|---|---|---|')
    L.append('| `evidence_excerpt` | 必须出自 `source.repo_path` | **可核验性**——摘录要能被机器回源比对 |')
    L.append('| `evidence_level` | 依据**整个仓库的材料**判断 | **材料是否明说**——E2 的定义没规定它必须在哪个文件里 |')
    L.append('')
    L.append('后果：worker 因为"讲义原话不在所引文件里"就把 E2 降成 E1，')
    L.append('把"材料明说"错记成"我自己推断"——**与虚标 E2 方向相反、但同样是失真**。')
    L.append('M6 实测提出该问题（M6-002/004/006/007），规则已修正。')
    L.append('')
    L.append('## ⚠️ 这是分诊，不是判决')
    L.append('')
    L.append('判据是机械的："notes 里有 `additional_evidence` 且含推理标记词"。')
    L.append('**标记词出现不等于原文真的陈述了该思路**——必须回到源文件读那句话才能定性。')
    L.append('')
    L.append('## 结果')
    L.append('')
    L.append('- 扫描 Episode：%d' % total)
    L.append('- evidence_level 分布：%s' % json.dumps(dict(level_dist), ensure_ascii=False))
    L.append('- **E1 总数：%d**' % e1)
    L.append('- **其中"跨文件 E2 候选"：%d（占 E1 的 %.0f%%）**' % (
        len(suspects), 100.0 * len(suspects) / max(1, e1)))
    L.append('')
    L.append('## 各 worker 的 evidence_level 分布')
    L.append('')
    L.append('| worker | E1 | E2 | 其他 | E1 占比 |')
    L.append('|---|---:|---:|---:|---:|')
    for w in sorted(by_worker):
        d = by_worker[w]
        n = sum(d.values())
        other = sum(v for k, v in d.items() if k not in ('E1', 'E2'))
        L.append('| %s | %d | %d | %d | %.0f%% |' % (
            w, d.get('E1', 0), d.get('E2', 0), other,
            100.0 * d.get('E1', 0) / max(1, n)))
    L.append('')
    if suspects:
        L.append('## 跨文件 E2 候选清单（需人工复核）')
        L.append('')
        L.append('| problem_id | worker | 领域 | notes 中出现的推理标记 | 所引文件 |')
        L.append('|---|---|---|---|---|')
        for r in suspects:
            L.append('| %s | %s | %s | %s | `%s` |' % (
                r['problem_id'], r['worker'], r['domain'],
                '、'.join(r['markers_in_notes'][:4]),
                r['repo_path'][-58:]))
        L.append('')
        L.append('## 复核方法')
        L.append('')
        L.append('对每条：读它 `notes` 里的 `additional_evidence` 段 → 打开所注明的源文件 →')
        L.append('确认那段话**是否真的在陈述该思路**（而不是仅仅主题相关）。')
        L.append('')
        L.append('- 真的陈述了 → 该条应为 **E2**（跨文件 E2），请在 `notes` 里注明"跨文件 E2"。')
        L.append('- 只是主题相关 → 维持 **E1**。')
        L.append('')
        L.append('**注意**：无论 E1 还是 E2，`evidence_excerpt` 都**必须**仍出自 `source.repo_path`。')
        L.append('不要把讲义原文搬回 `evidence_excerpt`——那会重新触发误引。')
        L.append('')
    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('episodes=%d E1=%d cross_file_candidates=%d' % (total, e1, len(suspects)))
        print('by worker E1:', {w: by_worker[w].get('E1', 0) for w in sorted(by_worker)})
    return 0


if __name__ == '__main__':
    sys.exit(main())
