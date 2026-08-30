#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高质量 OCR 产物章节化拆分与《讲义》结构构建引擎
将 8 本大体量全书 OCR Markdown 精准切分为章节单篇 Markdown，
自动提取并迁移关联的插图 assets，校正相对引用路径，
并生成独立且标准化的高质量《讲义》库（与旧配套讲义完全隔离）。
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import NamedTuple


class ChapterDef(NamedTuple):
    filename: str
    title: str
    start_pattern: str


def find_first_match_pos(text: str, pattern: str, search_start: int = 0) -> int:
    m = re.search(pattern, text[search_start:], re.M)
    if not m:
        return -1
    return search_start + m.start()


def split_book_by_patterns(
    source_md: Path,
    source_assets_dir: Path,
    target_dir: Path,
    chapters: list[ChapterDef],
):
    """根据正则模式列表将 Markdown 拆分为章节，并同步迁移 assets 图片。"""
    text = source_md.read_text(encoding="utf-8")
    target_dir.mkdir(parents=True, exist_ok=True)
    target_assets_dir = target_dir / "assets"
    target_assets_dir.mkdir(parents=True, exist_ok=True)

    # 依次定位每个章节的起始位置
    positions: list[int] = []
    curr_pos = 0
    for ch in chapters:
        pos = find_first_match_pos(text, ch.start_pattern, search_start=curr_pos)
        if pos == -1:
            # 降级：从 0 开始搜索
            pos = find_first_match_pos(text, ch.start_pattern, search_start=0)
        if pos == -1:
            print(f"  [WARN] 未匹配到章节: {ch.filename} (模式: {ch.start_pattern})")
            positions.append(-1)
        else:
            positions.append(pos)
            curr_pos = pos + 1

    # 拆分内容并写入文件
    for i, ch in enumerate(chapters):
        start_idx = positions[i]
        if start_idx == -1:
            continue
        
        # 寻找下一个有效章节的起始位置作为当前章节的结束位置
        end_idx = len(text)
        for j in range(i + 1, len(chapters)):
            if positions[j] != -1 and positions[j] > start_idx:
                end_idx = positions[j]
                break

        ch_content = text[start_idx:end_idx].strip()
        
        # 扫描并迁移本章引用的图片
        img_refs = re.findall(r"!\[([^\]]*)\]\((assets/[^)]+)\)", ch_content)
        for alt_text, img_rel_path in img_refs:
            src_img = (source_assets_dir / img_rel_path.replace("assets/", "")).resolve()
            if not src_img.exists():
                src_img = (source_assets_dir.parent / img_rel_path).resolve()
            if src_img.exists():
                dest_img = target_dir / img_rel_path
                dest_img.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_img, dest_img)

        target_file = target_dir / ch.filename
        target_file.write_text(ch_content + "\n", encoding="utf-8")
        print(f"  [OK] 写入: {target_file.relative_to(target_dir.parent.parent)} ({len(ch_content)} 字符, {len(img_refs)} 张图片)")


# =========================================================================
# 8 本书籍的章节定义与构建逻辑
# =========================================================================

def build_operating_system(base_out: Path, ocr_root: Path):
    """1. 操作系统"""
    print("\n>>> 处理: 操作系统")
    src_md = ocr_root / "408/操作系统_数学OCR/王道2027操作系统-高清带书签.md"
    src_assets = ocr_root / "408/操作系统_数学OCR/assets"
    out_dir = base_out / "操作系统"
    
    chapters = [
        ChapterDef("第01章_计算机系统概述.md", "第01章 计算机系统概述", r"(?m)^#+\s*第\s*1\s*章"),
        ChapterDef("第02章_进程与线程.md", "第02章 进程与线程", r"(?m)^#+\s*2\.1\s+进程与线程简介"),
        ChapterDef("第03章_内存管理.md", "第03章 内存管理", r"(?m)^#+\s*3\.1\s+内存管理概念"),
        ChapterDef("第04章_文件管理.md", "第04章 文件管理", r"(?m)^#+\s*4\.1\s+文件系统基础"),
        ChapterDef("第05章_输入输出管理.md", "第05章 输入输出管理", r"(?m)^#+\s*5\.1\s+I/O\s*管理概述"),
    ]
    split_book_by_patterns(src_md, src_assets, out_dir, chapters)


