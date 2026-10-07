# -*- coding: utf-8 -*-
"""Build a compact digest of all raw episodes for family clustering."""
import json, glob, os, io, sys

ROOT = r"E:\杂七杂八的垃圾堆\LearningOS\outputs"
RAW = os.path.join(ROOT, "raw_episodes")
OUT = os.path.join(ROOT, "problem_families", "_tools")

WORKERS = ["M1","M2","M3","M4","M5","M6","M7","M8","C1","C2","C3"]

def load(w):
    eps = []
    with io.open(os.path.join(RAW, w + ".jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            eps.append(json.loads(line))
    return eps

def clip(s, n):
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "…"

def geo(g):
    if not isinstance(g, dict):
        return {}
    return {k: v for k, v in g.items() if v}

def main():
    all_eps = []
    for w in WORKERS:
        for e in load(w):
            e["_worker"] = w
            all_eps.append(e)
    print("total", len(all_eps))

    # full digest (long) for deep reading
    with io.open(os.path.join(OUT, "digest_full.md"), "w", encoding="utf-8") as f:
        for e in all_eps:
            f.write("=" * 100 + "\n")
            f.write("## %s  [%s]  worker=%s\n" % (e.get("problem_id"), e.get("domain"), e.get("_worker")))
            src = e.get("source") or {}
            f.write("source: %s | %s | %s | year=%s\n" % (
                src.get("repo_path"), src.get("section"), src.get("example_or_question"), src.get("year")))
            f.write("qid: %s\n" % e.get("question_id"))
            f.write("raw_problem: %s\n" % clip(e.get("raw_problem"), 900))
            f.write("problem_goal: %s\n" % clip(e.get("problem_goal"), 400))
            f.write("main_obstacle: %s\n" % clip(e.get("main_obstacle"), 800))
            f.write("geometry: %s\n" % json.dumps(geo(e.get("initial_geometry")), ensure_ascii=False))
            f.write("init_objects: %s\n" % json.dumps((e.get("initial_state") or {}).get("objects"), ensure_ascii=False))
            f.write("init_free: %s\n" % json.dumps((e.get("initial_state") or {}).get("free_variables"), ensure_ascii=False))
            f.write("init_relations: %s\n" % json.dumps((e.get("initial_state") or {}).get("known_relations"), ensure_ascii=False))
            f.write("target_form: %s\n" % json.dumps((e.get("initial_state") or {}).get("target_form"), ensure_ascii=False))
            for i, r in enumerate(e.get("naive_routes") or []):
                f.write("  naive[%d]: %s || why: %s || bad: %s || type: %s\n" % (
                    i, clip(r.get("route"), 200), clip(r.get("why_natural"), 200),
                    clip(r.get("why_bad_or_expensive"), 250), r.get("failure_type")))
            for i, t in enumerate(e.get("trigger_signals") or []):
                f.write("  trigger[%d]: %s\n" % (i, clip(t, 300)))
            for i, t in enumerate(e.get("key_transitions") or []):
                f.write("  trans[%d]: BEFORE %s | OP %s | AFTER %s | exposed %s | preserved %s | discarded %s\n" % (
                    i, clip(t.get("before_state"), 300), clip(t.get("operation"), 300),
                    clip(t.get("after_state"), 300), clip(t.get("new_structure_exposed"), 250),
                    clip(t.get("preserved_information"), 200), clip(t.get("discarded_information"), 200)))
            f.write("skeleton: %s\n" % json.dumps([clip(x, 200) for x in (e.get("solution_skeleton") or [])], ensure_ascii=False))
            f.write("closure: %s\n" % clip(e.get("certificate_or_closure"), 300))
            f.write("anti_triggers: %s\n" % json.dumps([clip(x, 200) for x in (e.get("anti_triggers") or [])], ensure_ascii=False))
            f.write("transfer: %s\n" % json.dumps([clip(x, 250) for x in (e.get("transfer_candidates") or [])], ensure_ascii=False))
            f.write("ops: %s\n" % json.dumps(
                [{"id": m.get("operator_id"), "p": m.get("is_primary_move"), "why": clip(m.get("why"), 200)}
                 for m in (e.get("existing_operator_matches") or [])], ensure_ascii=False))
            f.write("new_op: %s\n" % json.dumps(e.get("possible_new_operator"), ensure_ascii=False))
            f.write("conf: %s\n" % e.get("confidence"))
            f.write("excerpt: %s\n" % clip(e.get("evidence_excerpt"), 300))
            f.write("notes: %s\n" % clip(e.get("notes"), 500))
            if e.get("system_state") or e.get("state_transition"):
                f.write("sys: state=%s\n" % clip(e.get("system_state"), 300))
                f.write("  resources: %s\n" % json.dumps(e.get("resources"), ensure_ascii=False))
                f.write("  invariants: %s\n" % json.dumps([clip(x,150) for x in (e.get("invariants") or [])], ensure_ascii=False))
                f.write("  state_transition: %s\n" % json.dumps(e.get("state_transition"), ensure_ascii=False))
                f.write("  bottleneck: %s\n" % clip(e.get("bottleneck"), 300))
                f.write("  local_vs_global: %s\n" % clip(e.get("local_vs_global_effect"), 250))
                f.write("  layer_interface: %s\n" % clip(e.get("layer_interface"), 250))
            f.write("\n")

    # short index
    with io.open(os.path.join(OUT, "digest_short.md"), "w", encoding="utf-8") as f:
        f.write("| problem_id | domain | source_section | main_obstacle (clip 160) | geo_axes | primary_ops |\n")
        f.write("|---|---|---|---|---|---|\n")
        for e in all_eps:
            src = e.get("source") or {}
            prim = [m.get("operator_id") for m in (e.get("existing_operator_matches") or []) if m.get("is_primary_move")]
            axes = "+".join(sorted(geo(e.get("initial_geometry")).keys()))
            f.write("| %s | %s | %s | %s | %s | %s |\n" % (
                e.get("problem_id"), e.get("domain"), clip(src.get("section"), 40),
                clip(e.get("main_obstacle"), 160).replace("|", "/"), axes, ",".join(prim)))
    print("done")

main()
