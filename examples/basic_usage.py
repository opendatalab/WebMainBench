#!/usr/bin/env python3
"""
WebMainBench Basic Usage Example
"""

import json
from pathlib import Path

# Import WebMainBench modules
from webmainbench import (
    DataLoader, DataSaver, BenchmarkDataset, DataSample,
    ExtractorFactory, Evaluator, 
    format_results, setup_logging
)


def create_sample_dataset():
    """Create a sample dataset"""

    # Create sample data - includes multiple content types (code, formulas, tables, etc.)
    samples = [
        {
            "track_id": "sample-001-programming-tutorial",
            "html": '''<html><body>
                <h1 cc-select="true">Python编程教程</h1>
                <p cc-select="true">这是一个Python基础教程，展示如何定义函数。</p>
                <pre cc-select="true"><code>def greet(name):
    """问候函数"""
    return f"Hello, {name}!"

# 使用示例
result = greet("World")
print(result)</code></pre>
                <p cc-select="true">这个函数可以用来问候任何人。</p>
            </body></html>''',
            "groundtruth_content": '''# Python编程教程

这是一个Python基础教程，展示如何定义函数。

```python
def greet(name):
    """问候函数"""
    return f"Hello, {name}!"

# 使用示例
result = greet("World")
print(result)
```

这个函数可以用来问候任何人。''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "Python编程教程", "level": 1},
                {"type": "paragraph", "content": "这是一个Python基础教程，展示如何定义函数。"},
                {"type": "code", "content": 'def greet(name):\n    """问候函数"""\n    return f"Hello, {name}!"\n\n# 使用示例\nresult = greet("World")\nprint(result)'},
                {"type": "paragraph", "content": "这个函数可以用来问候任何人。"}
            ],
            "url": "https://python-tutorial.example.com/functions",
            "layout_id": "python-tutorial_1",
            "max_layer_n": 8,
            "url_host_name": "python-tutorial.example.com",
            "raw_warc_path": "s3://cc-raw-tutorials/crawl-data/CC-MAIN-2025-13/segments/1742004433093.21/warc/tutorial-001.warc.gz",
            "language": "en",
            "__dom_depth": 12,
            "__dom_width": 5240,
            "__type": "__programming_tutorial",
            "__tag": "CODE_CONTENT",
            "marked_type": "normal",
            "content_type": "programming"
        },
        {
            "track_id": "sample-002-math-formulas",
            "html": '''<html><body>
                <h1 cc-select="true">数学公式示例</h1>
                <p cc-select="true">这里展示一些基本的数学公式。</p>
                <p cc-select="true">勾股定理：a² + b² = c²</p>
                <div cc-select="true" class="formula">
                    <p>二次方程的解为：</p>
                    <p>x = (-b ± √(b² - 4ac)) / 2a</p>
                </div>
                <p cc-select="true">欧拉公式是数学中最美丽的公式之一：e^(iπ) + 1 = 0</p>
                <table cc-select="true">
                    <tr><th>函数</th><th>导数</th></tr>
                    <tr><td>x²</td><td>2x</td></tr>
                    <tr><td>sin(x)</td><td>cos(x)</td></tr>
                </table>
            </body></html>''',
            "groundtruth_content": '''# 数学公式示例

这里展示一些基本的数学公式。

勾股定理：$a^2 + b^2 = c^2$

二次方程的解为：

$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

欧拉公式是数学中最美丽的公式之一：$e^{i\\pi} + 1 = 0$

| 函数 | 导数 |
|------|------|
| x² | 2x |
| sin(x) | cos(x) |''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "数学公式示例", "level": 1},
                {"type": "paragraph", "content": "这里展示一些基本的数学公式。"},
                {"type": "paragraph", "content": "勾股定理：a² + b² = c²"},
                {"type": "paragraph", "content": "二次方程的解为："},
                {"type": "equation-interline", "content": "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}"},
                {"type": "paragraph", "content": "欧拉公式是数学中最美丽的公式之一：e^(iπ) + 1 = 0"},
                {"type": "table", "content": "| 函数 | 导数 |\n|------|------|\n| x² | 2x |\n| sin(x) | cos(x) |"}
            ],
            "url": "https://math-examples.edu/formulas",
            "layout_id": "math-examples_2",
            "max_layer_n": 10,
            "url_host_name": "math-examples.edu",
            "raw_warc_path": "s3://cc-raw-academic/crawl-data/CC-MAIN-2025-13/segments/1742004433093.21/warc/math-002.warc.gz",
            "language": "zh",
            "__dom_depth": 15,
            "__dom_width": 6850,
            "__type": "__academic_content",
            "__tag": "FORMULA_TABLE",
            "marked_type": "normal",
            "content_type": "academic"
        },
        {
            "track_id": "sample-003-data-analysis",
            "html": '''<html><body>
                <h1 cc-select="true">数据分析报告</h1>
                <p cc-select="true">以下是2024年第一季度的销售数据分析。</p>
                <h2 cc-select="true">数据处理代码</h2>
                <pre cc-select="true"><code>import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv('sales_q1_2024.csv')

# 计算统计信息
monthly_avg = df.groupby('month')['sales'].mean()
print(f"平均销售额: {monthly_avg}")</code></pre>
                <h2 cc-select="true">销售统计</h2>
                <table cc-select="true">
                    <tr><th>月份</th><th>销售额(万元)</th><th>增长率</th></tr>
                    <tr><td>1月</td><td>120.5</td><td>+15.2%</td></tr>
                    <tr><td>2月</td><td>135.8</td><td>+12.7%</td></tr>
                    <tr><td>3月</td><td>148.3</td><td>+9.2%</td></tr>
                </table>
                <p cc-select="true">标准差公式：σ = √(Σ(xi - μ)² / n)</p>
                <p cc-select="true">总体来看，第一季度销售表现良好，呈现稳定增长趋势。</p>
            </body></html>''',
            "groundtruth_content": '''# 数据分析报告

以下是2024年第一季度的销售数据分析。

## 数据处理代码

```python
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv('sales_q1_2024.csv')

# 计算统计信息
monthly_avg = df.groupby('month')['sales'].mean()
print(f"平均销售额: {monthly_avg}")
```

## 销售统计

| 月份 | 销售额(万元) | 增长率 |
|------|-------------|--------|
| 1月 | 120.5 | +15.2% |
| 2月 | 135.8 | +12.7% |
| 3月 | 148.3 | +9.2% |

标准差公式：$\\sigma = \\sqrt{\\frac{\\Sigma(x_i - \\mu)^2}{n}}$

总体来看，第一季度销售表现良好，呈现稳定增长趋势。''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "数据分析报告", "level": 1},
                {"type": "paragraph", "content": "以下是2024年第一季度的销售数据分析。"},
                {"type": "heading", "content": "数据处理代码", "level": 2},
                {"type": "code", "content": "import pandas as pd\nimport numpy as np\n\n# 读取数据\ndf = pd.read_csv('sales_q1_2024.csv')\n\n# 计算统计信息\nmonthly_avg = df.groupby('month')['sales'].mean()\nprint(f\"平均销售额: {monthly_avg}\")"},
                {"type": "heading", "content": "销售统计", "level": 2},
                {"type": "table", "content": "| 月份 | 销售额(万元) | 增长率 |\n|------|-------------|--------|\n| 1月 | 120.5 | +15.2% |\n| 2月 | 135.8 | +12.7% |\n| 3月 | 148.3 | +9.2% |"},
                {"type": "paragraph", "content": "标准差公式：σ = √(Σ(xi - μ)² / n)"},
                {"type": "paragraph", "content": "总体来看，第一季度销售表现良好，呈现稳定增长趋势。"}
            ],
            "url": "https://data-report.company.com/q1-2024-analysis",
            "layout_id": "data-report_3",
            "max_layer_n": 12,
            "url_host_name": "data-report.company.com",
            "raw_warc_path": "s3://cc-raw-business/crawl-data/CC-MAIN-2025-13/segments/1742004433093.21/warc/analysis-003.warc.gz",
            "language": "zh",
            "__dom_depth": 18,
            "__dom_width": 8420,
            "__type": "__business_report",
            "__tag": "MIXED_CONTENT",
            "marked_type": "normal",
            "content_type": "business"
        },
        {
            "track_id": "sample-004-algorithm-explanation",
            "html": '''<html><body>
                <h1 cc-select="true">算法复杂度分析</h1>
                <p cc-select="true">这里介绍常见算法的时间复杂度。</p>
                <h2 cc-select="true">快速排序实现</h2>
                <pre cc-select="true"><code>def quicksort(arr):
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)</code></pre>
                <h2 cc-select="true">复杂度对比</h2>
                <table cc-select="true">
                    <tr><th>算法</th><th>最好情况</th><th>平均情况</th><th>最坏情况</th></tr>
                    <tr><td>快速排序</td><td>O(n log n)</td><td>O(n log n)</td><td>O(n²)</td></tr>
                    <tr><td>归并排序</td><td>O(n log n)</td><td>O(n log n)</td><td>O(n log n)</td></tr>
                    <tr><td>冒泡排序</td><td>O(n)</td><td>O(n²)</td><td>O(n²)</td></tr>
                </table>
                <p cc-select="true">Master定理：T(n) = aT(n/b) + f(n)</p>
                <p cc-select="true">其中 a ≥ 1, b > 1 是常数，f(n) 是正函数。</p>
            </body></html>''',
            "groundtruth_content": '''# 算法复杂度分析

