# -*- coding: utf-8 -*-
"""跨题错引检测：evidence_excerpt 是否与本题主题相关（关键词域匹配）"""
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

TOPIC={
 "链表":["链表","结点","指针","next","头结点"],
 "队列":["队列","队头","队尾","front","rear","入队","出队"],
 "栈":["栈","出栈","入栈","LIFO","后进先出"],
 "树":["树","结点","孩子","兄弟","二叉","叶","根"],
 "图":["顶点","边","图","邻接","路径","拓扑","关键路径"],
 "排序":["排序","归并","趟","比较次数","WPL","哈夫曼"],
 "查找":["查找","散列","哈希","冲突","平衡","B 树","B+树","红黑","探测","装填"],
 "串":["串","模式匹配","next 数组"],
}
def topic_of(text):
    sc={}
    for k,ws in TOPIC.items():
        sc[k]=sum(1 for w in ws if w in text)
    return sc

for w in ["C1"]:
    for r in load(w):
        pid=r["problem_id"]
        raw=(r.get("raw_problem") or "")+" "+(r.get("problem_goal") or "")+" "+(r.get("main_obstacle") or "")
        ex=r.get("evidence_excerpt") or ""
        tr=topic_of(raw); te=topic_of(ex)
        # best topic of raw
        if not tr: continue
        best=max(tr,key=lambda k:tr[k])
        if tr[best]==0: continue
        overlap = te.get(best,0)
        flag = "  <<< 主题不匹配" if overlap==0 else ""
        print(f"{pid:8s} raw主题={best}({tr[best]})  excerpt在该主题命中={overlap}{flag}")
        if overlap==0:
            print(f"    raw: {raw[:150]!r}")
            print(f"    ex : {ex[:150]!r}")
