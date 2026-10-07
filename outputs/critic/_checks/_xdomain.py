# -*- coding: utf-8 -*-
"""跨领域迁移审计：C1 使用的 20 个共享算子，逐条核对数学侧是否有同构实例"""
import json,os,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
math={}
for w in ["M5","M6","M8"]:
    for r in load(w):
        for m in (r.get("existing_operator_matches") or []):
            math.setdefault(m["operator_id"],[]).append((r["problem_id"],m.get("why","")))
print("C1 使用的算子 → 数学侧(M5/M6/M8)实例数")
rows=[]
for r in load("C1"):
    for m in (r.get("existing_operator_matches") or []):
        rows.append((m["operator_id"],r["problem_id"],m.get("is_primary_move"),m.get("why","")))
c=collections.Counter(x[0] for x in rows)
for op,n in c.most_common():
    m=math.get(op,[])
    print(f"  {op:34s} C1={n:2d}  数学侧={len(m):2d}  {'跨域成立' if m and n else '仅单侧'}")
    if op in ("SPACE_AUGMENTATION","INVARIANT_BLOCK_DECOMPOSITION","LOW_BANDWIDTH_INTERFACE","RIGIDIFY","SHARED_WORLD_EMBEDDING","STRUCTURAL_PROGRESS"):
        print("     C1 用法:")
        for o,pid,pm,why in rows:
            if o==op: print(f"       {pid} primary={pm}: {why[:130]}")
        print("     数学侧用法:")
        for pid,why in m[:4]: print(f"       {pid}: {why[:130]}")
