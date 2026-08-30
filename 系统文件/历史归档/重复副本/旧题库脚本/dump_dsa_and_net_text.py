# -*- coding: utf-8 -*-
import fitz

dsa_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648985139.pdf"
net_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648985329.pdf"

doc_dsa = fitz.open(dsa_pdf)
with open("scripts/dsa_full_text.txt", "w", encoding="utf-8") as f:
    for page_idx in range(len(doc_dsa)):
        page = doc_dsa[page_idx]
        text = page.get_text()
        f.write(f"\n\n==================== PAGE {page_idx+1} ====================\n\n")
        f.write(text)

doc_net = fitz.open(net_pdf)
with open("scripts/net_full_text.txt", "w", encoding="utf-8") as f:
    for page_idx in range(len(doc_net)):
        page = doc_net[page_idx]
        text = page.get_text()
        f.write(f"\n\n==================== PAGE {page_idx+1} ====================\n\n")
        f.write(text)

print("Dumped full text for DSA and Network.")
