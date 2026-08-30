# -*- coding: utf-8 -*-
import fitz
import os

dsa_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648985139.pdf"
net_pdf = r"C:\Users\HP\.gemini\antigravity-ide\brain\1160abdc-9de8-481b-8d05-f411084b21e7\.user_uploaded\media_1787648985329.pdf"

dsa_img_dir = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\images\dsa"
net_img_dir = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\images\network"

os.makedirs(dsa_img_dir, exist_ok=True)
os.makedirs(net_img_dir, exist_ok=True)

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

dsa_map = extract_imgs(dsa_pdf, dsa_img_dir, "DSA")
net_map = extract_imgs(net_pdf, net_img_dir, "Network")

with open("scripts/dsa_img_map.py", "w", encoding="utf-8") as f:
    f.write(f"dsa_page_images = {repr(dsa_map)}\n")

with open("scripts/net_img_map.py", "w", encoding="utf-8") as f:
    f.write(f"net_page_images = {repr(net_map)}\n")

print("Image extraction and mapping completed.")
