# -*- coding: utf-8 -*-
"""报告 evidence_excerpt 覆盖的源文件行号区间及被跳过的非空行"""
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

targets=[("C1","C1-004"),("C1","C1-006"),("C1","C1-003"),("C1","C1-005"),("M8","M8-002"),("M6","M6-002")]
for w,pid in targets:
    r=[x for x in load(w) if x["problem_id"]==pid][0]
    rel=r["source"]["repo_path"]; t=src(rel); raw=t.split("\n")
    ex=norm(r["evidence_excerpt"])
    # map normalized char index -> line
    offs=[]; acc=0
    for i,l in enumerate(raw):
        offs.append((acc,i+1)); acc+=len(norm(l))
    n=norm(t); start=n.find(ex[:min(30,len(ex))])
    if start<0: print(pid,"NOT FOUND"); continue
    end=start+len(ex)-1
    def line_at(p):
        for o,ln in offs:
            pass
        best=1
        for o,ln in offs:
            if o<=p: best=ln
            else: break
        return best
    a=line_at(start); b=line_at(end)
    skipped=[(i+1,raw[i][:110]) for i in range(a-1,b) if raw[i].strip() and norm(raw[i]) and norm(raw[i]) not in ex]
    print("="*95)
    print(f"{pid}  {rel}")
    print(f"  excerpt 覆盖 L{a}-L{b}   (normalized len={len(ex)})")
    print(f"  区间内非空但未被 excerpt 包含的行: {len(skipped)}")
    for ln,txt in skipped[:8]: print(f"     L{ln}: {txt!r}")
