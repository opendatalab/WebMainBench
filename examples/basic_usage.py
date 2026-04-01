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
                <h1 cc-select="true">Python Programming Tutorial</h1>
                <p cc-select="true">This is a basic Python tutorial demonstrating how to define functions.</p>
                <pre cc-select="true"><code>def greet(name):
    """Greeting function"""
    return f"Hello, {name}!"

# Usage example
result = greet("World")
print(result)</code></pre>
                <p cc-select="true">This function can be used to greet anyone.</p>
            </body></html>''',
            "groundtruth_content": '''# Python Programming Tutorial

This is a basic Python tutorial demonstrating how to define functions.

```python
def greet(name):
    """Greeting function"""
    return f"Hello, {name}!"

# Usage example
result = greet("World")
print(result)
```

This function can be used to greet anyone.''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "Python Programming Tutorial", "level": 1},
                {"type": "paragraph", "content": "This is a basic Python tutorial demonstrating how to define functions."},
                {"type": "code", "content": 'def greet(name):\n    """Greeting function"""\n    return f"Hello, {name}!"\n\n# Usage example\nresult = greet("World")\nprint(result)'},
                {"type": "paragraph", "content": "This function can be used to greet anyone."}
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
                <h1 cc-select="true">Math Formula Examples</h1>
                <p cc-select="true">Here are some basic math formulas.</p>
                <p cc-select="true">Pythagorean theorem: a² + b² = c²</p>
                <div cc-select="true" class="formula">
                    <p>The solution to the quadratic equation is:</p>
                    <p>x = (-b ± √(b² - 4ac)) / 2a</p>
                </div>
                <p cc-select="true">Euler's formula is one of the most beautiful formulas in mathematics: e^(iπ) + 1 = 0</p>
                <table cc-select="true">
                    <tr><th>Function</th><th>Derivative</th></tr>
                    <tr><td>x²</td><td>2x</td></tr>
                    <tr><td>sin(x)</td><td>cos(x)</td></tr>
                </table>
            </body></html>''',
            "groundtruth_content": '''# Math Formula Examples

Here are some basic math formulas.

Pythagorean theorem: $a^2 + b^2 = c^2$

The solution to the quadratic equation is:

$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

Euler's formula is one of the most beautiful formulas in mathematics: $e^{i\\pi} + 1 = 0$

| Function | Derivative |
|------|------|
| x² | 2x |
| sin(x) | cos(x) |''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "Math Formula Examples", "level": 1},
                {"type": "paragraph", "content": "Here are some basic math formulas."},
                {"type": "paragraph", "content": "Pythagorean theorem: a² + b² = c²"},
                {"type": "paragraph", "content": "The solution to the quadratic equation is:"},
                {"type": "equation-interline", "content": "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}"},
                {"type": "paragraph", "content": "Euler's formula is one of the most beautiful formulas in mathematics: e^(iπ) + 1 = 0"},
                {"type": "table", "content": "| Function | Derivative |\n|------|------|\n| x² | 2x |\n| sin(x) | cos(x) |"}
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
                <h1 cc-select="true">Data Analysis Report</h1>
                <p cc-select="true">The following is a sales data analysis for Q1 2024.</p>
                <h2 cc-select="true">Data Processing Code</h2>
                <pre cc-select="true"><code>import pandas as pd
import numpy as np

# Read data
df = pd.read_csv('sales_q1_2024.csv')

# Calculate statistics
monthly_avg = df.groupby('month')['sales'].mean()
print(f"Average sales: {monthly_avg}")</code></pre>
                <h2 cc-select="true">Sales Statistics</h2>
                <table cc-select="true">
                    <tr><th>Month</th><th>Sales (10k)</th><th>Growth Rate</th></tr>
                    <tr><td>Jan</td><td>120.5</td><td>+15.2%</td></tr>
                    <tr><td>Feb</td><td>135.8</td><td>+12.7%</td></tr>
                    <tr><td>Mar</td><td>148.3</td><td>+9.2%</td></tr>
                </table>
                <p cc-select="true">Standard deviation formula: σ = √(Σ(xi - μ)² / n)</p>
                <p cc-select="true">Overall, Q1 sales performance was strong, showing a steady growth trend.</p>
            </body></html>''',
            "groundtruth_content": '''# Data Analysis Report

The following is a sales data analysis for Q1 2024.

## Data Processing Code

```python
import pandas as pd
import numpy as np

# Read data
df = pd.read_csv('sales_q1_2024.csv')

# Calculate statistics
monthly_avg = df.groupby('month')['sales'].mean()
print(f"Average sales: {monthly_avg}")
```

## Sales Statistics

| Month | Sales (10k) | Growth Rate |
|------|-------------|--------|
| Jan | 120.5 | +15.2% |
| Feb | 135.8 | +12.7% |
| Mar | 148.3 | +9.2% |

Standard deviation formula: $\\sigma = \\sqrt{\\frac{\\Sigma(x_i - \\mu)^2}{n}}$