def build_data_structures(base_out: Path, ocr_root: Path):
    """2. 数据结构"""
    print("\n>>> 处理: 数据结构")
    src_md = ocr_root / "408/数据结构_数学OCR/27王道《数据结构》高清带书签【公众号：研料库，料最全】(1).md"
    src_assets = ocr_root / "408/数据结构_数学OCR/assets"
    out_dir = base_out / "数据结构"
    
    chapters = [
        ChapterDef("第01章_绪论.md", "第01章 绪论", r"(?m)^#+\s*1\.1\s+数据结构的基本概念"),
        ChapterDef("第02章_线性表.md", "第02章 线性表", r"(?m)^#+\s*2\.1\s+线性表的定义和基本操作"),
        ChapterDef("第03章_栈_队列和数组.md", "第03章 栈、队列和数组", r"(?m)^#+\s*第\s*3\s*章"),
        ChapterDef("第04章_串.md", "第04章 串", r"(?m)^#+\s*(?:第\s*4\s*章|4\.1\s+串的定义|4\.2\s+串的模式匹配)"),
        ChapterDef("第05章_树与二叉树.md", "第05章 树与二叉树", r"(?m)^#+\s*第\s*5\s*章"),
        ChapterDef("第06章_图.md", "第06章 图", r"(?m)^#+\s*6\.1\s+图的基本概念"),
        ChapterDef("第07章_查找.md", "第07章 查找", r"(?m)^#+\s*第\s*7\s*章"),
        ChapterDef("第08章_排序.md", "第08章 排序", r"(?m)^#+\s*第\s*8\s*章"),
    ]
    split_book_by_patterns(src_md, src_assets, out_dir, chapters)


def build_computer_organization(base_out: Path, ocr_root: Path):
    """3. 计算机组成原理"""
    print("\n>>> 处理: 计算机组成原理")
    src_md = ocr_root / "408/计组_数学OCR/2027计算机组成原理_高清带书签版.md"
    src_assets = ocr_root / "408/计组_数学OCR/assets"
    out_dir = base_out / "计算机组成原理"
    
    chapters = [
        ChapterDef("第01章_计算机系统概述.md", "第01章 计算机系统概述", r"(?m)^#+\s*1\.1(?:\.1)?\s+计算机硬件的发展"),
        ChapterDef("第02章_数据的表示和运算.md", "第02章 数据的表示和运算", r"(?m)^#+\s*第\s*2\s*章"),
        ChapterDef("第03章_存储系统.md", "第03章 存储系统", r"(?m)^#+\s*第\s*3\s*章"),
        ChapterDef("第04章_指令系统.md", "第04章 指令系统", r"(?m)^#+\s*第\s*4\s*章"),
        ChapterDef("第05章_中央处理器.md", "第05章 中央处理器", r"(?m)^#+\s*5\.1\s+CPU\s*的功能和基本结构"),
        ChapterDef("第06章_总线.md", "第06章 总线", r"(?m)^#+\s*6\.1\s+总线概述"),
        ChapterDef("第07章_输入输出系统.md", "第07章 输入输出系统", r"(?m)^#+\s*(?:第\s*7\s*章|7\.1\s+|7\.2\s+I/O\s*接口)"),
    ]
    split_book_by_patterns(src_md, src_assets, out_dir, chapters)


def build_computer_networks(base_out: Path, ocr_root: Path):
    """4. 计算机网络"""
    print("\n>>> 处理: 计算机网络")
    src_md = ocr_root / "408/计网_数学OCR/27王道《计算机网络》高清带书签【公众号：研料库，料最全】.md"
    src_assets = ocr_root / "408/计网_数学OCR/assets"
    out_dir = base_out / "计算机网络"
    
    chapters = [
        ChapterDef("第01章_计算机网络体系结构.md", "第01章 计算机网络体系结构", r"(?m)^#+\s*第\s*1\s*章"),
        ChapterDef("第02章_物理层.md", "第02章 物理层", r"(?m)^#+\s*第\s*2\s*章"),
        ChapterDef("第03章_数据链路层.md", "第03章 数据链路层", r"(?m)^#+\s*3\.1\s+数据链路层的功能"),
        ChapterDef("第04章_网络层.md", "第04章 网络层", r"(?m)^#+\s*4\.1\s+网络层的功能"),
        ChapterDef("第05章_传输层.md", "第05章 传输层", r"(?m)^#+\s*5\.1\s+传输层提供的服务"),
        ChapterDef("第06章_应用层.md", "第06章 应用层", r"(?m)^#+\s*6\.1\s+网络应用模型"),
    ]
    split_book_by_patterns(src_md, src_assets, out_dir, chapters)


