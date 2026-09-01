# OCR 定向修复报告

- 状态：**仍有阻断项**
- Markdown 文件：6
- 已执行的精确修改：0
- 已附源 PDF 原页/裁图：15
- 阻断项：25
- 警告项：12

自动修复只处理方向唯一的勘误；没有唯一答案的式子不会被猜改。

## 运行说明

- 已读取复查报告：OCR质量抽查报告_线性代数基础学习册.md
- 源 PDF：线代（基础）.pdf

## 尚待处理/核对

| 级别 | 文件 | 行 | 类型 | 说明 | PDF 页范围 |
|---|---|---:|---|---|---|
| warning | `**/*.md` |  | `AUDIT_PATCH_TEXT_NOT_FOUND` | 复查报告补丁 AUDIT_L66_5cb9cd35 的错误原文未精确命中；可能已修好，也可能排版形式不同，需核对。 |  |
| warning | `**/*向量*.md` |  | `AUDIT_PATCH_TEXT_NOT_FOUND` | 复查报告补丁 AUDIT_L101_6997a242 的错误原文未精确命中；可能已修好，也可能排版形式不同，需核对。 |  |
| warning | `**/*特征值*.md` |  | `AUDIT_PATCH_TEXT_NOT_FOUND` | 复查报告补丁 AUDIT_L119_ebeabdcf 的错误原文未精确命中；可能已修好，也可能排版形式不同，需核对。 |  |
| warning | `**/*二次型*.md` |  | `AUDIT_PATCH_TEXT_NOT_FOUND` | 复查报告补丁 AUDIT_L130_c7f5ca05 的错误原文未精确命中；可能已修好，也可能排版形式不同，需核对。 |  |
| warning | `**/*二次型*.md` |  | `AUDIT_PATCH_TEXT_NOT_FOUND` | 复查报告补丁 AUDIT_L131_1a4120db 的错误原文未精确命中；可能已修好，也可能排版形式不同，需核对。 |  |
| warning | `**/*二次型*.md` |  | `AUDIT_PATCH_TEXT_NOT_FOUND` | 复查报告补丁 AUDIT_L133_a74a787f 的错误原文未精确命中；可能已修好，也可能排版形式不同，需核对。 |  |
| blocker | `第01章_行列式.md` | 246 | `MATRIX_COLUMN_MISMATCH` | vmatrix 各行列数不一致：[2, 1, 3, 1]。 |  |
| blocker | `第01章_行列式.md` | 246 | `MATRIX_COLUMN_MISMATCH` | vmatrix 各行列数不一致：[3, 2, 3, 2]。 |  |
| blocker | `第01章_行列式.md` | 322 | `MATRIX_COLUMN_MISMATCH` | vmatrix 各行列数不一致：[5, 5, 5, 5, 2]。 |  |
| warning | `第01章_行列式.md` |  | `NO_PDF_PAGE_TRACE` | 文件中没有 PDF 页码或页范围标记，发现错误后难以回到原页。 |  |
| blocker | `第02章_矩阵.md` | 610 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 1, 3, 3, 3]。 |  |
| blocker | `第02章_矩阵.md` | 831 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[6, 5, 5]。 |  |
| blocker | `第02章_矩阵.md` | 871 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[6, 6, 6, 6, 2]。 |  |
| blocker | `第02章_矩阵.md` | 1009 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 4, 4, 2]。 |  |
| blocker | `第02章_矩阵.md` | 1084 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 4, 3, 4, 4]。 |  |
| blocker | `第02章_矩阵.md` | 1084 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 4, 1, 4, 4]。 |  |
| blocker | `第02章_矩阵.md` | 749 | `QUESTION_PROMPT_MAY_BE_MISSING` | 例题标题后立即进入解答，题干可能整段漏失。 |  |
| warning | `第02章_矩阵.md` |  | `NO_PDF_PAGE_TRACE` | 文件中没有 PDF 页码或页范围标记，发现错误后难以回到原页。 |  |
| blocker | `第03章_向量.md` | 573 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 4, 3, 4]。 |  |
| blocker | `第03章_向量.md` | 573 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 4, 3, 4]。 |  |
| blocker | `第03章_向量.md` | 585 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 5, 5]。 |  |
| blocker | `第03章_向量.md` | 601 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[3, 4, 4]。 |  |
| blocker | `第03章_向量.md` | 899 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[3, 2, 2, 2, 3, 2, 2]。 |  |
| blocker | `第03章_向量.md` | 899 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[2, 3, 3, 2, 3]。 |  |
| blocker | `第03章_向量.md` | 903 | `QUESTION_PROMPT_MAY_BE_MISSING` | 例题标题后立即进入解答，题干可能整段漏失。 |  |
| warning | `第03章_向量.md` |  | `NO_PDF_PAGE_TRACE` | 文件中没有 PDF 页码或页范围标记，发现错误后难以回到原页。 |  |
| blocker | `第04章_线性方程组.md` | 370 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[7, 7, 7, 8]。 |  |
| blocker | `第04章_线性方程组.md` | 426 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[5, 5, 4]。 |  |
| blocker | `第04章_线性方程组.md` | 470 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[6, 7, 6, 7, 7]。 |  |
| blocker | `第04章_线性方程组.md` | 474 | `MATRIX_COLUMN_MISMATCH` | matrix 各行列数不一致：[5, 4, 4, 5, 5, 5, 5, 5]。 |  |
| blocker | `第04章_线性方程组.md` | 565 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[5, 6, 6]。 |  |
| blocker | `第04章_线性方程组.md` | 579 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 4, 4, 5]。 |  |
| blocker | `第04章_线性方程组.md` | 579 | `MATRIX_COLUMN_MISMATCH` | bmatrix 各行列数不一致：[4, 3, 4, 4]。 |  |
| warning | `第04章_线性方程组.md` |  | `NO_PDF_PAGE_TRACE` | 文件中没有 PDF 页码或页范围标记，发现错误后难以回到原页。 |  |
| blocker | `第05章_特征值和特征向量.md` | 605 | `MATRIX_COLUMN_MISMATCH` | matrix 各行列数不一致：[3, 4, 2, 3, 2]。 | 129-171 |
| warning | `第05章_特征值和特征向量.md` |  | `COARSE_PDF_TRACE_ONLY` | 只有分块页范围标记，最宽覆盖 43 页；尚不能逐页定位。 |  |
| warning | `第06章_二次型.md` |  | `NO_PDF_PAGE_TRACE` | 文件中没有 PDF 页码或页范围标记，发现错误后难以回到原页。 |  |

## 判断边界

- 结构检查通过，不等于每个数学符号都正确。
- 漏掉整块题干、矩阵或推导时，必须以 PDF 原图/裁图回退，不能靠正则重建。
- 报告未抽到的潜在语义错误，不会因为本次修复而自动消失。