Overall, Q1 sales performance was strong, showing a steady growth trend.''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "Data Analysis Report", "level": 1},
                {"type": "paragraph", "content": "The following is a sales data analysis for Q1 2024."},
                {"type": "heading", "content": "Data Processing Code", "level": 2},
                {"type": "code", "content": "import pandas as pd\nimport numpy as np\n\n# Read data\ndf = pd.read_csv('sales_q1_2024.csv')\n\n# Calculate statistics\nmonthly_avg = df.groupby('month')['sales'].mean()\nprint(f\"Average sales: {monthly_avg}\")"},
                {"type": "heading", "content": "Sales Statistics", "level": 2},
                {"type": "table", "content": "| Month | Sales (10k) | Growth Rate |\n|------|-------------|--------|\n| Jan | 120.5 | +15.2% |\n| Feb | 135.8 | +12.7% |\n| Mar | 148.3 | +9.2% |"},
                {"type": "paragraph", "content": "Standard deviation formula: σ = √(Σ(xi - μ)² / n)"},
                {"type": "paragraph", "content": "Overall, Q1 sales performance was strong, showing a steady growth trend."}
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
                <h1 cc-select="true">Algorithm Complexity Analysis</h1>
                <p cc-select="true">Here we introduce the time complexity of common algorithms.</p>
                <h2 cc-select="true">Quicksort Implementation</h2>
                <pre cc-select="true"><code>def quicksort(arr):
    if len(arr) <= 1:
        return arr

    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    return quicksort(left) + middle + quicksort(right)</code></pre>
                <h2 cc-select="true">Complexity Comparison</h2>
                <table cc-select="true">
                    <tr><th>Algorithm</th><th>Best Case</th><th>Average Case</th><th>Worst Case</th></tr>
                    <tr><td>Quicksort</td><td>O(n log n)</td><td>O(n log n)</td><td>O(n²)</td></tr>
                    <tr><td>Merge Sort</td><td>O(n log n)</td><td>O(n log n)</td><td>O(n log n)</td></tr>
                    <tr><td>Bubble Sort</td><td>O(n)</td><td>O(n²)</td><td>O(n²)</td></tr>
                </table>
                <p cc-select="true">Master Theorem: T(n) = aT(n/b) + f(n)</p>
                <p cc-select="true">Where a ≥ 1, b > 1 are constants, and f(n) is a positive function.</p>
            </body></html>''',
            "groundtruth_content": '''# Algorithm Complexity Analysis

Here we introduce the time complexity of common algorithms.

## Quicksort Implementation

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

## Complexity Comparison

| Algorithm | Best Case | Average Case | Worst Case |
|------|----------|----------|----------|
| Quicksort | O(n log n) | O(n log n) | O(n²) |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) |
| Bubble Sort | O(n) | O(n²) | O(n²) |

Master Theorem: $T(n) = aT(n/b) + f(n)$

Where $a \\geq 1, b > 1$ are constants, and $f(n)$ is a positive function.''',
            "groundtruth_content_list": [
                {"type": "heading", "content": "Algorithm Complexity Analysis", "level": 1},
                {"type": "paragraph", "content": "Here we introduce the time complexity of common algorithms."},
                {"type": "heading", "content": "Quicksort Implementation", "level": 2},
                {"type": "code", "content": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    \n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    \n    return quicksort(left) + middle + quicksort(right)"},
                {"type": "heading", "content": "Complexity Comparison", "level": 2},
                {"type": "table", "content": "| Algorithm | Best Case | Average Case | Worst Case |\n|------|----------|----------|----------|\n| Quicksort | O(n log n) | O(n log n) | O(n²) |\n| Merge Sort | O(n log n) | O(n log n) | O(n log n) |\n| Bubble Sort | O(n) | O(n²) | O(n²) |"},
                {"type": "equation-inline", "content": "T(n) = aT(n/b) + f(n)"},
                {"type": "paragraph", "content": "Where a ≥ 1, b > 1 are constants, and f(n) is a positive function."}
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
            <h1>Python Programming Example</h1>
            <p>This is an introductory text about Python programming.</p>
            <pre><code>
def hello_world():
    print("Hello, World!")
    return True
            </code></pre>
            <p>The code above demonstrates a simple Python function.</p>
        </body>
        </html>
        """,
        groundtruth_content="""# Python Programming Example

This is an introductory text about Python programming.

```python
def hello_world():
    print("Hello, World!")
    return True
```

The code above demonstrates a simple Python function.""",
        groundtruth_content_list=[
            {"type": "heading", "content": "Python Programming Example", "level": 1},
            {"type": "text", "content": "This is an introductory text about Python programming."},
            {"type": "code", "content": "def hello_world():\n    print(\"Hello, World!\")\n    return True", "language": "python"},
            {"type": "text", "content": "The code above demonstrates a simple Python function."}
        ]
    ))

    # Sample 2: table
    samples.append(DataSample(
        id="table_sample",
        html="""
        <html>
        <body>
            <h2>Sales Data Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Sales</th>
                        <th>Revenue</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Product A</td>
                        <td>100</td>
                        <td>1000</td>
                    </tr>
                    <tr>
                        <td>Product B</td>
                        <td>200</td>
                        <td>3000</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """,
        groundtruth_content="""## Sales Data Summary

| Product | Sales | Revenue |
|------|------|------|
| Product A | 100 | 1000 |
| Product B | 200 | 3000 |""",
        groundtruth_content_list=[
            {"type": "heading", "content": "Sales Data Summary", "level": 2},
            {"type": "table", "content": "| Product | Sales | Revenue |\n|------|------|------|\n| Product A | 100 | 1000 |\n| Product B | 200 | 3000 |"}
        ]
    ))

    # Sample 3: formulas
    samples.append(DataSample(
        id="formula_sample",
        html="""
        <html>
        <body>
            <h2>Math Formula Example</h2>
            <p>This is an inline formula: $E = mc^2$</p>
            <p>This is a block formula:</p>
            <div>$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$</div>
        </body>
        </html>
        """,
        groundtruth_content="""## Math Formula Example

This is an inline formula: $E = mc^2$

This is a block formula:

$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$""",
        groundtruth_content_list=[
            {"type": "heading", "content": "Math Formula Example", "level": 2},
            {"type": "text", "content": "This is an inline formula: $E = mc^2$"},
            {"type": "text", "content": "This is a block formula:"},
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