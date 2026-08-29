# 考研动态学习项目 - 脚本工具集中管理仓库

本目录集中收录与管理本项目所有自动化脚本与工程引擎，根目录下不再保留任何零散 `.py` 脚本文件。

---

## 目录与功能分类

### 📁 01_讲义提取与OCR (`01_讲义提取与OCR/`)
负责针对考研数学与 408 计算机教材 PDF 执行硬件加速 OCR 识别与增量缓存：
- `extract_gaoshu_18jiang.py`: 《高等数学》全自动提取与公式排版引擎
- `extract_liyongle_basic_linear_algebra.py`: 《线性代数》（基础篇）提取与标准化引擎
- `extract_liyongle_linear_algebra.py`: 《线性代数》（强化篇）提取与标准化引擎
- `extract_probability_book.py`: 《概率论与数理统计》（基础+强化）提取与双篇章生成引擎
- `extract_wangdao_operating_system.py`: 《操作系统》提取与 C 代码块化引擎
- `extract_wangdao_computer_organization.py`: 《计算机组成原理》提取与汇编/硬件参数引擎
- `extract_wangdao_data_structures.py`: 《数据结构》提取与 C/C++ 算法/结构体代码块引擎
- `extract_wangdao_computer_networks.py`: 《计算机网络》提取与网络协议/信道容量公式引擎

---

### 📁 02_格式化与排版 (`02_格式化与排版/`)
负责二次微调、板块重构与特定专业课（代码/选择题/Callout）排版：
- `format_wangdao_os_master.py`: 操作系统主格式化与代码高亮引擎
- `format_wangdao_co_master.py`: 计算机组成原理主格式化与原码/补码/浮点数引擎
- `format_wangdao_ds_master.py`: 数据结构主格式化与算法伪代码块引擎

---

### 📁 03_质量审计与数学引擎 (`03_质量审计与数学引擎/`)
负责全库 Markdown 语法校验、LaTeX 规范性检测与 0 裸 TeX 严格审计：
- `math_quality_engine.py`: 考研数学与专业课核心 LaTeX 语法修复与定界引擎
- `run_math_audit.py`: 全库 Markdown 讲义行级质量审计脚本
- `regenerate_all_books_math_grade.py`: 全套数学/专业课讲义一键批量重构与质量校验引擎

---

### 📁 04_题库与数据构建 (`04_题库与数据构建/`)
收录真题解析、各章节经典习题、选择题与综合大题的构建与转换历史脚本。

---

### 📁 05_标注与规范校验 (`05_标注与规范校验/`)
负责题目元数据标注、JSON Schema 结构校验、仓库规范审计与数据迁移：
- `validate_annotations.py`: 题目多级元数据标注与 Schema 规则校验引擎
- `validate_usage_roles.py`: 试卷与题目使用场景（训练/测试/诊断）角色校验
- `json_schema_runtime.py`: 轻量无依赖 JSON Schema 校验运行时
- `audit_repository.py`: 全库真题唯一编号（ID）、元数据完整性与图片引用审计引擎
- `migrate_l3_v1.py`: 历史标注数据向标准 Schema 格式迁移引擎

