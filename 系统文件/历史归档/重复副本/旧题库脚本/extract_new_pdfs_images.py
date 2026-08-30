# -*- coding: utf-8 -*-
import fitz
import os

os_mcq_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787649280515.pdf"
dsa_big_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787649280562.pdf"

os_mcq_img_dir = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\images\os_mcq"
dsa_big_img_dir = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\images\dsa_big"

os.makedirs(os_mcq_img_dir, exist_ok=True)
os.makedirs(dsa_big_img_dir, exist_ok=True)

def extract_imgs(pdf_path, out_dir, prefix):
    doc = fitz.open(pdf_path)
    count = 0
    img_map = {}
    for p_idx in range(len(doc)):
        page = doc[p_idx]
        image_list = page.get_images(full=True)
        p_imgs = []
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            ext = base_image["ext"]
            if len(img_bytes) > 2000:
                count += 1
                fname = f"p{p_idx+1}_img{img_idx+1}.{ext}"
                fpath = os.path.join(out_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(img_bytes)
                p_imgs.append(fname)
        if p_imgs:
            img_map[p_idx + 1] = p_imgs
    print(f"{prefix}: extracted {count} images across {len(img_map)} pages.")
    return img_map

os_map = extract_imgs(os_mcq_pdf, os_mcq_img_dir, "OS_MCQ")
dsa_map = extract_imgs(dsa_big_pdf, dsa_big_img_dir, "DSA_BIG")

with open("scripts/os_mcq_img_map.py", "w", encoding="utf-8") as f:
    f.write(f"os_mcq_page_images = {repr(os_map)}\n")

with open("scripts/dsa_big_img_map.py", "w", encoding="utf-8") as f:
    f.write(f"dsa_big_page_images = {repr(dsa_map)}\n")

print("New image extraction completed.")
