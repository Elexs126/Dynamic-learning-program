# -*- coding: utf-8 -*-
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
for w in ["C2","C3","M7"]:
    print("="*100); print("###",w)
    recs=load(w)
    for r in recs:
        ex=(r.get("evidence_excerpt") or "").strip()
        raw=(r.get("raw_problem") or "").strip()
        if len(ex)<80:
            print(f"  [SHORT-EXCERPT {len(ex)}] {r['problem_id']}  {ex!r}")
        if len(raw)<40:
            print(f"  [SHORT-RAW {len(raw)}] {r['problem_id']}  {raw!r}")
        if not ex: print(f"  [EMPTY-EXCERPT] {r['problem_id']}")
        if not raw: print(f"  [EMPTY-RAW] {r['problem_id']}")
    print()
