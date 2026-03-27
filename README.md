# WebMainBench

[简体中文](README_zh.md) | English

WebMainBench is a specialized benchmark tool for end-to-end evaluation of web main content extraction quality.

## Features

### 🎯 **Core Features**
- **Multiple Extractor Support**: Supports various extraction tools such as trafilatura, resiliparse, and more
- **Comprehensive Evaluation Metrics**: Includes multi-dimensional metrics such as text edit distance, table structure similarity (TEDS), formula extraction quality, etc.
- **Manual Annotation Support**: 100% manually annotated evaluation dataset

#### Metric Details

| Metric Name | Calculation Method | Value Range | Description |
|---------|----------|----------|------|
| `overall` | Average of all successful metrics | 0.0-1.0 | Comprehensive quality score, higher is better |
| `text_edit` | `1 - (edit distance / max text length)` | 0.0-1.0 | Plain text similarity, higher is better |
| `code_edit` | `1 - (edit distance / max code length)` | 0.0-1.0 | Code content similarity, higher is better |
| `table_TEDS` | `1 - (tree edit distance / max nodes)` | 0.0-1.0 | Table structure similarity, higher is better |
| `table_edit` | `1 - (edit distance / max table length)` | 0.0-1.0 | Table content similarity, higher is better |
| `formula_edit` | `1 - (edit distance / max formula length)` | 0.0-1.0 | Formula content similarity, higher is better |


### 🏗️ **System Architecture**

![WebMainBench Architecture](docs/assets/arch.png)

### 🔧 **Core Modules**
1. **data module**: Read/write management of evaluation sets and results
2. **extractors module**: Unified interface for various extraction tools
3. **metrics module**: Implementation of evaluation metrics calculation
4. **evaluator module**: Execution and result output of evaluation tasks


## Quick Start

### Installation

```bash
# Basic installation
pip install webmainbench
```

### Basic Usage

```python
from webmainbench import DataLoader, Evaluator, ExtractorFactory

# 1. Load evaluation dataset
dataset = DataLoader.load_jsonl("data/WebMainBench_dataset_sample2.jsonl")

# 2. Create extractor
extractor = ExtractorFactory.create("trafilatura")

# 3. Run evaluation
evaluator = Evaluator(llm_config={
    "use_llm": True,
    "llm_base_url": "",
    "llm_api_key": "",
    "llm_model": "gpt-5-chat-latest",
})
result = evaluator.evaluate(dataset, extractor)

# 4. View results
print(f"Overall Score: {result.overall_metrics['overall']:.4f}")
```

### Data Format

Evaluation datasets should contain the following fields:

```jsonl
{
  "track_id": "0b7f2636-d35f-40bf-9b7f-94be4bcbb396",
  "html": "<html><body><h1 cc-select=\"true\">This is a title</h1></body></html>",   # Manually annotated with cc-select="true" attribute
  "url": "https://orderyourbooks.com/product-category/college-books-p-u/?products-per-page=all",
  "main_html": "<h1 cc-select=\"true\">This is a title</h1>",  # Main content HTML pruned from html
  "convert_main_content": "# This is a title",  # Converted from main_html + html2text
  "groundtruth_content": "# This is a title",  # Manually calibrated markdown (partially provided)
  "meta": {
    "language": "en",  # Web page language
    "style": "artical",  # Web page style
    "table": [],  # [], ["layout"], ["data"], ["layout", "data"]
    "equation": [],  # [], ["inline"], ["interline"], ["inline", "interline"]
    "code": [],  # [], ["inline"], ["interline"], ["inline", "interline"]
    "level": "mid"  # simple, mid, hard
  }
}
```

## Supported Extractors

- **trafilatura**: trafilatura extractor
- **resiliparse**: resiliparse extractor
- **mineru-html**: mineru-html extractor
- **magic-html**: magic-html extractor
- **Custom extractors**: Implement by inheriting from `BaseExtractor`

## Evaluation Leaderboard

