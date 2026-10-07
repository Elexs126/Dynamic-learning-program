# -*- coding: utf-8 -*-
"""E2 尺子：把 C2/C3 的 evidence_excerpt 与 raw_problem 比对（是否只是把答案句搬来），
   并统计 excerpt 内是否含"分析型"连接词。"""
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
def norm(s): return re.sub(r"\s+","",str(s or ""))
ANA=["之所以","因此","其原因","根本原因","为了","本质","关键","原因是","因而","于是","动机","思想是","意味着","需要注意","必须","否则","因此有","这说"]
for w in ["C2","C3"]:
    print("="*110); print("###",w)
    n_rawdup=0; n_ana=0
    for r in load(w):
        ex=norm(r.get("evidence_excerpt",""))
        raw=norm(r.get("raw_problem",""))
        dup = ex[:40] in raw if ex else False
        ana=[a for a in ANA if a in ex]
        if dup: n_rawdup+=1
        if ana: n_ana+=1
        prim=[m["operator_id"] for m in r.get("existing_operator_matches",[]) if m.get("is_primary_move")]
        print(f"  {r['problem_id']:8s} len={len(ex):5d} 与题面重合={'YES' if dup else 'no ':3s} 分析词={ana}  primary={prim}")
    print(f"  >>> excerpt 与 raw_problem 重合: {n_rawdup}/{len(load(w))}；含分析词: {n_ana}/{len(load(w))}")
