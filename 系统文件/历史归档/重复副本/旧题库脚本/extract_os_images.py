# -*- coding: utf-8 -*-
import fitz
import os

pdf_path = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648108414.pdf"
doc = fitz.open(pdf_path)

out_dir = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\images\os"
os.makedirs(out_dir, exist_ok=True)

img_count = 0
for page_idx in range(len(doc)):
    page = doc[page_idx]
    image_list = page.get_images(full=True)
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        # filter out very small images/logos if any (like tiny icons < 1KB)
        if len(image_bytes) > 2000:
            img_count += 1
            filename = f"p{page_idx+1}_img{img_index+1}.{image_ext}"
            filepath = os.path.join(out_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            print(f"Saved: {filename} ({len(image_bytes)} bytes) from page {page_idx+1}")

print(f"Total extracted images: {img_count}")
