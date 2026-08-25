# -*- coding: utf-8 -*-
import pypdf
import os

pdf_path = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648108414.pdf"
reader = pypdf.PdfReader(pdf_path)
print("Total pages:", len(reader.pages))

for i in range(min(15, len(reader.pages))):
    text = reader.pages[i].extract_text()
    first_few_lines = "\n".join(text.split("\n")[:5])
    print(f"--- Page {i+1} ---")
    print(first_few_lines)
