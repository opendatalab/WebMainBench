#!/usr/bin/env python3
"""
WebMainBench Basic Usage Example
"""

import json
from pathlib import Path

# Import WebMainBench modules
from webmainbench import (
    DataLoader, DataSaver, BenchmarkDataset, DataSample,
    ExtractorFactory, MainHTMLEvaluator,
    format_results, setup_logging
)


def load_benchdata(dataset_path: str) -> BenchmarkDataset:
    dataset_path = Path(dataset_path)
    print(f"📂 Dataset file: {dataset_path}")

    if not dataset_path.exists():
        print(f"❌ Data file does not exist: {dataset_path}")
        print("Please ensure the data extraction command has been run to create the sample dataset")
        return

    # Load dataset
    dataset = DataLoader.load_jsonl(dataset_path, include_results=False)
    dataset.name = "real_preprocessed_html_test"
    dataset.description = "Preprocessed HTML feature test based on real data"
    return dataset


def load_extractor(model_path: str):
    extractor = ExtractorFactory.create("dripper", config={"model_path": model_path})
    return extractor


def save_results(result_file: Path, results: list[dict]):
    with result_file.open("w", encoding="utf-8") as f:
        for res in results:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")



def demo_llm_webkit_with_preprocessed_html_evaluation(model_path: str):
    """Demonstrate evaluation of the LLM-WebKit preprocessed HTML feature"""

    print("\n=== LLM-WebKit Preprocessed HTML Feature Demo ===\n")

    # Set up logging
    setup_logging(level="INFO")

    # 1. Load preprocessed HTML data from the real dataset
    print("1. Loading preprocessed HTML data from the real dataset...")

    # Load real sample data using DataLoader
    dataset = load_benchdata("data/WebMainBench_llm-webkit_v1_WebMainBench_1827_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl")
    print(f"✅ Real dataset loaded successfully, contains {len(dataset)} samples")



    # 2. Create LLM-WebKit extractor in preprocessed HTML mode
    print("2. Creating LLM-WebKit extractor in preprocessed HTML mode...")

    extractor = load_extractor(model_path)
    print(f"✅ Extractor created successfully")
    print(f"📋 Configuration:")
    print(f"  - Skip LLM inference: Yes (process preprocessed HTML directly)")
    print()

    # 4. Run evaluation
    print("4. Starting evaluation...")
    print("=" * 50)

    evaluator = MainHTMLEvaluator()
    result = evaluator.evaluate(
        dataset=dataset,
        extractor=extractor,
        max_samples=None
    )

    # 5. Display evaluation results
    print("\n5. 📊 Preprocessed HTML mode evaluation results:")
    print("=" * 50)

    results_dict = result.to_dict()
    metrics = results_dict.get('overall_metrics', {})

    # Display key metrics
    print(f"\n🏆 Overall metrics:")
    for key in metrics.keys():
        print(f"  {key}: {metrics[key]:.4f}")

    print(f"\n⚡ Performance statistics:")
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
    print(f"\n6. 💾 Saving evaluation results...")

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    # Save enhanced dataset with extraction results (JSONL format)
    jsonl_dataset_path = results_dir / f"{extractor.name}_preprocessed_html_dataset_with_results.jsonl"
    save_results(jsonl_dataset_path, result.sample_results)
    print(f"✅ Results saved to: {jsonl_dataset_path}")


    print(f"✅ JSONL dataset with extraction results saved to: {jsonl_dataset_path}")
    results_path = results_dir / f"{extractor.name}_preprocessed_html_evaluation_results.json"
    report_path = results_dir / f"{extractor.name}_preprocessed_html_evaluation_report.csv"

    DataSaver.save_evaluation_results(result, results_path)
    DataSaver.save_summary_report(result, report_path)

    print(f"✅ Detailed results saved to: {results_path}")
    print(f"✅ CSV report saved to: {report_path}")



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WebMainBench Basic Usage Example")
    parser.add_argument("--model_path", required=True, help="LLM model path")
    args = parser.parse_args()
    try:
        demo_llm_webkit_with_preprocessed_html_evaluation(args.model_path)
        print("\n✅ Example completed!")

    except Exception as e:
        print(f"\n❌ Runtime error: {e}")
        import traceback
        traceback.print_exc()
