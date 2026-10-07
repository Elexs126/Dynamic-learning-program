# -*- coding: utf-8 -*-
"""C2/C3 概览：主算子、全部 transition operation、trigger 数、notes 中的 additional_evidence 数"""
import json,os,re,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
for w in ["C2","C3"]:
    print("="*110); print("###",w)
    for r in load(w):
        prim=[m["operator_id"] for m in r.get("existing_operator_matches",[]) if m.get("is_primary_move")]
        allop=[m["operator_id"] for m in r.get("existing_operator_matches",[])]
        ae=len(re.findall(r"additional_evidence", r.get("notes","")))
        m=re.search(r"evidence_level:\s*(E\d)", r.get("notes",""))
        print(f"\n--- {r['problem_id']}  conf={r.get('confidence')}  ev={m.group(1) if m else '?'}  primary={prim}  all={allop}  AE={ae}")
        for i,t in enumerate(r.get("key_transitions",[])):
            op=re.sub(r"\s+"," ",str(t.get("operation","")))
            print(f"    T{i}: {op[:190]}")
        # 词表外检查
        VOCAB=set("""STATE_REREPRESENTATION FREEDOM_REORGANIZATION QUOTIENT_KERNEL RESTRICT_SLICE NORMALIZE SPACE_AUGMENTATION AUXILIARY_OBJECT DEPENDENCY_REORGANIZATION LOW_BANDWIDTH_INTERFACE INVARIANT_BLOCK_DECOMPOSITION INFORMATION_AXIS_DECOMPOSITION SHARED_WORLD_EMBEDDING EXACT_ELIMINATION INTERFACE_RENORMALIZATION PROBE CRITICAL_SCALE_PROBE COUNTEREXAMPLE_PROBE RIGIDIFY CERTIFICATE_PRODUCTION BRIDGE_OBSERVABLE CONSTRAINT_COLLISION DEFECT_CENTERING DEFECT_FACTORIZATION UNIFORMIZATION THICKNESS_EXTRACTION SELF_IMPROVING_CLOSURE ENVIRONMENT_REWEIGHTING GLUE_LOCAL_TO_GLOBAL INFORMATION_PRESERVATION DEPENDENCY_ORDERING REPAIR_SCALE_MATCHING FRONTIER_NAVIGATION STRUCTURAL_PROGRESS""".split())
        out=[o for o in allop if o not in VOCAB]
        if out: print(f"    !! 词表外标签: {out}")
