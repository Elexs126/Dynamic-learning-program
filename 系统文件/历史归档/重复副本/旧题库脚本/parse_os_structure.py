# -*- coding: utf-8 -*-
import re

with open("scripts/os_full_text.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Let's see all page headers and question numbers
pages = content.split("==================== PAGE ")
print(f"Number of page chunks: {len(pages)}")

for p in pages[1:]:
    lines = [line.strip() for line in p.split("\n") if line.strip()]
    page_num = lines[0].replace(" ====================", "")
    print(f"\n--- Page {page_num} ---")
    for line in lines[1:15]:
        if any(line.startswith(prefix) for prefix in ["第", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."]) or "·" in line:
            print("  ", line)
