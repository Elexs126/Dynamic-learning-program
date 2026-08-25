# -*- coding: utf-8 -*-
import fitz

jizu_big_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787649687067.pdf"
net_big_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787649687365.pdf"

doc_jizu = fitz.open(jizu_big_pdf)
with open("scripts/jizu_big_full_text.txt", "w", encoding="utf-8") as f:
    for page_idx in range(len(doc_jizu)):
        page = doc_jizu[page_idx]
        text = page.get_text()
        f.write(f"\n\n==================== PAGE {page_idx+1} ====================\n\n")
        f.write(text)

doc_net = fitz.open(net_big_pdf)
with open("scripts/net_big_full_text.txt", "w", encoding="utf-8") as f:
    for page_idx in range(len(doc_net)):
        page = doc_net[page_idx]
        text = page.get_text()
        f.write(f"\n\n==================== PAGE {page_idx+1} ====================\n\n")
        f.write(text)

print("Dumped full text for Jizu Big and Net Big.")
