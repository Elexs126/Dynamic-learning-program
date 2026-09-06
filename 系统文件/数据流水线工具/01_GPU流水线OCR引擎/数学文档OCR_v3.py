#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学教材 / 长 PDF 结构化 OCR（MinerU 调度版）

目标
====
1. 不再使用“通用文字 OCR + 字符替换”猜测数学公式。
2. 使用 MinerU 的版面、公式、表格和阅读顺序解析能力生成 Markdown。
3. 面向 700～800 页乃至更长的 PDF：常驻模型、分块执行、断点续跑、
   失败重试、逐块落盘、原子状态文件和最终质量检查。
4. 永不修改输入 PDF，也不覆盖旧版程序；所有结果写入独立输出目录。

安装（建议使用独立 Python 3.10～3.12 环境）
================================================
    python -m pip install -U "mineru[all]" pypdf

最常用的命令
============
    # 自动检测 NVIDIA GPU；有合适 GPU 时使用 hybrid，否则使用 pipeline
    python 数学文档OCR_v3.py "教材.pdf"

    # 明确要求高精度 GPU 混合解析
    python 数学文档OCR_v3.py "教材.pdf" -o "输出目录" \
        --backend hybrid --effort high

    # 纯 CPU（比 RapidOCR 慢，但能识别公式与版面结构）
    python 数学文档OCR_v3.py "教材.pdf" -o "输出目录" \
        --backend pipeline

    # 先试报告中指出的困难页；页码均为人类习惯的 1-based
    python 数学文档OCR_v3.py "教材.pdf" -o "困难页试跑" \
        --pages "17,22,26,38,45,53,58,71,85,97,100,114,121,144,146-148,153-155,168"

    # 使用章节配置拆分输出
    python 数学文档OCR_v3.py "教材.pdf" -o "输出目录" \
        --chapters "chapters.json"

章节 JSON 示例
===============
    [
      {"file": "第01章_行列式.md", "title": "第一章 行列式",
       "start_page": 16, "end_page": 36},
      {"file": "第02章_矩阵.md", "title": "第二章 矩阵",
       "start_page": 37, "end_page": 69}
    ]

说明
====
- 默认每 128 页形成一个恢复单元，但 MinerU 内部仍以 64 页窗口控制内存；
  所有恢复单元通过一个常驻 mineru-api 复用模型。
- 默认预先生成分块 PDF，避免每个任务都重复读取和上传整本 800 页 PDF；
  若分块失败会自动退回 MinerU 自带的页范围模式。
- 单 GPU 默认串行提交分块；并行发生在 MinerU 内部的渲染和批处理阶段，
  避免多个进程争抢同一张 GPU。
- 自动检查只能发现裸 TeX、定界符失衡、私有区乱码、缺图等问题，不能证明
  每个负号、指数、下标和矩阵元素都正确。数学讲义仍应抽查题干、选项、
  定理条件、最终答案和高密度公式页。
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import hashlib
import html
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Sequence


SCRIPT_VERSION = "3.0.0"
STATE_SCHEMA_VERSION = 1
DEFAULT_CHUNK_PAGES = 128
DEFAULT_RENDER_THREADS = 2
DEFAULT_PROCESSING_WINDOW = 64
DEFAULT_STARTUP_TIMEOUT = 900
DEFAULT_TASK_TIMEOUT = 7200
DEFAULT_RENDER_TIMEOUT = 900

MATH_COMMAND_RE = re.compile(
    r"\\(?:alpha|beta|gamma|delta|varepsilon|theta|lambda|mu|eta|xi|sigma|"
    r"varphi|omega|pm|mp|partial|cdot|times|div|neq|ne|leq?|geq?|in|to|"
    r"infty|sum|prod|int|iint|iiint|oint|sqrt|frac|dfrac|tfrac|left|right|"
    r"begin|end|mathbf|mathrm|mathbb|operatorname|overline|underline|vec|hat|"
    r"bar|det|rank|lim|sin|cos|tan|ln|log)\b"
)
PRIVATE_USE_RE = re.compile(r"[\ue000-\uf8ff]")
SUSPICIOUS_LAMBDA_RE = re.compile(r"(?<![\u3400-\u9fff])入(?![\u3400-\u9fff])")
MARKDOWN_IMAGE_RE = re.compile(r"(!\[[^\]]*\]\()([^\n\r)]+)(\))")
HTML_IMAGE_RE = re.compile(r"(<img\b[^>]*?\bsrc=[\"'])([^\"']+)([\"'])", re.I)


class UserFacingError(RuntimeError):
    """可直接展示给用户的预期错误。"""


@dataclasses.dataclass(frozen=True)
class Chapter:
    key: str
    file: str
    title: str
    start_page: int
    end_page: int


@dataclasses.dataclass(frozen=True)
class Chunk:
    chunk_id: str
    sequence: int
    start_page: int
    end_page: int
    chapter_key: str

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page + 1


@dataclasses.dataclass(frozen=True)
class MinerUCliInfo:
    executable: str
    version: str
    help_text: str
    resolved_backend: str
    supports_page_range: bool
    supports_effort: bool
    supports_api_url: bool
    supports_client_side_output: bool
    supports_image_analysis: bool
    supports_language: bool


@dataclasses.dataclass
class ChunkResult:
    chunk: Chunk
    markdown_path: Path
    middle_json_path: Path | None
    output_root: Path
    attempt: int
    elapsed_seconds: float


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def human_seconds(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remain = divmod(seconds, 3600)
    minutes, secs = divmod(remain, 60)
    if hours:
        return f"{hours}小时{minutes:02d}分{secs:02d}秒"
    if minutes:
        return f"{minutes}分{secs:02d}秒"
    return f"{secs}秒"


def human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def sanitize_filename(value: str, default: str = "output.md") -> str:
    name = Path(value).name.strip()
    name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "_", name)
    name = name.rstrip(" .")
    if not name:
        name = default
    if not name.lower().endswith(".md"):
        name += ".md"
    return name


def parse_page_expression(expression: str, total_pages: int) -> list[int]:
    pages: set[int] = set()
    for raw_part in expression.replace("，", ",").split(","):
        part = raw_part.strip()
        if not part:
            continue
        match = re.fullmatch(r"(\d+)\s*[-~—–]\s*(\d+)", part)
        if match:
            start, end = int(match.group(1)), int(match.group(2))
            if start > end:
                start, end = end, start
            pages.update(range(start, end + 1))
        elif part.isdigit():
            pages.add(int(part))
        else:
            raise UserFacingError(f"无法理解页码片段：{part!r}")
    invalid = sorted(page for page in pages if page < 1 or page > total_pages)
    if invalid:
        preview = ", ".join(map(str, invalid[:10]))
        raise UserFacingError(f"页码超出 1～{total_pages}：{preview}")
    if not pages:
        raise UserFacingError("--pages 没有解析出任何页码。")
    return sorted(pages)


def pages_to_intervals(pages: Sequence[int]) -> list[tuple[int, int]]:
    if not pages:
        return []
    intervals: list[tuple[int, int]] = []
    start = previous = pages[0]
    for page in pages[1:]:
        if page == previous + 1:
            previous = page
            continue
        intervals.append((start, previous))
        start = previous = page
    intervals.append((start, previous))
    return intervals


