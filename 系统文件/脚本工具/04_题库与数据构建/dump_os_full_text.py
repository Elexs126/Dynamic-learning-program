# -*- coding: utf-8 -*-
import fitz

doc = fitz.open(r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648108414.pdf")

with open("scripts/os_full_text.txt", "w", encoding="utf-8") as f:
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text()
        f.write(f"\n\n==================== PAGE {page_idx+1} ====================\n\n")
        f.write(text)

print("Dumped full text to scripts/os_full_text.txt")
