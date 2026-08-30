# -*- coding: utf-8 -*-
import re

with open("scripts/dsa_full_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Find all section headers in the form: ^\s*(\d\.\d)\s+([^\n]+)
sec_headers = list(re.finditer(r'(?:\n|\A)\s*(\d\.\d[A-Za-z\+]*)\s+([^\n]+)', text))
print("Found section headers in DSA:")
for h in sec_headers:
    print(f"  {h.group(1)}: {h.group(2).strip()}")