def load_chapters(path: Path, total_pages: int) -> list[Chapter]:
    raw = load_json(path)
    if isinstance(raw, dict):
        raw = raw.get("chapters")
    if not isinstance(raw, list) or not raw:
        raise UserFacingError("章节配置必须是非空 JSON 数组，或包含 chapters 数组的对象。")

    chapters: list[Chapter] = []
    occupied: list[tuple[int, int, str]] = []
    used_filenames: set[str] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise UserFacingError(f"章节配置第 {index} 项不是对象。")
        try:
            start = int(item["start_page"])
            end = int(item["end_page"])
        except (KeyError, TypeError, ValueError) as exc:
            raise UserFacingError(f"章节配置第 {index} 项缺少有效的 start_page/end_page。") from exc
        if start < 1 or end < start or end > total_pages:
            raise UserFacingError(
                f"章节配置第 {index} 项页码无效：{start}～{end}，PDF 共 {total_pages} 页。"
            )
        title = str(item.get("title") or f"第 {index} 部分").strip()
        filename = sanitize_filename(str(item.get("file") or f"第{index:02d}部分.md"))
        filename_key = filename.casefold()
        if filename_key in used_filenames:
            raise UserFacingError(f"章节配置中存在重复输出文件名：{filename}")
        used_filenames.add(filename_key)
        key = f"chapter_{index:03d}"
        chapters.append(Chapter(key, filename, title, start, end))
        occupied.append((start, end, title))

    occupied.sort()
    for left, right in zip(occupied, occupied[1:]):
        if right[0] <= left[1]:
            raise UserFacingError(
                f"章节范围重叠：{left[2]}（{left[0]}～{left[1]}）与"
                f"{right[2]}（{right[0]}～{right[1]}）。"
            )
    return chapters


def build_plan(
    total_pages: int,
    chunk_pages: int,
    start_page: int,
    end_page: int,
    selected_pages: Sequence[int] | None,
    chapters: Sequence[Chapter] | None,
) -> tuple[list[Chapter], list[Chunk]]:
    if chunk_pages < 1:
        raise UserFacingError("--chunk-pages 必须大于 0。")

    effective_chapters: list[Chapter] = []
    if chapters:
        for chapter in chapters:
            start = max(chapter.start_page, start_page)
            end = min(chapter.end_page, end_page)
            if start <= end:
                effective_chapters.append(
                    Chapter(chapter.key, chapter.file, chapter.title, start, end)
                )
    elif selected_pages:
        for index, (start, end) in enumerate(pages_to_intervals(selected_pages), start=1):
            key = f"selection_{index:03d}"
            effective_chapters.append(
                Chapter(key, "", "抽选页", start, end)
            )
    else:
        effective_chapters.append(
            Chapter("book", "", "全文", start_page, end_page)
        )

    chunks: list[Chunk] = []
    sequence = 1
    for chapter in effective_chapters:
        cursor = chapter.start_page
        while cursor <= chapter.end_page:
            chunk_end = min(chapter.end_page, cursor + chunk_pages - 1)
            chunk_id = f"{sequence:04d}_p{cursor:06d}-{chunk_end:06d}"
            chunks.append(Chunk(chunk_id, sequence, cursor, chunk_end, chapter.key))
            sequence += 1
            cursor = chunk_end + 1

    if not chunks:
        raise UserFacingError("最终处理范围为空。")
    return effective_chapters, chunks


def count_pdf_pages(path: Path) -> int:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise UserFacingError(
            "缺少 pypdf。请先执行：python -m pip install -U pypdf"
        ) from exc
    try:
        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise UserFacingError("PDF 已加密，脚本无法读取页数。") from exc
        return len(reader.pages)
    except UserFacingError:
        raise
    except Exception as exc:
        raise UserFacingError(f"无法读取 PDF：{exc}") from exc


def detect_nvidia_gpu() -> tuple[bool, int | None, str]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return False, None, "未找到 nvidia-smi"
    command = [
        executable,
        "--query-gpu=index,name,memory.total",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=True)
    except Exception as exc:
        return False, None, f"nvidia-smi 不可用：{exc}"
    candidates: list[tuple[int, int, str]] = []
    for line in result.stdout.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) < 3:
            continue
        try:
            index = int(fields[0])
            memory_mib = int(fields[-1])
        except ValueError:
            continue
        name = ",".join(fields[1:-1]).strip()
        candidates.append((memory_mib, index, name))
    if not candidates:
        return False, None, "未检测到 NVIDIA GPU"
    memory_mib, index, name = max(candidates)
    if memory_mib < 7500:
        return False, index, f"GPU {name} 显存约 {memory_mib} MiB，默认改用 CPU pipeline"
    return True, index, f"GPU {index}: {name}，显存约 {memory_mib} MiB"


def resolve_executable(value: str) -> str:
    path = Path(value).expanduser()
    if path.is_file():
        return str(path.resolve())
    found = shutil.which(value)
    if found:
        return found
    raise UserFacingError(
        f"找不到命令 {value!r}。请先安装 MinerU：\n"
        "  python -m pip install -U \"mineru[all]\" pypdf"
    )