def build_linear_algebra_basic(base_out: Path, ocr_root: Path):
    """5. 线性代数 (基础篇)"""
    print("\n>>> 处理: 线性代数 (基础篇)")
    src_md = ocr_root / "线代（基础）_数学OCR/线代（基础）.md"
    src_assets = ocr_root / "线代（基础）_数学OCR/assets"
    out_dir = base_out / "线性代数" / "01_基础篇"

    chapters = [
        ChapterDef("第01章_行列式.md", "第01章 行列式", r"(?m)^#+\s*第一章\s+行列式"),
        ChapterDef("第02章_矩阵.md", "第02章 矩阵", r"(?m)^#+\s*第二章\s+矩阵"),
        ChapterDef("第03章_向量.md", "第03章 向量", r"(?m)^#+\s*第三章\s+向量"),
        ChapterDef("第04章_线性方程组.md", "第04章 线性方程组", r"(?m)^#+\s*第四章\s+线性方程组"),
        ChapterDef("第05章_特征值和特征向量.md", "第05章 特征值和特征向量", r"(?m)^#+\s*第五章\s+特征值和特征向量"),
        ChapterDef("第06章_二次型.md", "第06章 二次型", r"(?m)^#+\s*第六章\s+二次型"),
    ]
    split_book_by_patterns(src_md, src_assets, out_dir, chapters)


def build_linear_algebra_advanced(base_out: Path, ocr_root: Path):
    """6. 线性代数 (强化篇)"""
    print("\n>>> 处理: 线性代数 (强化篇)")
    src_md = ocr_root / "线代（强化）_数学OCR/线代（强化）.md"
    src_assets = ocr_root / "线代（强化）_数学OCR/assets"
    out_dir = base_out / "线性代数" / "02_强化篇"
    
    chapters = [
        ChapterDef("第01章_行列式.md", "第01章 行列式", r"(?m)^#+\s*第一章\s+行列式[—\-]每一章都有应用"),
        ChapterDef("第02章_矩阵.md", "第02章 矩阵", r"(?m)^#+\s*第二章\s+矩阵"),
        ChapterDef("第03章_n维向量.md", "第03章 n维向量", r"(?m)^#+\s*第三章\s+n\s*维向量"),
        ChapterDef("第04章_线性方程组.md", "第04章 线性方程组", r"(?m)^#+\s*第四章\s+线性方程组"),
        ChapterDef("第05章_特征值和特征向量.md", "第05章 特征值和特征向量", r"(?m)^#+\s*第五章\s+特征值和特征向量"),
        ChapterDef("第06章_二次型.md", "第06章 二次型", r"(?m)^#+\s*第六章\s+二次型"),
        ChapterDef("附录_45分钟水平测试.md", "附录 45分钟水平测试", r"(?m)^#+\s*附录\s*45\s*分钟水平测试"),
    ]
    split_book_by_patterns(src_md, src_assets, out_dir, chapters)


