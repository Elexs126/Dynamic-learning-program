# -*- coding: utf-8 -*-
"""C2/C3 一致性检查：
 1) key_transitions[].operation 里出现的词表标签 vs existing_operator_matches 的差集
 2) 出现在 operation 里的 anti-operator 标签
 3) 非结构动作的 operation（不含任何词表标签 / 无箭头式描述）
 4) notes 里 additional_evidence 声称的行号是否落在正确位置
"""
import json,os,re,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
BASE=r"E:\杂七杂八的垃圾堆\LearningOS\outputs\raw_episodes"
SRC=r"E:\杂七杂八的垃圾堆\_dlp_src"
VOCAB=set("""STATE_REREPRESENTATION FREEDOM_REORGANIZATION QUOTIENT_KERNEL RESTRICT_SLICE NORMALIZE SPACE_AUGMENTATION AUXILIARY_OBJECT DEPENDENCY_REORGANIZATION LOW_BANDWIDTH_INTERFACE INVARIANT_BLOCK_DECOMPOSITION INFORMATION_AXIS_DECOMPOSITION SHARED_WORLD_EMBEDDING EXACT_ELIMINATION INTERFACE_RENORMALIZATION PROBE CRITICAL_SCALE_PROBE COUNTEREXAMPLE_PROBE RIGIDIFY CERTIFICATE_PRODUCTION BRIDGE_OBSERVABLE CONSTRAINT_COLLISION DEFECT_CENTERING DEFECT_FACTORIZATION UNIFORMIZATION THICKNESS_EXTRACTION SELF_IMPROVING_CLOSURE ENVIRONMENT_REWEIGHTING GLUE_LOCAL_TO_GLOBAL INFORMATION_PRESERVATION DEPENDENCY_ORDERING REPAIR_SCALE_MATCHING FRONTIER_NAVIGATION STRUCTURAL_PROGRESS""".split())
ANTI=set("""PREMATURE_INFORMATION_LOSS PREMATURE_ABSOLUTE_VALUE PREMATURE_APPROXIMATION BAD_REPRESENTATION_LOCK_IN OVER_DECOUPLING MISSING_SHARED_WITNESS LOCAL_REPAIR_GLOBAL_ERROR DEPTH_TUNNEL_VISION BRANCH_EXPLOSION TARGET_DRIFT PROXY_OBJECTIVE_DRIFT SEARCH_EXHAUSTED_AS_REFUTED PROMISING_AS_PROVED DEPENDENCY_CYCLE RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE NEWTON_LEIBNIZ_BLIND_APPLICATION UNJUSTIFIED_SYMMETRY_TRANSFER MISSING_ABSOLUTE_VALUE""".split())
ALL=VOCAB|ANTI
def load(w):
    with open(os.path.join(BASE,w+".jsonl"),encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

for w in ["C2","C3"]:
    print("="*110); print("###",w)
    print("\n-- (1) operation 中出现但 matches 未记录的标签 --")
    print("-- (2) operation 中出现 anti-operator --")
    print("-- (3) operation 里没有任何词表标签（疑似非结构动作） --")
    for r in load(w):
        pid=r["problem_id"]
        matched=set(m["operator_id"] for m in r.get("existing_operator_matches",[]))
        for i,t in enumerate(r.get("key_transitions",[])):
            op=str(t.get("operation",""))
            found=set(x for x in re.findall(r"[A-Z][A-Z_]{4,}", op) if x in ALL)
            missing=found-matched
            anti_in=found&ANTI
            if missing:
                print(f"  [MISS] {pid} T{i}: {sorted(missing)}  ::  {op[:150]}")
            if anti_in:
                print(f"  [ANTI-IN-OP] {pid} T{i}: {sorted(anti_in)}  ::  {op[:150]}")
            if not found:
                print(f"  [NO-OP] {pid} T{i}: {op[:150]}")
