# -*- coding: utf-8 -*-
"""按 problem_id 打印指定记录的选定字段（供 Critic 逐条阅读）"""
import json,os,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def dump(w, pids, fields):
    recs={r["problem_id"]:r for r in load(w)}
    for pid in pids:
        r=recs[pid]
        print("#"*110)
        print(f"### {pid}  |  {r.get('source',{}).get('repo_path')}  |  {r.get('source',{}).get('section')}  | {r.get('source',{}).get('example_or_question')}")
        print(f"--- confidence={r.get('confidence')}")
        print(f"--- raw_problem:\n{r.get('raw_problem')}")
        print(f"--- problem_goal: {r.get('problem_goal')}")
        for f in fields:
            v=r.get(f)
            if isinstance(v,list):
                print(f"--- {f}:")
                for i,x in enumerate(v):
                    if isinstance(x,dict):
                        print(f"    [{i}] " + " || ".join(f"{k}={vv}" for k,vv in x.items()))
                    else:
                        print(f"    [{i}] {x}")
            elif isinstance(v,dict):
                print(f"--- {f}:")
                for k,vv in v.items(): print(f"    {k}: {vv}")
            else:
                print(f"--- {f}: {v}")
        print(f"--- evidence_excerpt:\n{r.get('evidence_excerpt')}")
        print(f"--- notes:\n{r.get('notes')}")
        print()

if __name__=="__main__":
    w=sys.argv[1]; pids=sys.argv[2].split(","); fields=sys.argv[3].split(",")
    dump(w,pids,fields)
