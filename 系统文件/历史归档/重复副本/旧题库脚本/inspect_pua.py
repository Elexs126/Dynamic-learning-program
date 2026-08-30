# -*- coding: utf-8 -*-
import re

with open("scripts/os_full_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

pua_chars = set()
for c in text:
    if 0xe000 <= ord(c) <= 0xf8ff:
        pua_chars.add(c)

with open("scripts/pua_report.txt", "w", encoding="utf-8") as out:
    out.write(f"Total unique PUA characters: {len(pua_chars)}\n")
    for c in sorted(pua_chars, key=lambda x: ord(x)):
        code = hex(ord(c))
        occurrences = [m.start() for m in re.finditer(re.escape(c), text)]
        contexts = []
        for idx in occurrences[:3]:
            start = max(0, idx - 20)
            end = min(len(text), idx + 21)
            snip = text[start:end].replace('\n', ' ')
            contexts.append(snip)
        out.write(f"PUA {code} (count: {len(occurrences)}): {contexts}\n")

print("PUA report saved to scripts/pua_report.txt")
