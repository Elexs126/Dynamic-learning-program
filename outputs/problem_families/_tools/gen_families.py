# -*- coding: utf-8 -*-
"""Generate FAMILIES.md, family_index.json and _NOTES.md for the problem-family clustering."""
import json, io, os, collections, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from famdefs import FAM, ORPHAN, UNASSIGNED, CONFUSABLE

ROOT = r'E:\杂七杂八的垃圾堆\LearningOS\outputs'
RAW = os.path.join(ROOT, 'raw_episodes')
PF = os.path.join(ROOT, 'problem_families')
WORKERS = ['M1','M2','M3','M4','M5','M6','M7','M8','C1','C2','C3']
SHORT = {'高等数学':'高数','线性代数':'线代','概率论与数理统计':'概率',
         '数据结构':'数据结构','操作系统':'操作系统','计算机组成原理':'组原'}
ORDER = ['F%02d' % i for i in range(1, 25) if 'F%02d' % i in FAM]


def load():
    eps = {}
    for w in WORKERS:
        with io.open(os.path.join(RAW, w + '.jsonl'), encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    e = json.loads(line)
                    eps[e['problem_id']] = e
    return eps


def stats(eps, members):
    ops, prim, fail = collections.Counter(), collections.Counter(), collections.Counter()
    for pid in members:
        e = eps[pid]
        for m in e.get('existing_operator_matches') or []:
            ops[m['operator_id']] += 1
            if m.get('is_primary_move'):
                prim[m['operator_id']] += 1
        for r in e.get('naive_routes') or []:
            if r.get('failure_type'):
                fail[r['failure_type']] += 1
    return ops, prim, fail


def main():
    eps = load()
    idset = set(eps)
    seen = {}
    for fid in ORDER:
        for pid in FAM[fid]['members']:
            assert pid in idset, (fid, pid)
            assert pid not in seen, (fid, pid, seen.get(pid))
            seen[pid] = fid
    for pid in ORPHAN['members']:
        assert pid in idset and pid not in seen, pid
        seen[pid] = 'F21o'
    for pid in UNASSIGNED:
        assert pid in idset and pid not in seen, pid

    # ---- HARD GATES (must pass before anything is written) --------------------
    fam_members = [pid for fid in ORDER for pid in FAM[fid]['members']]
    orph_members = list(ORPHAN['members'])
    all_members = fam_members + orph_members
    dup = sorted({p for p in all_members if all_members.count(p) > 1})
    assert not dup, '同一 Episode 落进多个族/孤儿组：%s' % dup
    assert len(set(all_members) | set(UNASSIGNED)) == len(idset), (
        '归属总数 %d != 语料规模 %d；未归属：%s' % (
            len(set(all_members) | set(UNASSIGNED)), len(idset),
            sorted(idset - set(all_members) - set(UNASSIGNED))))
    assert len(set(all_members) & set(UNASSIGNED)) == 0, 'UNASSIGNED 与族成员重叠'
    assert len(ORDER) == len(FAM), 'ORDER 与 FAM 数量不符'
    for fid in ORDER:
        assert len(FAM[fid]['members']) >= 3, '族 %s 少于 3 条' % fid
    assert len(ORPHAN['members']) < 3, '孤儿组已达 3 条，应升级为正式族'
    print('GATES OK: corpus=%d families=%d fam_members=%d orphan=%d unassigned=%d'
          % (len(idset), len(ORDER), len(fam_members), len(orph_members), len(UNASSIGNED)))
    # --------------------------------------------------------------------------

    idx = []
    md = []
    md.append('# Problem Families —— 按问题几何聚类\n')
    md.append('> **语料**：`outputs/raw_episodes/` 下全部 11 个 worker 的 **255 条** Episode'
              '（M1 22 / M2 22 / M3 25 / M4 22 / M5 20 / M6 20 / M7 26 / M8 24 / C1 24 / C2 26 / C3 24）。\n')
    md.append('> ⚠️ **本次聚类基于 255 条，C4 未参与**——C4（计算机网络）在本报告生成时已有 '
              '**23 条** Episode 落盘，但**未参与本次聚类**，本报告不含任何 C4 内容，也不对网络侧结构做任何推断。'
              '（覆盖 255 / 278 条。）\n')
    md.append('> **第一依据**是 `_protocol/EPISODE_SPEC.md` §6.1 的八个问题几何轴；'
              '母算子只用于描述族内的**结构动作**，**不作为分族依据**（按算子分组只能得到 29 个桶，那不是问题族）。\n')
    md.append('> **规模**：**22 个正式族**（每族 ≥3 条，覆盖 %d 条）+ **1 个孤儿组**（2 条）+ **4 条 UNASSIGNED**。\n'
              % sum(len(FAM[f]['members']) for f in ORDER))
    md.append('> 方法论、失败尝试与全部 UNASSIGNED 理由见 [`_NOTES.md`](_NOTES.md)；'
              '机器可读见 [`family_index.json`](family_index.json)。\n')
    md.append('\n## 总览\n')
    md.append('| family | 族名（问题几何语言） | 条数 | 覆盖领域 | 跨领域 | 代表 |\n|---|---|---:|---|---|---|\n')

    for fid in ORDER:
        d = FAM[fid]
        members = d['members']
        doms = sorted(set(SHORT[eps[p]['domain']] for p in members))
        reps = [p for p in d['reps'] if p in members]
        md.append('| %s | %s | %d | %s | %s | %s |\n' % (
            fid, d['name'], len(members), ' / '.join(doms),
            '**是**' if len(doms) >= 2 else '否', ' '.join('`%s`' % p for p in reps)))

    for fid in ORDER:
        d = FAM[fid]
        members = d['members']
        ops, prim, fail = stats(eps, members)
        doms = sorted(set(SHORT[eps[p]['domain']] for p in members))
        cross = len(doms) >= 2
        reps = [p for p in d['reps'] if p in members]
        md.append('\n---\n\n## %s — %s\n' % (fid, d['name']))
        md.append('- **条数**：%d ｜ **领域**：%s ｜ **跨领域**：%s\n'
                  % (len(members), ' / '.join(doms), '**是**' if cross else '否'))
        md.append('- **几何轴**：%s\n' % ', '.join('`%s`' % a for a in d['axes']))
        md.append('- **共享结构动作**（族内高频母算子，非分族依据）：%s\n' % ', '.join(
            '%s ×%d' % (k, v) for k, v in ops.most_common(6)))
        md.append('- **代表 Episode**：%s\n' % '、'.join('`%s`' % p for p in reps))
        md.append('\n### 判据（可判定条件）\n\n%s\n' % d['criteria'])
        md.append('\n### 典型 trigger（从题面可观察）\n')
        for t in d['triggers']:
            md.append('- %s\n' % t)
        md.append('\n### 常见第一反应（naive route）\n')
        for t in d['naive']:
            md.append('- %s\n' % t)
        md.append('\n### 更好的结构动作\n')
        for t in d['better']:
            md.append('- %s\n' % t)
        md.append('\n### 常见错误路线\n')
        md.append('| 路线 | failure_type | 后果 |\n|---|---|---|\n')
        for r, ft, c in d['errors']:
            md.append('| %s | `%s` | %s |\n' % (r, ft, c))
        if fail:
            md.append('\n> 本族成员实际记录的 anti-operator 计数：%s\n'
                      % ', '.join('%s ×%d' % (k, v) for k, v in fail.most_common(5)))
        md.append('\n### 变式边界\n\n%s\n' % d['boundary'])
        md.append('\n### 跨学科迁移\n\n%s\n' % d['transfer'])
        md.append('\n### 容易混淆的族与分界问句\n\n%s\n' % d['confuse'])
        idx.append(dict(
            family_id=fid, name=d['name'],
            criteria=d['criteria'].replace('\n', ' ')[:400],
            members=members, representative=reps,
            axes=d['axes'], shared_operators=[k for k, _ in ops.most_common(5)],
            confusable_with=CONFUSABLE.get(fid, []),
            domains=doms, cross_domain=cross,
            top_anti_operators=[k for k, _ in fail.most_common(3)]))

    d = ORPHAN
    ops, prim, fail = stats(eps, d['members'])

    # cross-domain id lists (口径 A 宽 / 口径 B 严) — computed BEFORE they are written out
    def doms_of(fid):
        return sorted(set(SHORT[eps[p]['domain']] for p in FAM[fid]['members']))
    def _math(fid): return bool(set(doms_of(fid)) & {'高数','线代','概率'})
    def _408(fid):  return bool(set(doms_of(fid)) & {'数据结构','操作系统','组原'})
    a_ids = [f for f in ORDER if len(doms_of(f)) >= 2]
    b_ids = [f for f in ORDER if _math(f) and _408(f)]

    md.append('\n---\n\n## F21o — %s（孤儿组，不计入族数）\n' % d['name'])
    md.append('- **条数**：%d ｜ **领域**：%s ｜ **跨领域**：**是**\n'
              % (len(d['members']), ' / '.join(sorted(set(SHORT[eps[p]['domain']] for p in d['members'])))))
    md.append('- **几何轴**：%s\n' % ', '.join('`%s`' % a for a in d['axes']))
    md.append('- **共享结构动作**：%s\n' % ', '.join('%s ×%d' % (k, v) for k, v in ops.most_common(5)))
    md.append('- **代表 Episode**：%s\n\n### 判据\n\n%s\n' % (
        '、'.join('`%s`' % p for p in d['reps']), d['criteria']))
    md.append('\n### 典型 trigger\n')
    for t in d['triggers']:
        md.append('- %s\n' % t)
    md.append('\n### 更好的结构动作\n')
    for t in d['better']:
        md.append('- %s\n' % t)
    md.append('\n### 跨学科迁移\n\n%s\n' % d['transfer'])
    md.append('\n### 分界问句\n\n%s\n' % d['confuse'])
    orphan_payload = dict(
        family_id='F21o', name=d['name'], criteria=d['criteria'].replace('\n', ' ')[:400],
        members=d['members'], representative=d['reps'], axes=d['axes'],
        shared_operators=[k for k, _ in ops.most_common(5)],
        confusable_with=CONFUSABLE.get('F21o', []),
        domains=sorted(set(SHORT[eps[p]['domain']] for p in d['members'])),
        cross_domain=True, top_anti_operators=[k for k, _ in fail.most_common(3)],
        status='orphan_group')

    md.append('\n---\n\n## UNASSIGNED（%d 条，不硬塞）\n' % len(UNASSIGNED))
    md.append('\n这些 Episode **不归入任何族**。共同特征是：抽取者本人已标 `confidence: unknown`，'
              '且障碍结构在现有八个几何轴与算子词表里**无格可填**。\n\n')
    md.append('| problem_id | 领域 | 为什么不归入任何族 |\n|---|---|---|\n')
    for pid in UNASSIGNED:
        md.append('| `%s` | %s | %s |\n' % (pid, SHORT[eps[pid]['domain']], UNASSIGNED[pid]))

    md.append('\n---\n\n## 跨领域族清单（两个口径，必须分开引用）\n\n')
    md.append('「跨领域」在本项目里被用过两种含义，因此这里**显式给出两个口径**，'
              '并在 `family_index.json` 的 `cross_domain_definitions` 字段里同时给出数字与族 ID 列表。\n\n')
    md.append('### 口径 A（宽）：族内覆盖 ≥2 个学科领域\n\n')
    md.append('共 **%d 个**：%s\n\n' % (len(a_ids), ' '.join('`%s`' % x for x in a_ids)))
    md.append('> 其中包含 8 个**纯数学跨章族**（高数 × 线代，或高数 × 概率）与 2 个**纯 408 跨课族**，'
              '它们**不是**数学 × 408 迁移。\n\n')
    md.append('### 口径 B（严）：族内同时含数学侧与 408 侧成员\n\n')
    md.append('共 **%d 个**：%s\n\n' % (len(b_ids), ' '.join('`%s`' % x for x in b_ids)))
    md.append('| family | 族名 | 条数 | 数学侧条数 | 408 侧条数 |\n|---|---|---:|---:|---:|\n')
    for fid in b_ids:
        d = FAM[fid]
        math = [p for p in d['members'] if eps[p]['domain'] in ('高等数学','线性代数','概率论与数理统计')]
        cs = [p for p in d['members'] if eps[p]['domain'] not in ('高等数学','线性代数','概率论与数理统计')]
        md.append('| %s | %s | %d | %d | %d |\n' % (fid, d['name'], len(d['members']), len(math), len(cs)))
    md.append('\n> ⚠️ **引用规则**：说「跨领域迁移」用**口径 B（%d 个）**；'
              '说「族覆盖的学科广度」用**口径 A（%d 个）**。两者不可互换。\n' % (len(b_ids), len(a_ids)))
    md.append('\n另有 4 个族**完全单一学科**：%s。\n'
              % ' '.join('`%s`' % f for f in ORDER
                         if len(set(SHORT[eps[p]['domain']] for p in FAM[f]['members'])) == 1))

    with io.open(os.path.join(PF, 'FAMILIES.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(md))

    payload = dict(
        generated_from='outputs/raw_episodes/*.jsonl — 11 workers, 255 episodes (M1..M8, C1..C3)',
        corpus_size=len(idset),
        corpus_note=('本次聚类基于 255 条（M1 22 / M2 22 / M3 25 / M4 22 / M5 20 / M6 20 / '
                     'M7 26 / M8 24 / C1 24 / C2 26 / C3 24）。'
                     'C4（计算机网络）在本报告生成时已有 23 条 Episode 落盘，但**未参与本次聚类**，'
                     '其归属未做任何推断。'),
        not_covered='C4 的 23 条未参与聚类；C4 也未出现在任何族的 members 中。',
        method='semantic clustering by initial problem geometry + obstacle type; operators used only as descriptors',
        # --- 两个「跨领域」口径，必须同时给出，避免 coverage_report 用错 ---
        cross_domain_definitions=dict(
            definition_a_any_two_domains=dict(
                label='口径 A（宽）：族内覆盖 ≥2 个学科领域（不区分是哪两个）',
                count=None, families=None),
            definition_b_math_x_408=dict(
                label='口径 B（严）：族内同时含数学侧（高数/线代/概率）与 408 侧（数据结构/操作系统/组原）成员',
                count=None, families=None),
            note=('口径 A（18 个）中，有 6 个是「纯数学跨章」族（高数 × 线代，或高数 × 概率），'
                  '2 个是「纯 408 跨课」族（F06 数据结构 × 操作系统；F22 数据结构 × 组原），'
                  '它们都不是数学 × 408 迁移。引用时必须指明口径：'
                  '说「跨领域迁移」用口径 B，说「族覆盖的学科广度」用口径 A。'),
        ),
        # --- 三个计数必须与各自的列表长度严格相等 ---
        family_count=len(ORDER),
        orphan_group_count=1,
        unassigned_count=len(UNASSIGNED),
        covered_by_families=len(fam_members),
        covered_by_families_incl_orphan_group=len(all_members),
        coverage_total=len(set(all_members) | set(UNASSIGNED)),
        families=idx,
        orphan_groups=[orphan_payload],
        unassigned=[dict(problem_id=p, domain=SHORT[eps[p]['domain']], reason=UNASSIGNED[p])
                    for p in UNASSIGNED],
    )

    # fill cross-domain definitions from the data actually written
    def is_math(f):  return bool(set(f['domains']) & {'高数','线代','概率'})
    def is_408(f):   return bool(set(f['domains']) & {'数据结构','操作系统','组原'})
    a = [f['family_id'] for f in payload['families'] if len(f['domains']) >= 2]
    b = [f['family_id'] for f in payload['families'] if is_math(f) and is_408(f)]
    payload['cross_domain_definitions']['definition_a_any_two_domains']['count'] = len(a)
    payload['cross_domain_definitions']['definition_a_any_two_domains']['families'] = a
    payload['cross_domain_definitions']['definition_b_math_x_408']['count'] = len(b)
    payload['cross_domain_definitions']['definition_b_math_x_408']['families'] = b
    payload['cross_domain_definitions']['definition_b_math_x_408']['families_excluding_orphan'] = [
        f for f in b if f != 'F21o']

    # final self-check on the serialized payload
    fam_ids = {f['family_id'] for f in payload['families']}
    og_ids = {g['family_id'] for g in payload['orphan_groups']}
    assert not (fam_ids & og_ids), '族 ID 同时出现在两个数组：%s' % (fam_ids & og_ids)
    fmem = [p for f in payload['families'] for p in f['members']]
    ogm = [p for g in payload['orphan_groups'] for p in g['members']]
    assert not (set(fmem) & set(ogm)), '同一 Episode 既在族里又在孤儿组：%s' % (set(fmem) & set(ogm))
    assert len(set(fmem) | set(ogm) | {u['problem_id'] for u in payload['unassigned']}) \
        == payload['corpus_size'], '三个数组的并集不等于语料规模'
    assert payload['family_count'] == len(payload['families']), 'family_count 与 families 不符'
    assert payload['orphan_group_count'] == len(payload['orphan_groups']), 'orphan_group_count 与列表不符'
    assert payload['unassigned_count'] == len(payload['unassigned']), 'unassigned_count 与列表不符'
    assert payload['covered_by_families'] == len(fmem), 'covered_by_families 与族成员之和不符'
    assert payload['covered_by_families_incl_orphan_group'] == len(fmem) + len(ogm), \
        'covered_by_families_incl_orphan_group 不符'
    assert payload['coverage_total'] == payload['corpus_size'], 'coverage_total 与 corpus_size 不符'

    with io.open(os.path.join(PF, 'FAMILIES.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(md))
    with io.open(os.path.join(PF, 'family_index.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=1))
    print('families=%d cross_A=%d cross_B=%d' % (len(ORDER), len(a), len(b)))
    for fid in ORDER:
        print('  %s %3d %s' % (fid, len(FAM[fid]['members']), FAM[fid]['name']))


main()
