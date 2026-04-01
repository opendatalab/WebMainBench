from webmainbench import DataLoader, Evaluator, ExtractorFactory

# 1. Load evaluation dataset
dataset = DataLoader.load_jsonl("WebMainBench/data/WebMainBench_llm-webkit_v1_WebMainBench_dataset_merge_2549_llm_webkit.jsonl")

# 2. Create extractor
extractor = ExtractorFactory.create("test-model")

# 3. Run evaluation
evaluator = Evaluator()
result = evaluator.evaluate(dataset, extractor)

# 4. View results
print(f"Overall Score: {result.overall_metrics}")
print(f"Category Metrics: {result.category_metrics}")
print(f"Error Analysis: {result.error_analysis}")
