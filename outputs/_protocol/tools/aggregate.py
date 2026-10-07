#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aggregate.py — 从 raw_episodes/*.jsonl 机械聚合出证据矩阵与统计。

用法:
  python aggregate.py --dir <raw_episodes> --outdir <outputs>

产出:
  <outdir>/operator_evidence_matrix.csv        任务书 §15 要求
  <outdir>/_index/operator_stats.json          每个算子的跨域/跨章节统计 + 机械推导的证据等级
  <outdir>/_index/trigger_signals_raw.jsonl    扁平化 trigger 信号（供语义聚类 worker 消费）
  <outdir>/_index/anti_trigger_raw.jsonl       扁平化 anti-trigger / naive_routes
  <outdir>/_index/geometry_axes.json           八个问题几何轴的填充分布
  <outdir>/_index/family_seeds.json            按主算子+几何签名分组的聚类种子

证据等级机械推导规则（对应 SPEC §5）:
  n_domains >= 2                                  -> E5  跨领域
  n_distinct_sections >= 2 且 n_episodes >= 2      -> E4  不同章节/题型出现同一问题结构
  n_episodes >= 2                                  -> E3  多题反复出现同一 trigger -> transition
  n_episodes == 1                                  -> E1  单题（由答案事后推断）
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

GEOMETRY_AXES = [
    'representation_issue', 'redundant_freedom', 'coupling',
    'scale_competition', 'dependency_structure', 'information_risk',
    'state_transition_structure', 'resource_or_bottleneck_structure',
]

# 这些不是母算子：anti-operator 与哨兵值不应进入算子统计
NON_OPERATOR_LABELS = {
    'UNKNOWN', 'UNEXPLAINED', 'NONE', 'NULL',
    'PREMATURE_INFORMATION_LOSS', 'PREMATURE_ABSOLUTE_VALUE',
    'PREMATURE_APPROXIMATION', 'BAD_REPRESENTATION_LOCK_IN',
    'OVER_DECOUPLING', 'MISSING_SHARED_WITNESS', 'LOCAL_REPAIR_GLOBAL_ERROR',
    'DEPTH_TUNNEL_VISION', 'BRANCH_EXPLOSION', 'TARGET_DRIFT',
    'PROXY_OBJECTIVE_DRIFT', 'SEARCH_EXHAUSTED_AS_REFUTED',
    'PROMISING_AS_PROVED', 'DEPENDENCY_CYCLE',
    'RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE',
}

CSV_COLUMNS = [
    'operator_id', 'domain', 'problem_id', 'trigger_signal',
    'before_state', 'after_state', 'evidence_quality',
    'is_primary_move', 'is_posthoc_only', 'notes',
]


