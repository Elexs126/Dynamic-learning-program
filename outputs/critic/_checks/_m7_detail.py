# -*- coding: utf-8 -*-
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
recs={r["problem_id"]:r for r in load("M7")}
print("=== M7 中 EXACT_ELIMINATION 是否曾被标 primary ===")
for pid,r in recs.items():
    for m in r.get("existing_operator_matches",[]):
        if m["operator_id"]=="EXACT_ELIMINATION":
            print(f"  {pid}: primary={m.get('is_primary_move')} why={m['why'][:100]}")
print()
print("=== M7 主算子 >1 的条目 ===")
for pid,r in recs.items():
    pr=[m["operator_id"] for m in r.get("existing_operator_matches",[]) if m.get("is_primary_move")]
    if len(pr)>1: print(f"  {pid}: {pr}")
print()
print("=== M7-005 全文关键字段 ===")
r=recs["M7-005"]
for k in ["raw_problem","problem_goal","main_obstacle","trigger_signals","key_transitions","existing_operator_matches","naive_routes","evidence_excerpt","notes"]:
    v=r.get(k)
    print(f"--- {k}:")
    if isinstance(v,list):
        for i,x in enumerate(v):
            if isinstance(x,dict): print(f"   [{i}] "+" || ".join(f"{a}={b}" for a,b in x.items()))
            else: print(f"   [{i}] {x}")
    else: print(f"   {v}")
print()
print("=== M7-011 被跳过的源文件行 L203 附近 ===")
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
rel=recs["M7-011"]["source"]["repo_path"]
t=open(os.path.join(SRC,rel.replace("/",os.sep)),encoding="utf-8").read().split("\n")
for i in range(198,208): print(f"  L{i+1}: {t[i][:200]}")
print("  evidence_excerpt:",recs["M7-011"]["evidence_excerpt"][:300])
