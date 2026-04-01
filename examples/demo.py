from webmainbench import DataLoader, Evaluator, ExtractorFactory
from pathlib import Path

# 1. Load evaluation dataset
dataset = DataLoader.load_jsonl(Path("data/sample_dataset.jsonl"))

# 2. Create extractor
extractor = ExtractorFactory.create("llm-webkit")

# 3. Run evaluation
evaluator = Evaluator()
result = evaluator.evaluate(dataset, extractor)

# 4. View results
print(f"Overall Score: {result}")
