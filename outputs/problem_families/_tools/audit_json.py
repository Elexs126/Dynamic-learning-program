# -*- coding: utf-8 -*-
"""Audit family_index.json for internal numeric consistency."""
import json, io, os, collections
PF = r'E:\杂七杂八的垃圾堆\LearningOS\outputs\problem_families'
RAW = r'E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes'
WORKERS = ['M1','M2','M3','M4','M5','M6','M7','M8','C1','C2','C3']

d = json.load(io.open(os.path.join(PF, 'family_index.json'), encoding='utf-8'))
fams = d['families']
orph = d.get('orphan_groups', [])
print('family_count field :', d['family_count'])
print('families list len  :', len(fams))
print('orphan_group_count :', d['orphan_group_count'])
print('orphan_groups len  :', len(orph))
print('covered_by_families:', d['covered_by_families'])
print('sum(len(members)) over families list:', sum(len(f['members']) for f in fams))
print('sum over families excluding orphan  :', sum(len(f['members']) for f in fams if f.get('status') != 'orphan_group'))
print('sum over orphan_groups              :', sum(len(f['members']) for f in orph))
print('unassigned_count    :', d['unassigned_count'])
print('unassigned list len :', len(d['unassigned']))
print('covered_by_families_incl_orphan_group:', d['covered_by_families_incl_orphan_group'])
print('coverage_total     :', d['coverage_total'])
cd = d['cross_domain_definitions']
print('cross-domain A (any 2+ domains) count:', cd['definition_a_any_two_domains']['count'])
print('  A families:', cd['definition_a_any_two_domains']['families'])
print('cross-domain B (math x 408)     count:', cd['definition_b_math_x_408']['count'])
print('  B families:', cd['definition_b_math_x_408']['families'])
print('  B families excl orphan:', cd['definition_b_math_x_408']['families_excluding_orphan'])

# duplicates across everything
allp = []
for f in fams:
    allp += f['members']
for f in orph:
    allp += f['members']
un = [u['problem_id'] for u in d['unassigned']]
c = collections.Counter(allp)
print('duplicate members:', [p for p, n in c.items() if n > 1])
print('sum(members)+orphan+unassigned =', len(allp) + len(un))
print('union size =', len(set(allp) | set(un)))

ids = []
for w in WORKERS:
    for line in io.open(os.path.join(RAW, w + '.jsonl'), encoding='utf-8'):
        line = line.strip()
        if line:
            ids.append(json.loads(line)['problem_id'])
print('corpus size =', len(ids))
print('in corpus but unassigned/assigned nowhere:', [p for p in ids if p not in set(allp) | set(un)])

# cross-domain tallies under the two definitions
any_multi = [f['family_id'] for f in fams if len(f['domains']) >= 2]
math408 = [f['family_id'] for f in fams if f.get('cross_domain') and
           set(f['domains']) & {'高数','线代','概率'} and
           set(f['domains']) & {'数据结构','操作系统','组原'}]
print('any 2+ domains :', len(any_multi), any_multi)
print('math x 408     :', len(math408), math408)

# --- structural assertions (same gates as the generator, applied to the written file) ---
fam_ids = {f['family_id'] for f in fams}
og_ids = {g['family_id'] for g in orph}
assert not (fam_ids & og_ids), '族 ID 同时出现在两个数组: %s' % (fam_ids & og_ids)
fmem = [p for f in fams for p in f['members']]
ogm = [p for g in orph for p in g['members']]
assert not (set(fmem) & set(ogm)), '同一 Episode 既在族里又在孤儿组: %s' % (set(fmem) & set(ogm))
assert len(set(fmem) | set(ogm) | set(un)) == len(ids), '三数组并集 != 语料规模'
assert d['family_count'] == len(fams)
assert d['orphan_group_count'] == len(orph)
assert d['unassigned_count'] == len(un)
assert d['covered_by_families'] == len(fmem)
assert d['coverage_total'] == len(ids)
print('ALL STRUCTURAL ASSERTIONS PASSED')