def load_all(raw_dir):
    """返回 [(worker, rec)]，worker 从文件名推导。"""
    out = []
    for fn in sorted(f for f in os.listdir(raw_dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        worker = os.path.splitext(fn)[0]
        path = os.path.join(raw_dir, fn)
        with io.open(path, encoding='utf-8') as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                rec['_worker'] = worker
                rec['_line'] = lineno
                out.append((worker, rec))
    return out


def derive_level(n_ep, n_dom, n_sec, meaningful_cross=False):
    """机械推导证据等级。

    ⚠️ 关键修正：早先的规则是"n_dom >= 2 → E5"，结果在只有 3 个领域、
    标签又被宽松使用时，**93% 的算子证据行都被判成 E5**——E5 变成了默认值，
    失去了区分力。

    一个覆盖 45% 题目的算子会**必然**出现在每个领域里，它的"跨领域"是
    覆盖率高的副产品，不是迁移证据。因此：
      * 只有当跨领域**且**覆盖率 < 25%（meaningful_cross）时，才判 E5；
      * 否则若它在多个领域出现但属万能标签，**降级按章节数判定**（最多 E4）。
    """
    if meaningful_cross:
        return 'E5'
    if n_sec >= 2 and n_ep >= 2:
        return 'E4'
    if n_ep >= 2:
        return 'E3'
    return 'E1'


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--outdir', default=os.path.abspath(os.path.join(here, '..', '..')))
    args = ap.parse_args()

    idx_dir = os.path.join(args.outdir, '_index')
    os.makedirs(idx_dir, exist_ok=True)

    eps = load_all(args.dir)
    if not eps:
        print('no episodes found in %s' % args.dir)
        return 1

    # ---------------------------------------------------------- 证据矩阵
    rows = []
    op_eps = defaultdict(set)          # operator_id -> set(problem_id)
    op_domains = defaultdict(set)
    op_sections = defaultdict(set)
    op_primary = Counter()
    domain_eps = Counter()
    geom_fill = Counter()
    geom_nonempty = Counter()
    trigger_rows = []
    anti_rows = []
    fam_seeds = defaultdict(list)
    non_op_labels = Counter()
    non_op_examples = defaultdict(list)
    failure_types = Counter()
    failure_examples = defaultdict(list)
    unknown_claimed = []

    for worker, rec in eps:
        pid = rec.get('problem_id', '?')
        dom = rec.get('domain', '')
        src = rec.get('source') or {}
        section = '%s#%s' % (src.get('repo_path', ''), src.get('section', ''))
        domain_eps[dom] += 1

        geo = rec.get('initial_geometry') or {}
        for ax in GEOMETRY_AXES:
            v = geo.get(ax, '')
            if isinstance(v, str) and v.strip():
                geom_nonempty[ax] += 1
            geom_fill[ax] += 1

        ts = rec.get('trigger_signals') or []
        ts_joined = ' || '.join(str(t) for t in ts)
        kts = rec.get('key_transitions') or []
        first_kt = kts[0] if kts else {}

        matches = rec.get('existing_operator_matches') or []
        emitted_real = False

        # ⚠️ Critic / UNEXPLAINED worker 两次指出：部分被 worker 自己标为
        # UNKNOWN/UNEXPLAINED 的 Episode，其 existing_operator_matches 里
        # 仍留着 is_primary_move: true 的母算子。若照单全收，下游按
        # is_primary_move 聚合时会把"worker 承认解释不了的条目"当成正常证据，
        # **污染算子覆盖率与 E4/E5 判定**。
        #
        # 判据演化史（三次修正，值得记录）：
        #   v1 `UNKNOWN\b`          → 误伤 29 条（含 M8 的"UNKNOWN 子步骤"）
        #   v2 窄模式（标 UNKNOWN 等）→ 只拦下 20 条
        #   v3 本版：三路并集，并用 `possible_new_operator` 作为主信号
        # `unexplained_cases.md` 实测应为 **36 条**，v2 只拦下 20 条（漏 44%）。
        notes_blob = (rec.get('notes') or '')
        has_candidate = bool(rec.get('possible_new_operator'))
        # "UNKNOWN 子步骤"是合法的部分未知，不能据此排除整条 —— 显式豁免
        partial_only = bool(re.search(r'UN(?:KNOWN|EXPLAINED)\s*子步骤', notes_blob))
        is_unknown = (
            rec.get('confidence') == 'unknown'
            or has_candidate
            or (not partial_only and re.search(
                r'UN(?:KNOWN|EXPLAINED)', notes_blob) is not None)
        )
        if is_unknown and matches:
            unknown_claimed.append({
                'problem_id': pid,
                'worker': worker,
                'domain': dom,
                'confidence': rec.get('confidence'),
                'claimed_operators': [m.get('operator_id') for m in matches
                                      if isinstance(m, dict)],
                'claimed_primary': [m.get('operator_id') for m in matches
                                    if isinstance(m, dict) and m.get('is_primary_move')],
            })
            matches = []

        for m in matches:
            if not isinstance(m, dict):
                continue
            oid = m.get('operator_id', '')
            if not oid:
                continue
            is_primary = bool(m.get('is_primary_move'))
            if oid in NON_OPERATOR_LABELS:
                # 记入非算子标签，不污染算子统计
                non_op_labels[oid] += 1
                non_op_examples[oid].append(pid)
                continue
            op_eps[oid].add(pid)
            op_domains[oid].add(dom)
            op_sections[oid].add(section)
            if is_primary:
                op_primary[oid] += 1
            emitted_real = True
            note = (m.get('why', '') or '')
            rows.append({
                'operator_id': oid,
                'domain': dom,
                'problem_id': pid,
                'trigger_signal': ts_joined[:300],
                'before_state': str(first_kt.get('before_state', ''))[:300],
                'after_state': str(first_kt.get('after_state', ''))[:300],
                'evidence_quality': 'E1',
                'is_primary_move': 'true' if is_primary else 'false',
                'is_posthoc_only': 'false' if is_primary else 'true',
                'notes': note[:200],
            })

        # 没有任何**母算子**命中（未填 matches，或只填了 anti-operator）→ 记 UNKNOWN
        if not emitted_real:
            rows.append({
                'operator_id': 'UNKNOWN',
                'domain': dom,
                'problem_id': pid,
                'trigger_signal': ts_joined[:300],
                'before_state': str(first_kt.get('before_state', ''))[:300],
                'after_state': str(first_kt.get('after_state', ''))[:300],
                'evidence_quality': 'E1',
                'is_primary_move': 'unknown',
                'is_posthoc_only': 'unknown',
                'notes': (rec.get('notes') or '')[:200],
            })

        # 聚类种子：主算子 + 几何签名
        primary_ops = [m.get('operator_id') for m in matches
                       if isinstance(m, dict) and m.get('is_primary_move')]
        geo_sig = '|'.join(ax for ax in GEOMETRY_AXES
                           if isinstance(geo.get(ax, ''), str) and geo.get(ax, '').strip())
        key = (primary_ops[0] if primary_ops else 'UNKNOWN') + ' :: ' + (geo_sig or '(no-geometry)')
        fam_seeds[key].append({
            'problem_id': pid,
            'domain': dom,
            'main_obstacle': (rec.get('main_obstacle') or '')[:200],
            'repo_path': src.get('repo_path', ''),
        })

        for i, t in enumerate(ts):
            trigger_rows.append({
                'problem_id': pid,
                'domain': dom,
                'worker': worker,
                'signal_index': i,
                'signal': t,
                'operator_hint': (primary_ops[0] if primary_ops else None),
            })

        for i, a in enumerate(rec.get('anti_triggers') or []):
            anti_rows.append({
                'problem_id': pid, 'domain': dom, 'kind': 'anti_trigger',
                'index': i, 'text': a,
            })
        for i, r in enumerate(rec.get('naive_routes') or []):
            if isinstance(r, dict):
                ft = (r.get('failure_type') or '').strip()
                if ft:
                    failure_types[ft] += 1
                    if len(failure_examples[ft]) < 5:
                        failure_examples[ft].append(pid)
                anti_rows.append({
                    'problem_id': pid, 'domain': dom, 'kind': 'naive_route',
                    'index': i,
                    'text': r.get('route', ''),
                    'why_natural': r.get('why_natural', ''),
                    'why_bad': r.get('why_bad_or_expensive', ''),
                    'failure_type': ft,
                })

    # 回填每条行的 evidence_quality（用算子级推导等级）
    op_stats = {}
    for oid in sorted(op_eps):
        n_ep = len(op_eps[oid])
        n_dom = len(op_domains[oid])
        n_sec = len(op_sections[oid])
        coverage = n_ep / max(1, len(eps))
        meaningful_cross = (n_dom >= 2 and coverage < 0.25)
        op_stats[oid] = {
            'operator_id': oid,
            'n_episodes': n_ep,
            'n_domains': n_dom,
            'n_distinct_sections': n_sec,
            'coverage': round(coverage, 3),
            'domains': sorted(op_domains[oid]),
            'n_primary_move': op_primary[oid],
            'derived_evidence_level': derive_level(n_ep, n_dom, n_sec, meaningful_cross),
            'cross_domain': n_dom >= 2,
            # ⚠️ 关键区分：一个覆盖 45% 题目的算子会**必然**出现在每个领域里，
            # 因此"跨领域"本身不构成有意义的迁移证据。只有当算子**不是**
            # 万能标签（覆盖率 < 25%）却仍跨领域时，才说明它捕捉到了
            # 真正可迁移的结构。否则它只是"哪儿都能套"的另一种表现。
            'cross_domain_meaningful': meaningful_cross,
            'enters_stable_ontology': derive_level(n_ep, n_dom, n_sec, meaningful_cross) in ('E3', 'E4', 'E5'),
        }
    for r in rows:
        st = op_stats.get(r['operator_id'])
        if st:
            r['evidence_quality'] = st['derived_evidence_level']

    # ---------------------------------------------------------- 写 CSV
    csv_path = os.path.join(args.outdir, 'operator_evidence_matrix.csv')
    with io.open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x['operator_id'], x['problem_id'])):
            w.writerow(r)

    def dump_json(name, obj):
        with io.open(os.path.join(idx_dir, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=1))

    def dump_jsonl(name, items):
        with io.open(os.path.join(idx_dir, name), 'w', encoding='utf-8', newline='\n') as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + '\n')

    # ---------------------------------------------------------- 集中度分析
    # 任务书 §18 的核心担忧："如果一个标签什么题都能套，要求降级或拆分"。
    # 这里把它量化：单一算子覆盖率过高即判定为"万能标签嫌疑"。
    ranked = sorted(op_stats.values(), key=lambda v: -v['n_episodes'])
    n_eps = max(1, len(eps))
    concentration = []
    for v in ranked:
        concentration.append({
            'operator_id': v['operator_id'],
            'n_episodes': v['n_episodes'],
            'coverage': round(v['n_episodes'] / n_eps, 3),
            'as_primary': v['n_primary_move'],
            'primary_share': round(v['n_primary_move'] / n_eps, 3),
        })
    top1 = concentration[0]['coverage'] if concentration else 0.0
    top2 = round(sum(c['coverage'] for c in concentration[:2]), 3)
    top3 = round(sum(c['coverage'] for c in concentration[:3]), 3)
    overused = [c for c in concentration if c['coverage'] >= 0.25]

    dump_json('operator_stats.json', {
        'total_episodes': len(eps),
        'operators_seen': len(op_stats),
        'operators_entering_ontology': sum(1 for v in op_stats.values() if v['enters_stable_ontology']),
        'operators_cross_domain': sum(1 for v in op_stats.values() if v['cross_domain']),
        # Critic 发现 A2：被标 UNKNOWN 却仍挂着主算子的条目（已从算子统计中剔除）
        'unknown_episodes_excluded_from_operator_stats': {
            'count': len(unknown_claimed),
            'note': ('这些 Episode 的 worker 自己标了 UNKNOWN/UNEXPLAINED，'
                     '但 existing_operator_matches 里仍有 is_primary_move: true 的母算子。'
                     '本脚本已把它们**排除在算子统计之外**，以免污染覆盖率与 E4/E5 判定。'
                     '原始数据未改动——是否清理由聚合/人工决定。'),
            'episodes': unknown_claimed,
        },
        'operators_cross_domain_meaningful': sum(
            1 for v in op_stats.values() if v['cross_domain_meaningful']),
        'cross_domain_caveat': (
            'cross_domain 只表示该算子在 >=2 个领域出现过。一个覆盖率很高的'
            '万能标签会必然跨领域，因此 cross_domain 本身不构成迁移证据；'
            '只有 cross_domain_meaningful（跨领域且覆盖率 < 25%）才是。'),
        'non_operator_labels': {k: {'count': v, 'examples': non_op_examples[k][:5]}
                                for k, v in non_op_labels.most_common()},
        'concentration': {
            'top1_coverage': top1,
            'top2_coverage': top2,
            'top3_coverage': top3,
            'overused_threshold': 0.25,
            'overused_operators': overused,
            'verdict': (
                'WARNING: 单一算子覆盖 >= 25%%，存在万能标签风险，必须拆分或降级'
                if overused else 'OK: 无算子覆盖率超过 25%%'
            ),
            'ranking': concentration,
        },
        # 对照：anti-operator（failure_type）的集中度。
        # 与母算子集中度对比，可以看出"为什么失败"的语言是否比
        # "做了什么"的语言更有区分度。
        'anti_operator_concentration': {
            'total_naive_routes': sum(failure_types.values()),
            'distinct_failure_types': len(failure_types),
            'top1_share': round(
                (failure_types.most_common(1)[0][1] / max(1, sum(failure_types.values())))
                if failure_types else 0.0, 3),
            'top3_share': round(
                (sum(v for _, v in failure_types.most_common(3)) / max(1, sum(failure_types.values())))
                if failure_types else 0.0, 3),
            'distribution': [
                {'failure_type': k, 'count': v,
                 'share': round(v / max(1, sum(failure_types.values())), 3),
                 'examples': failure_examples[k]}
                for k, v in failure_types.most_common()
            ],
        },
        'operators': op_stats,
    })
    dump_json('geometry_axes.json', {
        'axes': {ax: {'nonempty': geom_nonempty[ax], 'total': geom_fill[ax]} for ax in GEOMETRY_AXES},
        'domain_episode_counts': dict(domain_eps),
    })
    seed_sizes = [len(v) for v in fam_seeds.values()]
    dump_json('family_seeds.json', {
        'seed_count': len(fam_seeds),
        'fragmentation': {
            'seeds_total': len(fam_seeds),
            'seeds_with_ge3': sum(1 for x in seed_sizes if x >= 3),
            'seeds_with_2': sum(1 for x in seed_sizes if x == 2),
            'seeds_with_1': sum(1 for x in seed_sizes if x == 1),
            'largest_seed': max(seed_sizes) if seed_sizes else 0,
            'note': ('机械签名（主算子+几何轴集合）几乎逐题唯一，'
                     'seed 只能当作"可能相关的提示"，不是已经分好的类。'
                     '聚类 worker 必须做语义聚类；最终 family 数应远小于 seed 数。'),
        },
        'seeds': [{'seed': k, 'episodes': v} for k, v in
                  sorted(fam_seeds.items(), key=lambda kv: -len(kv[1]))],
    })
    dump_jsonl('trigger_signals_raw.jsonl', trigger_rows)
    dump_jsonl('anti_trigger_raw.jsonl', anti_rows)

    print('episodes=%d operators=%d cross_domain=%d csv_rows=%d' % (
        len(eps), len(op_stats),
        sum(1 for v in op_stats.values() if v['cross_domain']), len(rows)))
    print('written %s' % csv_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
