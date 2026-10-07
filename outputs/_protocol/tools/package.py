#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
package.py — 清理 + 规范化 + 打包 outputs/ 到源仓库，并生成 manifest。

用法:
  python package.py --outputs <outputs 目录> --dest <源仓库根> [--dry-run]

动作:
  1. 删除 raw_episodes/ 下的临时文件（形如 _*.py / _*.jsonl / _*.md / _*.txt），
     但保留 *_protocol/ 与 _index/ 目录本身。
  2. 规范化：M* 记录若八个 408 专属字段全为空，则删除这些字段
     （SPEC §6.2 只要求 C1–C4 带；空字段属噪声）。
  3. 校验每行 JSON 合法；统计 Episode 总数。
  4. 复制 outputs/ 整棵树到 <dest>/outputs/。
  5. 生成 <dest>/outputs/MANIFEST.json（文件清单 + 字节数 + SHA256）。
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys

F408_FIELDS = [
    'system_state', 'resources', 'agents_or_components', 'invariants',
    'state_transition', 'bottleneck', 'local_vs_global_effect', 'layer_interface',
]

GEOMETRY_AXES = [
    'representation_issue', 'redundant_freedom', 'coupling',
    'scale_competition', 'dependency_structure', 'information_risk',
    'state_transition_structure', 'resource_or_bottleneck_structure',
]

INITIAL_STATE_KEYS = [
    'objects', 'constraints', 'free_variables', 'known_relations', 'target_form',
]

SCRATCH_RE = re.compile(r'^_.*\.(py|jsonl|json|csv|md|txt|ps1|bak|log|pyc)$')

# ⚠️⚠️ 目录清理**必须用显式清单，绝不能用 `^_` 这类通配**。
# 实测事故（本项目真实发生过）：我曾写成 `SCRATCH_DIR_RE = re.compile(r'^_')`，
# 它匹配了 `_index/`（45 个闸门报告）与 `_protocol/`（38 个契约与工具），
# **一次运行把整个支撑产物目录删光**（源 outputs 从 259 文件掉到 89）。
# 靠打包前做的整体备份才恢复。
#
# 教训：**破坏性操作用"显式列举要删的"比"用模式匹配要留的"安全得多**——
# 模式写错时，前者漏删（可发现、可补），后者误删（不可逆）。
SCRATCH_DIRS = {'_unx_out', '__pycache__'}   # 显式列举；新增请加入
# 注意：`critic/_checks/` **刻意保留**——那是三位 Critic 为了让报告可复跑而
# 单独组织的脚本目录（30 个）。它不是散落的临时文件，而是 Critic 结论的证据。
# 与之同理保留的还有 `_protocol/tools/`（闸门工具）。

# raw_episodes 下唯一合法的文件名：<worker>.jsonl 与 <worker>.notes.md
LEGIT_EPISODE_RE = re.compile(r'^[A-Za-z]\d+\.(jsonl|notes\.md)$')


