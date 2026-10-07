# -*- coding: utf-8 -*-
"""M5 additional_evidence 逐段核验 + M8-006 行号核对 + C1-022 空引文核对"""
import json, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
SRC  = r"E:\杂七杂八的垃圾堆\_dlp_src"

def load(w):
    with open(os.path.join(BASE, w+".jsonl"), encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

CACHE={}
def src(rel):
    if rel in CACHE: return CACHE[rel]
    try: t=open(os.path.join(SRC, rel.replace("/",os.sep)),encoding="utf-8").read()
    except Exception: t=None
    CACHE[rel]=t; return t
def norm(s): return re.sub(r"\s+","",str(s or "").replace("\u00a0"," "))

print("###### M5：additional_evidence 中每段单引号引文逐条回源 ######")
for r in load("M5"):
    pid=r["problem_id"]; notes=r.get("notes","") or ""
    idxs=[m.start() for m in re.finditer(r"additional_evidence",notes)]
    for k,i in enumerate(idxs):
        j=idxs[k+1] if k+1<len(idxs) else len(notes)
        block=notes[i:j]
        rel=r.get("source",{}).get("repo_path","")
        tt=src(rel); h=norm(tt) if tt else ""
        quotes=re.findall(r"[\u2018\u2019'\"]([^\u2018\u2019'\"]{12,})[\u2018\u2019'\"]", block)
        if not quotes:
            print(f"  {pid}: (无引号段) {block[:120]}"); continue
        for qi,q in enumerate(quotes):
            qn=norm(q)
            ok = qn in h
            # allow trailing/leading OCR-punct noise: try trimming last 3 chars
            if not ok:
                for t in (3,5,8):
                    if qn[:-t] and qn[:-t] in h: ok="PARTIAL(-%d)"%t; break
            print(f"  {pid} [{qi}] {'OK' if ok is True else (ok if ok else 'FAIL')}  {q[:95]!r}")

print("\n###### M8-006 行号核对 ######")
r=[x for x in load("M8") if x["problem_id"]=="M8-006"][0]
rel=r["source"]["repo_path"]; L=src(rel).split("\n")
print("  rel:", rel)
for n in range(755, 772):
    if n-1 < len(L):
        print(f"  L{n}: {L[n-1][:150]!r}")

print("\n###### C1-022 notes 全文 ######")
r=[x for x in load("C1") if x["problem_id"]=="C1-022"][0]
print(r.get("notes",""))

print("\n###### M5-017 notes 全文 ######")
r=[x for x in load("M5") if x["problem_id"]=="M5-017"][0]
print(r.get("notes",""))
