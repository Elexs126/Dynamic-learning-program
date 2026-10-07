# -*- coding: utf-8 -*-
import json,os,re,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
ANTI=set("""PREMATURE_INFORMATION_LOSS PREMATURE_ABSOLUTE_VALUE PREMATURE_APPROXIMATION BAD_REPRESENTATION_LOCK_IN OVER_DECOUPLING MISSING_SHARED_WITNESS LOCAL_REPAIR_GLOBAL_ERROR DEPTH_TUNNEL_VISION BRANCH_EXPLOSION TARGET_DRIFT PROXY_OBJECTIVE_DRIFT SEARCH_EXHAUSTED_AS_REFUTED PROMISING_AS_PROVED DEPENDENCY_CYCLE RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE NEWTON_LEIBNIZ_BLIND_APPLICATION UNJUSTIFIED_SYMMETRY_TRANSFER MISSING_ABSOLUTE_VALUE UNRESOLVED_CONSTRAINT_CONFLICT MISMATCHED_ENCODING_ORDER MISSING_BOUNDARY_CASE""".split())
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
print("=== C2/C3 naive_routes[].failure_type 分布 ===")
for w in ["C2","C3"]:
    c=collections.Counter(); unknown=[]
    for r in load(w):
        for nr in r.get("naive_routes",[]):
            ft=nr.get("failure_type","")
            c[ft]+=1
            if ft not in ANTI: unknown.append((r["problem_id"],ft))
    print(f"\n{w}: {dict(c)}")
    print(f"  词表外 failure_type: {unknown}")
print()
print("=== C2/C3 operation 字段里出现的 anti-operator（含未在 matches 中的） ===")
ALLANTI=ANTI
for w in ["C2","C3"]:
    for r in load(w):
        for i,t in enumerate(r.get("key_transitions",[])):
            op=str(t.get("operation",""))
            found=[x for x in re.findall(r"[A-Z][A-Z_]{4,}",op) if x in ALLANTI]
            if found: print(f"  {r['problem_id']} T{i}: {found} :: {op[:130]}")
print()
print("=== C2-014 源文件是否含 4MB / 4 字节 ===")
p="核心真题/408/2024年全国硕士研究生招生考试408计算机学科专业基础综合真题.md"
t=open(os.path.join(SRC,p.replace("/",os.sep)),encoding="utf-8").read().split("\n")
for i,l in enumerate(t,1):
    if "4MB" in l or "页表项的大小" in l or "页大小" in l:
        print(f"  L{i}: {l[:260]}")
