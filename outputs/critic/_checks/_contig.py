# -*- coding: utf-8 -*-
"""严格连续性核验：evidence_excerpt 必须落在源文件的连续片段内（去掉行间空白后仍连续）"""
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
CACHE={}
def src(rel):
    if rel in CACHE: return CACHE[rel]
    try: t=open(os.path.join(SRC,rel.replace("/",os.sep)),encoding="utf-8").read()
    except Exception: t=None
    CACHE[rel]=t; return t
def norm(s): return re.sub(r"\s+","",str(s or "").replace("\u00a0"," "))

for w in ["M5","M6","M8","C1"]:
    print("="*100); print("###",w)
    bad=[]
    for r in load(w):
        pid=r["problem_id"]; rel=r.get("source",{}).get("repo_path","")
        ex=norm(r.get("evidence_excerpt") or "")
        if not ex: print(f"  [EMPTY] {pid}"); bad.append(pid); continue
        t=src(rel)
        if t is None: print(f"  [SRCMISS] {pid}"); bad.append(pid); continue
        n=norm(t)
        if ex in n: continue
        # longest contiguous prefix present
        seed=ex[:min(30,len(ex))]
        pos=n.find(seed); best=0; at=-1
        while pos!=-1:
            k=0
            while k<len(ex) and pos+k<len(n) and ex[k]==n[pos+k]: k+=1
            if k>best: best=k; at=pos
            pos=n.find(seed,pos+1)
        # which source line does it start on
        raw=t.split("\n"); line=None; acc=0
        for i,l in enumerate(raw,1):
            acc+=len(norm(l))
            if acc>=at+1: line=i; break
        print(f"  [SPLICE?] {pid} matched {best}/{len(ex)} chars, starts ~L{line} of {rel}")
        print(f"      diverges at: ...{ex[max(0,best-60):best+80]!r}")
        bad.append(pid)
    print(f"  >>> 不连续/异常: {len(bad)} -> {bad}")
