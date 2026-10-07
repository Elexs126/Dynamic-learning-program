# -*- coding: utf-8 -*-
import json, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from famdefs import FAM, ORPHAN, UNASSIGNED
ROOT = r'E:\杂七杂八的垃圾堆\LearningOS\outputs'
RAW = os.path.join(ROOT, 'raw_episodes')
WORKERS = ['M1','M2','M3','M4','M5','M6','M7','M8','C1','C2','C3']
all_ids = []
for w in WORKERS:
    with io.open(os.path.join(RAW, w + '.jsonl'), encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                all_ids.append(json.loads(line)['problem_id'])
assigned = set()
for fid, d in FAM.items():
    assigned |= set(d['members'])
assigned |= set(ORPHAN['members'])
assigned |= set(UNASSIGNED)
print('total', len(all_ids), 'assigned', len(assigned))
miss = [p for p in all_ids if p not in assigned]
print('MISSING (%d): %s' % (len(miss), ' '.join(miss)))
