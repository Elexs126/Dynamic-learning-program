# -*- coding: utf-8 -*-
"""trigger_signals 可观察性：把 trigger 里引号内的短语与 raw_problem 对照"""
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
def norm(s): return re.sub(r"\s+","",str(s or ""))
for w in ["C2","C3"]:
    print("="*110); print("###",w)
    for r in load(w):
        raw=norm(r.get("raw_problem",""))
        miss=[]; tot=0
        for t in r.get("trigger_signals",[]):
            tot+=1
            quotes=re.findall(r"[\"'“”‘’]([^\"'“”‘’]{4,})[\"'“”‘’]", t)
            if not quotes:
                miss.append(("NOQUOTE", t[:100])); continue
            hit=any(norm(q) in raw for q in quotes)
            if not hit:
                miss.append(("QUOTE_NOT_IN_RAW", quotes, t[:110]))
        if miss:
            print(f"\n  [{r['problem_id']}]  {len(miss)}/{tot} 条 trigger 的引号内容不在 raw_problem 里")
            for m in miss:
                print(f"      {m[0]}  {m[1] if m[0]=='QUOTE_NOT_IN_RAW' else ''}")
                print(f"         trigger: {m[2] if m[0]=='QUOTE_NOT_IN_RAW' else m[1]}")