def clean_scratch(raw_dir, dry):
    """清理临时文件。

    raw_episodes/ 采用**白名单**：只保留 `<worker>.jsonl` 与 `<worker>.notes.md`，
    其余一律视为临时产物删除。这比"匹配 _ 前缀"可靠——M5 就写过一个
    不带下划线的 `m5_build.py`，黑名单式匹配会漏掉它并把它带进交付。

    critic/ 与 problem_families/ 采用**扩展名白名单**：只保留 `.md` 报告，
    其余（分析脚本、dump、txt）全部删除。实测 Critic 会在 critic/ 下留下
    40+ 个中间文件，若不清理会全部进入交付树。

    outputs/ 根与 _protocol/ 下则删除 `_` 前缀文件。
    """
    removed = []
    outputs_root = os.path.dirname(os.path.abspath(raw_dir))

    # 1) raw_episodes：白名单（文件）+ 删显式清单里的临时子目录
    if os.path.isdir(raw_dir):
        for fn in sorted(os.listdir(raw_dir)):
            p = os.path.join(raw_dir, fn)
            if os.path.isdir(p):
                # `raw_episodes/__pycache__/` 这类：白名单只认文件，
                # 目录必须显式处理，否则 Python 缓存会跟着交付。
                if fn in SCRATCH_DIRS or fn == '__pycache__':
                    n = len(os.listdir(p))
                    removed.append('raw_episodes/%s/ (临时目录，%d 项)' % (fn, n))
                    if not dry:
                        shutil.rmtree(p, ignore_errors=True)
                continue
            if LEGIT_EPISODE_RE.match(fn):
                continue
            removed.append('raw_episodes/' + fn)
            if not dry:
                os.remove(p)

    # 2) critic/ 与 problem_families/：只留 .md 报告
    for sub in ('critic', 'problem_families'):
        d = os.path.join(outputs_root, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            if fn.lower().endswith('.md') and not fn.startswith('_'):
                continue
            removed.append('%s/%s' % (sub, fn))
            if not dry:
                os.remove(p)

    # 3) outputs/ 根、_protocol/、_index/：删 _ 前缀文件；另删**显式清单**里的临时目录
    for sub in ('', '_protocol', '_index'):
        d = os.path.join(outputs_root, sub) if sub else outputs_root
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if os.path.isfile(p) and SCRATCH_RE.match(fn):
                removed.append(('%s/' % sub if sub else '') + fn)
                if not dry:
                    os.remove(p)
            elif (sub == '' and os.path.isdir(p) and fn in SCRATCH_DIRS):
                n = len(os.listdir(p))
                removed.append('%s/ (临时目录，%d 项)' % (fn, n))
                if not dry:
                    shutil.rmtree(p, ignore_errors=True)
    return removed


def fill_missing_axes(rec):
    """补齐 SPEC §6 要求存在但可能被省略的键（不适用填空）。
    这是安全规范化：只添加缺失的键，不覆盖任何已有值。"""
    changed = []
    geo = rec.get('initial_geometry')
    if isinstance(geo, dict):
        for ax in GEOMETRY_AXES:
            if ax not in geo:
                geo[ax] = ''
                changed.append('initial_geometry.%s' % ax)
    st = rec.get('initial_state')
    if isinstance(st, dict):
        for k in INITIAL_STATE_KEYS:
            if k not in st:
                st[k] = []
                changed.append('initial_state.%s' % k)
    return changed


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def normalize(raw_dir, dry):
    """规范化：
      * M* 记录：若八个 408 专属字段全为空则删除（SPEC §6.2 只要求 C1–C4 带）
      * 所有记录：补齐 initial_geometry 八个轴 / initial_state 五个键中缺失的键
    返回 (改动文件数, 记录数, 补齐明细计数)。
    """
    changed_files = 0
    total = 0
    fill_counter = {}
    for fn in sorted(f for f in os.listdir(raw_dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        worker = os.path.splitext(fn)[0]
        path = os.path.join(raw_dir, fn)
        out_lines = []
        changed = False
        with io.open(path, encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                rec = json.loads(s)
                total += 1

                # 1) M* 去掉全空的 408 字段
                if worker.startswith('M'):
                    drop = [k for k in F408_FIELDS
                            if k in rec and (rec[k] == '' or rec[k] == [] or rec[k] is None)]
                    if len(drop) == len(F408_FIELDS):
                        for k in drop:
                            rec.pop(k, None)
                        changed = True

                # 2) 补齐缺失的 geometry 轴 / initial_state 键
                filled = fill_missing_axes(rec)
                if filled:
                    changed = True
                    for k in filled:
                        fill_counter[k] = fill_counter.get(k, 0) + 1

                out_lines.append(json.dumps(rec, ensure_ascii=False))
        if changed:
            changed_files += 1
            if not dry:
                with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write('\n'.join(out_lines) + '\n')
    return changed_files, total, fill_counter


def verify_all(outputs_dir):
    bad = []
    total = 0
    raw = os.path.join(outputs_dir, 'raw_episodes')
    for fn in sorted(f for f in os.listdir(raw)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        with io.open(os.path.join(raw, fn), encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                s = line.strip()
                if not s:
                    continue
                total += 1
                try:
                    json.loads(s)
                except Exception as e:
                    bad.append('%s:%d %s' % (fn, i, e))
    for fn in ('trigger_index.json', 'anti_trigger_index.json'):
        p = os.path.join(outputs_dir, fn)
        if os.path.isfile(p):
            try:
                json.load(io.open(p, encoding='utf-8'))
            except Exception as e:
                bad.append('%s %s' % (fn, e))
    return total, bad


def copy_tree(src, dst, dry):
    if dry:
        return 0
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    n = 0
    for _root, _dirs, files in os.walk(dst):
        n += len(files)
    return n


def source_provenance(repo_root):
    """读取源仓库的 git 出处，写进 MANIFEST 供溯源。
    数据集必须能回答"我是从哪个 commit 建的"。"""
    import subprocess
    out = {}
    try:
        def git(*a):
            # encoding 必须显式指定 utf-8：默认走系统 locale（本机为 GBK），
            # 遇到中文 commit message 会 UnicodeDecodeError 并返回 None。
            p = subprocess.run(['git', '-C', repo_root] + list(a),
                               capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=30)
            return (p.stdout or '').strip()
        out['repo_root_basename'] = os.path.basename(os.path.abspath(repo_root))
        out['head_commit'] = git('rev-parse', 'HEAD')
        out['branch'] = git('rev-parse', '--abbrev-ref', 'HEAD')
        out['commit_date'] = git('log', '-1', '--format=%ad', '--date=iso')
        out['commit_subject'] = git('log', '-1', '--format=%s')
        # 确认源仓库未被本任务修改
        dirty = git('status', '--porcelain')
        out['working_tree_clean'] = (dirty == '')
        out['working_tree_dirty_entries'] = len([x for x in dirty.split('\n') if x.strip()])
    except Exception as e:
        out['error'] = str(e)
    return out


def build_manifest(root, dest_repo_root=None):
    entries = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fn in sorted(files):
            if fn == 'MANIFEST.json':
                continue
            p = os.path.join(r, fn)
            rel = os.path.relpath(p, root).replace('\\', '/')
            entries.append({
                'path': rel,
                'bytes': os.path.getsize(p),
                'sha256': sha256_file(p),
            })
    entries.sort(key=lambda e: e['path'])
    manifest = {
        'manifest_version': 'problem-space-trajectory-dataset-v1.0.0',
        'file_count': len(entries),
        'total_bytes': sum(e['bytes'] for e in entries),
        'source_provenance': source_provenance(dest_repo_root) if dest_repo_root else None,
        'files': entries,
    }
    with io.open(os.path.join(root, 'MANIFEST.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=1))
    return manifest


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--outputs', default=os.path.abspath(os.path.join(here, '..', '..')))
    ap.add_argument('--dest', required=True, help='源仓库根目录')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--normalize-only', action='store_true',
                    help='只做规范化（补缺失键 / 去空 408 字段），不清理、不复制、不建 manifest')
    args = ap.parse_args()

    if args.normalize_only:
        raw = os.path.join(args.outputs, 'raw_episodes')
        changed, total, fill_counter = normalize(raw, False)
        total2, bad = verify_all(args.outputs)
        report = {
            'mode': 'normalize-only',
            'files_normalized': changed,
            'keys_filled': fill_counter,
            'episodes_total': total2,
            'json_errors': bad,
        }
        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 1 if bad else 0

    raw = os.path.join(args.outputs, 'raw_episodes')
    removed = clean_scratch(raw, args.dry_run)
    changed, total, fill_counter = normalize(raw, args.dry_run)
    total2, bad = verify_all(args.outputs)

    dest_outputs = os.path.join(args.dest, 'outputs')
    copied = copy_tree(args.outputs, dest_outputs, args.dry_run)

    manifest = None
    if not args.dry_run:
        manifest = build_manifest(dest_outputs, args.dest)

    report = {
        'dry_run': args.dry_run,
        'scratch_removed': removed,
        'files_normalized': changed,
        'keys_filled': fill_counter,
        'episodes_total': total2,
        'json_errors': bad,
        'dest': dest_outputs,
        'files_copied': copied,
        'manifest_file_count': manifest['file_count'] if manifest else None,
        'manifest_total_bytes': manifest['total_bytes'] if manifest else None,
    }
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
