from webmainbench import DataLoader, Evaluator, ExtractorFactory
from pathlib import Path

# 1. 加载评测数据集
dataset = DataLoader.load_jsonl(Path("data/sample_dataset.jsonl"))

# 2. 创建抽取器
extractor = ExtractorFactory.create("llm-webkit")

# 3. 运行评测
evaluator = Evaluator()
result = evaluator.evaluate(dataset, extractor)

# 4. 查看结果
print(f"Overall Score: {result}")
