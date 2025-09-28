from webmainbench import DataLoader, Evaluator, ExtractorFactory, DataSaver
from pathlib import Path

# 全局LLM配置
LLM_CONFIG = {
    'llm_base_url': '',
    'llm_api_key': '',
    'llm_model': '',
    'use_llm': True
}

def all_extractor_comparison():
    """演示多抽取器对比"""
    
    print("\n=== 多抽取器对比演示 ===\n")
    
    # 创建数据集
    dataset_path = Path("../data/test_math.jsonl")
    dataset = DataLoader.load_jsonl(dataset_path)

    # 创建webkit抽取器
    config = {
        "use_preprocessed_html": True,          # 🔑 关键配置：启用预处理HTML模式
        "preprocessed_html_field": "llm_webkit_html"  # 指定预处理HTML字段名
    }

    webkit_extractor = ExtractorFactory.create("llm-webkit", config=config)
    # 创建magic-extractor抽取器
    magic_extractor = ExtractorFactory.create("magic-html")
    # 创建trafilatura抽取器
    trafilatura_extractor = ExtractorFactory.create("trafilatura")
    # 创建resiliparse抽取器
    resiliparse_extractor = ExtractorFactory.create("resiliparse")
    
    # 运行对比
    evaluator = Evaluator()
    extractors = [webkit_extractor, magic_extractor, trafilatura_extractor, resiliparse_extractor]
    # extractors = [webkit_extractor]

    
    results = evaluator.compare_extractors(
        dataset=dataset,
        extractors=extractors
    )
    
    # 显示对比结果
    print("对比结果:")
    print("-" * 40)
    for extractor_name, result in results.items():
        overall_score = result.overall_metrics.get('overall', 0)
        print(f"{extractor_name}: {overall_score:.4f}")
    
    # 保存多抽取器对比榜单
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
        dataset=dataset,  # 原始数据集对象
        file_path=jsonl_dataset_path
    )
    print(f"\n📊 榜单已保存到: {leaderboard_path}")


if __name__ == "__main__":
    all_extractor_comparison()
