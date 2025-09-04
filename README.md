# WebMainBench

WebMainBench 是一个专门用于端到端评测网页正文抽取质量的基准测试工具。

## 功能特点

### 🎯 **核心功能**
- **多抽取器支持**: 支持 LLM-WebKit、Jina AI 等多种抽取工具
- **全面的评测指标**: 包含文本编辑距离、表格结构相似度(TEDS)、公式抽取质量等多维度指标
- **人工标注支持**: 评测数据集100%人工标注

#### 指标详细说明

| 指标名称 | 计算方式 | 取值范围 | 说明 |
|---------|----------|----------|------|
| `overall` | 所有成功指标的平均值 | 0.0-1.0 | 综合质量评分，分数越高质量越好 |
| `text_edit` | `1 - (编辑距离 / 最大文本长度)` | 0.0-1.0 | 纯文本相似度，分数越高质量越好 |
| `code_edit` | `1 - (编辑距离 / 最大代码长度)` | 0.0-1.0 | 代码内容相似度，分数越高质量越好 |
| `table_TEDS` | `1 - (树编辑距离 / 最大节点数)` | 0.0-1.0 | 表格结构相似度，分数越高质量越好 |
| `table_edit` | `1 - (编辑距离 / 最大表格长度)` | 0.0-1.0 | 表格内容相似度，分数越高质量越好 |
| `formula_edit` | `1 - (编辑距离 / 最大公式长度)` | 0.0-1.0 | 公式内容相似度，分数越高质量越好 |


### 🏗️ **系统架构**

![WebMainBench Architecture](docs/assets/arch.png)

### 🔧 **核心模块**
1. **data 模块**: 评测集文件和结果的读写管理
2. **extractors 模块**: 各种抽取工具的统一接口
3. **metrics 模块**: 评测指标的计算实现
4. **evaluator 模块**: 评测任务的执行和结果输出


## 快速开始

### 安装

```bash
# 基础安装
pip install webmainbench

# 安装所有可选依赖
pip install webmainbench[all]

# 开发环境安装
pip install webmainbench[dev]
```

### 基本使用

```python
from webmainbench import DataLoader, Evaluator, ExtractorFactory

# 1. 加载评测数据集
dataset = DataLoader.load_jsonl("your_dataset.jsonl")

# 2. 创建抽取器
extractor = ExtractorFactory.create("llm-webkit")

# 3. 运行评测
evaluator = Evaluator()
result = evaluator.evaluate(dataset, extractor)

# 4. 查看结果
print(f"Overall Score: {result.overall_metrics['overall']:.4f}")
```

### 数据格式

评测数据集应包含以下字段：

```jsonl
{
  "track_id": "0b7f2636-d35f-40bf-9b7f-94be4bcbb396",
  "html": "<html><body><h1 cc-select=\"true\">这是标题</h1></body></html>",   # 人工标注带cc-select="true" 属性
  "url": "https://orderyourbooks.com/product-category/college-books-p-u/?products-per-page=all",
  "main_html": "<h1 cc-select=\"true\">这是标题</h1>",  # 从html中剪枝得到的正文html
  "convert_main_content": "# 这是标题",  # 从main_html+html2text转化来
  "groundtruth_content": "# 这是标题",  # 人工校准的markdown（部分提供）
  "meta": {
    "language": "en",  # 网页的语言
    "style": "artical",  # 网页的文体
    "DOM_WIDTH": 176,
    "DOM_DEPTH": 27,
    "text_linktext_ratio": 0.12252270850536746,
    "table_text_ratio": 0,
    "table_dom_depth": -1,
    "text_distribution_dispersion": 0.2663,
    "table": [],  # [], ["layout"], ["data"], ["layout", "data"]
    "equation": [],  # [], ["inline"], ["interline"], ["inline", "interline"]
    "code": [],  # [], ["inline"], ["interline"], ["inline", "interline"]
    "table_complexity_score": 0,
    "dom_complexity_score": 0.8442,
    "text_dispersion_score": 0.2663,
    "content_diversity_score": 0,
    "link_complexity_score": 0.1225,
    "overall_complexity_score": 0.3083,
    "level": "mid"  # simple, mid, hard
  }
}
```

## 支持的抽取器

- **LLM-WebKit**: 基于大语言模型的智能抽取
- **Jina AI**: Reader API 服务
- **自定义抽取器**: 通过继承 `BaseExtractor` 实现


## 高级功能

### 多抽取器对比评估

```python
# 对比多个抽取器
extractors = ["llm-webkit", "jina-ai"]
results = evaluator.compare_extractors(dataset, extractors)

for name, result in results.items():
    print(f"{name}: {result.overall_metrics['overall']:.4f}")
```

#### 具体示例

```python
python examples/multi_extractor_compare.py
```

这个例子演示了如何：

1. **加载测试数据集**：使用包含代码、公式、表格、文本等多种内容类型的样本数据
2. **创建多个抽取器**：
   - `llm-webkit`：支持预处理HTML的智能抽取器
   - `magic-html`：基于 magic-html 库的抽取器
   - `trafilatura`：基于 trafilatura 库的抽取器  
   - `resiliparse`：基于 resiliparse 库的抽取器
3. **批量评估对比**：使用 `evaluator.compare_extractors()` 同时评估所有抽取器
4. **生成对比报告**：自动保存多种格式的评估结果

#### 输出文件说明

评估完成后会在 `results/` 目录下生成三个重要文件：

| 文件名 | 格式 | 内容描述 |
|--------|------|----------|
| `leaderboard.csv` | CSV | **排行榜文件**：包含各抽取器的整体排名和分项指标对比，便于快速查看性能差异 |
| `evaluation_results.json` | JSON | **详细评估结果**：包含每个抽取器的完整评估数据、指标详情和元数据信息 |
| `dataset_with_results.jsonl` | JSONL | **增强数据集**：原始测试数据加上所有抽取器的提取结果，便于人工检查和分析 |


