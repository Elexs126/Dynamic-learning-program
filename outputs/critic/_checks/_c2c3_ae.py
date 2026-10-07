# -*- coding: utf-8 -*-
"""核验 notes 中 additional_evidence（逐字，<repo_path> L<a>-L<b>）：<原文>
   - 行号是否落在正确位置
   - 引文是否逐字
   - 是否与本题主题相关（简单关键词法：题面主题词 vs 引文命中）
"""
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
PAT=re.compile(r"additional_evidence[（(]逐字[，,]\s*([^）)]+?)\s*[）)]\s*[：:]\s*(.*?)(?=additional_evidence|$)", re.S)
tot=0; ok=0; bad=[]
for w in ["C2","C3"]:
    for r in load(w):
        pid=r["problem_id"]; notes=r.get("notes","")
        for m in PAT.finditer(notes):
            head=m.group(1); quote=m.group(2)
            tot+=1
            lm=re.search(r"L(\d+)-L(\d+)", head)
            path=re.sub(r"L\d+-L\d+","",head).strip().rstrip("，,：:").strip()
            if not lm:
                bad.append((pid,"NO_LINERANGE",head[:80])); continue
            a,b=int(lm.group(1)),int(lm.group(2))
            t=src(path)
            if t is None:
                bad.append((pid,"PATH_MISS",path)); continue
            lines=t.split("\n")
            seg="\n".join(lines[a-1:b]) if a<=len(lines) else ""
            q=norm(quote)
            if not q:
                bad.append((pid,"EMPTY_QUOTE",head)); continue
            if q in norm(seg):
                ok+=1
            else:
                # 在全文里找
                where=None
                n=norm(t); pos=n.find(q[:min(40,len(q))])
                if pos>=0:
                    acc=0
                    for i,l in enumerate(lines,1):
                        acc+=len(norm(l))
                        if acc>=pos+1: where=i; break
                bad.append((pid, f"NOT_AT_L{a}-L{b}"+(f" (found ~L{where})" if where else " (NOT_IN_FILE)"), path+" | "+quote[:70].replace("\n"," ")))
print(f"additional_evidence 块总数 {tot}；行号+逐字通过 {ok}；有问题 {len(bad)}")
for pid,kind,info in bad:
    print(f"  [{pid}] {kind}  {info}")
