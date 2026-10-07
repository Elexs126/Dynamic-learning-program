# -*- coding: utf-8 -*-
"""混合组(M5/M6/M8/C1) 算子集中度 + E3+ 自评检查"""
import json,os,sys,io,re,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
recs=[]
for w in ["M5","M6","M8","C1"]:
    for r in load(w): r["_w"]=w; recs.append(r)
N=len(recs)
cnt=collections.Counter(); prim=collections.Counter()
for r in recs:
    for m in (r.get("existing_operator_matches") or []):
        cnt[m["operator_id"]]+=1
        if m.get("is_primary_move"): prim[m["operator_id"]]+=1
print(f"混合组 Episode 数 = {N}")
print(f"不同算子数 = {len(cnt)}")
print("\n算子覆盖（按 episode 数）：")
cum=0
for op,n in cnt.most_common():
    cum+=n
    print(f"  {op:34s} {n:3d}  {n/N*100:5.1f}%  primary={prim[op]:3d}")
print(f"\ntop1={cnt.most_common(1)[0][1]/N*100:.1f}%  top2={sum(x[1] for x in cnt.most_common(2))/N*100:.1f}%  top3={sum(x[1] for x in cnt.most_common(3))/N*100:.1f}%")
print(f"覆盖 <25% 的算子数: {sum(1 for _,n in cnt.items() if n/N<0.25)} / {len(cnt)}")
# 只算数学组 vs 加 C1
for label,ws in [("数学组 M5+M6+M8",["M5","M6","M8"]),("混合组含 C1",["M5","M6","M8","C1"])]:
    sub=[r for r in recs if r["_w"] in ws]
    c=collections.Counter()
    for r in sub:
        for m in (r.get("existing_operator_matches") or []): c[m["operator_id"]]+=1
    n=len(sub)
    print(f"\n{label}: n={n}  top1={c.most_common(1)[0][1]/n*100:.1f}% ({c.most_common(1)[0][0]})  top3={sum(x[1] for x in c.most_common(3))/n*100:.1f}%")
# E3+ 自评
print("\nE3+ 自评检查：")
bad=[]
for r in recs:
    n=r.get("notes","") or ""
    for m in re.finditer(r"evidence_level:\s*(E\d)",n):
        if int(m.group(1)[1])>=3: bad.append((r["problem_id"],m.group(1)))
print("  自评 E3+ 的条数:",len(bad),bad)
# confidence 分布
print("\nconfidence 分布（混合组）:",dict(collections.Counter(r["confidence"] for r in recs)))
lv=collections.Counter()
for r in recs:
    m=re.search(r"evidence_level:\s*(E\d)",r.get("notes","") or "")
    lv[m.group(1) if m else "MISSING"]+=1
print("evidence_level 分布（混合组）:",dict(lv))
print("\n分 worker：")
for w in ["M5","M6","M8","C1"]:
    sub=[r for r in recs if r["_w"]==w]
    c=collections.Counter(r["confidence"] for r in sub)
    l=collections.Counter()
    for r in sub:
        m=re.search(r"evidence_level:\s*(E\d)",r.get("notes","") or "")
        l[m.group(1) if m else "MISSING"]+=1
    print(f"  {w}: n={len(sub)} conf={dict(c)} ev={dict(l)}")