`leaderboard.csv` 内容示例：
```csv
extractor,dataset,total_samples,success_rate,overall,code_edit,formula_edit,table_TEDS,table_edit,text_edit
llm-webkit,sample_dataset,4,1.0,0.2196,0.5,0.0,0.0,0.0,0.5982
magic-html,sample_dataset,4,1.0,0.1526,0.1007,0.0,0.0,0.0,0.6624
resiliparse,sample_dataset,4,1.0,0.1379,0.0,0.0,0.0,0.0,0.6897
trafilatura,sample_dataset,4,1.0,0.1151,0.1007,0.0,0.0,0.0,0.4746
```

### 自定义指标

```python
from webmainbench.metrics import BaseMetric, MetricResult

class CustomMetric(BaseMetric):
    def _setup(self):
        pass
    
    def _calculate_score(self, predicted, groundtruth, **kwargs):
        # 实现自定义评测逻辑
        score = your_calculation(predicted, groundtruth)
        return MetricResult(
            metric_name=self.name,
            score=score,
            details={"custom_info": "value"}
        )

# 添加到评测器
evaluator.metric_calculator.add_metric("custom", CustomMetric("custom"))
```

### 自定义抽取器

```python
from webmainbench.extractors import BaseExtractor, ExtractionResult

class MyExtractor(BaseExtractor):
    def _setup(self):
        # 初始化抽取器
        pass
    
    def _extract_content(self, html, url=None):
        # 实现抽取逻辑
        content = your_extraction_logic(html)
        
        return ExtractionResult(
            content=content,
            content_list=[...],
            success=True
        )

# 注册自定义抽取器
ExtractorFactory.register("my-extractor", MyExtractor)
```

### 数据集统计分析工具

WebMainBench 提供了强大的数据集统计分析工具 `scripts/statics.py`，用于分析数据集的各种特征并自动生成复杂度评分和难易程度分类。

#### 功能特性

- **DOM结构分析**：计算网页DOM树的深度和宽度
- **文本链接比例分析**：统计文本与链接的比例关系
- **表格复杂度分析**：评估表格内容的复杂程度
- **内容类型检测**：自动识别公式、代码、表格等特殊内容
- **复杂度评分**：基于多维度指标计算综合复杂度得分
- **动态难易程度分类**：基于数据分布自动分类为 simple/mid/hard

#### 使用方法

```bash
# 基本用法
python scripts/statics.py data/input.jsonl --output data/output_with_stats.jsonl

# 使用默认数据集
python scripts/statics.py
```

#### 参数说明

```bash
# 查看所有可用参数
python scripts/statics.py --help

```

#### 输出结果

工具会在每条数据的 `meta` 字段中添加以下统计信息：

```json
{
  "meta": {
    "DOM_DEPTH": 25,                    // DOM树深度
    "DOM_WIDTH": 1200,                  // DOM树宽度
    "text_linktext_ratio": 0.85,        // 文本链接比例
    "table_complexity_score": 0.3,      // 表格复杂度得分
    "dom_complexity_score": 0.6,        // DOM复杂度得分
    "text_dispersion_score": 0.4,       // 文本分布得分
    "content_diversity_score": 0.7,     // 内容多样性得分
    "link_complexity_score": 0.5,       // 链接复杂度得分
    "overall_complexity_score": 0.52,   // 综合复杂度得分
    "level": "mid"                      // 难易程度 (simple/mid/hard)
  }
}
```

#### 复杂度评分算法

综合复杂度得分由以下维度加权计算：

- **DOM结构复杂度 (25%)**：基于DOM深度和宽度，使用动态归一化
- **文本分布复杂度 (25%)**：基于文本在DOM中的分布离散程度
- **内容多样性 (25%)**：基于公式、代码、表格等特殊内容的种类
- **链接复杂度 (25%)**：基于文本与链接的比例关系

#### 运行示例

```bash
# 分析数据集并生成统计报告
python scripts/statics.py data/sample_dataset.jsonl --output data/analyzed_dataset.jsonl

# 输出示例：
🔄 第一阶段: 计算基础统计和复杂度得分...
  📊 已处理 100 条数据...
  📊 已处理 200 条数据...

🔄 第二阶段: 计算动态阈值和难易程度分类...
📊 复杂度分布阈值计算:
   总样本数: 1,827
   30%分位数 (simple/mid分界): 0.3245
   70%分位数 (mid/hard分界): 0.6789
   复杂度得分范围: 0.0944 - 1.0000

📊 难易程度分类结果:
   Simple: 548 (30.0%)
   Mid:    731 (40.0%)  
   Hard:   548 (30.0%)

📝 正在写入数据到: data/analyzed_dataset.jsonl
✅ 成功写入 1,827 条数据
```


## 项目架构

```
webmainbench/
├── data/           # 数据处理模块
│   ├── dataset.py  # 数据集类
│   ├── loader.py   # 数据加载器
│   └── saver.py    # 数据保存器
├── extractors/     # 抽取器模块
│   ├── base.py     # 基础接口
│   ├── factory.py  # 工厂模式
│   └── ...         # 具体实现
├── metrics/        # 指标模块
│   ├── base.py     # 基础接口
│   ├── text_metrics.py    # 文本指标
│   ├── table_metrics.py   # 表格指标
│   └── calculator.py      # 指标计算器
├── evaluator/      # 评估器模块
│   └── evaluator.py       # 主评估器
└── utils/          # 工具模块
    └── helpers.py          # 辅助函数
```


## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
