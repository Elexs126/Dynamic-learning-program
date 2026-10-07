# -*- coding: utf-8 -*-
"""C1 408 八字段实质性质检：长度、是否复述题面、跨条重复度"""
import json,os,sys,io,re,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
F=["system_state","resources","agents_or_components","invariants","state_transition","bottleneck","local_vs_global_effect","layer_interface"]
def flat(v):
    if isinstance(v,list): return " | ".join(str(x) for x in v)
    return str(v or "")
recs=load("C1")
print(f"{'pid':8s} " + " ".join(f"{f[:9]:>10s}" for f in F))
tot=collections.Counter(); empty=collections.Counter()
for r in recs:
    lens=[]
    for f in F:
        s=flat(r.get(f))
        lens.append(len(s)); tot[f]+=len(s)
        if not s.strip(): empty[f]+=1
    print(f"{r['problem_id']:8s} " + " ".join(f"{x:>10d}" for x in lens))
print("\n平均长度:", {f:round(tot[f]/len(recs)) for f in F})
print("空字段数:", dict(empty))
print("\n=== 字段间重复（同一字段内容在多少条记录里高度相似）===")
for f in F:
    vals=[flat(r.get(f)) for r in recs]
    # 4-gram jaccard 近似：统计完全相同的
    c=collections.Counter(vals)
    dup=[(v[:60],n) for v,n in c.items() if n>1]
    print(f"  {f:26s} 完全重复值: {len(dup)}")
print("\n=== 检查是否只是把题面换个说法：字段内容与 raw_problem 的字面重合率 ===")
def norm(s): return re.sub(r"[\s，。、（）()\[\]]+","",str(s or ""))
for r in recs:
    raw=norm(r.get("raw_problem"))
    for f in F:
        s=norm(flat(r.get(f)))
        if not s: continue
        # 取最长公共连续子串近似：看是否有>=12字的连续重合
        best=0
        for i in range(0,len(s)-11):
            if s[i:i+12] in raw:
                j=12
                while i+j<len(s) and s[i:i+j+1] in raw: j+=1
                best=max(best,j)
        if best>=12:
            print(f"  {r['problem_id']} {f}: 与题面连续重合 {best} 字 -> {s[:90]}")
