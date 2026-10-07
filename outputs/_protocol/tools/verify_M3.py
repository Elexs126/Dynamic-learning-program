# -*- coding: utf-8 -*-
"""Verify M3.jsonl: evidence_excerpt must be a verbatim contiguous run of the source file."""
import json, io, os, re, collections, sys

SRC = r"E:\杂七杂八的垃圾堆\_dlp_src"
OUT = r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes\M3.jsonl"

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

recs = []
with io.open(OUT, "r", encoding="utf-8") as f:
    raw = f.read()
for line in raw.splitlines():
    if line.strip():
        recs.append(json.loads(line))

print("records:", len(recs))
cache = {}
bad = []
for r in recs:
    p = os.path.join(SRC, r["source"]["repo_path"].replace("/", os.sep))
    if p not in cache:
        cache[p] = norm(io.open(p, "r", encoding="utf-8").read())
    src = cache[p]
    ex = norm(r["evidence_excerpt"])
    ok = ex in src
    if not ok:
        bad.append((r["problem_id"], r["source"]["repo_path"], ex[:90]))
    print("%-8s %-6s %s" % (r["problem_id"], "OK" if ok else "MISS", r["source"]["repo_path"]))

print("\n--- MISSES ---")
for pid, path, head in bad:
    print(pid, "|", path, "|", head)

conf = collections.Counter(r["confidence"] for r in recs)
lvl = collections.Counter(re.search(r"evidence_level: (E\d)", r["notes"]).group(1)
                          if re.search(r"evidence_level: (E\d)", r["notes"]) else "?" for r in recs)
print("\nconfidence:", dict(conf))
print("evidence_level:", dict(lvl))
print("UNKNOWN/UNEXPLAINED mentions:", sum(1 for r in recs if "UNEXPLAINED" in r["notes"] or "UNKNOWN" in r["notes"]))
print("CANDIDATE_NEW_OPERATOR:", sum(1 for r in recs if r.get("possible_new_operator")))
print("bom:", raw.startswith("\ufeff"), "| crlf:", "\r\n" in raw)
