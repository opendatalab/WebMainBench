# 域名分布统计工具使用说明

## 概述

`domain_stats.py` 是一个专门用于统计WebMainBench数据集中域名分布的工具。它可以帮助你分析：

- 域名的分布情况
- TLD（顶级域名）的分布
- 域名与内容类型的关系
- TLD与语言的关系

## 快速开始

### 基本使用

```bash
python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl
```

### 指定输出目录

```bash
python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl \
  --output-dir results/my_domain_analysis
```

## 输入数据格式

脚本需要JSONL格式的输入文件，每行一个JSON对象：

```json
{
  "track_id": "xxx",
  "url": "https://example.com/page",
  "html": "...",
  "main_html": "...",
  "convert_main_content": "...",
  "meta": {
    "language": "en",
    "table": [],
    "code": [],
    "equation": [],
    "level": "simple",
    "style": "Article"
  }
}
```

## 输出文件

脚本会在指定的输出目录生成以下文件：

### 1. domain_statistics.csv

**完整的域名统计表格**，包含每个域名的详细信息：

| 字段 | 说明 |
|------|------|
| Domain | 域名 |
| Sample_Count | 该域名的样本数量 |
| Percentage | 占总样本的百分比 |
| Top_Language | 该域名最常见的语言 |
| Top_Style | 该域名最常见的网页风格 |
| Top_Level | 该域名最常见的复杂度级别 |
| Has_Table | 包含表格的样本数 |
| Has_Code | 包含代码的样本数 |
| Has_Equation | 包含公式的样本数 |

**示例：**
```csv
Domain,Sample_Count,Percentage,Top_Language,Top_Style,Top_Level,Has_Table,Has_Code,Has_Equation
aniruddhadeb.com,39,0.49%,en,Article,mid,11,9,36
politics.stackexchange.com,30,0.38%,en,Forum_or_Article_with_commentsection,mid,10,0,0
```

### 2. tld_statistics.csv

**TLD分布统计表格**：

```csv
TLD,Count,Percentage
com,4550,57.69%
org,816,10.35%
cn,459,5.82%
```

### 3. unique_domains.txt

**所有独立域名的列表**（每行一个域名，按字母顺序排序）：

```
aniruddhadeb.com
en.wikipedia.org
money.cnn.com
...
```

### 4. domain_stats.json

**JSON格式的统计摘要**，包含：

```json
{
  "summary": {
    "total_samples": 7887,
    "unique_domains": 5945,
    "unique_tlds": 150
  },
  "tld_distribution": {
    "com": 4550,
    "org": 816,
    ...
  },
  "top_50_domains": {
    "aniruddhadeb.com": 39,
    "politics.stackexchange.com": 30,
    ...
  }
}
```

## 统计结果示例

基于 `WebMainBench_7887_with_meta.jsonl` 的统计结果：

### 📊 基本统计

- **总样本数**: 7,887
- **独立域名数**: 5,945
- **平均每域名样本数**: 1.33
- **只有1个样本的域名**: 4,828 (81.2%)

### 🌐 TLD分布 (Top 10)

| TLD | 数量 | 占比 |
|-----|------|------|
| .com | 4,550 | 57.69% |
| .org | 816 | 10.35% |
| .cn | 459 | 5.82% |
| .net | 318 | 4.03% |
| .uk | 235 | 2.98% |
| .edu | 180 | 2.28% |
| .de | 101 | 1.28% |
| .au | 94 | 1.19% |
| .ru | 69 | 0.87% |
| .gov | 59 | 0.75% |

### 🏆 Top 10 域名

| 域名 | 样本数 | 占比 |
|------|--------|------|
| aniruddhadeb.com | 39 | 0.49% |
| politics.stackexchange.com | 30 | 0.38% |
| www.ask.com | 29 | 0.37% |
| en.wikipedia.org | 27 | 0.34% |
| www.china.org.cn | 23 | 0.29% |
| money.cnn.com | 22 | 0.28% |
| data.epo.org | 21 | 0.27% |
| m.weibo.cn | 19 | 0.24% |
| spanish.china.org.cn | 15 | 0.19% |
| china.org.cn | 14 | 0.18% |

### 📑 内容类型分布

- **包含表格的域名**: 2,876 个
- **包含代码的域名**: 406 个
- **包含公式的域名**: 148 个

**包含表格最多的域名 (Top 5):**
1. data.epo.org - 21个样本
2. www.china.org.cn - 21个样本
3. en.wikipedia.org - 20个样本
4. money.cnn.com - 18个样本
5. spanish.china.org.cn - 14个样本

**包含代码最多的域名 (Top 5):**
1. aniruddhadeb.com - 9个样本
2. oca.weizmann.ac.il - 6个样本
3. elitetvstream.com - 6个样本
4. www.economagic.com - 5个样本
5. studylibfr.com - 5个样本