def build_probability(base_out: Path, ocr_root: Path):
    """7. 概率论与数理统计 (基础篇 + 强化篇)"""
    print("\n>>> 处理: 概率论与数理统计")
    src_md = ocr_root / "概率统计_数学OCR/01.27考研数学-概率论与数理统计-辅导讲义-基础强化一本通【数一二三通用.md"
    src_assets = ocr_root / "概率统计_数学OCR/assets"
    text = src_md.read_text(encoding="utf-8")

    m_ch1 = list(re.finditer(r"(?m)^#+\s*第一章\s+随机事件和概率", text))
    basic_end_pos = m_ch1[1].start() if len(m_ch1) > 1 else len(text) // 2

    # 基础篇
    out_basic = base_out / "概率论与数理统计" / "01_基础篇"
    basic_chapters = [
        ChapterDef("第01章_随机事件和概率.md", "第01章 随机事件和概率", r"(?m)^#+\s*第一章\s+随机事件和概率"),
        ChapterDef("第02章_一维随机变量及其分布.md", "第02章 一维随机变量及其分布", r"(?m)^#+\s*第二章\s+一维随机变量及其分布"),
        ChapterDef("第03章_多维随机变量及其分布.md", "第03章 多维随机变量及其分布", r"(?m)^#+\s*第三章\s+多维随机变量及其分布"),
        ChapterDef("第04章_随机变量的数字特征.md", "第04章 随机变量的数字特征", r"(?m)^#+\s*第四章\s+数字特征"),
        ChapterDef("第05章_大数定律和中心极限定理.md", "第05章 大数定律和中心极限定理", r"(?m)^#+\s*第五章\s+大数定律和中心极限定理"),
        ChapterDef("第06章_数理统计的基本概念.md", "第06章 数理统计的基本概念", r"(?m)^#+\s*第六章\s+数理统计的基本概念"),
        ChapterDef("第07章_参数估计.md", "第07章 参数估计与假设检验", r"(?m)^#+\s*第七章\s+参数估计与假设检验"),
    ]
    
    basic_text = text[:basic_end_pos]
    adv_text = text[basic_end_pos:]
    
    tmp_basic = src_md.parent / "_tmp_basic.md"
    tmp_adv = src_md.parent / "_tmp_adv.md"
    tmp_basic.write_text(basic_text, encoding="utf-8")
    tmp_adv.write_text(adv_text, encoding="utf-8")

    split_book_by_patterns(tmp_basic, src_assets, out_basic, basic_chapters)

    # 强化篇
    out_adv = base_out / "概率论与数理统计" / "02_强化篇"
    adv_chapters = [
        ChapterDef("第01章_随机事件和概率.md", "第01章 随机事件和概率", r"(?m)^#+\s*第一章\s+随机事件和概率"),
        ChapterDef("第02章_一维随机变量及其分布.md", "第02章 一维随机变量及其分布", r"(?m)^#+\s*第二章\s+一维随机变量及其分布"),
        ChapterDef("第03章_多维随机变量及其分布.md", "第03章 多维随机变量及其分布", r"(?m)^#+\s*第三章\s+多维随机变量及其分布"),
        ChapterDef("第04章_随机变量的数字特征.md", "第04章 随机变量的数字特征", r"(?m)^#+\s*第四章\s+数字特征"),
        ChapterDef("第05章_大数定律和中心极限定理.md", "第05章 大数定律和中心极限定理", r"(?m)^#+\s*第五章\s+大数定律和中心极限定理"),
        ChapterDef("第06章_数理统计的基本概念.md", "第06章 数理统计的基本概念", r"(?m)^#+\s*第六章\s+数理统计的基本概念"),
        ChapterDef("第07章_参数估计.md", "第07章 参数估计与假设检验", r"(?m)^#+\s*第七章\s+参数估计与假设检验"),
    ]
    split_book_by_patterns(tmp_adv, src_assets, out_adv, adv_chapters)

    tmp_basic.unlink(missing_ok=True)
    tmp_adv.unlink(missing_ok=True)


