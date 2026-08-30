# -*- coding: utf-8 -*-
import fitz
import re
import os

pdf_path = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648108414.pdf"
doc = fitz.open(pdf_path)

out_log = []
out_log.append(f"Total pages: {len(doc)}")

for page_idx in range(len(doc)):
    page = doc[page_idx]
    text = page.get_text()
    # clean PUA characters
    clean_text = "".join(c if ord(c) < 0xe000 or ord(c) > 0xf8ff else f"[PUA_{hex(ord(c))}]" for c in text)
    lines = clean_text.splitlines()
    first_lines = " | ".join(lines[:6])
    out_log.append(f"Page {page_idx+1}: {first_lines}")

with open("scripts/os_pages_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_log))

print("Dumped summary of all 78 pages to scripts/os_pages_summary.txt")