这里介绍常见算法的时间复杂度。

## 快速排序实现

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)
```

## 复杂度对比

| 算法 | 最好情况 | 平均情况 | 最坏情况 |
|------|----------|----------|----------|
| 快速排序 | O(n log n) | O(n log n) | O(n²) |
| 归并排序 | O(n log n) | O(n log n) | O(n log n) |
| 冒泡排序 | O(n) | O(n²) | O(n²) |

Master定理：$T(n) = aT(n/b) + f(n)$

其中 $a \\geq 1, b > 1$ 是常数，$f(n)$ 是正函数。''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "算法复杂度分析", "level": 1},
                {"type": "paragraph", "content": "这里介绍常见算法的时间复杂度。"},
                {"type": "heading", "content": "快速排序实现", "level": 2},
                {"type": "code", "content": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    \n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    \n    return quicksort(left) + middle + quicksort(right)"},
                {"type": "heading", "content": "复杂度对比", "level": 2},
                {"type": "table", "content": "| 算法 | 最好情况 | 平均情况 | 最坏情况 |\n|------|----------|----------|----------|\n| 快速排序 | O(n log n) | O(n log n) | O(n²) |\n| 归并排序 | O(n log n) | O(n log n) | O(n log n) |\n| 冒泡排序 | O(n) | O(n²) | O(n²) |"},
                {"type": "equation-inline", "content": "T(n) = aT(n/b) + f(n)"},
                {"type": "paragraph", "content": "其中 a ≥ 1, b > 1 是常数，f(n) 是正函数。"}
            ],
            "url": "https://algorithm-guide.cs.edu/complexity-analysis",
            "layout_id": "algorithm-guide_4",
            "max_layer_n": 14,
            "url_host_name": "algorithm-guide.cs.edu",
            "raw_warc_path": "s3://cc-raw-computer-science/crawl-data/CC-MAIN-2025-13/segments/1742004433093.21/warc/algo-004.warc.gz",
            "language": "zh",
            "__dom_depth": 16,
            "__dom_width": 7320,
            "__type": "__computer_science",
            "__tag": "ALGORITHM_CONTENT",
            "marked_type": "normal",
            "content_type": "computer_science"
        }
    ]
    
    # Create dataset
    dataset = BenchmarkDataset(name="sample_dataset", description="Sample evaluation dataset")
    
    for sample_data in samples:
        sample = DataSample.from_dict(sample_data)
        dataset.add_sample(sample)
    
    return dataset


def demo_basic_mock_evaluation():
    """Demonstrate the basic evaluation workflow"""

    print("=== WebMainBench Basic Usage Example ===\n")

    # Set up logging
    setup_logging(level="INFO")

    # 1. Create or load dataset
    print("1. Creating sample dataset...")
    dataset = create_sample_dataset()
    print(f"Dataset contains {len(dataset)} samples")
    print(f"Dataset statistics: {dataset.get_statistics()}\n")

    # 2. Save dataset to file
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    dataset_path = data_dir / "sample_dataset.jsonl"
    DataSaver.save_jsonl(dataset, dataset_path, include_results=False)
    print(f"Dataset saved to: {dataset_path}\n")

    # 3. Reload dataset
    print("2. Reloading dataset...")
    loaded_dataset = DataLoader.load_jsonl(dataset_path)
    print(f"Loaded dataset contains {len(loaded_dataset)} samples\n")

    # 4. List available extractors
    print("3. Available extractors:")
    available_extractors = ExtractorFactory.list_available()
    for extractor_name in available_extractors:
        print(f"  - {extractor_name}")
    print()

    # 5. Create evaluator
    print("4. Creating evaluator...")
    evaluator = Evaluator()
    print(f"Available evaluation metrics: {evaluator.metric_calculator.list_available_metrics()}\n")

    # 6. Create a mock extractor for demonstration
    print("5. Creating mock extractor...")

    from webmainbench.extractors import BaseExtractor, ExtractionResult

    class MockExtractor(BaseExtractor):
        """Mock extractor for demonstration"""

        def _setup(self):
            pass

        def _extract_content(self, html, url=None):
            # Simple mock extraction logic
            if "heading" in html.lower() or "title" in html.lower():
                content = "# Extracted Title\n\nExtracted body content."
                content_list = [
                    {"type": "heading", "content": "Extracted Title", "level": 1},
                    {"type": "paragraph", "content": "Extracted body content."}
                ]
            else:
                content = "Extracted content"
                content_list = [{"type": "paragraph", "content": "Extracted content"}]

            return ExtractionResult(
                content=content,
                content_list=content_list,
                success=True,
                confidence_score=0.85
            )

    # Register mock extractor
    ExtractorFactory.register("mock", MockExtractor)
    mock_extractor = ExtractorFactory.create("mock")
    print("Mock extractor created\n")

    # 7. Run evaluation
    print("6. Running evaluation...")
    result = evaluator.evaluate(
        dataset=loaded_dataset,
        extractor=mock_extractor,
        max_samples=2  # Limit sample count for demonstration
    )

    # 8. Display results
    print("\n7. Evaluation results:")
    print("=" * 50)
    formatted_results = format_results(result.to_dict())
    print(formatted_results)

    # 9. Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    results_path = results_dir / "mock_evaluation_results.json"
    DataSaver.save_evaluation_results(result, results_path)
    print(f"\nResults saved to: {results_path}")

    # 10. Generate report
    report_path = results_dir / "mock_evaluation_report.csv"
    DataSaver.save_summary_report(result, report_path)
    print(f"Report saved to: {report_path}")


def demo_llm_webkit_evaluation():
    """Demonstrate 6-metric evaluation with LLM-WebKit extractor"""

    print("=== LLM-WebKit Extractor 6-Metric Evaluation Example ===\n")

    # Set up logging
    setup_logging(level="INFO")

    # 1. Create test dataset with various content types
    print("1. Creating test dataset with multiple content types...")

    samples = []

    # Sample 1: text and code
    samples.append(DataSample(
        id="text_code_sample",
        html="""
        <html>
        <body>
            <h1>Python编程示例</h1>
            <p>这是一段关于Python编程的介绍文本。</p>
            <pre><code>
def hello_world():
    print("Hello, World!")
    return True
            </code></pre>
            <p>以上代码展示了一个简单的Python函数。</p>
        </body>
        </html>
        """,
        groundtruth_content="""# Python编程示例

这是一段关于Python编程的介绍文本。

```python
def hello_world():
    print("Hello, World!")
    return True
