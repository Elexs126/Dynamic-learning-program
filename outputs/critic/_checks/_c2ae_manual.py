# -*- coding: utf-8 -*-
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
def show(rel,a,b):
    t=open(os.path.join(SRC,rel.replace("/",os.sep)),encoding="utf-8").read().split("\n")
    for i in range(a-1,min(b,len(t))):
        print(f"  L{i+1}: {t[i]}")
print("=== C2-007 声称 L2316（讲义/操作系统/第02章_进程与线程.md）===")
show("讲义/操作系统/第02章_进程与线程.md",2310,2320)
print()
print("=== C2-019 声称 L493（讲义/操作系统/第04章_文件管理.md）===")
show("讲义/操作系统/第04章_文件管理.md",488,500)
print()
print("=== C2-021 声称 L533（讲义/操作系统/第04章_文件管理.md）===")
show("讲义/操作系统/第04章_文件管理.md",528,540)
print()
print("=== C2-010 声称 核心真题/408/2024年...真题.md L2079-L2081 ===")
for f in os.listdir(os.path.join(SRC,"核心真题","408")):
    if f.startswith("2024"):
        print("  FILE:",f)
        show("核心真题/408/"+f,2075,2085)
print()
print("=== C2-012 声称 核心真题/408/2026年...真题.md ===")
for f in os.listdir(os.path.join(SRC,"核心真题","408")):
    if f.startswith("2026"):
        print("  FILE:",f)
