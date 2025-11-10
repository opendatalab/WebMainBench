# Scripts 使用说明

本目录包含数据处理和分析的工具脚本。

## 📋 主要脚本

### 数据处理脚本

| 脚本 | 功能 | 添加字段 |
|------|------|----------|
| `statics.py` | 统计分析 | `meta.level`, `meta.table`, `meta.code`, `meta.equation` |
| `language_classify.py` | 语言检测 | `meta.language` |
| `style_classify.py` | 类型分类 | `meta.style` |
| `process_dataset.sh` | 一键处理 | 上述所有字段 |

### 数据管理脚本

| 脚本 | 功能 |
|------|------|
| `merge_jsonl.py` | 合并多个 JSONL 文件 |
| `filter_by_scores.py` | 按评分筛选数据 |
| `diff_jsonl.py` | 对比 JSONL 文件差异 |
| `add_raw_html_field.py` | 添加原始 HTML 字段 |
| `merge_meta_data.py` | 合并 meta 数据 |

### 分析脚本

| 脚本 | 功能 |
|------|------|
| `analyze_style_results.py` | 分析网页类型分布 |
| `quick_style_stats.py` | 快速统计网页类型 |

## 🚀 快速开始

### 方式一：一键处理（推荐）

```bash
# 赋予执行权限（仅首次需要）
chmod +x scripts/process_dataset.sh

# 执行处理，默认用的 gpt-5 model
./scripts/process_dataset.sh \
  data/sample_dataset_with_fields.jsonl \
  data/final_dataset.jsonl \
  YOUR_API_KEY \
  YOUR_BASE_URL
```

### 方式二：分步处理

```bash
# 步骤 1: 统计分析
python scripts/statics.py \
  --input data/input.jsonl \
  --output data/step1.jsonl

# 步骤 2: 语言检测
python scripts/language_classify.py \
  data/step1.jsonl \
  --output data/step2.jsonl \
  --api-key YOUR_API_KEY \
  --base-url https://api.deepseek.com/v1

# 步骤 3: 类型分类
python scripts/style_classify.py \
  data/step2.jsonl \
  --output data/final.jsonl \
  --api-key YOUR_API_KEY \
  --base-url https://api.deepseek.com/v1
```

## 🔑 环境变量

```bash
# 设置 API 密钥（推荐）
export OPENAI_API_KEY="your_api_key"

# 或在命令行中通过 --api-key 参数传递
```

## ⚙️ 常用参数

### statics.py

```bash
python scripts/statics.py --input <input_file> --output <output_file>
```

**无需 API 密钥**

### language_classify.py

```bash
python scripts/language_classify.py <input_file> \
  --output <output_file> \
  --api-key <api_key> \
  --base-url <base_url> \
  --batch-size <size>
```

**参数：**
- `--api-key`: API 密钥（必需）
- `--base-url`: API 地址（默认：`https://api.deepseek.com/v1`）
- `--batch-size`: 批处理大小（默认：100）

### style_classify.py

```bash
python scripts/style_classify.py <input_file> \
  --output <output_file> \
  --api-key <api_key> \
  --base-url <base_url> \
  --batch-size <size>
```

**参数：**
- `--api-key`: API 密钥（必需）
- `--base-url`: API 地址（必需）
- `--batch-size`: 批处理大小（默认：100）


## 🐛 故障排查

### 问题 1: API 调用失败

```bash
# 检查 API 密钥
echo $OPENAI_API_KEY

# 测试 API 连接
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 问题 2: 数据行数不匹配

```bash
# 检查文件行数
wc -l data/input.jsonl
wc -l data/output.jsonl

# 检查 JSON 格式
head -n 1 data/output.jsonl | python -m json.tool
```

### 问题 3: 脚本权限不足

```bash
# 赋予执行权限
chmod +x scripts/process_dataset.sh
chmod +x scripts/*.py
```


