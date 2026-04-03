from webmainbench import DataLoader, Evaluator, ExtractorFactory, DataSaver
from pathlib import Path

# To use LLM to correct extraction results, configure the LLM API in webmainbench/config.py

def all_extractor_comparison():
    """Demonstrate multi-extractor comparison"""

    print("\n=== Multi-Extractor Comparison Demo ===\n")

    # Create dataset
    dataset_path = Path("../data/WebMainBench_llm-webkit_v1_WebMainBench_7887_within_formula.jsonl")
    dataset = DataLoader.load_jsonl(dataset_path)

    # Create webkit extractor
    config = {
        "use_preprocessed_html": True,          # Key config: enable preprocessed HTML mode
        "preprocessed_html_field": "llm_webkit_html"  # Specify the preprocessed HTML field name
    }

    webkit_extractor = ExtractorFactory.create("llm-webkit", config=config)
    # Create magic-extractor extractor
    magic_extractor = ExtractorFactory.create("magic-html")
    # Create trafilatura extractor, extract to markdown
    trafilatura_extractor = ExtractorFactory.create("trafilatura")
    # Create trafilatura extractor, extract to txt
    trafilatura_txt_extractor = ExtractorFactory.create("trafilatura_txt")
    # Create resiliparse extractor
    resiliparse_extractor = ExtractorFactory.create("resiliparse")

    # Run comparison
    evaluator = Evaluator()
    extractors = [webkit_extractor, magic_extractor, trafilatura_extractor,trafilatura_txt_extractor, resiliparse_extractor]
    # extractors = [webkit_extractor]


    results = evaluator.compare_extractors(
        dataset=dataset,
        extractors=extractors
    )

    # Display comparison results
    print("Comparison results:")
    print("-" * 40)
    for extractor_name, result in results.items():
        overall_score = result.overall_metrics.get('overall', 0)
        print(f"{extractor_name}: {overall_score:.4f}")

    # Save multi-extractor comparison leaderboard
    all_results = []
    for extractor_name, result in results.items():
        all_results.append(result.to_dict())

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    leaderboard_path = results_dir / "leaderboard.csv"
    evaluation_results_path = results_dir / "evaluation_results.json"
    jsonl_dataset_path = results_dir / f"dataset_with_results.jsonl"
    DataSaver.save_summary_report(all_results, leaderboard_path)
    DataSaver.save_evaluation_results(all_results, evaluation_results_path)
    DataSaver.save_dataset_with_extraction(
        results=all_results,
        dataset=dataset,  # Original dataset object
        file_path=jsonl_dataset_path
    )
    print(f"\nLeaderboard saved to: {leaderboard_path}")


if __name__ == "__main__":
    all_extractor_comparison()