| extractor | extractor_version | dataset | total_samples | overall (macro avg) | code_edit | formula_edit | table_TEDS | table_edit | text_edit |
|-----------|-------------------|---------|---------------|---------------------|-----------|--------------|------------|-----------|-----------|
| mineru-html | 4.1.1 | WebMainBench1.0 | 545 | 0.8256 | 0.9093 | 0.9399 | 0.7388 | 0.678 | 0.8621 |
| magic-html | 0.1.5 | WebMainBench1.0 | 545 | 0.5141 | 0.4117 | 0.7204 | 0.3984 | 0.2611 | 0.7791 |
| trafilatura_md | 2.0.0 | WebMainBench1.0 | 545 | 0.3858 | 0.1305 | 0.6242 | 0.3203 | 0.1653 | 0.6887 |
| trafilatura_txt | 2.0.0 | WebMainBench1.0 | 545 | 0.2657 | 0 | 0.6162 | 0 | 0 | 0.7126 |
| resiliparse | 0.14.5 | WebMainBench1.0 | 545 | 0.2954 | 0.0641 | 0.6747 | 0 | 0 | 0.7381 |

## Advanced Features

### Multi-Extractor Comparison

```python
# Compare multiple extractors
extractors = ["trafilatura", "resiliparse"]
results = evaluator.compare_extractors(dataset, extractors)

for name, result in results.items():
    print(f"{name}: {result.overall_metrics['overall']:.4f}")
```

#### Detailed Example

```python
python examples/multi_extractor_compare.py
```

This example demonstrates how to:

1. **Load test dataset**: Use sample data containing multiple content types such as code, formulas, tables, text, etc.
2. **Create multiple extractors**:
   - `magic-html`: Extractor based on magic-html library
   - `trafilatura`: Extractor based on trafilatura library  
   - `resiliparse`: Extractor based on resiliparse library
3. **Batch evaluation comparison**: Use `evaluator.compare_extractors()` to evaluate all extractors simultaneously
4. **Generate comparison report**: Automatically save evaluation results in multiple formats

#### Output File Description

After evaluation is complete, three important files will be generated in the `results/` directory:

| File Name | Format | Content Description |
|--------|------|----------|
| `leaderboard.csv` | CSV | **Leaderboard file**: Contains overall rankings and sub-metric comparisons for each extractor, for quick performance comparison |
| `evaluation_results.json` | JSON | **Detailed evaluation results**: Contains complete evaluation data, metric details and metadata for each extractor |
| `dataset_with_results.jsonl` | JSONL | **Enhanced dataset**: Original test data plus extraction results from all extractors, for manual inspection and analysis |


`leaderboard.csv` content example:
```csv
extractor,dataset,total_samples,success_rate,overall,code_edit,formula_edit,table_TEDS,table_edit,text_edit
magic-html,sample_dataset,4,1.0,0.1526,0.1007,0.0,0.0,0.0,0.6624
resiliparse,sample_dataset,4,1.0,0.1379,0.0,0.0,0.0,0.0,0.6897
trafilatura,sample_dataset,4,1.0,0.1151,0.1007,0.0,0.0,0.0,0.4746
```

### Custom Metrics

```python
from webmainbench.metrics import BaseMetric, MetricResult

class CustomMetric(BaseMetric):
    def _setup(self):
        pass
    
    def _calculate_score(self, predicted, groundtruth, **kwargs):
        # Implement custom evaluation logic
        score = your_calculation(predicted, groundtruth)
        return MetricResult(
            metric_name=self.name,
            score=score,
            details={"custom_info": "value"}
        )

# Add to evaluator
evaluator.metric_calculator.add_metric("custom", CustomMetric("custom"))
```

### Custom Extractors

```python
from webmainbench.extractors import BaseExtractor, ExtractionResult

class MyExtractor(BaseExtractor):
    def _setup(self):
        # Initialize extractor
        pass
    
    def _extract_content(self, html, url=None):
        # Implement extraction logic
        content = your_extraction_logic(html)
        
        return ExtractionResult(
            content=content,
            content_list=[...],
            success=True
        )

# Register custom extractor
ExtractorFactory.register("my-extractor", MyExtractor)
```

## Project Architecture

```
webmainbench/
├── data/           # Data processing module
│   ├── dataset.py  # Dataset class
│   ├── loader.py   # Data loader
│   └── saver.py    # Data saver
├── extractors/     # Extractor module
│   ├── base.py     # Base interface
│   ├── factory.py  # Factory pattern
│   └── ...         # Specific implementations
├── metrics/        # Metrics module
│   ├── base.py     # Base interface
│   ├── text_metrics.py    # Text metrics
│   ├── table_metrics.py   # Table metrics
│   └── calculator.py      # Metric calculator
├── evaluator/      # Evaluator module
│   └── evaluator.py       # Main evaluator
└── utils/          # Utility module
    └── helpers.py          # Helper functions
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

