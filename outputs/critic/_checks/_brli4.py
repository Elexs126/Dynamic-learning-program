# -*- coding: utf-8 -*-
"""BAD_REPRESENTATION_LOCK_IN 独立分类 v3（54 条全部人工判定，键=编号）"""
import json,os,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
routes=[]
for w in ["M5","M6","M8","C1"]:
    for r in load(w):
        for i,nr in enumerate(r.get("naive_routes") or []):
            if nr.get("failure_type")!="BAD_REPRESENTATION_LOCK_IN": continue
            routes.append((w,r["problem_id"],i,nr))

# 编号(1-based) -> 类别
# C = 违反题面明写硬约束（复杂度/空间/"不许改动"等）
# R = 表示/标准形锁死（用错表示或标准形硬算）
# M = 结构或对象身份误判
# A = 缺统一抽象 / 无离线判据
CLS = {
 1:"R", 2:"R", 3:"R", 4:"R", 5:"R", 6:"R", 7:"R", 8:"R", 9:"R",10:"R",
 11:"R",12:"R",13:"R",14:"R",15:"R",16:"R",
 17:"R",18:"R",19:"R",20:"R",21:"M",22:"R",23:"R",24:"R",
 25:"R",26:"M",27:"R",28:"M",29:"R",30:"M",31:"M",32:"M",33:"M",34:"M",
 35:"M",36:"R",37:"R",38:"M",39:"R",
 40:"M",41:"A",42:"C",43:"C",44:"A",45:"C",46:"C",47:"C",48:"R",49:"M",
 50:"R",51:"M",52:"R",53:"M",54:"M",
}
assert len(CLS)==len(routes), (len(CLS),len(routes))
NAME={"C":"CONSTRAINT_VIOLATION  违反题面明写硬约束","R":"REPRESENTATION_LOCK  表示/标准形锁死",
      "M":"STRUCTURE_MISREAD     结构或对象身份误判","A":"NO_ABSTRACTION         缺统一抽象/无离线判据"}
cnt=collections.Counter(); byw=collections.defaultdict(collections.Counter)
for n,(w,pid,i,nr) in enumerate(routes,1):
    c=CLS[n]; cnt[c]+=1; byw[w][c]+=1
tot=sum(cnt.values())
print("我负责的 4 worker：BAD_REPRESENTATION_LOCK_IN 共",tot,"条，独立分类：")
for k in ["R","M","C","A"]:
    print(f"  {NAME[k]:48s} {cnt[k]:3d}  ({cnt[k]/tot*100:.0f}%)")
print("\n按 worker（C1 与数学组的分野）：")
for w in ["M5","M6","M8","C1"]:
    print(f"  {w}: n={sum(byw[w].values()):2d}  " + "  ".join(f"{k}={byw[w][k]}" for k in ["R","M","C","A"]))
print("\nC1 中判为 CONSTRAINT_VIOLATION 的条目：")
for n,(w,pid,i,nr) in enumerate(routes,1):
    if CLS[n]=="C": print(f"  {pid}  {nr.get('route')}")
print("\n数学组(M5/M6/M8)中判为 CONSTRAINT_VIOLATION 的条目：")
for n,(w,pid,i,nr) in enumerate(routes,1):
    if CLS[n]=="C" and w!="C1": print(f"  {pid}  {nr.get('route')}")
