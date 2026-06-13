"""Run the 545-sample fine-grained leaderboard.

Required environment variables for LLM-enhanced formula splitting:
    LLM_BASE_URL
    LLM_API_KEY
    LLM_MODEL

Example:
    python examples/run_545_leaderboard.py WebMainBench_545.jsonl
"""

import os
import sys
from pathlib import Path

from webmainbench import DataLoader, Evaluator


METRICS = [
    "overall",
    "text_edit",
    "code_edit",
    "formula_edit",
    "table_edit",
    "table_TEDS",
]


def build_llm_config() -> dict:
    config = {
        "use_llm": os.getenv("USE_LLM", "true").lower() == "true",
        "llm_base_url": os.getenv("LLM_BASE_URL", ""),
        "llm_api_key": os.getenv("LLM_API_KEY", ""),
        "llm_model": os.getenv("LLM_MODEL", "deepseek-chat"),
        "llm_timeout": float(os.getenv("LLM_TIMEOUT", "60")),
    }
    if os.getenv("LLM_CACHE_DIR"):
        config["cache_dir"] = os.getenv("LLM_CACHE_DIR")
    return config


def main() -> None:
    dataset_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/WebMainBench_545.jsonl")
    extractors = sys.argv[2:] or ["magic-html", "trafilatura", "resiliparse", "trafilatura_txt"]
    llm_config = build_llm_config()

    dataset = DataLoader.load_jsonl(dataset_path)
    evaluator = Evaluator(llm_config=llm_config, metric_config=llm_config)
    results = evaluator.compare_extractors(dataset, extractors)

    print("| Extractor | " + " | ".join(METRICS) + " |")
    print("|---|" + "|".join(["---:"] * len(METRICS)) + "|")
    for name, result in results.items():
        scores = [result.overall_metrics.get(metric, 0.0) for metric in METRICS]
        print(f"| {name} | " + " | ".join(f"{score:.4f}" for score in scores) + " |")


if __name__ == "__main__":
    main()
