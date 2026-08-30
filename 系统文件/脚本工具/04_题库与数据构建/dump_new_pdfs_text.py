# -*- coding: utf-8 -*-
import fitz

os_mcq_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787649280515.pdf"
dsa_big_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787649280562.pdf"

doc_os = fitz.open(os_mcq_pdf)
with open("scripts/os_mcq_full_text.txt", "w", encoding="utf-8") as f:
    for page_idx in range(len(doc_os)):
        page = doc_os[page_idx]
        text = page.get_text()
        f.write(f"\n\n==================== PAGE {page_idx+1} ====================\n\n")
        f.write(text)

doc_dsa = fitz.open(dsa_big_pdf)
with open("scripts/dsa_big_full_text.txt", "w", encoding="utf-8") as f:
    for page_idx in range(len(doc_dsa)):
        page = doc_dsa[page_idx]
        text = page.get_text()
        f.write(f"\n\n==================== PAGE {page_idx+1} ====================\n\n")
        f.write(text)

print("Dumped full text for OS MCQ and DSA BIG.")
