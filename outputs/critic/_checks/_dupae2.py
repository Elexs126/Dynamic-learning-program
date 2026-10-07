# -*- coding: utf-8 -*-
"""additional_evidence 块内重复统计（用子串切分，不依赖行边界）"""
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
for w in ["M5","M6","M8","C1"]:
    tot=0; uniq=0; bad=[]
    for r in load(w):
        n=r.get("notes","") or ""
        idx=[m.start() for m in re.finditer(r"additional_evidence",n)]
        blocks=[]
        for k,i in enumerate(idx):
            j=idx[k+1] if k+1<len(idx) else len(n)
            blocks.append(re.sub(r"\s+","",n[i:j]))
        if not blocks: continue
        tot+=len(blocks); u=len(set(blocks)); uniq+=u
        if len(blocks)!=u: bad.append((r["problem_id"],len(blocks),u))
    print(f"{w}: 块数={tot} 去重后={uniq} 冗余={tot-uniq}")
    for pid,t,u in bad: print(f"    {pid}: {t} 块 -> {u} 个不同（重复 {t-u} 次）")
