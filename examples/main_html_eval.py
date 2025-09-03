#!/usr/bin/env python3
"""
WebMainBench 基本使用示例
"""

import json
from pathlib import Path

# 导入 WebMainBench 模块
from webmainbench import (
    DataLoader, DataSaver, BenchmarkDataset, DataSample,
    ExtractorFactory, MainHTMLEvaluator,
    format_results, setup_logging
)


def load_benchdata(dataset_path: str) -> BenchmarkDataset:
    dataset_path = Path(dataset_path)
    print(f"📂 数据集文件: {dataset_path}")
    
    if not dataset_path.exists():
        print(f"❌ 数据文件不存在: {dataset_path}")
        print("请确保已运行数据提取命令创建样本数据集")
        return
    
    # 加载数据集
    dataset = DataLoader.load_jsonl(dataset_path, include_results=False)
    dataset.name = "real_preprocessed_html_test"
    dataset.description = "基于真实数据的预处理HTML功能测试"
    return dataset


def load_extractor(model_path: str):
    extractor = ExtractorFactory.create("dripper", config={"model_path": model_path})
    return extractor


def save_results(result_file: Path, results: list[dict]):
    with result_file.open("w", encoding="utf-8") as f:
        for res in results:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
    
    

def demo_llm_webkit_with_preprocessed_html_evaluation(model_path: str):
    """演示LLM-WebKit预处理HTML功能的评测"""
    
    print("\n=== LLM-WebKit 预处理HTML功能演示 ===\n")
    
    # 设置日志
    setup_logging(level="INFO")
    
    # 1. 从真实数据集加载包含预处理HTML的数据
    print("1. 从真实数据集加载预处理HTML数据...")
    
    # 使用DataLoader加载真实的样本数据
   
    dataset = load_benchdata("data/WebMainBench_llm-webkit_v1_WebMainBench_1827_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl")
    print(f"✅ 真实数据集加载成功，包含 {len(dataset)} 个样本")
    

    
    # 2. 创建预处理HTML模式的LLM-WebKit抽取器
    print("2. 创建预处理HTML模式的LLM-WebKit抽取器...")
    
    extractor = load_extractor(model_path)
    print(f"✅ 抽取器创建成功")
    print(f"📋 配置信息:")
    print(f"  - 跳过LLM推理: 是（直接处理预处理HTML）")
    print()
    
    # 4. 运行评测
    print("4. 开始评测...")
    print("=" * 50)
    
    evaluator = MainHTMLEvaluator()
    result = evaluator.evaluate(
        dataset=dataset,
        extractor=extractor,
        max_samples=None
    )
    
    # 5. 显示评测结果
    print("\n5. 📊 预处理HTML模式评测结果:")
    print("=" * 50)
    
    results_dict = result.to_dict()
    metrics = results_dict.get('overall_metrics', {})
    
    # 显示关键指标
    print(f"\n🏆 综合指标:")
    for key in metrics.keys():
        print(f"  {key}: {metrics[key]:.4f}")
    
    print(f"\n⚡ 性能统计:")
    sample_results = results_dict.get('sample_results', [])
    if sample_results:
        extraction_times = [s.get('extraction_time', 0) for s in sample_results if s.get('extraction_success')]
        if extraction_times:
            avg_time = sum(extraction_times) / len(extraction_times)
            print(f"  平均提取时间: {avg_time:.3f}秒")
            print(f"  处理速度: {1/avg_time:.1f}样本/秒")
    
    success_count = len([s for s in sample_results if s.get('extraction_success', False)])
    print(f"  成功样本数: {success_count}/{len(dataset)}")
    
    # 7. 保存结果
    print(f"\n6. 💾 保存评测结果...")
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    # 新增：保存带抽取结果的增强数据集（JSONL格式）
    jsonl_dataset_path = results_dir / f"{extractor.name}_preprocessed_html_dataset_with_results.jsonl"
    save_results(jsonl_dataset_path, result.sample_results)
    print(f"✅ 结果已保存到: {jsonl_dataset_path}")
    
    
    print(f"✅ 带抽取结果的JSONL数据集已保存到: {jsonl_dataset_path}")
    results_path = results_dir / f"{extractor.name}_preprocessed_html_evaluation_results.json"
    report_path = results_dir / f"{extractor.name}_preprocessed_html_evaluation_report.csv"
    
    DataSaver.save_evaluation_results(result, results_path)
    DataSaver.save_summary_report(result, report_path)
    
    print(f"✅ 详细结果已保存到: {results_path}")
    print(f"✅ CSV报告已保存到: {report_path}")
    


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WebMainBench 基本使用示例")
    parser.add_argument("--model_path", required=True, help="LLM model路径")
    args = parser.parse_args()
    try:
        demo_llm_webkit_with_preprocessed_html_evaluation(args.model_path)
        print("\n✅ 示例运行完成！")
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc() 