**包含公式最多的域名 (Top 5):**
1. aniruddhadeb.com - 36个样本
2. www.esaral.com - 8个样本
3. www.layoutready.com - 8个样本
4. eng.libretexts.org - 8个样本
5. money.cnn.com - 7个样本

### 🌍 TLD与语言关系

**主要TLD的语言分布：**

| TLD | 主要语言 | 占比 |
|-----|----------|------|
| .com | 英文 | 90.3% |
| .org | 英文 | 96.8% |
| .cn | 中文 | 66.0% |
| .net | 英文 | 86.8% |
| .uk | 英文 | 99.1% |
| .edu | 英文 | 98.9% |

## 使用场景

### 1. 数据集质量评估

```bash
# 分析域名多样性
python scripts/domain_stats.py data/dataset.jsonl

# 查看是否有域名过度集中的问题
head -20 results/domain_statistics.csv
```

### 2. 内容类型分析

查看哪些域名包含特定类型的内容（表格、代码、公式），帮助：
- 理解数据集的内容分布
- 识别专业性网站（如教育、技术类）
- 评估基准测试的覆盖范围

### 3. 语言多样性评估

通过TLD与语言的关系分析：
- 验证数据集的国际化程度
- 识别特定地区的网站集中度
- 评估语言标注的准确性

### 4. 与Common Crawl集成

导出的域名列表可用于查询Common Crawl图数据：

```bash
# 获取域名列表
python scripts/domain_stats.py data/dataset.jsonl

# 使用域名列表查询CC图（如果有对应工具）
# 分析域名的PageRank、流量等级等
```

## 进阶使用

### 筛选特定TLD

```bash
# 统计后，用grep筛选特定TLD
grep "\.edu" results/domain_analysis/domain_statistics.csv
```

### 分析高频域名

```bash
# 查看样本数>=10的域名
awk -F',' '$2 >= 10' results/domain_analysis/domain_statistics.csv
```

### 统计域名分类

```python
import pandas as pd

# 读取统计结果
df = pd.read_csv('results/domain_analysis/domain_statistics.csv')

# 按风格分组统计
style_counts = df.groupby('Top_Style').agg({
    'Domain': 'count',
    'Sample_Count': 'sum'
})
print(style_counts)
```

## 常见问题

### Q1: 为什么有些域名的样本数特别多？

**A:** 这可能表明：
- 数据采集过程中对某些网站采样较多
- 某些网站内容丰富，适合作为测试样本
- 需要检查是否存在数据偏倚

### Q2: 如何判断域名分布是否合理？

**A:** 可以参考以下指标：
- **单样本域名占比**: 理想情况下应该较高（如>80%），表示域名多样性好
- **Top域名占比**: 最大域名的样本数不应超过总样本的5%
- **TLD多样性**: 应包含多种国家和地区的TLD

### Q3: CSV文件太大怎么办？

**A:** 可以只查看前几行或使用编程方式处理：

```bash
# 查看前100行
head -100 results/domain_analysis/domain_statistics.csv

# 或使用pandas
python -c "import pandas as pd; df = pd.read_csv('results/domain_analysis/domain_statistics.csv'); print(df.head(50))"
```

## 输出示例

运行脚本后，终端会显示：

```
============================================================
1. 基本统计
============================================================
总样本数: 7887
独立域名数: 5945
平均每域名样本数: 1.33

每域名样本数统计:
  最小值: 1
  最大值: 39
  平均值: 1.33
  中位数: 1

只有1个样本的域名: 4828 (81.2%)

============================================================
2. 顶级域名(TLD)分布
============================================================

总共 150 种TLD

  .com        4550 (57.69%) ████████████████████████████
  .org         816 (10.35%) █████
  .cn          459 ( 5.82%) ██
  ...

[更多统计信息...]
```

## 技术细节

### 域名提取

使用Python的`urlparse`从URL中提取域名：

```python
from urllib.parse import urlparse

url = "https://www.example.com/path"
domain = urlparse(url).netloc  # 结果: www.example.com
```

### TLD提取

简单地提取域名最后一个点后的部分：

```python
domain = "www.example.com"
tld = domain.split('.')[-1]  # 结果: com
```

### Meta信息聚合

对每个域名，统计其所有样本的meta信息：
- 语言分布（Counter）
- 风格分布（Counter）
- 复杂度分布（Counter）
- 特殊内容计数（表格、代码、公式）

## 更新日志

### 2024-11-18
- ✅ 创建初始版本
- ✅ 支持基本域名统计
- ✅ 支持TLD分布分析
- ✅ 支持内容类型分析
- ✅ 支持语言-TLD关联分析
- ✅ 生成多种格式输出（CSV, JSON, TXT）

---

*文档由WebMainBench团队维护*

