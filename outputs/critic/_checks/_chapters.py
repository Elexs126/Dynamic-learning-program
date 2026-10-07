# -*- coding: utf-8 -*-
"""良哥解读 分章分布 + M8 各章 E1/E2 + C1/M 算子交集"""
import os,re,sys,io,json,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"

print("###### 概率论讲义：良哥解读 / 分析 / 注 / 考点及方法小结 分文件统计 ######")
root=os.path.join(SRC,"讲义","概率论与数理统计")
for dirpath,dirs,files in os.walk(root):
    for fn in sorted(files):
        if not fn.endswith(".md"): continue
        p=os.path.join(dirpath,fn); t=open(p,encoding="utf-8").read()
        rel=os.path.relpath(p,SRC).replace("\\","/")
        cnt={k:t.count(k) for k in ["良哥解读","分析","注","考点及方法小结"]}
        print(f"  {rel:70s} lines={t.count(chr(10))+1:5d} 良哥解读={cnt['良哥解读']:3d} 分析={cnt['分析']:3d} 注={cnt['注']:3d} 小结={cnt['考点及方法小结']:2d}")

print("\n###### M8 每条：源文件 + evidence_level ######")
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
for r in load("M8"):
    lv=re.search(r"evidence_level:\s*(E\d)",r.get("notes","") or "")
    print(f"  {r['problem_id']:8s} {lv.group(1) if lv else '?':3s} {r['confidence']:7s} {r['source']['repo_path'].replace('讲义/概率论与数理统计/','')}")

print("\n###### 算子领域交集 ######")
ops={}
for w in ["M5","M6","M8","C1"]:
    c=collections.Counter()
    for r in load(w):
        for m in (r.get("existing_operator_matches") or []):
            c[m.get("operator_id")]+=1
    ops[w]=c
allop=set()
for w in ops: allop|=set(ops[w])
print(f"  {'operator':38s} {'M5':>4s} {'M6':>4s} {'M8':>4s} {'C1':>4s}  {'M合计':>6s} 跨C1?")
shared=[]
for o in sorted(allop, key=lambda o:-sum(ops[w].get(o,0) for w in ops)):
    m=sum(ops[w].get(o,0) for w in ["M5","M6","M8"]); c=ops["C1"].get(o,0)
    flag="YES" if (c>0 and m>0) else ("仅C1" if c>0 else "")
    if c>0 and m>0: shared.append(o)
    print(f"  {o:38s} {ops['M5'].get(o,0):4d} {ops['M6'].get(o,0):4d} {ops['M8'].get(o,0):4d} {c:4d}  {m:6d}  {flag}")
print("\n  真正跨数学↔408 的算子:", len(shared), shared)
