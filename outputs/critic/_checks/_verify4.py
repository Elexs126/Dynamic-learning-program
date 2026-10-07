# -*- coding: utf-8 -*-
"""Critic: additional_evidence 严格核验 v2 —— 只取引文段（在下一个结构标记前截断）"""
import json, os, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
SRC  = r"E:\杂七杂八的垃圾堆\_dlp_src"

def load(w):
    with open(os.path.join(BASE, w + ".jsonl"), encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

CACHE = {}
def src(rel):
    if rel in CACHE: return CACHE[rel]
    try: t = open(os.path.join(SRC, rel.replace("/", os.sep)), encoding="utf-8").read()
    except Exception: t = None
    CACHE[rel] = t; return t

def norm(s): return re.sub(r"\s+", "", str(s or "").replace("\u00a0", " "))

STOP = re.compile(r"(检索标签|confidence|题型标签|ocr_fixed|ocr_note|UNKNOWN 子步骤|基础篇侧样本|强化篇侧样本|同结构对照|说明[:：]|依据[:：]|additional_evidence|来源[:：]|CANDIDATE|第\s*\d+\s*行)")

for w in ["M5", "M6", "M8", "C1"]:
    recs = load(w)
    print("="*100); print(f"### {w}")
    tot=ok=part=fail=0
    for r in recs:
        pid = r["problem_id"]; notes = r.get("notes","") or ""
        idxs = [m.start() for m in re.finditer(r"additional_evidence", notes)]
        for k,i in enumerate(idxs):
            j = idxs[k+1] if k+1 < len(idxs) else len(notes)
            block = notes[i:j]
            pm = re.search(r"((?:讲义|核心真题|配套习题)/[^\s，,、）\)\]]+?\.md)", block)
            rel = pm.group(1) if pm else r.get("source",{}).get("repo_path","")
            lm = re.search(r"L(\d+)\s*[-–~]\s*L?(\d+)", block) or re.search(r"[Ll](?:ine|ines)?\s*(\d+)\s*[-–~]\s*(\d+)", block) or re.search(r"[Ll]ines?\s*(\d+)", block)
            # quote begins at the LAST colon before the actual quotation; robust approach:
            # take everything after the colon that follows the path/line reference, then cut at STOP
            after = block
            if pm:
                after = block[pm.end():]
            # strip leading line ref and punctuation up to first colon
            cm = re.search(r"[：:]", after)
            if cm:
                after = after[cm.end():]
            else:
                # M5-style: "第 331 行 '...'"  -> strip leading 第 N 行
                after = re.sub(r"^[^\'\u2018\u201c]*", "", after, count=1)
            sm = STOP.search(after)
            quote = (after[:sm.start()] if sm else after).strip().strip("。").strip()
            quote = quote.strip("'\"\u2018\u2019\u201c\u201d")
            tot += 1
            if not quote.strip():
                print(f"  [NOQUOTE] {pid}"); fail+=1; continue
            tt = src(rel)
            if tt is None: print(f"  [SRCMISS] {pid} {rel}"); fail+=1; continue
            q=norm(quote); h=norm(tt)
            hit = q in h
            if hit:
                ok += 1
                # line-range cross-check
                if lm:
                    L = tt.split("\n"); a=int(lm.group(1)); b=int(lm.group(2)) if lm.lastindex and lm.lastindex>=2 else a
                    seg = norm("\n".join(L[a-1:b])) if a<=len(L) else ""
                    if q not in seg:
                        print(f"  [LINERANGE] {pid} quote verbatim in file but NOT within claimed L{a}-L{b}"); part+=1; ok-=1
            else:
                # try longest prefix
                seed=q[:min(20,len(q))]; best=0; s=h.find(seed)
                while s!=-1:
                    m=0
                    while m<len(q) and s+m<len(h) and q[m]==h[s+m]: m+=1
                    best=max(best,m); s=h.find(seed,s+1)
                if best>=max(30,len(q)*0.7):
                    print(f"  [PARTIAL {best}/{len(q)}] {pid} rel={rel} q={quote[:90]!r}"); part+=1
                else:
                    print(f"  [FAIL {best}/{len(q)}] {pid} rel={rel} q={quote[:90]!r}"); fail+=1
    print(f"  >>> blocks={tot} 逐字通过={ok} PARTIAL={part} FAIL={fail}")