def build_gaoshu(base_out: Path, ocr_root: Path):
    """8. 高等数学 (高数18讲)"""
    print("\n>>> 处理: 高等数学 (高数18讲)")
    src_md = ocr_root / "高数18讲_数学OCR/高数18讲.md"
    src_assets = ocr_root / "高数18讲_数学OCR/assets"
    out_dir = base_out / "高等数学" / "01_强化篇"

    chapters = [
        ChapterDef("第01讲_函数极限与连续.md", "第01讲 函数极限与连续", r"(?m)^##\s*第1讲"),
        ChapterDef("第02讲_数列极限.md", "第02讲 数列极限", r"证明数列极限的存在性"),
        ChapterDef("第03讲_一元函数微分学的概念.md", "第03讲 一元函数微分学的概念", r"一元函数微分学的概念</td>"),
        ChapterDef("第04讲_一元函数微分学的计算.md", "第04讲 一元函数微分学的计算", r"(?m)^#\s*第4讲"),
        ChapterDef("第05讲_一元函数微分学的应用_一__几何应用.md", "第05讲 一元函数微分学的应用(一)", r"(?m)^##\s*第5讲"),
        ChapterDef("第06讲_一元函数微分学的应用_二__中值定理_微分等式与微分不等式.md", "第06讲 一元函数微分学的应用(二)", r"(?m)^##\s*第6讲"),
        ChapterDef("第07讲_一元函数微分学的应用_三__物理应用与经济应用.md", "第07讲 一元函数微分学的应用(三)", r"(?m)^##\s*第7讲"),
        ChapterDef("第08讲_一元函数积分学的概念与性质.md", "第08讲 一元函数积分学的概念与性质", r"(?m)^##\s*第8讲"),
        ChapterDef("第09讲_一元函数积分学的计算.md", "第09讲 一元函数积分学的计算", r"(?m)^##\s*第9讲"),
        ChapterDef("第10讲_一元函数积分学的应用_一__几何应用.md", "第10讲 一元函数积分学的应用(一)", r"(?m)^##\s*第10讲"),
        ChapterDef("第11讲_一元函数积分学的应用_二__积分等式与积分不等式.md", "第11讲 一元函数积分学的应用(二)", r"(?m)^##\s*第11讲"),
        ChapterDef("第12讲_一元函数积分学的应用_三__物理应用与经济应用.md", "第12讲 一元函数积分学的应用(三)", r"(?m)^##\s*第12讲"),
        ChapterDef("第13讲_多元函数微分学.md", "第13讲 多元函数微分学", r"(?m)^##\s*第13讲"),
        ChapterDef("第14讲_二重积分.md", "第14讲 二重积分", r"二重积分</td>"),
        ChapterDef("第15讲_微分方程.md", "第15讲 微分方程", r"微分方程、一阶线性微分方程"),
        ChapterDef("第16讲_无穷级数.md", "第16讲 无穷级数", r"叫作无穷级数，简称级数"),
        ChapterDef("第17讲_多元函数积分学的预备知识.md", "第17讲 多元函数积分学的预备知识", r"(?m)^##\s*第17讲"),
        ChapterDef("第18讲_多元函数积分学.md", "第18讲 多元函数积分学", r"(?m)^##\s*第18讲"),
        ChapterDef("附录_1_图像变换.md", "附录 1 图像变换", r"图像变换方式一般有如下三种"),
        ChapterDef("附录_2_常用平面图形.md", "附录 2 常用平面图形", r"\(1\)心形线（外摆线的一种）"),
        ChapterDef("附录_3_常用空间图形.md", "附录 3 常用空间图形", r"(?m)^##\s*附录3"),
        ChapterDef("附录_4_重要公式.md", "附录 4 重要公式", r"(?m)^##\s*附录4"),
        ChapterDef("附录_5_从指数函数到双曲函数.md", "附录 5 从指数函数到双曲函数", r"指数函数 \$y = \\mathrm\{e\}\^\{-x\}"),
        ChapterDef("附录_6_变形技巧.md", "附录 6 变形技巧", r"(?m)^##\s*附录6"),
    ]
    split_book_by_patterns(src_md, src_assets, out_dir, chapters)


def main():
    base_out = Path("讲义")
    if Path("系统文件/临时OCR归档").exists():
        ocr_root = Path("系统文件/临时OCR归档")
    else:
        ocr_root = Path(".")
    print("==================================================")
    print("开始生成全学科独立标准化《讲义》...")
    print(f"OCR 数据源: {ocr_root.resolve()}")
    print(f"目标目录: {base_out.resolve()}")
    print("==================================================")

    build_operating_system(base_out, ocr_root)
    build_data_structures(base_out, ocr_root)
    build_computer_organization(base_out, ocr_root)
    build_computer_networks(base_out, ocr_root)
    build_linear_algebra_basic(base_out, ocr_root)
    build_linear_algebra_advanced(base_out, ocr_root)
    build_probability(base_out, ocr_root)
    build_gaoshu(base_out, ocr_root)

    print("\n==================================================")
    print("全学科《讲义》章节化排布构建完成！")
    print("==================================================")


if __name__ == "__main__":
    main()
