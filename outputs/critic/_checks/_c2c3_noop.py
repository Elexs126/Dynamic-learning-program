# -*- coding: utf-8 -*-
import json,re,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
VOCAB=set("""STATE_REREPRESENTATION FREEDOM_REORGANIZATION QUOTIENT_KERNEL RESTRICT_SLICE NORMALIZE SPACE_AUGMENTATION AUXILIARY_OBJECT DEPENDENCY_REORGANIZATION LOW_BANDWIDTH_INTERFACE INVARIANT_BLOCK_DECOMPOSITION INFORMATION_AXIS_DECOMPOSITION SHARED_WORLD_EMBEDDING EXACT_ELIMINATION INTERFACE_RENORMALIZATION PROBE CRITICAL_SCALE_PROBE COUNTEREXAMPLE_PROBE RIGIDIFY CERTIFICATE_PRODUCTION BRIDGE_OBSERVABLE CONSTRAINT_COLLISION DEFECT_CENTERING DEFECT_FACTORIZATION UNIFORMIZATION THICKNESS_EXTRACTION SELF_IMPROVING_CLOSURE ENVIRONMENT_REWEIGHTING GLUE_LOCAL_TO_GLOBAL INFORMATION_PRESERVATION DEPENDENCY_ORDERING REPAIR_SCALE_MATCHING FRONTIER_NAVIGATION STRUCTURAL_PROGRESS""".split())
for w in ["C2","C3"]:
    recs=[json.loads(l) for l in open(BASE+"\\"+w+".jsonl",encoding="utf-8") if l.strip()]
    print("="*110); print("###",w,"  非结构动作的 key_transition 明细")
    n=0
    for r in recs:
        for i,t in enumerate(r.get("key_transitions",[])):
            op=str(t.get("operation",""))
            found=set(x for x in re.findall(r"[A-Z][A-Z_]{4,}",op) if x in VOCAB)
            if found: continue
            n+=1
            print("\n  [%s T%d]  operation=%r" % (r["problem_id"], i, op))
            for k in ["before_state","after_state","why_triggered","preserved_information","discarded_information","new_structure_exposed"]:
                print("      %s: %r" % (k, t.get(k)))
    print("\n  >>> 非结构动作 transition 总数: %d" % n)
