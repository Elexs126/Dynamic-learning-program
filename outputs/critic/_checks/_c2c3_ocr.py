# -*- coding: utf-8 -*-
import json,os,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
for w in ["C2","C3"]:
    print("="*110); print("###",w)
    for r in load(w):
        pid=r["problem_id"]
        blob=json.dumps(r,ensure_ascii=False)
        marks=[]
        for k in ["[OCR?]","OCR","ocr_fixed","ocr_note","无法无歧义","照实保留","未作改写","未改动"]:
            if k in blob: marks.append(k)
        print(f"  {pid}: {marks}")
        # 打印所有含 OCR 相关词的字段片段
        for f,v in r.items():
            s=json.dumps(v,ensure_ascii=False)
            if "OCR" in s or "[OCR?]" in s or "ocr_fixed" in s:
                print(f"      <{f}> {s[:600]}")
