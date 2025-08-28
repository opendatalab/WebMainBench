#!/usr/bin/env python3
"""
合并多个JSONL文件，基于track_id字段去重
"""
import json
import sys
from pathlib import Path
from collections import OrderedDict

def load_jsonl_with_dedup(jsonl_files):
    """
    加载多个JSONL文件并基于track_id去重
    
    Args:
        jsonl_files: JSONL文件路径列表
        
    Returns:
        dict: {track_id: data} 的有序字典
    """
    merged_data = OrderedDict()
    total_loaded = 0
    duplicates_found = 0
    
    for file_path in jsonl_files:
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"⚠️ 文件不存在，跳过: {file_path}")
            continue
            
        print(f"📖 正在读取文件: {file_path.name}")
        
        line_count = 0
        file_loaded = 0
        file_duplicates = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    line_count += 1
                    
                    # 每处理1000行显示进度
                    if line_count % 1000 == 0:
                        print(f"  📊 已处理 {line_count} 行...")
                    
                    try:
                        data = json.loads(line)
                        track_id = data.get('track_id')
                        
                        if not track_id:
                            print(f"  ⚠️ 第 {line_num} 行缺少track_id字段，跳过")
                            continue
                        
                        if track_id in merged_data:
                            # 发现重复的track_id
                            file_duplicates += 1
                            duplicates_found += 1
                            print(f"  🔄 发现重复track_id: {track_id} (第 {line_num} 行)")
                        else:
                            # 新的track_id，添加到合并数据中
                            merged_data[track_id] = data
                            file_loaded += 1
                            total_loaded += 1
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ 第 {line_num} 行JSON解析错误: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ 读取文件 {file_path} 时出错: {e}")
            continue
        
        print(f"  ✅ 文件处理完成:")
        print(f"    📄 总行数: {line_count}")
        print(f"    ➕ 新增数据: {file_loaded}")
        print(f"    🔄 重复数据: {file_duplicates}")
        print()
    
    print(f"📊 合并统计:")
    print(f"  📄 总处理数据: {total_loaded + duplicates_found}")
    print(f"  ✅ 唯一数据: {len(merged_data)}")
    print(f"  🔄 重复去除: {duplicates_found}")
    
    return merged_data

def save_merged_data(merged_data, output_file):
    """
    保存合并后的数据到JSONL文件
    
    Args:
        merged_data: 合并后的数据字典
        output_file: 输出文件路径
    """
    output_path = Path(output_file)
    
    print(f"💾 正在保存合并结果到: {output_path}")
    
    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for track_id, data in merged_data.items():
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"✅ 成功保存 {len(merged_data)} 条数据到: {output_path}")
        print(f"📁 文件大小: {output_path.stat().st_size / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")

def main():
    """主函数"""
    # 默认输入文件
    default_files = [
        "data/filtered_normal_data_1883.jsonl",
        "data/track_id_diff_result_56.jsonl"
    ]
    
    # 检查命令行参数
    if len(sys.argv) > 2:
        input_files = sys.argv[1:-1]  # 除了最后一个参数外都是输入文件
        output_file = sys.argv[-1]    # 最后一个参数是输出文件
    elif len(sys.argv) == 2:
        input_files = default_files
        output_file = sys.argv[1]
    else:
        input_files = default_files
        output_file = "data/merged_data.jsonl"
    
    print("=" * 80)
    print("🔗 合并JSONL文件并基于track_id去重")
    print("=" * 80)
    print("📁 输入文件:")
    for i, file in enumerate(input_files, 1):
        print(f"  {i}. {file}")
    print(f"📄 输出文件: {output_file}")
    print()
    
    # 检查输入文件是否存在
    existing_files = []
    for file_path in input_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            # 尝试一些常见的文件名变体
            base_name = Path(file_path).stem
            parent_dir = Path(file_path).parent
            
            # 如果文件名包含数字，尝试不同的数字
            if "track_id_diff_result" in base_name:
                # 尝试寻找实际的差异结果文件
                potential_files = list(parent_dir.glob("track_id_diff_result*.jsonl"))
                if potential_files:
                    actual_file = potential_files[0]
                    print(f"🔍 找到相似文件: {actual_file}")
                    existing_files.append(str(actual_file))
                    continue
            
            print(f"⚠️ 文件不存在: {file_path}")
    
    if not existing_files:
        print("❌ 没有找到有效的输入文件")
        return
    
    # 执行合并
    print("🔸 步骤1: 加载和去重数据...")
    merged_data = load_jsonl_with_dedup(existing_files)
    
    if not merged_data:
        print("❌ 没有找到有效数据")
        return
    
    print()
    print("🔸 步骤2: 保存合并结果...")
    save_merged_data(merged_data, output_file)
    
    print()
    print("=" * 80)
    print("🎉 合并完成!")
    print("=" * 80)
    
    # 显示一些统计信息
    if merged_data:
        print("📋 合并结果统计:")
        print(f"  🎯 唯一track_id数量: {len(merged_data):,}")
        
        # 显示前几个track_id作为示例
        sample_track_ids = list(merged_data.keys())[:5]
        print(f"  📝 示例track_id:")
        for i, track_id in enumerate(sample_track_ids, 1):
            print(f"    {i}. {track_id}")
        
        if len(merged_data) > 5:
            print(f"    ... 还有 {len(merged_data) - 5:,} 个")

if __name__ == "__main__":
    main()