def run_probe(command: Sequence[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command), capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise UserFacingError(f"执行 {' '.join(command)} 失败：{exc}") from exc


def choose_backend_alias(requested: str, help_text: str) -> str:
    if requested == "pipeline":
        candidates = ["pipeline"]
    elif requested == "hybrid":
        candidates = ["hybrid-engine", "hybrid-auto-engine"]
    elif requested == "vlm":
        candidates = ["vlm-engine", "vlm-auto-engine"]
    else:
        candidates = [requested]
    for candidate in candidates:
        if candidate in help_text:
            return candidate
    if requested in help_text:
        return requested
    available = sorted(
        set(re.findall(r"(?:pipeline|hybrid-[a-z-]+|vlm-[a-z-]+)", help_text))
    )
    raise UserFacingError(
        f"当前 MinerU 不支持请求的后端 {requested!r}。"
        f"检测到的候选：{', '.join(available) or '未知'}"
    )


def probe_mineru(mineru_bin: str, requested_backend: str) -> MinerUCliInfo:
    executable = resolve_executable(mineru_bin)
    help_result = run_probe([executable, "--help"])
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if help_result.returncode != 0 or "--output" not in help_text:
        raise UserFacingError(f"{executable} --help 未返回有效的 MinerU 帮助信息。")
    version_result = run_probe([executable, "--version"])
    version = ((version_result.stdout or version_result.stderr) or "unknown").strip()
    resolved_backend = choose_backend_alias(requested_backend, help_text)
    return MinerUCliInfo(
        executable=executable,
        version=version,
        help_text=help_text,
        resolved_backend=resolved_backend,
        supports_page_range=("--start" in help_text and "--end" in help_text),
        supports_effort="--effort" in help_text,
        supports_api_url="--api-url" in help_text,
        supports_client_side_output="--client-side-output-generation" in help_text,
        supports_image_analysis="--image-analysis" in help_text,
        supports_language=("--lang" in help_text or "-l," in help_text),
    )


def make_runtime_env(args: argparse.Namespace, resolved_backend: str) -> dict[str, str]:
    env = os.environ.copy()
    env["MINERU_FORMULA_ENABLE"] = "true"
    env["MINERU_TABLE_ENABLE"] = "true"
    env["MINERU_PDF_RENDER_THREADS"] = str(args.render_threads)
    env["MINERU_PROCESSING_WINDOW_SIZE"] = str(args.processing_window)
    env["MINERU_API_MAX_CONCURRENT_REQUESTS"] = "1"
    env["MINERU_PDF_RENDER_TIMEOUT"] = str(args.render_timeout)
    env["MINERU_TASK_RESULT_TIMEOUT_SECONDS"] = str(args.task_timeout)
    env["MINERU_LOCAL_API_STARTUP_TIMEOUT_SECONDS"] = str(args.startup_timeout)
    env["MINERU_INTRA_OP_NUM_THREADS"] = str(args.intra_op_threads)
    env["MINERU_INTER_OP_NUM_THREADS"] = "1"
    env.setdefault("TOKENIZERS_PARALLELISM", "false")
    if resolved_backend == "pipeline":
        env["MINERU_FORMULA_CH_SUPPORT"] = "true"
    if args.gpu_index is not None and resolved_backend != "pipeline":
        env["CUDA_VISIBLE_DEVICES"] = str(args.gpu_index)
    return env


def find_free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def api_is_healthy(api_url: str, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(api_url.rstrip("/") + "/health", timeout=timeout) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


class LocalMinerUService:
    """启动一次本地 API，让多个分块复用同一模型。"""

    def __init__(
        self,
        api_bin: str,
        output_dir: Path,
        env: dict[str, str],
        startup_timeout: int,
        preload_vlm: bool,
    ) -> None:
        self.api_bin = resolve_executable(api_bin)
        self.output_dir = output_dir
        self.env = dict(env)
        self.startup_timeout = startup_timeout
        self.preload_vlm = preload_vlm
        self.process: subprocess.Popen[str] | None = None
        self.log_handle: Any = None
        self.api_url: str | None = None
        # 重启时沿用同一端口，使外层保存的 API URL 不会失效。
        self.port = find_free_local_port()

    def start(self) -> str:
        if self.process and self.process.poll() is None and self.api_url:
            if api_is_healthy(self.api_url):
                return self.api_url
            self.stop()

        service_dir = self.output_dir / "_service"
        service_dir.mkdir(parents=True, exist_ok=True)
        self.env["MINERU_API_OUTPUT_ROOT"] = str(service_dir / "server_output")
        command = [self.api_bin, "--host", "127.0.0.1", "--port", str(self.port)]
        api_help_result = run_probe([self.api_bin, "--help"])
        api_help = (api_help_result.stdout or "") + "\n" + (api_help_result.stderr or "")
        if self.preload_vlm and "--enable-vlm-preload" in api_help:
            command += ["--enable-vlm-preload", "true"]

        log_path = service_dir / "mineru-api.log"
        self.log_handle = log_path.open("a", encoding="utf-8", buffering=1)
        self.log_handle.write(f"\n[{now_iso()}] START {shlex.join(command)}\n")

        popen_kwargs: dict[str, Any] = {
            "stdout": self.log_handle,
            "stderr": subprocess.STDOUT,
            "text": True,
            "env": self.env,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["start_new_session"] = True
        self.process = subprocess.Popen(command, **popen_kwargs)
        self.api_url = f"http://127.0.0.1:{self.port}"

        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                code = self.process.returncode
                self.stop()
                raise UserFacingError(
                    f"mineru-api 启动失败，退出码 {code}。日志：{log_path}"
                )
            if api_is_healthy(self.api_url):
                return self.api_url
            time.sleep(1.0)
        self.stop()
        raise UserFacingError(
            f"mineru-api 在 {self.startup_timeout} 秒内未就绪。日志：{log_path}"
        )

    def healthy(self) -> bool:
        return bool(
            self.process
            and self.process.poll() is None
            and self.api_url
            and api_is_healthy(self.api_url)
        )

    def stop(self) -> None:
        process = self.process
        self.process = None
        if process and process.poll() is None:
            try:
                if os.name == "nt":
                    with contextlib.suppress(Exception):
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    process.wait(timeout=15)
                else:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=15)
            except Exception:
                try:
                    if os.name == "nt":
                        process.kill()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
                except Exception:
                    pass
        if self.log_handle:
            with contextlib.suppress(Exception):
                self.log_handle.close()
        self.log_handle = None
        self.api_url = None


def extract_pdf_chunk(source_pdf: Path, target_pdf: Path, start_page: int, end_page: int) -> None:
    """旧版 MinerU 没有 -s/-e 时的兼容后备；页码参数为 1-based。"""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise UserFacingError("缺少 pypdf，无法生成兼容分块。") from exc
    target_pdf.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".chunk.", suffix=".pdf", dir=target_pdf.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        reader = PdfReader(str(source_pdf), strict=False)
        writer = PdfWriter()
        for page_index in range(start_page - 1, end_page):
            writer.add_page(reader.pages[page_index])
        with temp_path.open("wb") as handle:
            writer.write(handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target_pdf)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


def materialize_chunk_inputs(
    source_pdf: Path,
    output_dir: Path,
    chunks: Sequence[Chunk],
) -> dict[str, Path]:
    """一次打开源 PDF，按恢复单元生成输入块，避免每块重复上传整本书。"""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise UserFacingError("缺少 pypdf，无法生成长文档输入分块。") from exc

    input_dir = output_dir / "_chunk_inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Path] = {}
    missing: list[tuple[Chunk, Path]] = []
    for chunk in chunks:
        target = input_dir / f"{chunk.chunk_id}.pdf"
        if target.is_file() and target.stat().st_size > 0:
            result[chunk.chunk_id] = target
        else:
            missing.append((chunk, target))
    if not missing:
        return result

    reader = PdfReader(str(source_pdf), strict=False)
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise UserFacingError("PDF 已加密，无法生成输入分块。") from exc

    print(f"准备 {len(missing)} 个长文档输入分块（只需执行一次）……")
    for index, (chunk, target) in enumerate(missing, start=1):
        fd, temp_name = tempfile.mkstemp(prefix=".chunk.", suffix=".pdf", dir=input_dir)
        os.close(fd)
        temp_path = Path(temp_name)
        try:
            writer = PdfWriter()
            for page_index in range(chunk.start_page - 1, chunk.end_page):
                writer.add_page(reader.pages[page_index])
            with temp_path.open("wb") as handle:
                writer.write(handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, target)
            result[chunk.chunk_id] = target
            print(
                f"  [{index}/{len(missing)}] PDF {chunk.start_page}～{chunk.end_page} 页"
            )
        finally:
            with contextlib.suppress(FileNotFoundError):
                temp_path.unlink()
    return result


def build_mineru_command(
    cli: MinerUCliInfo,
    args: argparse.Namespace,
    source_pdf: Path,
    chunk: Chunk,
    attempt_dir: Path,
    api_url: str | None,
    chunk_input_pdf: Path | None,
) -> tuple[list[str], Path, str]:
    if chunk_input_pdf is not None:
        input_pdf = chunk_input_pdf
        expected_stem = input_pdf.stem
        use_page_range = False
    elif cli.supports_page_range:
        input_pdf = source_pdf
        expected_stem = source_pdf.stem
        use_page_range = True
    else:
        input_pdf = attempt_dir / f"{chunk.chunk_id}.pdf"
        if not input_pdf.exists():
            extract_pdf_chunk(source_pdf, input_pdf, chunk.start_page, chunk.end_page)
        expected_stem = input_pdf.stem
        use_page_range = False

    raw_output = attempt_dir / "mineru_output"
    raw_output.mkdir(parents=True, exist_ok=True)
    command = [
        cli.executable,
        "-p", str(input_pdf),
        "-o", str(raw_output),
        "-m", args.method,
        "-b", cli.resolved_backend,
        "-f", "true",
        "-t", "true",
    ]
    if use_page_range:
        command += ["-s", str(chunk.start_page - 1), "-e", str(chunk.end_page - 1)]
    if api_url and cli.supports_api_url:
        command += ["--api-url", api_url]
    if cli.supports_effort and cli.resolved_backend.startswith("hybrid"):
        command += ["--effort", args.effort]
    if cli.supports_image_analysis:
        command += ["--image-analysis", str(args.image_analysis).lower()]
    if cli.supports_language and cli.resolved_backend == "pipeline":
        command += ["-l", args.language]
    if api_url and cli.supports_client_side_output:
        command += ["--client-side-output-generation", "true"]
    return command, raw_output, expected_stem


def run_logged_command(
    command: Sequence[str],
    env: dict[str, str],
    log_path: Path,
    quiet: bool,
) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", buffering=1) as log_handle:
        log_handle.write(f"\n[{now_iso()}] RUN {shlex.join(command)}\n")
        process = subprocess.Popen(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
        assert process.stdout is not None
        try:
            for line in process.stdout:
                log_handle.write(line)
                if not quiet:
                    print(f"    {line}", end="")
        except KeyboardInterrupt:
            with contextlib.suppress(Exception):
                process.terminate()
            with contextlib.suppress(Exception):
                process.wait(timeout=15)
            raise
        return process.wait()


def choose_artifact(root: Path, expected_stem: str, suffix: str) -> Path | None:
    exact_name = f"{expected_stem}{suffix}"
    exact = [path for path in root.rglob(exact_name) if path.is_file()]
    candidates = exact or [path for path in root.rglob(f"*{suffix}") if path.is_file()]
    if not candidates:
        return None
    candidates.sort(key=lambda path: (path.stat().st_size, path.stat().st_mtime_ns), reverse=True)
    return candidates[0]


def validate_chunk_output(raw_output: Path, expected_stem: str) -> tuple[Path, Path | None]:
    markdown = choose_artifact(raw_output, expected_stem, ".md")
    if markdown is None or markdown.stat().st_size == 0:
        raise UserFacingError("MinerU 返回成功，但没有找到非空 Markdown。")
    middle = choose_artifact(raw_output, expected_stem, "_middle.json")
    if middle is not None:
        try:
            payload = load_json(middle)
            if not isinstance(payload, dict) or not isinstance(payload.get("pdf_info"), list):
                raise ValueError("缺少 pdf_info")
        except Exception as exc:
            raise UserFacingError(f"middle.json 无效：{exc}") from exc
    return markdown, middle


def copy_file_atomic(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        shutil.copy2(source, temp_path)
        os.replace(temp_path, target)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


def normalize_local_link(raw: str) -> str | None:
    value = html.unescape(raw.strip())
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1]
    value = value.split("#", 1)[0].split("?", 1)[0]
    if not value or re.match(r"^[a-z][a-z0-9+.-]*:", value, re.I) or value.startswith("//"):
        return None
    value = urllib.parse.unquote(value).replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return str(path)


def rewrite_and_copy_assets(
    markdown_text: str,
    markdown_path: Path,
    output_dir: Path,
    chunk_id: str,
) -> tuple[str, list[str], int]:
    missing: list[str] = []
    copied = 0

    def replace_link(raw_link: str) -> str:
        nonlocal copied
        normalized = normalize_local_link(raw_link)
        if normalized is None:
            return raw_link
        source = (markdown_path.parent / Path(normalized)).resolve()
        try:
            source.relative_to(markdown_path.parent.resolve())
        except ValueError:
            missing.append(raw_link)
            return raw_link
        if not source.is_file():
            missing.append(raw_link)
            return raw_link
        target_relative = Path("assets") / chunk_id / Path(normalized)
        target = output_dir / target_relative
        copy_file_atomic(source, target)
        copied += 1
        return target_relative.as_posix()

    def replace_markdown(match: re.Match[str]) -> str:
        return match.group(1) + replace_link(match.group(2)) + match.group(3)

    def replace_html(match: re.Match[str]) -> str:
        return match.group(1) + replace_link(match.group(2)) + match.group(3)

    markdown_text = MARKDOWN_IMAGE_RE.sub(replace_markdown, markdown_text)
    markdown_text = HTML_IMAGE_RE.sub(replace_html, markdown_text)
    return markdown_text, missing, copied


def iter_nested_dicts(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_nested_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_nested_dicts(child)


def extract_formula_records(result: ChunkResult) -> list[dict[str, Any]]:
    if result.middle_json_path is None:
        return []
    try:
        middle = load_json(result.middle_json_path)
    except Exception:
        return []
    records: list[dict[str, Any]] = []
    for local_index, page in enumerate(middle.get("pdf_info") or []):
        if not isinstance(page, dict):
            continue
        page_idx = page.get("page_idx")
        if not isinstance(page_idx, int):
            page_idx = local_index
        if 0 <= page_idx < result.chunk.page_count:
            global_page = result.chunk.start_page + page_idx
        elif result.chunk.start_page - 1 <= page_idx <= result.chunk.end_page - 1:
            global_page = page_idx + 1
        else:
            global_page = result.chunk.start_page + local_index
        seen: set[tuple[str, str, str]] = set()
        for item in iter_nested_dicts(page):
            formula_type = str(item.get("type") or "")
            if formula_type not in {"interline_equation", "inline_equation"}:
                continue
            content = item.get("content") or item.get("latex") or ""
            if not isinstance(content, str) or not content.strip():
                # middle.json 常同时包含外层公式 block 与内部 span；外层通常无内容。
                # 忽略空容器，避免一条公式被重复计入审计索引。
                continue
            content = content.strip()
            bbox = item.get("bbox")
            signature = (
                formula_type,
                json.dumps(bbox, ensure_ascii=False, sort_keys=True),
                str(content),
            )
            if signature in seen:
                continue
            seen.add(signature)
            record = {
                "chunk_id": result.chunk.chunk_id,
                "page": global_page,
                "local_page_index": page_idx,
                "type": formula_type,
                "bbox": bbox,
                "latex": content,
            }
            if "score" in item:
                record["score"] = item["score"]
            if "page_size" in page:
                record["page_size"] = page["page_size"]
            records.append(record)
    return records


def strip_fenced_code(text: str) -> str:
    return re.sub(r"```.*?```|~~~.*?~~~", lambda m: " " * len(m.group(0)), text, flags=re.S)


def extract_math_spans(text: str) -> tuple[list[str], str, list[str]]:
    """返回（公式内容、去除公式后的文本、定界符问题）。"""
    spans: list[str] = []
    problems: list[str] = []
    chars = list(text)
    index = 0
    length = len(text)

    def escaped(position: int) -> bool:
        count = 0
        cursor = position - 1
        while cursor >= 0 and text[cursor] == "\\":
            count += 1
            cursor -= 1
        return count % 2 == 1

    pairs = {"\\(": "\\)", "\\[": "\\]", "$$": "$$", "$": "$"}
    while index < length:
        opener = None
        for token in ("\\[", "\\(", "$$", "$"):
            if text.startswith(token, index) and not escaped(index):
                opener = token
                break
        if opener is None:
            index += 1
            continue
        closer = pairs[opener]
        search_from = index + len(opener)
        cursor = search_from
        found = -1
        while cursor < length:
            if text.startswith(closer, cursor) and not escaped(cursor):
                if opener == "$" and text.startswith("$$", cursor):
                    cursor += 2
                    continue
                found = cursor
                break
            cursor += 1
        if found < 0:
            problems.append(f"未闭合数学定界符 {opener!r}，字符位置 {index}")
            index += len(opener)
            continue
        spans.append(text[search_from:found])
        for pos in range(index, found + len(closer)):
            chars[pos] = " "
        index = found + len(closer)
    return spans, "".join(chars), problems


def brace_balance_problem(formula: str) -> str | None:
    balance = 0
    index = 0
    while index < len(formula):
        char = formula[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            balance += 1
        elif char == "}":
            balance -= 1
            if balance < 0:
                return "出现多余的右花括号"
        index += 1
    if balance:
        return f"花括号未配对，净差 {balance}"
    return None


def lint_markdown(text: str) -> dict[str, Any]:
    without_code = strip_fenced_code(text)
    formulas, outside_math, delimiter_problems = extract_math_spans(without_code)
    brace_problems: list[dict[str, Any]] = []
    environment_problems: list[dict[str, Any]] = []
    for index, formula in enumerate(formulas, start=1):
        brace_problem = brace_balance_problem(formula)
        if brace_problem:
            brace_problems.append({"formula_index": index, "problem": brace_problem})
        env_tokens = re.findall(r"\\(begin|end)\{([^{}]+)\}", formula)
        stack: list[str] = []
        env_error: str | None = None
        for tag_type, env in env_tokens:
            if tag_type == "begin":
                stack.append(env)
            elif tag_type == "end":
                if not stack or stack[-1] != env:
                    env_error = f"mismatched \\end{{{env}}}, stack was {stack}"
                    break
                stack.pop()
        if not env_error and stack:
            env_error = f"unclosed environments: {stack}"
        if env_error:
            begins = [env for t, env in env_tokens if t == "begin"]
            ends = [env for t, env in env_tokens if t == "end"]
            environment_problems.append(
                {"formula_index": index, "begin": begins, "end": ends, "error": env_error}
            )
    bare_commands = sorted(set(MATH_COMMAND_RE.findall(outside_math)))
    pua = PRIVATE_USE_RE.findall(text)
    return {
        "formula_span_count": len(formulas),
        "delimiter_problems": delimiter_problems,
        "brace_problems": brace_problems,
        "environment_problems": environment_problems,
        "bare_tex_command_count": len(MATH_COMMAND_RE.findall(outside_math)),
        "bare_tex_commands": bare_commands,
        "private_use_character_count": len(pua),
        "private_use_characters": sorted(set(pua)),
        "suspicious_lambda_as_chinese_count": len(SUSPICIOUS_LAMBDA_RE.findall(text)),
    }


def load_or_initialize_state(
    state_path: Path,
    event_path: Path,
    source: dict[str, Any],
    config: dict[str, Any],
    chunks: Sequence[Chunk],
) -> dict[str, Any]:
    config_hash = sha256_json(config)
    if state_path.exists():
        state = load_json(state_path)
        if state.get("schema_version") != STATE_SCHEMA_VERSION:
            raise UserFacingError(
                "输出目录中存在不兼容的状态文件。请换一个新输出目录，旧结果不会被改动。"
            )
        old_source = state.get("source") or {}
        if old_source.get("sha256") != source.get("sha256"):
            raise UserFacingError(
                "输出目录属于另一份 PDF。请换一个新输出目录，避免混合两本书的结果。"
            )
        if state.get("config_hash") != config_hash:
            raise UserFacingError(
                "本次参数与该输出目录的既有任务不一致。请沿用原参数，或换一个新输出目录。"
            )
        expected_ids = [chunk.chunk_id for chunk in chunks]
        if state.get("planned_chunk_ids") != expected_ids:
            raise UserFacingError(
                "分块计划与既有任务不一致。请换一个新输出目录，旧缓存不会被覆盖。"
            )
        state.setdefault("chunks", {})
        return state

    state = {
        "schema_version": STATE_SCHEMA_VERSION,
        "script_version": SCRIPT_VERSION,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "source": source,
        "config": config,
        "config_hash": config_hash,
        "planned_chunk_ids": [chunk.chunk_id for chunk in chunks],
        "chunks": {},
    }
    atomic_write_json(state_path, state)
    append_jsonl(event_path, {"time": now_iso(), "event": "task_created"})
    return state


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    atomic_write_json(state_path, state)


def state_chunk_result(
    output_dir: Path,
    chunk: Chunk,
    state_entry: dict[str, Any],
) -> ChunkResult | None:
    if state_entry.get("status") != "done":
        return None
    markdown_rel = state_entry.get("markdown")
    if not isinstance(markdown_rel, str):
        return None
    markdown = output_dir / markdown_rel
    if not markdown.is_file() or markdown.stat().st_size == 0:
        return None
    middle_rel = state_entry.get("middle_json")
    middle = output_dir / middle_rel if isinstance(middle_rel, str) else None
    if middle is not None and not middle.is_file():
        middle = None
    return ChunkResult(
        chunk=chunk,
        markdown_path=markdown,
        middle_json_path=middle,
        output_root=output_dir / str(state_entry.get("attempt_dir") or ""),
        attempt=int(state_entry.get("attempt") or 0),
        elapsed_seconds=float(state_entry.get("elapsed_seconds") or 0),
    )


def process_one_chunk(
    source_pdf: Path,
    output_dir: Path,
    chunk: Chunk,
    cli: MinerUCliInfo,
    args: argparse.Namespace,
    env: dict[str, str],
    api_url: str | None,
    prior_attempts: int,
    service: LocalMinerUService | None = None,
    chunk_input_pdf: Path | None = None,
) -> ChunkResult:
    last_error = "未知错误"
    for retry_index in range(args.retries + 1):
        if service and not service.healthy():
            print("  检测到常驻服务异常，重启后再尝试当前分块……")
            api_url = service.start()
        attempt = prior_attempts + retry_index + 1
        attempt_dir = output_dir / "chunks" / chunk.chunk_id / f"attempt_{attempt:02d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        command, raw_output, expected_stem = build_mineru_command(
            cli, args, source_pdf, chunk, attempt_dir, api_url, chunk_input_pdf
        )
        log_path = attempt_dir / "mineru.log"
        started = time.monotonic()
        print(
            f"[{chunk.sequence}] PDF {chunk.start_page}～{chunk.end_page} 页 "
            f"（{chunk.page_count} 页），尝试 {attempt}"
        )
        return_code = run_logged_command(command, env, log_path, args.quiet_mineru)
        elapsed = time.monotonic() - started
        if return_code == 0:
            try:
                markdown, middle = validate_chunk_output(raw_output, expected_stem)
                return ChunkResult(chunk, markdown, middle, attempt_dir, attempt, elapsed)
            except Exception as exc:
                last_error = str(exc)
        else:
            last_error = f"MinerU 退出码 {return_code}；详见 {log_path}"
        atomic_write_json(
            attempt_dir / "failed.json",
            {
                "time": now_iso(),
                "chunk_id": chunk.chunk_id,
                "attempt": attempt,
                "error": last_error,
                "elapsed_seconds": round(elapsed, 3),
            },
        )
        if retry_index < args.retries:
            print(f"  本次失败，将重试：{last_error}")
    raise UserFacingError(last_error)


def merge_outputs(
    source_pdf: Path,
    output_dir: Path,
    chapters: Sequence[Chapter],
    chunks: Sequence[Chunk],
    results: dict[str, ChunkResult],
    cli: MinerUCliInfo,
) -> tuple[list[Path], list[str], int, list[dict[str, Any]]]:
    grouped: dict[str, list[Chunk]] = defaultdict(list)
    for chunk in chunks:
        grouped[chunk.chapter_key].append(chunk)

    rewritten_by_chunk: dict[str, str] = {}
    missing_assets: list[str] = []
    copied_assets = 0
    formula_records: list[dict[str, Any]] = []
    for chunk in chunks:
        result = results.get(chunk.chunk_id)
        if result is None:
            continue
        text = result.markdown_path.read_text(encoding="utf-8", errors="replace")
        rewritten, missing, copied = rewrite_and_copy_assets(
            text, result.markdown_path, output_dir, chunk.chunk_id
        )
        rewritten_by_chunk[chunk.chunk_id] = rewritten.strip()
        missing_assets.extend(f"{chunk.chunk_id}: {item}" for item in missing)
        copied_assets += copied
        formula_records.extend(extract_formula_records(result))

    generated: list[Path] = []
    chapter_dir = output_dir / "chapters"
    has_named_chapters = any(chapter.file for chapter in chapters)

    def compose(chapter: Chapter, selected_chunks: Sequence[Chunk], include_title: bool) -> str:
        parts = [
            "<!--",
            f"Generated by 数学文档OCR_v3.py {SCRIPT_VERSION}",
            f"Source: {source_pdf.name}",
            f"MinerU: {cli.version}",
            f"Pages: {chapter.start_page}-{chapter.end_page}",
            "Do not treat automated OCR as proof of mathematical correctness.",
            "-->",
            "",
        ]
        if include_title:
            parts += [f"# {chapter.title}", ""]
        for chunk in selected_chunks:
            parts += [
                f"<!-- PDF pages {chunk.start_page}-{chunk.end_page}; chunk {chunk.chunk_id} -->",
                "",
                rewritten_by_chunk.get(chunk.chunk_id, ""),
                "",
            ]
        return "\n".join(parts).rstrip() + "\n"

    if has_named_chapters:
        for chapter in chapters:
            path = chapter_dir / chapter.file
            atomic_write_text(path, compose(chapter, grouped[chapter.key], include_title=True))
            generated.append(path)

    combined_chunks = sorted(chunks, key=lambda item: item.sequence)
    combined_parts = [
        "<!--",
        f"Generated by 数学文档OCR_v3.py {SCRIPT_VERSION}",
        f"Source: {source_pdf.name}",
        f"MinerU: {cli.version}",
        "Do not treat automated OCR as proof of mathematical correctness.",
        "-->",
        "",
        f"# {source_pdf.stem}",
        "",
    ]
    chapter_lookup = {chapter.key: chapter for chapter in chapters}
    last_chapter: str | None = None
    for chunk in combined_chunks:
        chapter = chapter_lookup[chunk.chapter_key]
        if has_named_chapters and chapter.key != last_chapter:
            combined_parts += [f"## {chapter.title}", ""]
            last_chapter = chapter.key
        combined_parts += [
            f"<!-- PDF pages {chunk.start_page}-{chunk.end_page}; chunk {chunk.chunk_id} -->",
            "",
            rewritten_by_chunk.get(chunk.chunk_id, ""),
            "",
        ]
    combined_path = output_dir / f"{sanitize_filename(source_pdf.stem)}"
    atomic_write_text(combined_path, "\n".join(combined_parts).rstrip() + "\n")
    generated.insert(0, combined_path)

    formula_index = output_dir / "formula_audit.jsonl"
    formula_text = "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in formula_records
    )
    atomic_write_text(formula_index, formula_text)
    return generated, missing_assets, copied_assets, formula_records


def build_quality_report(
    source_pdf: Path,
    markdown_files: Sequence[Path],
    planned_chunks: Sequence[Chunk],
    successful_chunks: dict[str, ChunkResult],
    failed_chunks: dict[str, str],
    missing_assets: Sequence[str],
    copied_assets: int,
    formula_records: Sequence[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    markdown_reports: list[dict[str, Any]] = []
    total_bare = total_pua = total_lambda = 0
    hard_problem_count = 0
    for file_index, path in enumerate(markdown_files):
        text = path.read_text(encoding="utf-8", errors="replace")
        lint = lint_markdown(text)
        lint["file"] = path.relative_to(output_dir).as_posix()
        markdown_reports.append(lint)
        # 第一个文件始终是全书合并版；章节文件只是它的拆分副本，不能重复计数。
        if file_index == 0:
            total_bare += lint["bare_tex_command_count"]
            total_pua += lint["private_use_character_count"]
            total_lambda += lint["suspicious_lambda_as_chinese_count"]
            hard_problem_count += (
                len(lint["delimiter_problems"])
                + len(lint["brace_problems"])
                + len(lint["environment_problems"])
            )

    status = "pass"
    if failed_chunks or missing_assets or hard_problem_count:
        status = "fail"
    elif total_bare or total_pua or total_lambda:
        status = "warning"

    return {
        "generated_at": now_iso(),
        "script_version": SCRIPT_VERSION,
        "source": source_pdf.name,
        "status": status,
        "summary": {
            "planned_chunks": len(planned_chunks),
            "successful_chunks": len(successful_chunks),
            "failed_chunks": len(failed_chunks),
            "formula_records_in_middle_json": len(formula_records),
            "copied_assets": copied_assets,
            "missing_assets": len(missing_assets),
            "bare_tex_command_count": total_bare,
            "private_use_character_count": total_pua,
            "suspicious_lambda_as_chinese_count": total_lambda,
            "structural_math_problem_count": hard_problem_count,
        },
        "failed_chunk_details": failed_chunks,
        "missing_asset_details": list(missing_assets),
        "markdown_reports": markdown_reports,
        "limitations": [
            "自动检查通过不代表公式语义正确。",
            "负号、指数、上下标、矩阵元素、转置、逆矩阵和伴随矩阵仍需抽查。",
            "题干、选项、定理条件与最终答案是最高优先级人工复核区域。",
        ],
    }


def quality_report_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    status_map = {"pass": "通过自动结构检查", "warning": "有警告", "fail": "未通过"}
    lines = [
        "# OCR 自动质量报告",
        "",
        f"- 状态：**{status_map.get(report['status'], report['status'])}**",
        f"- 分块：{summary['successful_chunks']} / {summary['planned_chunks']} 成功",
        f"- 中间结果中检测到的公式记录：{summary['formula_records_in_middle_json']}",
        f"- 已复制图片资源：{summary['copied_assets']}",
        f"- 缺失图片资源：{summary['missing_assets']}",
        f"- 裸 TeX 命令：{summary['bare_tex_command_count']}",
        f"- 私有区乱码字符：{summary['private_use_character_count']}",
        f"- 可疑汉字“入”：{summary['suspicious_lambda_as_chinese_count']}",
        f"- 数学结构问题：{summary['structural_math_problem_count']}",
        "",
        "## 重要说明",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    if report["failed_chunk_details"]:
        lines += ["", "## 失败分块", ""]
        lines.extend(
            f"- `{chunk_id}`：{error}"
            for chunk_id, error in report["failed_chunk_details"].items()
        )
    if report["missing_asset_details"]:
        lines += ["", "## 缺失图片", ""]
        lines.extend(f"- `{item}`" for item in report["missing_asset_details"][:100])
    return "\n".join(lines).rstrip() + "\n"


def build_source_identity(
    source_pdf: Path,
    total_pages: int,
    existing_state: dict[str, Any] | None,
) -> dict[str, Any]:
    stat = source_pdf.stat()
    if existing_state:
        old = existing_state.get("source") or {}
        if (
            old.get("path") == str(source_pdf)
            and old.get("size") == stat.st_size
            and old.get("mtime_ns") == stat.st_mtime_ns
            and isinstance(old.get("sha256"), str)
        ):
            digest = old["sha256"]
        else:
            digest = sha256_file(source_pdf)
    else:
        digest = sha256_file(source_pdf)
    return {
        "path": str(source_pdf),
        "name": source_pdf.name,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": digest,
        "pages": total_pages,
    }


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="使用 MinerU 进行数学教材/长 PDF 结构化 OCR，支持断点续跑。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("pdf", type=Path, help="输入 PDF")
    parser.add_argument("-o", "--output", type=Path, help="输出目录；默认位于 PDF 同目录")
    parser.add_argument(
        "--backend",
        default="auto",
        help="auto、hybrid、pipeline、vlm，或 MinerU 支持的完整后端名",
    )
    parser.add_argument("--effort", choices=["medium", "high"], default="high")
    parser.add_argument("--method", choices=["auto", "txt", "ocr"], default="auto")
    parser.add_argument("--language", default="ch", help="pipeline OCR 语言")
    parser.add_argument("--chunk-pages", type=int, default=DEFAULT_CHUNK_PAGES)
    parser.add_argument(
        "--chunk-input-mode",
        choices=["materialized", "range"],
        default="materialized",
        help="materialized 避免每块重复传整本 PDF；range 节省临时磁盘",
    )
    parser.add_argument("--start-page", type=int, default=1, help="起始页，1-based")
    parser.add_argument("--end-page", type=int, help="结束页，1-based；默认最后一页")
    parser.add_argument("--pages", help="抽选页，例如 17,22,26,38-45")
    parser.add_argument("--chapters", type=Path, help="章节 JSON；与 --pages 互斥")
    parser.add_argument("--retries", type=int, default=2, help="每个失败分块的重试次数")
    parser.add_argument("--render-threads", type=int, default=DEFAULT_RENDER_THREADS)
    parser.add_argument("--processing-window", type=int, default=DEFAULT_PROCESSING_WINDOW)
    parser.add_argument(
        "--intra-op-threads", type=int, default=max(1, min(8, os.cpu_count() or 1))
    )
    parser.add_argument("--startup-timeout", type=int, default=DEFAULT_STARTUP_TIMEOUT)
    parser.add_argument("--task-timeout", type=int, default=DEFAULT_TASK_TIMEOUT)
    parser.add_argument("--render-timeout", type=int, default=DEFAULT_RENDER_TIMEOUT)
    parser.add_argument("--gpu-index", type=int, help="指定 NVIDIA GPU；auto 模式会自动选择")
    parser.add_argument(
        "--image-analysis",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="分析图片/图表语义；公式和普通图片提取不依赖此选项",
    )
    parser.add_argument("--mineru-bin", default="mineru")
    parser.add_argument("--mineru-api-bin", default="mineru-api")
    parser.add_argument("--api-url", help="复用已有 mineru-api；提供后不启动本地服务")
    parser.add_argument(
        "--persistent-api",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="分块之间复用常驻本地模型",
    )
    parser.add_argument(
        "--quiet-mineru", action="store_true", help="不把 MinerU 详细日志打印到终端"
    )
    parser.add_argument("--dry-run", action="store_true", help="只检查环境并显示计划")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.pages and args.chapters:
        raise UserFacingError("--pages 与 --chapters 不能同时使用。")
    for name in (
        "chunk_pages", "render_threads", "processing_window", "intra_op_threads",
        "startup_timeout", "task_timeout", "render_timeout",
    ):
        if getattr(args, name) < 1:
            raise UserFacingError(f"--{name.replace('_', '-')} 必须大于 0。")
    if args.retries < 0:
        raise UserFacingError("--retries 不能小于 0。")


def run(args: argparse.Namespace) -> int:
    validate_args(args)
    source_pdf = args.pdf.expanduser().resolve()
    if not source_pdf.is_file():
        raise UserFacingError(f"输入文件不存在：{source_pdf}")
    if source_pdf.suffix.lower() != ".pdf":
        raise UserFacingError("当前脚本只接受 PDF。")

    output_dir = (
        args.output.expanduser().resolve()
        if args.output
        else source_pdf.with_name(source_pdf.stem + "_数学OCR")
    )
    if output_dir == source_pdf:
        raise UserFacingError("输出目录不能与输入 PDF 相同。")

    total_pages = count_pdf_pages(source_pdf)
    args.end_page = args.end_page or total_pages
    if not (1 <= args.start_page <= args.end_page <= total_pages):
        raise UserFacingError(
            f"处理范围必须位于 1～{total_pages}，当前为 {args.start_page}～{args.end_page}。"
        )
    selected_pages = parse_page_expression(args.pages, total_pages) if args.pages else None
    if selected_pages:
        selected_pages = [
            page for page in selected_pages if args.start_page <= page <= args.end_page
        ]
        if not selected_pages:
            raise UserFacingError("抽选页与 start/end 范围没有交集。")
    configured_chapters = load_chapters(args.chapters.resolve(), total_pages) if args.chapters else None
    chapters, chunks = build_plan(
        total_pages,
        args.chunk_pages,
        args.start_page,
        args.end_page,
        selected_pages,
        configured_chapters,
    )

    gpu_ok, detected_gpu, gpu_description = detect_nvidia_gpu()
    requested_backend = args.backend
    if requested_backend == "auto":
        requested_backend = "hybrid" if gpu_ok else "pipeline"
        if args.gpu_index is None and gpu_ok:
            args.gpu_index = detected_gpu
    elif requested_backend in {"hybrid", "vlm"} and args.gpu_index is None and gpu_ok:
        args.gpu_index = detected_gpu

    cli = probe_mineru(args.mineru_bin, requested_backend)
    if args.api_url and not cli.supports_api_url:
        raise UserFacingError("当前 MinerU 版本不支持 --api-url，无法复用指定服务。")
    if args.persistent_api and not args.api_url and not cli.supports_api_url:
        raise UserFacingError(
            "当前 MinerU 版本不支持常驻 API 分块调度。请升级 MinerU，或使用 --no-persistent-api。"
        )

    if args.dry_run:
        source_stat = source_pdf.stat()
        print(f"输入：{source_pdf}")
        print(f"输出：{output_dir}")
        print(f"页数：{total_pages}；文件大小：{human_bytes(source_stat.st_size)}")
        print(f"后端：{cli.resolved_backend}；MinerU：{cli.version}")
        print(f"硬件判断：{gpu_description}")
        print(f"计划：{len(chunks)} 个分块；单块最多 {args.chunk_pages} 页")
        for chunk in chunks:
            print(f"  {chunk.chunk_id}: PDF {chunk.start_page}～{chunk.end_page} 页")
        print("试运行未创建目录、状态文件或 OCR 结果。")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "ocr_state.json"
    event_path = output_dir / "ocr_events.jsonl"
    if not state_path.exists():
        existing_items = [item for item in output_dir.iterdir()]
        if existing_items:
            preview = ", ".join(item.name for item in existing_items[:5])
            raise UserFacingError(
                "输出目录非空且不属于本脚本的可续跑任务。为避免覆盖旧成果，"
                f"请换一个新目录。现有内容示例：{preview}"
            )
    existing_state = load_json(state_path) if state_path.exists() else None

    source = build_source_identity(source_pdf, total_pages, existing_state)
    config = {
        "script_version": SCRIPT_VERSION,
        "mineru_version": cli.version,
        "backend": cli.resolved_backend,
        "method": args.method,
        "effort": args.effort,
        "language": args.language,
        "chunk_pages": args.chunk_pages,
        "chunk_input_mode": args.chunk_input_mode,
        "start_page": args.start_page,
        "end_page": args.end_page,
        "selected_pages": selected_pages,
        "chapters": [dataclasses.asdict(chapter) for chapter in chapters],
        "formula": True,
        "table": True,
        "image_analysis": args.image_analysis,
    }
    state = load_or_initialize_state(state_path, event_path, source, config, chunks)

    done_count = sum(
        1
        for chunk in chunks
        if state_chunk_result(output_dir, chunk, state.get("chunks", {}).get(chunk.chunk_id, {}))
    )
    pending_chunks = [
        chunk
        for chunk in chunks
        if not state_chunk_result(
            output_dir, chunk, state.get("chunks", {}).get(chunk.chunk_id, {})
        )
    ]
    print(f"输入：{source_pdf}")
    print(f"页数：{total_pages}；文件大小：{human_bytes(source['size'])}")
    print(f"后端：{cli.resolved_backend}；MinerU：{cli.version}")
    print(f"硬件判断：{gpu_description}")
    print(
        f"计划：{len(chunks)} 个分块，已完成 {done_count}，"
        f"待处理 {len(chunks) - done_count}；单块最多 {args.chunk_pages} 页"
    )

    env = make_runtime_env(args, cli.resolved_backend)
    chunk_inputs: dict[str, Path] = {}
    if args.chunk_input_mode == "materialized" and pending_chunks:
        try:
            chunk_inputs = materialize_chunk_inputs(source_pdf, output_dir, pending_chunks)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if not cli.supports_page_range:
                raise UserFacingError(
                    f"生成分块 PDF 失败，且当前 MinerU 不支持页范围后备模式：{exc}"
                ) from exc
            print(f"警告：生成分块 PDF 失败，将退回 MinerU 页范围模式：{exc}")
            chunk_inputs = {}

    service: LocalMinerUService | None = None
    active_api_url = args.api_url
    if not active_api_url and args.persistent_api and pending_chunks:
        service = LocalMinerUService(
            args.mineru_api_bin,
            output_dir,
            env,
            args.startup_timeout,
            preload_vlm=cli.resolved_backend != "pipeline",
        )
        print("启动常驻 MinerU 服务并预载模型……")
        active_api_url = service.start()
        print("常驻服务已就绪；后续分块复用同一模型。")

    successful: dict[str, ChunkResult] = {}
    failed: dict[str, str] = {}
    started_all = time.monotonic()
    try:
        for chunk in chunks:
            entry = state.get("chunks", {}).get(chunk.chunk_id, {})
            cached = state_chunk_result(output_dir, chunk, entry)
            if cached:
                successful[chunk.chunk_id] = cached
                print(
                    f"[缓存] PDF {chunk.start_page}～{chunk.end_page} 页："
                    f"{cached.markdown_path.relative_to(output_dir)}"
                )
                continue

            if service and not service.healthy():
                print("常驻服务已退出，正在重新启动……")
                active_api_url = service.start()
            prior_attempts = int(entry.get("attempt") or 0)
            append_jsonl(
                event_path,
                {
                    "time": now_iso(), "event": "chunk_started",
                    "chunk_id": chunk.chunk_id, "start_page": chunk.start_page,
                    "end_page": chunk.end_page,
                },
            )
            try:
                result = process_one_chunk(
                    source_pdf, output_dir, chunk, cli, args, env,
                    active_api_url, prior_attempts, service,
                    chunk_inputs.get(chunk.chunk_id),
                )
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                error = str(exc)
                failed[chunk.chunk_id] = error
                state.setdefault("chunks", {})[chunk.chunk_id] = {
                    "status": "failed",
                    "attempt": prior_attempts + args.retries + 1,
                    "error": error,
                    "updated_at": now_iso(),
                }
                save_state(state_path, state)
                append_jsonl(
                    event_path,
                    {"time": now_iso(), "event": "chunk_failed", "chunk_id": chunk.chunk_id, "error": error},
                )
                print(f"  分块失败但已保留此前成果：{error}")
                if service and not service.healthy():
                    active_api_url = service.start()
                continue

            successful[chunk.chunk_id] = result
            state.setdefault("chunks", {})[chunk.chunk_id] = {
                "status": "done",
                "attempt": result.attempt,
                "start_page": chunk.start_page,
                "end_page": chunk.end_page,
                "chapter_key": chunk.chapter_key,
                "markdown": result.markdown_path.relative_to(output_dir).as_posix(),
                "middle_json": (
                    result.middle_json_path.relative_to(output_dir).as_posix()
                    if result.middle_json_path else None
                ),
                "attempt_dir": result.output_root.relative_to(output_dir).as_posix(),
                "elapsed_seconds": round(result.elapsed_seconds, 3),
                "completed_at": now_iso(),
            }
            save_state(state_path, state)
            append_jsonl(
                event_path,
                {
                    "time": now_iso(), "event": "chunk_done",
                    "chunk_id": chunk.chunk_id,
                    "elapsed_seconds": round(result.elapsed_seconds, 3),
                },
            )
            completed = len(successful)
            elapsed_all = time.monotonic() - started_all
            average = elapsed_all / max(1, completed - done_count)
            remaining = len(chunks) - completed - len(failed)
            print(
                f"  完成，用时 {human_seconds(result.elapsed_seconds)}；"
                f"粗略剩余 {human_seconds(average * max(0, remaining))}"
            )
    finally:
        if service:
            service.stop()

    generated, missing_assets, copied_assets, formula_records = merge_outputs(
        source_pdf, output_dir, chapters, chunks, successful, cli
    )
    report = build_quality_report(
        source_pdf, generated, chunks, successful, failed,
        missing_assets, copied_assets, formula_records, output_dir,
    )
    atomic_write_json(output_dir / "quality_report.json", report)
    atomic_write_text(output_dir / "quality_report.md", quality_report_markdown(report))
    manifest = {
        "generated_at": now_iso(),
        "source": source,
        "config": config,
        "outputs": [path.relative_to(output_dir).as_posix() for path in generated],
        "formula_audit": "formula_audit.jsonl",
        "quality_report": "quality_report.md",
        "quality_status": report["status"],
    }
    atomic_write_json(output_dir / "run_manifest.json", manifest)

    print("\n处理结束。")
    for path in generated:
        print(f"  Markdown：{path}")
    print(f"  质量报告：{output_dir / 'quality_report.md'}")
    print(f"  公式审计索引：{output_dir / 'formula_audit.jsonl'}")
    if failed:
        print("存在失败分块；修复环境后原命令重跑即可续传。")
        return 2
    if report["status"] == "fail":
        print("自动结构检查未通过，请先查看质量报告。")
        return 3
    if report["status"] == "warning":
        print("自动结构检查有警告，请查看质量报告并抽查公式。")
    else:
        print("自动结构检查通过；数学语义仍需按抽样计划人工核对。")
    return 0


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    try:
        return run(args)
    except KeyboardInterrupt:
        print("\n已中断。完成分块均已落盘，下次执行相同命令会从断点继续。", file=sys.stderr)
        return 130
    except UserFacingError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"未预期错误：{exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
