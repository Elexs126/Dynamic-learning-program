# -*- coding: utf-8 -*-
"""核验 M8/M6/M5/C1 notes 中声明的行号是否真的包含所引原话"""
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
CACHE={}
def lines(rel):
    if rel in CACHE: return CACHE[rel]
    try: t=open(os.path.join(SRC,rel.replace("/",os.sep)),encoding="utf-8").read().split("\n")
    except Exception: t=[]
    CACHE[rel]=t; return t
def norm(s): return re.sub(r"\s+","",str(s or ""))

print("###### M8 全部 notes（找 line NNN 声明 + 逐条核对）######")
for r in load("M8"):
    pid=r["problem_id"]; notes=r.get("notes","") or ""; rel=r["source"]["repo_path"]
    lv=re.search(r"evidence_level:\s*(E\d)",notes)
    # find declared line numbers
    decl=re.findall(r"line\s*(\d+)",notes)
    ex=norm(r.get("evidence_excerpt"))
    hit=[]
    for d in decl:
        n=int(d); L=lines(rel)
        seg=norm("\n".join(L[max(0,n-3):n+2]))
        hit.append(f"L{n}:{'IN' if (ex and ex[:20] in seg) else 'out'}")
    print(f"  {pid:8s} {lv.group(1) if lv else '?':3s} {r['confidence']:7s} decl={decl} excerpt_in_range={hit}")
