# -*- coding: utf-8 -*-
"""检查 raw_problem 是否含有实际的'问'/'求'/题号标记；并输出长度"""
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
Q=re.compile(r"(试|请|要求|问|说明|写出|给出|判断|指出|计算|求|分析|比较|为何|为什么|下列|关于|正确的是|错误的是|不正确的是)")
for w in ["C2","C3"]:
    print("="*110); print("###",w)
    for r in load(w):
        rp=r.get("raw_problem","")
        hit=Q.findall(rp)
        tail=rp[-70:].replace("\n","\\n")
        print(f"  {r['problem_id']}  len={len(rp):4d}  问句标记={len(hit)}  题号={'有' if re.search(r'^\s*\d+[\.、]|【.*?】第|例\d', rp) else '无'}  ...{tail!r}")
