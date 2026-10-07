# -*- coding: utf-8 -*-
"""对 M5/M6/M8/C1 做 trigger 可观察性分诊（复用 observability_check 的思路，符号级）"""
import json,os,re,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

SYM=re.compile(r"\\[a-zA-Z]+|[A-Za-z]_\{?[a-zA-Z0-9]+\}?|[a-zA-Z]{2,}|\d+")
STOP=set("""看到说明可以因此所以应该必须出现存在如果就是要求目标问题结构动作步骤时的是在和中为对从到与及或则当若其不无有能会需把将被让使做用即等""".split())

for w in ["M5","M6","M8","C1"]:
    recs=load(w); ok=miss=nosym=0; flagged=[]
    for r in recs:
        raw=(r.get("raw_problem") or "")+" "+(r.get("problem_goal") or "")
        rawsym=set(x for x in SYM.findall(raw))
        for t in (r.get("trigger_signals") or []):
            syms=set(x for x in SYM.findall(t))
            syms={s for s in syms if len(s)>=2 and s not in STOP}
            if not syms: nosym+=1; continue
            # symbols appearing in trigger but NOT in problem statement
            extra=syms-rawsym
            if extra: miss+=1; flagged.append((r["problem_id"],sorted(extra)[:8],t[:120]))
            else: ok+=1
    print("="*100); print(f"### {w}: OK={ok} SYMBOL_MISSING={miss} NO_SYMBOLS={nosym}")
    for pid,extra,t in flagged:
        print(f"  {pid}  缺失符号={extra}")
        print(f"      {t}")
