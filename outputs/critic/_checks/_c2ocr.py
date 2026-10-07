# -*- coding: utf-8 -*-
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
def show(rel, a, b):
    t=open(os.path.join(SRC,rel.replace("/",os.sep)),encoding="utf-8").read().split("\n")
    for i in range(a-1,min(b,len(t))):
        print(f"  L{i+1}: {t[i]}")
print("=== 2024 真题 L2018-L2035（C2-014 声称的 OCR 损坏处） ===")
show("核心真题/408/2024年全国硕士研究生招生考试408计算机学科专业基础综合真题.md",2018,2035)
print()
print("=== 讲义/操作系统/第03章_内存管理.md L348-L356（C2-013） ===")
show("讲义/操作系统/第03章_内存管理.md",348,356)
print()
print("=== 讲义/操作系统/第05章_输入输出管理.md L1436-L1446（C2-024） ===")
show("讲义/操作系统/第05章_输入输出管理.md",1436,1446)
print()
print("=== 2025 真题 L1966-L1980（C2-011） ===")
show("核心真题/408/2025年全国硕士研究生招生考试408计算机学科专业基础综合真题.md",1966,1980)
