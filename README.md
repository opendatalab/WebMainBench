# WebMainBench

[简体中文](README_zh.md) | English

[![Dataset on HF](https://huggingface.co/datasets/huggingface/badges/resolve/main/dataset-on-hf-md-dark.svg)](https://huggingface.co/datasets/opendatalab/WebMainBench)
[![arXiv](https://img.shields.io/badge/arXiv-2511.23119-b31b1b.svg)](https://arxiv.org/abs/2511.23119)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**WebMainBench** is a high-precision benchmark for evaluating web main content extraction. It provides:

- A **7,809-page, 100% human-annotated** evaluation dataset covering 5,434 unique domains, 150 TLDs, and 46 languages.
- A **545-sample subset** with manually calibrated ground-truth markdown (`groundtruth_content`), enabling fine-grained metric evaluation across text, code, formula, and table dimensions.
- A unified **evaluation toolkit** (`webmainbench`) that scores extractors with both ROUGE-N and content-type-specific edit-distance metrics.

> WebMainBench is introduced in the paper [*Dripper: Token-Efficient Main HTML Extraction with a Lightweight LM*](https://arxiv.org/abs/2511.23119) and serves as the primary benchmark for the [MinerU-HTML](https://github.com/opendatalab/MinerU-HTML) project.

## Architecture

![WebMainBench Architecture](docs/assets/arch.png)

**Core Modules:**

| Module | Description |
|---|---|
| `data` | Dataset loading, saving, and sample management |
| `extractors` | Unified interface for content extractors and a factory registry |
| `metrics` | Edit-distance, TEDS, and ROUGE metric implementations |
| `evaluator` | Orchestrates extraction, scoring, and report generation |

## Dataset Statistics

The full dataset (7,809 samples) is annotated at the HTML tag level through a rigorous 3-round process (annotator → reviewer → senior inspector).

**Language Distribution (Top 10 of 46)**

| Language | Count | % |
|---|---|---|
| English | 6,711 | 85.09 |
| Chinese | 716 | 9.08 |
| Spanish | 61 | 0.77 |
| German | 51 | 0.65 |
| Japanese | 48 | 0.61 |
| Russian | 45 | 0.57 |
| French | 36 | 0.46 |
| Italian | 22 | 0.28 |
| Korean | 20 | 0.25 |
| Portuguese | 17 | 0.22 |

**TLD Distribution (Top 10 of 150)**

| TLD | Count | % |
|---|---|---|
| .com | 4,550 | 57.69 |
| .org | 816 | 10.35 |
| .cn | 459 | 5.82 |
| .net | 318 | 4.03 |
| .uk | 235 | 2.98 |
| .edu | 180 | 2.28 |
| .de | 101 | 1.28 |
| .au | 94 | 1.19 |
| .ru | 69 | 0.87 |
| .gov | 59 | 0.75 |

**Page Style & Difficulty**

Pages are classified by GPT-5 into styles (Article, Content Listing, Forum, etc.) and assigned difficulty levels (Simple / Mid / Hard) based on DOM structural complexity, text distribution sparsity, content-type diversity, and link density.

## Evaluation Metrics

WebMainBench supports two complementary evaluation protocols:

### ROUGE-N F1 (primary metric from the paper)

All extracted content is converted to canonical Markdown via `html2text`, then scored with ROUGE-N (N=5, jieba tokenization). This is the metric reported in the [Dripper paper](https://arxiv.org/abs/2511.23119).

### Fine-Grained Edit-Distance Metrics (from this toolkit)

Computed on the 545-sample subset with manually calibrated `groundtruth_content`:

| Metric | Formula | Description |
|---|---|---|
| `overall` | arithmetic mean of the five sub-metrics | Composite quality score |
| `text_edit` | 1 − edit\_dist / max(len\_pred, len\_gt) | Plain-text similarity |
| `code_edit` | same, on code blocks only | Code content similarity |
| `formula_edit` | same, on formulas only | Formula content similarity |
| `table_edit` | same, on table text only | Table content similarity |
| `table_TEDS` | 1 − tree\_edit\_dist / max(nodes\_pred, nodes\_gt) | Table structure similarity |

All scores are in **[0, 1]**; higher is better.

## Leaderboard

### ROUGE-N F1 on Full Dataset (7,809 samples)

**How to reproduce:** Use the evaluation scripts in the [MinerU-HTML](https://github.com/opendatalab/MinerU-HTML) repository:

```bash
# Clone MinerU-HTML and prepare the full dataset (WebMainBench_7809.jsonl)
git clone https://github.com/opendatalab/MinerU-HTML.git
cd MinerU-HTML

# Run evaluation (example for MinerU-HTML extractor)
python eval_baselines.py \
    --bench benchmark/WebMainBench_7809.jsonl \
    --task_dir benchmark_results/mineru_html-html-md \
    --extractor_name mineru_html-html-md \
    --model_path YOUR_MODEL_PATH \
    --default_config gpu

# For CPU-based extractors (e.g. trafilatura, resiliparse, magic-html)
python eval_baselines.py \
    --bench benchmark/WebMainBench_7809.jsonl \
    --task_dir benchmark_results/trafilatura-html-md \
    --extractor_name trafilatura-html-md
```

Results are written to `benchmark_results/<extractor>/mean_eval_result.json`. See `run_eval.sh` for a complete multi-extractor example.

Results from the [Dripper paper](https://arxiv.org/abs/2511.23119) (Table 2):

| Extractor | Mode | All | Simple | Mid | Hard |
|---|---|---|---|---|---|
| DeepSeek-V3.2* | Html+MD | 0.9098 | 0.9415 | 0.9104 | 0.8771 |
| GPT-5* | Html+MD | 0.9024 | 0.9382 | 0.9042 | 0.8638 |
| Gemini-2.5-Pro* | Html+MD | 0.8979 | 0.9345 | 0.8978 | 0.8610 |
| **Dripper_fallback** | Html+MD | **0.8925** | 0.9325 | 0.8958 | 0.8477 |
| **Dripper** (0.6B) | Html+MD | **0.8779** | 0.9205 | 0.8804 | 0.8313 |
| magic-html | Html+MD | 0.7138 | 0.7857 | 0.7121 | 0.6434 |
| Readability | Html+MD | 0.6543 | 0.7415 | 0.6550 | 0.5652 |
| Trafilatura | Html+MD | 0.6402 | 0.7309 | 0.6417 | 0.5466 |
| Resiliparse | TEXT | 0.6290 | 0.7140 | 0.6323 | 0.5388 |

\* Frontier models used as drop-in replacements within the Dripper pipeline.

### Fine-Grained Metrics on 545-Sample Subset

| Extractor | Version | overall | text\_edit | code\_edit | formula\_edit | table\_edit | table\_TEDS |
|---|---|---|---|---|---|---|---|
| **mineru-html** | 4.1.1 | **0.8256** | 0.8621 | 0.9093 | 0.9399 | 0.6780 | 0.7388 |
| magic-html | 0.1.5 | 0.5141 | 0.7791 | 0.4117 | 0.7204 | 0.2611 | 0.3984 |
| trafilatura (md) | 2.0.0 | 0.3858 | 0.6887 | 0.1305 | 0.6242 | 0.1653 | 0.3203 |
| resiliparse | 0.14.5 | 0.2954 | 0.7381 | 0.0641 | 0.6747 | 0.0000 | 0.0000 |
| trafilatura (txt) | 2.0.0 | 0.2657 | 0.7126 | 0.0000 | 0.6162 | 0.0000 | 0.0000 |

Contributions of new extractor results are welcome — open a PR!

## Quick Start

### Installation

```bash
pip install webmainbench

# Or install from source
git clone https://github.com/opendatalab/WebMainBench.git
cd WebMainBench
pip install -e .
```

### Download the Dataset

The dataset is hosted on Hugging Face: [opendatalab/WebMainBench](https://huggingface.co/datasets/opendatalab/WebMainBench)

```python
from huggingface_hub import hf_hub_download

hf_hub_download(
    repo_id="opendatalab/WebMainBench",
    repo_type="dataset",
    filename="WebMainBench_545.jsonl",
    local_dir="data/",
)
```

### Configure LLM (Optional)

LLM-enhanced content splitting improves formula/table/code extraction accuracy. To enable it, copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
# Edit .env and set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
```

### Run an Evaluation

```python
from webmainbench import DataLoader, Evaluator, ExtractorFactory

dataset = DataLoader.load_jsonl("data/WebMainBench_545.jsonl")
result = Evaluator().evaluate(dataset, ExtractorFactory.create("trafilatura"))

m = result.overall_metrics

print(f"Overall Score: {result.overall_metrics['overall']:.4f}")
```

### Compare Multiple Extractors

```python
extractors = ["trafilatura", "resiliparse", "magic-html"]
results = evaluator.compare_extractors(dataset, extractors)

for name, result in results.items():
    print(f"{name}: {result.overall_metrics['overall']:.4f}")
```

A complete example is available at `examples/multi_extractor_compare.py`.

## Dataset Format

Each JSONL line represents one web page:

```json
{
  "track_id": "0b7f2636-d35f-40bf-9b7f-94be4bcbb396",
  "url": "https://example.com/page",
  "html": "<html>...<h1 cc-select=\"true\">Title</h1>...</html>",
  "main_html": "<h1>Title</h1><p>Body text...</p>",
  "convert_main_content": "# Title\n\nBody text...",
  "groundtruth_content": "# Title\n\nBody text...",
  "meta": {
    "language": "en",
    "style": "Article",
    "level": "mid",
    "table": [],
    "code": ["interline"],
    "equation": ["inline"]
  }
}
```

| Field | Description |
|---|---|
| `track_id` | Unique sample identifier (UUID) |
| `url` | Original page URL |
| `html` | Full page HTML; human-annotated regions carry `cc-select="true"` |
| `main_html` | Ground-truth HTML subtree pruned from `html` (available for all 7,809 samples) |
| `convert_main_content` | Markdown converted from `main_html` via `html2text` (available for all 7,809 samples) |
| `groundtruth_content` | Manually calibrated ground-truth markdown (available for the 545-sample subset) |
| `meta.language` | Language code — `en`, `zh`, `es`, `de`, `ja`, `ko`, `ru`, … (46 languages) |
| `meta.style` | Page style — `Article`, `Content Listing`, `Forum_or_Article_with_commentsection`, `Other` |
| `meta.level` | Complexity — `simple`, `mid`, `hard` |
| `meta.table` | Table types: `[]`, `["data"]`, `["layout"]`, `["data", "layout"]` |
| `meta.code` | Code types: `[]`, `["inline"]`, `["interline"]`, `["inline", "interline"]` |
| `meta.equation` | Formula types: `[]`, `["inline"]`, `["interline"]`, `["inline", "interline"]` |

## Supported Extractors

| Extractor | Package | Output |
|---|---|---|
| `mineru-html` | [MinerU-HTML](https://github.com/opendatalab/MinerU-HTML) | HTML → Markdown |
| `trafilatura` | [trafilatura](https://github.com/adbar/trafilatura) | Markdown or plain text |
| `resiliparse` | [resiliparse](https://resiliparse.chatnoir.eu/) | Plain text |
| `magic-html` | [magic-html](https://github.com/opendatalab/magic-html) | HTML |
| Custom | Inherit from `BaseExtractor` | Any |

## Advanced Usage

### Custom Extractor

```python
from webmainbench.extractors import BaseExtractor, ExtractionResult, ExtractorFactory

class MyExtractor(BaseExtractor):
    def _setup(self):
        pass

    def _extract_content(self, html, url=None):
        content = your_extraction_logic(html)
        return ExtractionResult(content=content, content_list=[], success=True)

ExtractorFactory.register("my-extractor", MyExtractor)
```

### Custom Metric

```python
from webmainbench.metrics import BaseMetric, MetricResult

class CustomMetric(BaseMetric):
    def _setup(self):
        pass

    def _calculate_score(self, predicted, groundtruth, **kwargs):
        score = your_scoring_logic(predicted, groundtruth)
        return MetricResult(metric_name=self.name, score=score, details={})

evaluator.metric_calculator.add_metric("custom", CustomMetric("custom"))
```

### Output Files

After evaluation, the following files are generated in `results/`:

| File | Description |
|---|---|
| `leaderboard.csv` | Per-extractor overall and per-metric scores |
| `evaluation_results.json` | Full evaluation details with metadata |
| `dataset_with_results.jsonl` | Original samples enriched with extraction outputs |

## Project Structure

```
webmainbench/
├── data/           # Dataset loading and saving
├── extractors/     # Extractor implementations and factory
├── metrics/        # Metric implementations and calculator
├── evaluator/      # Orchestrates extraction + scoring
└── utils/          # Logging and helper functions
```

## Citation

If you use WebMainBench in your research, please cite the Dripper paper:

```bibtex
@misc{liu2025dripper,
    title   = {Dripper: Token-Efficient Main HTML Extraction with a Lightweight LM},
    author  = {Mengjie Liu and Jiahui Peng and Pei Chu and Jiantao Qiu and Ren Ma and He Zhu and Rui Min and Lindong Lu and Wenchang Ning and Linfeng Hou and Kaiwen Liu and Yuan Qu and Zhenxiang Li and Chao Xu and Zhongying Tu and Wentao Zhang and Conghui He},
    year    = {2025},
    eprint  = {2511.23119},
    archivePrefix = {arXiv},
    primaryClass  = {cs.CL},
    url     = {https://arxiv.org/abs/2511.23119},
}
```

## License

This project is licensed under the Apache License 2.0 — see [LICENSE](LICENSE) for details.
