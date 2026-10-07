# -*- coding: utf-8 -*-
"""C2/C3 的 evidence_excerpt 逐字 + 连续性核验（evidence_verify.md 未覆盖这两个 worker）"""
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
    except Exception as e: t=None
    CACHE[rel]=t; return t
def norm(s): return re.sub(r"\s+","",str(s or "").replace("\u00a0"," "))

for w in ["C2","C3"]:
    print("="*100); print("###",w)
    bad=[]
    for r in load(w):
        pid=r["problem_id"]; rel=r.get("source",{}).get("repo_path","")
        ex=norm(r.get("evidence_excerpt") or "")
        if not ex: print(f"  [EMPTY] {pid}"); bad.append(pid); continue
        t=src(rel)
        if t is None: print(f"  [SRCMISS] {pid} {rel}"); bad.append(pid); continue
        n=norm(t)
        if ex in n:
            # 定位覆盖行区间
            raw=t.split("\n"); offs=[]; acc=0
            for i,l in enumerate(raw):
                offs.append((acc,i+1)); acc+=len(norm(l))
            start=n.find(ex); end=start+len(ex)-1
            def line_at(p):
                best=1
                for o,ln in offs:
                    if o<=p: best=ln
                    else: break
                return best
            a=line_at(start); b=line_at(end)
            skipped=[(i+1,raw[i][:80]) for i in range(a-1,b) if raw[i].strip() and norm(raw[i]) and norm(raw[i]) not in ex]
            flag = "CONTIG_OK" if not skipped else f"SKIPPED={len(skipped)}"
            print(f"  [EXACT] {pid:8s} {rel.split('/')[-1]:40s} L{a}-L{b} len={len(ex):5d} {flag}")
            for ln,txt in skipped[:4]:
                print(f"        L{ln}: {txt!r}")
            if skipped: bad.append(pid)
            continue
        seed=ex[:min(30,len(ex))]
        pos=n.find(seed); best=0; at=-1
        while pos!=-1:
            k=0
            while k<len(ex) and pos+k<len(n) and ex[k]==n[pos+k]: k+=1
            if k>best: best=k; at=pos
            pos=n.find(seed,pos+1)
        raw=t.split("\n"); line=None; acc=0
        for i,l in enumerate(raw,1):
            acc+=len(norm(l))
            if acc>=at+1: line=i; break
        print(f"  [SPLICE?] {pid} matched {best}/{len(ex)} chars, starts ~L{line} of {rel}")
        print(f"      diverges at: ...{ex[max(0,best-60):best+80]!r}")
        bad.append(pid)
    print(f"  >>> 不逐字/不连续: {len(bad)} -> {bad}")