```

以上代码展示了一个简单的Python函数。""",
        groundtruth_content_list=[
            {"type": "heading", "content": "Python编程示例", "level": 1},
            {"type": "text", "content": "这是一段关于Python编程的介绍文本。"},
            {"type": "code", "content": "def hello_world():\n    print(\"Hello, World!\")\n    return True", "language": "python"},
            {"type": "text", "content": "以上代码展示了一个简单的Python函数。"}
        ]
    ))

    # 样本2: 包含表格
    samples.append(DataSample(
        id="table_sample",
        html="""
        <html>
        <body>
            <h2>销售数据统计</h2>
            <table>
                <thead>
                    <tr>
                        <th>产品</th>
                        <th>销量</th>
                        <th>收入</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>产品A</td>
                        <td>100</td>
                        <td>1000</td>
                    </tr>
                    <tr>
                        <td>产品B</td>
                        <td>200</td>
                        <td>3000</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """,
        groundtruth_content="""## 销售数据统计

| 产品 | 销量 | 收入 |
|------|------|------|
| 产品A | 100 | 1000 |
| 产品B | 200 | 3000 |""",
        groundtruth_content_list=[
            {"type": "heading", "content": "销售数据统计", "level": 2},
            {"type": "table", "content": "| 产品 | 销量 | 收入 |\n|------|------|------|\n| 产品A | 100 | 1000 |\n| 产品B | 200 | 3000 |"}
        ]
    ))

    # 样本3: 包含公式
    samples.append(DataSample(
        id="formula_sample",
        html="""
        <html>
        <body>
            <h2>数学公式示例</h2>
            <p>这是一个行内公式: $E = mc^2$</p>
            <p>这是一个行间公式:</p>
            <div>$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$</div>
        </body>
        </html>
        """,
        groundtruth_content="""## 数学公式示例

这是一个行内公式: $E = mc^2$

这是一个行间公式:

$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$""",
        groundtruth_content_list=[
            {"type": "heading", "content": "数学公式示例", "level": 2},
            {"type": "text", "content": "这是一个行内公式: $E = mc^2$"},
            {"type": "text", "content": "这是一个行间公式:"},
            {"type": "formula", "content": "\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}"}
        ]
    ))

    # Create dataset and add samples
    dataset = BenchmarkDataset(name="llm_webkit_test", description="LLM-WebKit 6-metric test dataset")
    for sample in samples:
        dataset.add_sample(sample)

    print(f"Test dataset contains {len(dataset)} samples")
    print(f"Sample types: text+code, table, formula\n")

    # 2. Create LLM-WebKit extractor
    print("2. Creating LLM-WebKit extractor...")

    # Show all available extractors
    available_extractors = ExtractorFactory.list_available()
    print(f"Available extractors: {available_extractors}")

    # Create LLM-WebKit extractor directly with model path
    config = {
        "model_path": "/Users/chupei/model/checkpoint-3296"
    }
    extractor = ExtractorFactory.create("llm-webkit", config=config)
    print(f"LLM-WebKit extractor created successfully, model path: {config['model_path']}")

    print()

    # 3. Create evaluator and show all available metrics
    print("3. Creating evaluator...")
    evaluator = Evaluator()
    available_metrics = evaluator.metric_calculator.list_available_metrics()
    print(f"Available evaluation metrics ({len(available_metrics)} total):")

    # Display by the 6 metric categories
    target_metrics = ["overall", "text_edit", "code_edit", "table_edit", "table_TEDS", "formula_edit"]

    for metric in target_metrics:
        if metric in available_metrics:
            print(f"  {metric}")
        else:
            print(f"  {metric} (not registered)")

    print()

    # 4. Run evaluation
    print("4. Starting evaluation...")
    print("=" * 60)

    result = evaluator.evaluate(
        dataset=dataset,
        extractor=extractor,
        max_samples=None  # Evaluate all samples
    )

    # 5. Display detailed 6-metric results
    print("\n5. 6-metric detailed evaluation results:")
    print("=" * 60)

    results_dict = result.to_dict()

    # Extract metric results from overall_metrics
    metrics = results_dict.get('overall_metrics', {})

    # Display by metric category
    print(f"\nOverall metrics:")
    if 'overall' in metrics:
        print(f"  overall (combined score): {metrics['overall']:.4f}")
    else:
        print("  overall: not calculated")

    print(f"\nText-related metrics:")
    if 'text_edit' in metrics:
        print(f"  text_edit (text edit distance): {metrics['text_edit']:.4f}")
    else:
        print("  text_edit: not calculated")
    if 'code_edit' in metrics:
        print(f"  code_edit (code edit distance): {metrics['code_edit']:.4f}")
    else:
        print("  code_edit: not calculated")

    print(f"\nTable-related metrics:")
    if 'table_edit' in metrics:
        print(f"  table_edit (table edit distance): {metrics['table_edit']:.4f}")
    else:
        print("  table_edit: not calculated")
    if 'table_TEDS' in metrics:
        print(f"  table_TEDS (table structure similarity): {metrics['table_TEDS']:.4f}")
    else:
        print("  table_TEDS: not calculated")

    print(f"\nFormula-related metrics:")
    if 'formula_edit' in metrics:
        print(f"  formula_edit (formula edit distance): {metrics['formula_edit']:.4f}")
    else:
        print("  formula_edit: not calculated")

    print(f"\nDetailed statistics:")
    print(f"  Total samples: {len(dataset)}")
    success_count = len([s for s in results_dict.get('sample_results', []) if s.get('extraction_success', False)])
    failure_count = len(dataset) - success_count
    print(f"  Successful samples: {success_count}")
    print(f"  Failed samples: {failure_count}")

    # 6. Save results to file
    print("\n" + "=" * 60)
    print("6. Saving evaluation results...")

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Save detailed results
    results_path = results_dir / "llm_webkit_evaluation_results.json"
    DataSaver.save_evaluation_results(result, results_path)  # Pass result object directly
    print(f"Detailed results saved to: {results_path}")

    # Generate CSV report
    report_path = results_dir / "llm_webkit_evaluation_report.csv"
    DataSaver.save_summary_report(result, report_path)  # Pass result object directly
    print(f"CSV report saved to: {report_path}")

    print("\n" + "=" * 60)
    print("LLM-WebKit 6-metric evaluation complete!")


def demo_dataset_with_extraction():
    """Demonstrate saving a dataset with extracted content"""
    print("=== Demo: Saving a Dataset with Extracted Content ===")

    from webmainbench import DataLoader, DataSaver, Evaluator, ExtractorFactory
    from pathlib import Path

    # Configure file paths
    data_dir = Path("data")
    dataset_path = data_dir / "sample_dataset.jsonl"
    # dataset_path = "/Users/chupei/Downloads/WebMainBench_dataset_merge_2549.jsonl"

    print(f"Dataset file: {dataset_path}")

    # Create llm-webkit extractor (used uniformly)
    extractor_config = {"model_path": "/Users/chupei/model/checkpoint-3296"}
    extractor = ExtractorFactory.create("llm-webkit", config=extractor_config)
    print(f"Using extractor: {extractor.name}")

    # Create evaluator
    evaluator = Evaluator()

    # Choose evaluation mode: in-memory mode vs batched mode
    USE_BATCHED_MODE = True  # Set to True to use batched mode (suitable for large datasets)

    if USE_BATCHED_MODE:
        print("Using batched mode (memory-optimized)")

        # Batched evaluation (suitable for large datasets)
        result = evaluator.evaluate_batched(
            jsonl_file_path=dataset_path,
            extractor=extractor,  # Pass extractor object directly
            batch_size=10,        # Small batch size
            max_samples=20        # For demonstration
        )
        print(f"Batched evaluation complete, overall score: {result.overall_metrics.get('overall', 0):.4f}")

        # To save the dataset with extraction content, reload the original dataset temporarily
        # Note: this is only a brief load for saving and does not affect the memory-optimized evaluation above
        dataset = DataLoader.load_jsonl(dataset_path, include_results=False)
        dataset.name = result.dataset_name

    else:
        print("Using traditional in-memory mode")

        # Load dataset from file
        print(f"Loading dataset from file: {dataset_path}")
        dataset = DataLoader.load_jsonl(dataset_path, include_results=False)
        dataset.name = "WebMainBench_with_extraction"
        dataset.description = "Test dataset demonstrating extraction content saving"

        print(f"Dataset loaded, contains {len(dataset.samples)} samples")

        # Run evaluation
        result = evaluator.evaluate(dataset, extractor)

    print(f"Evaluation complete, overall score: {result.overall_metrics.get('overall', 0):.4f}")

    # Save dataset with extracted content
    results_dir = Path("results")
    enriched_dataset_path = results_dir / f"{dataset.name}_with_{extractor.name}_extraction.jsonl"

    DataSaver.save_dataset_with_extraction(
        results=result,
        dataset=dataset,
        file_path=enriched_dataset_path,
        extractor_name=extractor.name
    )

    print(f"Dataset with extracted content saved to: {enriched_dataset_path}")

    # Save evaluation results and summary report
    evaluation_results_path = results_dir / f"{dataset.name}_{extractor.name}_evaluation_results.json"
    summary_report_path = results_dir / f"{dataset.name}_{extractor.name}_evaluation_report.csv"

    DataSaver.save_evaluation_results(result, evaluation_results_path)
    DataSaver.save_summary_report(result, summary_report_path)

    print(f"Evaluation results saved to: {evaluation_results_path}")
    print(f"Summary report saved to: {summary_report_path}")

    # Display saved field info
    print("\nNewly saved fields include:")
    print(f"  - {extractor.name}_content: extracted content")
    print(f"  - {extractor.name}_content_list: extracted structured content list")
    print(f"  - {extractor.name}_success: whether extraction succeeded")
    print(f"  - {extractor.name}_time: extraction time")
    print(f"  - {extractor.name}_*_score: metric scores")


def demo_multi_extraction():
    """Demonstrate saving a dataset with content from multiple extractors (supports batched mode)"""
    print("=== Demo: Saving a Dataset with Multiple Extractor Results ===")

    from webmainbench import DataLoader, DataSaver, Evaluator, ExtractorFactory
    from pathlib import Path
    import time

    # Set up logging
    setup_logging(level="INFO")

    # Configure file paths
    data_dir = Path("../data")
    # dataset_path = data_dir / "sample_dataset.jsonl"
    dataset_path = "/home/lulindong/Pycharm_projects/cc/WebMainBench_1904_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl"

    print(f"Dataset file: {dataset_path}")

    # Define list of extractors and their configurations
    extractors_info = [
        {"name": "resiliparse", "config": {
            "main_content": True,
            "alt_texts": True,
            "links": False,
            "list_bullets": True,
            "preserve_formatting": True
        }},
        {"name": "trafilatura", "config": {}},
        {"name": "magic-html", "config": {}},
    ]

    # Choose evaluation mode: in-memory mode vs batched mode
    USE_BATCHED_MODE = True  # Recommended True for large datasets
    BATCH_SIZE = 10  # Batch size
    MAX_SAMPLES = None  # For demonstration (set None for full evaluation)

    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Store evaluation results and performance data for all extractors
    all_results = []
    extractor_performance = []

    # Run evaluation for each extractor
    for info in extractors_info:
        extractor_name = info["name"]
        config = info["config"]

        try:
            # Create extractor instance
            extractor = ExtractorFactory.create(extractor_name, config=config)
            print(f"\nUsing extractor: {extractor.name}")
        except Exception as e:
            print(f"Failed to create extractor {extractor_name}: {e}")
            continue

        # Record total elapsed time
        start_time = time.time()

        # Initialize evaluator
        evaluator = Evaluator()

        # Choose batched or traditional mode
        if USE_BATCHED_MODE:
            print(f"Using batched mode (batch size: {BATCH_SIZE}, max samples: {MAX_SAMPLES or 'all'})")
            # Batched evaluation (memory-optimized)
            result = evaluator.evaluate_batched(
                jsonl_file_path=dataset_path,
                extractor=extractor,
                batch_size=BATCH_SIZE,
                max_samples=MAX_SAMPLES
            )
            # Temporarily load original data for saving (does not affect memory-optimized evaluation)
            dataset = DataLoader.load_jsonl(dataset_path, include_results=False, max_samples=MAX_SAMPLES)
            dataset.name = result.dataset_name
        else:
            print("Using traditional in-memory mode")
            # Load full dataset into memory
            dataset = DataLoader.load_jsonl(dataset_path, include_results=False, max_samples=MAX_SAMPLES)
            dataset.name = "WebMainBench_with_multi_extraction"
            dataset.description = "Multi-extractor content saving demo dataset"
            print(f"Dataset loaded, contains {len(dataset.samples)} samples")

            # Traditional mode evaluation
            result = evaluator.evaluate(dataset, extractor)

        # Calculate elapsed time metrics
        total_time = time.time() - start_time
        total_samples = len(dataset.samples)
        avg_time_per_sample = total_time / total_samples if total_samples else 0

        # Save performance data
        extractor_performance.append({
            "name": extractor_name,
            "total_samples": total_samples,
            "total_time": total_time,
            "avg_time_per_sample": avg_time_per_sample
        })

        # Output evaluation results
        print(f"Total time: {total_time:.4f}s (avg per sample: {avg_time_per_sample:.4f}s)")
        print(f"Core metrics:")
        print(f"   code_edit: {result.overall_metrics.get('code_edit', 0):.4f}")
        print(f"   formula_edit: {result.overall_metrics.get('formula_edit', 0):.4f}")
        print(f"   table_TEDS: {result.overall_metrics.get('table_TEDS', 0):.4f}")
        print(f"   table_edit: {result.overall_metrics.get('table_edit', 0):.4f}")
        print(f"   text_edit: {result.overall_metrics.get('text_edit', 0):.4f}")
        print(f"Overall score: {result.overall_metrics.get('overall', 0):.4f}")

        all_results.append(result)

        # Save dataset with current extractor's content
        enriched_dataset_path = results_dir / f"{dataset.name}_{extractor.name}_extraction_infer.jsonl"
        DataSaver.save_dataset_with_extraction(
            results=result,
            dataset=dataset,
            file_path=enriched_dataset_path,
            extractor_name=extractor.name
        )
        print(f"Extracted content saved to: {enriched_dataset_path}")

        # Save individual extractor evaluation results
        eval_results_path = results_dir / f"{dataset.name}_{extractor.name}_evaluation_results.json"
        DataSaver.save_evaluation_results(result, eval_results_path)
        print(f"Evaluation results saved to: {eval_results_path}")

    # Save summary report for all extractors
    if all_results:
        summary_path = results_dir / f"{dataset.name}_multi_extractors_summary_report.csv"
        DataSaver.save_summary_report(all_results, summary_path)
        print(f"\nSummary report saved to: {summary_path}")

    # Display performance comparison
    if extractor_performance:
        print("\nExtractor performance comparison:")
        for perf in extractor_performance:
            print(f"  {perf['name']}:")
            print(f"    Samples: {perf['total_samples']}")
            print(f"    Total time: {perf['total_time']:.4f}s")
            print(f"    Time per sample: {perf['avg_time_per_sample']:.4f}s")
            print(f"    Throughput: {1 / perf['avg_time_per_sample']:.2f} samples/s")

    # Display saved field information
    print("\nSaved new field descriptions:")
    for info in extractors_info:
        name = info["name"]
        print(f"  {name} related fields:")
        print(f"    - {name}_content: extracted raw content")
        print(f"    - {name}_content_list: structured content list (with type field)")
        print(f"    - {name}_success: whether extraction succeeded (boolean)")
        print(f"    - {name}_time: per-sample extraction time (seconds)")
        print(f"    - {name}_*_score: metric scores (e.g. {name}_text_edit)")


def demo_llm_webkit_with_preprocessed_html_evaluation():
    """Demonstrate evaluation of LLM-WebKit preprocessed HTML feature"""

    print("\n=== LLM-WebKit Preprocessed HTML Feature Demo ===\n")

    # Set up logging
    setup_logging(level="INFO")

    # 1. Load preprocessed HTML data from the real dataset
    print("1. Loading preprocessed HTML data from the real dataset...")
    dataset_path = Path("data/track_id_diff_result_56.jsonl")
    print(f"Dataset file: {dataset_path}")

    # Load dataset
    dataset = DataLoader.load_jsonl(dataset_path, include_results=False)
    dataset.name = "real_preprocessed_html_test"
    dataset.description = "Preprocessed HTML feature test based on real data"

    print(f"Real dataset loaded successfully, contains {len(dataset)} samples")
    print("Real data samples include:")
    print("  - html: raw web page HTML")
    print("  - llm_webkit_html: LLM-preprocessed simplified HTML (with _item_id markers)")
    print("  - groundtruth_content: manually annotated ground truth")
    print("  - llm_webkit_md: LLM-extracted markdown content")


    # 2. Create LLM-WebKit extractor in preprocessed HTML mode
    print("2. Creating LLM-WebKit extractor in preprocessed HTML mode...")

    config = {
        "use_preprocessed_html": True,          # Key config: enable preprocessed HTML mode
        "preprocessed_html_field": "llm_webkit_html"  # Specify preprocessed HTML field name
    }

    extractor = ExtractorFactory.create("llm-webkit", config=config)

    # 4. Run evaluation
    print("4. Starting evaluation...")
    print("=" * 50)

    evaluator = Evaluator()
    result = evaluator.evaluate(
        dataset=dataset,
        extractor=extractor,
        max_samples=None
    )

    # 5. Display evaluation results
    print("\n5. Preprocessed HTML mode evaluation results:")
    print("=" * 50)

    results_dict = result.to_dict()
    metrics = results_dict.get('overall_metrics', {})

    # Display key metrics
    print(f"\nOverall metrics:")
    print(f"  overall: {metrics.get('overall', 0):.4f}")

    print(f"\nContent extraction quality:")
    print(f"  text_edit: {metrics.get('text_edit', 0):.4f}")
    print(f"  code_edit: {metrics.get('code_edit', 0):.4f}")
    print(f"  table_edit: {metrics.get('table_edit', 0):.4f}")
    print(f"  table_TEDS: {metrics.get('table_TEDS', 0):.4f}")

    print(f"\nPerformance statistics:")
    sample_results = results_dict.get('sample_results', [])
    if sample_results:
        extraction_times = [s.get('extraction_time', 0) for s in sample_results if s.get('extraction_success')]
        if extraction_times:
            avg_time = sum(extraction_times) / len(extraction_times)
            print(f"  Average extraction time: {avg_time:.3f}s")
            print(f"  Processing speed: {1/avg_time:.1f} samples/s")

    success_count = len([s for s in sample_results if s.get('extraction_success', False)])
    print(f"  Successful samples: {success_count}/{len(dataset)}")

    # 7. Save results
    print(f"\n7. Saving evaluation results...")

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    # Save enhanced dataset with extraction results (JSONL format)
    jsonl_dataset_path = results_dir / f"{extractor.name}_preprocessed_html_dataset_with_results.jsonl"
    DataSaver.save_dataset_with_extraction(
        results=result,
        dataset=dataset,  # Original dataset object
        file_path=jsonl_dataset_path,
        extractor_name="llm-webkit"  # Extractor name prefix
    )
    print(f"JSONL dataset with extraction results saved to: {jsonl_dataset_path}")
    results_path = results_dir / f"{extractor.name}_preprocessed_html_evaluation_results.json"
    report_path = results_dir / f"{extractor.name}_preprocessed_html_evaluation_report.csv"

    DataSaver.save_evaluation_results(result, results_path)
    DataSaver.save_summary_report(result, report_path)

    print(f"Detailed results saved to: {results_path}")
    print(f"CSV report saved to: {report_path}")
    


if __name__ == "__main__":
    try:
        # demo_basic_mock_evaluation()
        # demo_llm_webkit_evaluation()  # LLM-WebKit evaluation example
        demo_llm_webkit_with_preprocessed_html_evaluation()
        # demo_extractor_comparison()
        # demo_dataset_with_extraction()  # Demo saving dataset with extracted content
        # demo_multi_extraction() # Demo evaluating with multiple extractors simultaneously
        print("\nExample completed!")

    except Exception as e:
        print(f"\nRuntime error: {e}")
        import traceback
        traceback.print_exc() 