# -*- coding: utf-8 -*-
"""M7 审查：逐字/连续性、E1-E2、算子分布与 notes 自述是否一致"""
import json,os,re,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
CACHE={}
def src(rel):
    if rel in CACHE: return CACHE[rel]
    try: t=open(os.path.join(SRC,rel.replace("/",os.sep)),encoding="utf-8").read()
    except Exception: t=None
    CACHE[rel]=t; return t
def norm(s): return re.sub(r"\s+","",str(s or "").replace("\u00a0"," "))
recs=load("M7")
print(f"### M7  {len(recs)} 条")
conf=collections.Counter(r.get("confidence") for r in recs); print("confidence:",dict(conf))
ev=collections.Counter()
for r in recs:
    m=re.search(r"evidence_level:\s*(E\d)", r.get("notes","")); ev[m.group(1) if m else "NONE"]+=1
print("evidence_level(in notes):",dict(ev))
ops=collections.Counter(); prim=collections.Counter()
for r in recs:
    for m in r.get("existing_operator_matches",[]):
        ops[m["operator_id"]]+=1
        if m.get("is_primary_move"): prim[m["operator_id"]]+=1
print("primary:",prim.most_common())
print("total:",ops.most_common())
print("primary count per rec:",collections.Counter(sum(1 for m in r.get("existing_operator_matches",[]) if m.get("is_primary_move")) for r in recs))
print("possible_new_operator:",[r["problem_id"] for r in recs if r.get("possible_new_operator")])
print("naive_routes:",sum(len(r.get("naive_routes",[])) for r in recs),
      " key_transitions:",sum(len(r.get("key_transitions",[])) for r in recs),
      " triggers:",sum(len(r.get("trigger_signals",[])) for r in recs))
# verbatim + contiguity
bad=[]
for r in recs:
    pid=r["problem_id"]; rel=r.get("source",{}).get("repo_path","")
    ex=norm(r.get("evidence_excerpt") or "")
    if not ex: bad.append((pid,"EMPTY")); continue
    t=src(rel)
    if t is None: bad.append((pid,"SRCMISS "+rel)); continue
    n=norm(t)
    if ex not in n:
        bad.append((pid,"NOT_VERBATIM")); continue
    raw=t.split("\n"); offs=[]; acc=0
    for i,l in enumerate(raw): offs.append((acc,i+1)); acc+=len(norm(l))
    start=n.find(ex); end=start+len(ex)-1
    def line_at(p):
        best=1
        for o,ln in offs:
            if o<=p: best=ln
            else: break
        return best
    a=line_at(start); b=line_at(end)
    sk=[i+1 for i in range(a-1,b) if raw[i].strip() and norm(raw[i]) and norm(raw[i]) not in ex]
    if sk: bad.append((pid,f"SKIPPED_LINES {sk}"))
print("逐字/连续问题:",bad if bad else "0")
# 词表错位
VOCAB=set("""STATE_REREPRESENTATION FREEDOM_REORGANIZATION QUOTIENT_KERNEL RESTRICT_SLICE NORMALIZE SPACE_AUGMENTATION AUXILIARY_OBJECT DEPENDENCY_REORGANIZATION LOW_BANDWIDTH_INTERFACE INVARIANT_BLOCK_DECOMPOSITION INFORMATION_AXIS_DECOMPOSITION SHARED_WORLD_EMBEDDING EXACT_ELIMINATION INTERFACE_RENORMALIZATION PROBE CRITICAL_SCALE_PROBE COUNTEREXAMPLE_PROBE RIGIDIFY CERTIFICATE_PRODUCTION BRIDGE_OBSERVABLE CONSTRAINT_COLLISION DEFECT_CENTERING DEFECT_FACTORIZATION UNIFORMIZATION THICKNESS_EXTRACTION SELF_IMPROVING_CLOSURE ENVIRONMENT_REWEIGHTING GLUE_LOCAL_TO_GLOBAL INFORMATION_PRESERVATION DEPENDENCY_ORDERING REPAIR_SCALE_MATCHING FRONTIER_NAVIGATION STRUCTURAL_PROGRESS""".split())
ANTI=set("""PREMATURE_INFORMATION_LOSS PREMATURE_ABSOLUTE_VALUE PREMATURE_APPROXIMATION BAD_REPRESENTATION_LOCK_IN OVER_DECOUPLING MISSING_SHARED_WITNESS LOCAL_REPAIR_GLOBAL_ERROR DEPTH_TUNNEL_VISION BRANCH_EXPLOSION TARGET_DRIFT PROXY_OBJECTIVE_DRIFT SEARCH_EXHAUSTED_AS_REFUTED PROMISING_AS_PROVED DEPENDENCY_CYCLE RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE""".split())
print("\n词表错位:")
for r in recs:
    for i,m in enumerate(r.get("existing_operator_matches",[])):
        if m["operator_id"] not in VOCAB:
            print(f"  {r['problem_id']} [{i}] {m['operator_id']} primary={m.get('is_primary_move')}")
    for nr in r.get("naive_routes",[]):
        if nr.get("failure_type") not in ANTI:
            print(f"  {r['problem_id']} failure_type 词表外/新增: {nr.get('failure_type')}")
print("\n=== 每条：主算子 / operation / trigger 数 ===")
for r in recs:
    pr=[m["operator_id"] for m in r.get("existing_operator_matches",[]) if m.get("is_primary_move")]
    print(f"\n  {r['problem_id']} conf={r.get('confidence')} primary={pr}")
    print(f"     src={r['source']['repo_path']} | {r['source'].get('section')} | {r['source'].get('example_or_question')}")
    for i,t in enumerate(r.get("key_transitions",[])):
        print(f"     T{i}: {re.sub(chr(10),' ',str(t.get('operation')))[:170]}")
