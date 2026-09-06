#!/usr/bin/env python3
"""Meaningful regression tests for source preservation and conservative L1."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import build_l1 as b

PROJECT = Path(__file__).resolve().parents[3]


def example(qid="ZY30-GS-01-X01", value=3):
    return f"""# Synthetic exercise fixture
### 【{qid}】第 1 题
**【题目】**
已知演示变量取值为 {value}，请选择对应的演示选项。
A. 1 B. 2 C. 3 D. 4
> **【唯一编号】** `{qid}`
> **【科目】** 高等数学篇
> **【专题】** 第1讲 函数极限与连续
**【参考答案】** SECRET_ANSWER_TEST_ONLY
**【解析】** SECRET_SOLUTION_TEST_ONLY
"""


class L1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scopes = {s["scope_id"]: s for s in b.load_json(PROJECT / b.SCOPE_FILE)}
        cls.rules = b.load_json(b.RULE_FILE)

    def test_parser_never_exports_answers(self):
        item = list(b.parse_file(example(), "source.md"))[0]
        self.assertNotIn("SECRET_", item["body"])
        self.assertNotIn("SECRET_", json.dumps(item["metadata"]))
        self.assertEqual(item["block_hash"], b.digest((example().split("### ", 1)[1].join(["### ", ""])).encode()))

    def test_unmatched_marker_fails(self):
        text = example().replace("### 【ZY30-GS-01-X01】", "### 【WRONG-ID】")
        with self.assertRaises(ValueError):
            list(b.parse_file(text, "source.md"))

    def test_repeated_marker_fails(self):
        with self.assertRaises(ValueError):
            list(b.parse_file(example() + example(), "source.md"))

    def test_conflicting_type_is_not_verified(self):
        typ, status, basis = b.infer_type("M3-26-C-T01", {"题型": "解答题"}, "", "")
        self.assertEqual((typ, status), ("choice", "needs_review"))
        self.assertIn("conflict", basis)

    def test_conflicting_subject_fails(self):
        with self.assertRaises(ValueError):
            b.subject_for("ZY30-GL-01-X01", {"科目": "线性代数"}, "source.md")

    def test_type_requires_all_four_options(self):
        self.assertNotEqual(b.infer_type("EXAMPLE", {}, "A. 一个标记 B. 第二个", "")[0], "choice")
        self.assertEqual(b.infer_type("EXAMPLE", {}, "A. 1 B. 2 C. 3 D. 4", "")[0], "choice")

    def test_ambiguous_scope_stays_course_level(self):
        route = b.route_scope("probability", "第6讲 数理统计", self.scopes, self.rules)
        self.assertEqual(route[3], "needs_review")
        self.assertEqual(route[1], [])
        mixed = b.route_scope("linear_algebra", "特征值与二次型", self.scopes, self.rules)
        self.assertEqual(mixed[3], "needs_review")

    def test_syllabus_chapter_routing(self):
        cases = [
            ("data_structure", "第4章 串 · 4.2 串的模式匹配", "SCOPE_408_DS_06"),
            ("data_structure", "堆的概念", "SCOPE_408_DS_04"),
            ("computer_organization", "第3章 存储系统 · 3.3 主存储器与 CPU 的连接", "SCOPE_408_CO_03"),
            ("calculus", "第17章 多元函数积分学的预备知识", "SCOPE_M1_CALC_04"),
            ("probability", "多维随机变量函数的分布", "SCOPE_M1_PROB_03"),
            ("probability", "参数估计与假设检验、矩估计和最大似然估计", "SCOPE_M1_PROB_07"),
        ]
        for subject, label, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(b.route_scope(subject, label, self.scopes, self.rules)[1], [expected])

    def test_fingerprint_keeps_numbers_and_variables(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            text = "这是一个足够长的演示题干；$x_1 = 21$，求取题目要求的量。"
            fp = b.image_fingerprint(root, "s.md", text, {})[0]
            self.assertIsNotNone(fp)
            self.assertNotEqual(fp, b.image_fingerprint(root, "s.md", text.replace("21", "22"), {})[0])
            self.assertNotEqual(fp, b.image_fingerprint(root, "s.md", text.replace("x_1", "x_2"), {})[0])
            self.assertEqual(fp, b.image_fingerprint(root, "s.md", text.replace(" ", "\n"), {})[0])

    def test_image_content_controls_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.png").write_bytes(b"image-A")
            (root / "b.png").write_bytes(b"image-A")
            (root / "c.png").write_bytes(b"image-C")
            text = "足够长的演示题干，请根据图中提供的内容作答。![图](a.png)"
            fp = b.image_fingerprint(root, "s.md", text, {})[0]
            self.assertEqual(fp, b.image_fingerprint(root, "s.md", text.replace("a.png", "b.png"), {})[0])
            self.assertNotEqual(fp, b.image_fingerprint(root, "s.md", text.replace("a.png", "c.png"), {})[0])
            self.assertIsNone(b.image_fingerprint(root, "s.md", text.replace("a.png", "missing.png"), {})[0])
            self.assertIsNone(b.image_fingerprint(root, "s.md", text.replace("a.png", "https://example.com/a.png"), {})[0])

    def fixture_root(self, root):
        paths = [b.SCOPE_FILE, b.SCHEMA, "系统文件/数据规范/question_annotation.schema.json",
                 "系统文件/数据规范/标签说明.md", "系统文件/数据规范/README.md", "完整执行协议.md", "启动合同.md",
                 f"{b.TOOL_DIR}/validate_annotations.py", f"{b.TOOL_DIR}/json_schema_runtime.py"]
        for rel in paths:
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT / rel, dest)
        manifest = {"manifest_version": "test-v1", "expected_unique_question_records": 3,
                    "sources": [{"source_id": "TEST_BOOK", "canonical_path": "题源",
                                 "exam_track": "MATH1", "expected_records": 3}]}
        (root / b.MANIFEST).parent.mkdir(parents=True, exist_ok=True)
        b.write_json(root / b.MANIFEST, manifest)
        (root / "题源").mkdir()
        for i, value in enumerate([3, 3, 4], 1):
            (root / "题源" / f"{i}.md").write_text(example(f"ZY30-GS-01-X0{i}", value))

    def test_end_to_end_reuse_integrity_and_schema_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.fixture_root(root)
            out = root / "result"
            result = b.build(root, out)
            self.assertEqual(result["records"], 3)
            self.assertEqual(result["duplicate_groups"], 1)
            self.assertEqual(result["unknown_original_points"], 3)
            before = {p.name: b.file_hash(p) for p in out.iterdir()}
            self.assertEqual(b.build(root, out)["action"], "reused_verified_snapshot")
            self.assertEqual(before, {p.name: b.file_hash(p) for p in out.iterdir()})
            bundle = b.load_json(out / "question_annotations_l1_v1.json")
            self.assertNotIn("SECRET_", json.dumps(bundle))
            self.assertEqual(bundle["records"][2]["l1"]["duplicate_candidate"]["is_candidate"], None)
            modified = copy.deepcopy(bundle)
            modified["records"][0]["answer"] = "forbidden"
            b.write_json(root / "bad.json", modified)
            with self.assertRaises(ValueError):
                b.validate_bundle(root, root / "bad.json")
            report = out / "l1_build_report.json"
            original = report.read_bytes()
            report.write_bytes(original + b" ")
            with self.assertRaises(ValueError):
                b.verify(root, out)
            report.write_bytes(original)
            (root / "题源/1.md").write_text(example("ZY30-GS-01-X01", 999))
            with self.assertRaises(ValueError):
                b.build(root, out)

    def test_hash_compatible_with_existing_math1_migration(self):
        sys.path.insert(0, str(PROJECT / b.TOOL_DIR))
        from migrate_l3_v1 import canonical_question_hash
        count = 0
        for p in sorted((PROJECT / "核心真题/数学一").glob("*.md")):
            rel = p.relative_to(PROJECT).as_posix()
            for item in b.parse_file(p.read_text(), rel):
                self.assertEqual(item["block_hash"], canonical_question_hash(PROJECT, rel, item["question_id"]))
                count += 1
        self.assertEqual(count, 431)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=PROJECT)
    known, rest = parser.parse_known_args()
    PROJECT = known.project_root.resolve()
    unittest.main(argv=[sys.argv[0], *rest], verbosity=2)
