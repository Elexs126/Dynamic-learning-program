#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_coverage_data.py — 把所有 _index 报告的机械数据汇总成 coverage_report 的数据表。

为什么需要：coverage_report.md 要引用十来个报告的统计数字。若由 worker 手工抄写，
必然出现数字不一致（写报告时的快照 vs 报告生成后的重跑）。
本工具把机械部分**一次性生成**，worker 只需在表上写散文与判断。

用法:
  python build_coverage_data.py --index <_index 目录> --out-json <json> --out-md <md>
"""
import argparse
import io
import json
import os
import sys


def load(path):
    if not os.path.isfile(path):
        return None
    try:
        return json.load(io.open(path, encoding='utf-8'))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    idx = os.path.abspath(os.path.join(here, '..', '..', '_index'))
    ap.add_argument('--index', default=idx)
    ap.add_argument('--out-json', default=None)
    ap.add_argument('--out-md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    I = args.index
    val = load(os.path.join(I, 'validation_report.json'))
    ev = load(os.path.join(I, 'evidence_verify.json'))
    ops = load(os.path.join(I, 'operator_stats.json'))
    geo = load(os.path.join(I, 'geometry_axes.json'))
    dup = load(os.path.join(I, 'duplicates.json'))
    obs = load(os.path.join(I, 'observability_check.json'))
    lvl = load(os.path.join(I, 'evidence_level_audit.json'))
    syl = load(os.path.join(I, 'syllabus_map.json'))
    mk = load(os.path.join(I, 'source_marker_survey.json'))
    unex = load(os.path.join(I, 'unexplained_raw.json'))
    fam = load(os.path.join(I, 'family_seeds.json'))

    data = {
        'episodes': {
            'total': (val or {}).get('total_episodes'),
            'by_worker': (val or {}).get('workers'),
            'errors': (val or {}).get('error_count'),
            'warnings': (val or {}).get('warning_count'),
            'confidence': (val or {}).get('confidence'),
        },
        'evidence_integrity': {
            'total': (ev or {}).get('total'),
            'verdicts': (ev or {}).get('verdicts'),
            'verbatim_ok': (ev or {}).get('verbatim_ok'),
        },
        'evidence_level': {
            'distribution': (lvl or {}).get('evidence_level_distribution'),
            'by_worker': (lvl or {}).get('by_worker'),
            'e1_total': (lvl or {}).get('e1_total'),
            'cross_file_e2_candidates': (lvl or {}).get('e1_with_cross_file_candidate'),
        },
        'operators': {
            'seen': (ops or {}).get('operators_seen'),
            'entering_ontology': (ops or {}).get('operators_entering_ontology'),
            'cross_domain': (ops or {}).get('operators_cross_domain'),
            'cross_domain_meaningful': (ops or {}).get('operators_cross_domain_meaningful'),
            'concentration': (ops or {}).get('concentration'),
            'anti_operator_concentration': (ops or {}).get('anti_operator_concentration'),
        },
        'geometry_axes': (geo or {}).get('axes'),
        'domains': (geo or {}).get('domain_episode_counts'),
        'duplicates': {
            'pairs': (dup or {}).get('duplicate_pairs'),
            'cross_worker_pairs': (dup or {}).get('cross_worker_pairs'),
            'estimated_unique_questions': (dup or {}).get('estimated_unique_questions'),
            'estimated_inflation': (dup or {}).get('estimated_inflation'),
            'operator_disagreement_pairs': (dup or {}).get('pairs_with_operator_disagreement'),
        },
        'observability': (obs or {}).get('verdicts'),
        'syllabus': (syl or {}).get('stats'),
        'markers': (mk or {}).get('courses'),
        'unexplained': {
            'candidates': (unex or {}).get('candidate_new_operators'),
            'recommended_promotion': (unex or {}).get('candidates_recommended_for_promotion'),
            'unknown_episodes': (unex or {}).get('unknown_episodes'),
            'no_operator_match': (unex or {}).get('episodes_without_operator_match'),
        },
        'family_seeds': (fam or {}).get('fragmentation'),
    }

    if args.out_json:
        with io.open(args.out_json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1))

    L = ['# coverage_report 数据表（机械生成）', '']
    L.append('由 `build_coverage_data.py` 汇总 `_index/` 下各报告的统计数字。')
    L.append('**Coverage worker 应直接引用本表，不要手工抄数字**——手抄必然与重跑结果不一致。')
    L.append('')

    e = data['episodes']
    L.append('## 1. 产量与结构校验')
    L.append('')
    L.append('- Episode 行数：**%s**' % e['total'])
    if e.get('by_worker'):
        L.append('- 各 worker：%s' % '、'.join('%s=%s' % (k, v) for k, v in sorted(e['by_worker'].items())))
    L.append('- 结构 ERROR：%s ｜ WARNING：%s' % (e['errors'], e['warnings']))
    if e.get('confidence'):
        L.append('- confidence 分布：%s' % json.dumps(e['confidence'], ensure_ascii=False))
    if data['duplicates'].get('estimated_unique_questions'):
        d = data['duplicates']
        L.append('- **估算唯一题目数：%s（虚高 %s 条）** —— 存在 %s 对跨 worker 重复' % (
            d['estimated_unique_questions'], d['estimated_inflation'], d['cross_worker_pairs']))
        L.append('  - 其中同一题被不同 worker 指派不同主算子的对数：**%s**' % d['operator_disagreement_pairs'])
    L.append('')

    v = data['evidence_integrity']
    L.append('## 2. 证据真实性（逐字回源）')
    L.append('')
    L.append('- 核验条数：%s ｜ 逐字/强匹配通过：**%s**' % (v['total'], v['verbatim_ok']))
    L.append('- 判定分布：%s' % json.dumps(v['verdicts'], ensure_ascii=False))
    L.append('')

    lv = data['evidence_level']
    L.append('## 3. 证据等级分布')
    L.append('')
    L.append('- 全库：%s' % json.dumps(lv['distribution'], ensure_ascii=False))
    L.append('- E1 总数：%s ｜ **其中跨文件 E2 候选：%s**（机械分诊，含假阳性，需人工复核）' % (
        lv['e1_total'], lv['cross_file_e2_candidates']))
    L.append('')
    if lv.get('by_worker'):
        L.append('| worker | E1 | E2 | 其他 | E1 占比 |')
        L.append('|---|---:|---:|---:|---:|')
        for w in sorted(lv['by_worker']):
            d = lv['by_worker'][w]
            n = sum(d.values()) or 1
            other = sum(x for k, x in d.items() if k not in ('E1', 'E2'))
            L.append('| %s | %d | %d | %d | %.0f%% |' % (
                w, d.get('E1', 0), d.get('E2', 0), other, 100.0 * d.get('E1', 0) / n))
        L.append('')

    o = data['operators']
    L.append('## 4. 算子证据与集中度')
    L.append('')
    L.append('- 出现的算子：%s ｜ 进入稳定 ontology（E3+）：%s' % (o['seen'], o['entering_ontology']))
    L.append('- 跨领域算子：%s ｜ **其中"有意义"的（覆盖率 < 25%%）：%s**' % (
        o['cross_domain'], o['cross_domain_meaningful']))
    c = o.get('concentration') or {}
    if c:
        L.append('- 母算子集中度：top1 **%.1f%%**、top2 **%.1f%%**、top3 **%.1f%%**' % (
            100 * c['top1_coverage'], 100 * c['top2_coverage'], 100 * c['top3_coverage']))
        L.append('- 超阈值（>=25%%）算子：%s' % '、'.join(
            '`%s`' % x['operator_id'] for x in c.get('overused_operators', [])))
    a = o.get('anti_operator_concentration') or {}
    if a:
        L.append('- 对照 anti-operator：top1 %.1f%%、top3 **%.1f%%**（%d 个不同标签）' % (
            100 * a['top1_share'], 100 * a['top3_share'], a['distinct_failure_types']))
        L.append('  → **"为什么失败"的语言比"做了什么"的语言区分度更高**，此差异需在报告中解释')
    L.append('')

    if data['geometry_axes']:
        L.append('## 5. 问题几何轴填充率')
        L.append('')
        L.append('| 轴 | 非空 | 总数 | 填充率 |')
        L.append('|---|---:|---:|---:|')
        for ax, v2 in data['geometry_axes'].items():
            pct = 100.0 * v2['nonempty'] / max(1, v2['total'])
            L.append('| `%s` | %d | %d | %.1f%% |' % (ax, v2['nonempty'], v2['total'], pct))
        L.append('')
        if data.get('domains'):
            L.append('- 领域 Episode 分布：%s' % json.dumps(data['domains'], ensure_ascii=False))
            L.append('')

    if data['observability']:
        L.append('## 6. trigger 可观察性（符号级分诊）')
        L.append('')
        L.append('- %s' % json.dumps(data['observability'], ensure_ascii=False))
        L.append('- ⚠️ 这是**分诊不是判决**：触发信号是诊断而非引文，'
                 '合法引入的新符号（辅助对象、已知关系）会被一并标出。')
        L.append('')

    if data['syllabus']:
        s = data['syllabus']
        L.append('## 7. 大纲覆盖边界')
        L.append('')
        L.append('- %d 个 track ｜ %d 门课 ｜ %d 个主题 ｜ %d 个条目' % (
            s['tracks'], s['courses'], s['topics'], s['items']))
        L.append('')

    if data['markers']:
        L.append('## 8. 各科推理层标记词')
        L.append('')
        L.append('> ⚠️ **下表（`source_marker_survey.md`）已被证明不完整，仅作历史对照。**')
        L.append('> 它由"**猜标记名再搜**"得出，三次被 worker 抓出漏项：')
        L.append('> ① 漏 `良哥解读`(134)、`展示新知`(153)、`学习札记`(70)（M8 发现）；')
        L.append('> ② 漏 `【评注】`(48)、`【提示】`(17)（M7 发现）；')
        L.append('> ③ 未覆盖 408 的答案层 `【解答】`(426) 与 `【另解】`(34)。')
        L.append('>')
        L.append('> **权威版本见 `_index/inline_markers.md`**（`discover_inline_markers.py` 生成：')
        L.append('> 不猜名字，用与对象同形态的行内模式扫全库）。')
        L.append('>')
        L.append('> **关键教训**：发现式方法必须与被发现对象的**形态**匹配——')
        L.append('> 猜名字会漏掉想不到的；统计整行会漏掉行内的；')
        L.append('> 同一个词在不同科目里形态还不同（高数用裸 `分析`，线代用 `【分析】`）。')
        L.append('')
        L.append('| 课程 | 总行数 | `分析` | `方法总结` | `良哥解读` | `展示新知` | `学习札记` | `考点追踪` |')
        L.append('|---|---:|---:|---:|---:|---:|---:|---:|')
        for r in data['markers']:
            m = r['markers']
            L.append('| %s | %d | %d | %d | %d | %d | %d | %d |' % (
                r['course'], r['total_lines'], m.get('分析', 0), m.get('方法总结', 0),
                m.get('良哥解读', 0), m.get('展示新知', 0), m.get('学习札记', 0),
                m.get('考点追踪', 0)))
        L.append('')
        L.append('### 8.1 权威版本：行内标记全库清单（44 个，>=3 次）')
        L.append('')
        L.append('| 标记 | 全库次数 | 分布 |')
        L.append('|---|---:|---|')
        L.append('| `【解答】` | 426 | **408 三科全部**（数据 160 / 操作 110 / 计算 77 / 网络 79） |')
        L.append('| `【解析】` | 342 | **概率 337** |')
        L.append('| `【例】` | 177 | 概率 177 |')
        L.append('| `【分析】` | 68 | **仅线代** |')
        L.append('| `【评注】` | 48 | **仅线代** |')
        L.append('| `【YYYY统考真题】` | 40–47 × 16 年 | 408 全部（**年份指针，非推理**） |')
        L.append('| `【注】` | 35 | 线代 31 / 概率 4 |')
        L.append('| **`【另解】`** | **34** | **数据结构 26** —— 材料自己标出的"**另一条合法解法**" |')
        L.append('')
        L.append('**三条此前不知道的事实**：')
        L.append('')
        L.append('1. **408 的答案标记是 `【解答】`（426 次），不是 `【解析】`**——早先的调研完全没覆盖 408 的答案层。')
        L.append('2. **`【另解】` 是"另一条合法解法"标记**——任务书要区分"自然的错误路线"与"另一条合法路线"，'
                 '而材料**自己就标出了后者**，这对轨迹数据集价值很高。')
        L.append('3. **同一个词在不同科目里形态不同**：高数用**裸** `分析`，线代用 `【分析】`。'
                 '任何单一形态的正则都会系统性漏掉一半。')
        L.append('')

    u = data['unexplained']
    L.append('## 9. 未解释案例与候选新算子')
    L.append('')
    L.append('- 候选新算子：%s ｜ 达升级阈值（>=3 次）：**%s**' % (
        u['candidates'], u['recommended_promotion']))
    L.append('- 标 UNKNOWN/UNEXPLAINED 的 Episode：%s' % u['unknown_episodes'])
    L.append('- 无任何母算子命中的 Episode：**%s**' % u['no_operator_match'])
    L.append('  → 这个"零"值得警惕：**一套从不"解释不了"的词表，本身就是需要怀疑的对象**')
    L.append('')

    if data['family_seeds']:
        fs = data['family_seeds']
        L.append('## 10. 机械聚类种子的碎片化（Family 阶段的警示）')
        L.append('')
        L.append('- 种子总数 %s ｜ >=3 条的 %s ｜ 2 条的 %s ｜ **单例 %s** ｜ 最大 %s' % (
            fs['seeds_total'], fs['seeds_with_ge3'], fs['seeds_with_2'],
            fs['seeds_with_1'], fs['largest_seed']))
        L.append('- → 机械签名**几乎逐题唯一**，只能当提示、不能当类。'
                 'Family worker 必须做语义聚类，最终 family 数应远小于种子数。')
        L.append('')

    text = '\n'.join(L) + '\n'
    if args.out_md:
        with io.open(args.out_md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
