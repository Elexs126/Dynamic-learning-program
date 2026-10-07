# -*- coding: utf-8 -*-
"""C2/C3 408 八字段实质性质检：长度、空值、跨条完全重复、与题面连续重合"""
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
def norm(s): return re.sub(r"[\s，。、（）()\[\]]+","",str(s or ""))

for w in ["C2","C3"]:
    recs=load(w)
    print("="*100); print(f"### {w}  ({len(recs)} 条)")
    print(f"{'pid':8s} " + " ".join(f"{f[:9]:>10s}" for f in F))
    tot=collections.Counter(); empty=collections.Counter()
    for r in recs:
        lens=[]
        for f in F:
            s=flat(r.get(f)); lens.append(len(s)); tot[f]+=len(s)
            if not s.strip(): empty[f]+=1
        print(f"{r['problem_id']:8s} " + " ".join(f"{x:>10d}" for x in lens))
    print("\n平均长度:", {f:round(tot[f]/len(recs)) for f in F})
    print("空字段数:", dict(empty))
    print("\n=== 跨条完全重复值 ===")
    for f in F:
        vals=[flat(r.get(f)) for r in recs]
        c=collections.Counter(vals)
        dup=[(v[:70],n) for v,n in c.items() if n>1 and v.strip()]
        print(f"  {f:26s} 完全重复值: {len(dup)}")
        for v,n in dup[:5]: print(f"      x{n}: {v!r}")
    print("\n=== 与题面连续重合 >=12 字（疑似把题面换个说法） ===")
    hit=0
    for r in recs:
        raw=norm(r.get("raw_problem"))
        for f in F:
            s=norm(flat(r.get(f)))
            if not s: continue
            best=0; seg=""
            for i in range(0,max(0,len(s)-11)):
                if s[i:i+12] in raw:
                    j=12
                    while i+j<len(s) and s[i:i+j+1] in raw: j+=1
                    if j>best: best=j; seg=s[i:i+j]
            if best>=12:
                hit+=1
                print(f"  {r['problem_id']} {f}: 重合 {best} 字 -> {seg!r}")
    print(f"  >>> 共 {hit} 处")
