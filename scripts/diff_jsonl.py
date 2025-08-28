#!/usr/bin/env python3
"""
比较两个JSONL文件，找出track_id在文件1中存在但在文件2中不存在的数据
"""
import json
import sys
from pathlib import Path

def load_track_ids(jsonl_file):
    """
    从JSONL文件中加载所有track_id
    
    Args:
        jsonl_file: JSONL文件路径
        
    Returns:
        set: track_id集合
    """
    track_ids = set()
    file_path = Path(jsonl_file)
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return track_ids
    
    print(f"📖 正在读取文件: {file_path.name}")
    
    line_count = 0
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
                    
                    if track_id:
                        track_ids.add(track_id)
                        
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ 第 {line_num} 行JSON解析错误: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return set()
    
    print(f"  ✅ 共找到 {len(track_ids)} 个唯一track_id")
    return track_ids

def load_data_with_track_ids(jsonl_file, target_track_ids):
    """
    从JSONL文件中加载指定track_id的数据
    
    Args:
        jsonl_file: JSONL文件路径
        target_track_ids: 目标track_id集合
        
    Returns:
        list: 匹配的数据列表
    """
    matched_data = []
    file_path = Path(jsonl_file)
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return matched_data
    
    print(f"📖 正在从 {file_path.name} 中提取目标数据...")
    
    line_count = 0
    found_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                line_count += 1
                
                # 每处理1000行显示进度
                if line_count % 1000 == 0:
                    print(f"  📊 已处理 {line_count} 行，找到 {found_count} 条目标数据...")
                
                try:
                    data = json.loads(line)
                    track_id = data.get('track_id')
                    
                    if track_id in target_track_ids:
                        matched_data.append(data)
                        found_count += 1
                        
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ 第 {line_num} 行JSON解析错误: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return []
    
    print(f"  ✅ 共找到 {len(matched_data)} 条目标数据")
    return matched_data

def main():
    """主函数"""
    # 默认输入文件
    file1_default = "data/filtered_normal_data_1883.jsonl"
    file2_default = "data/WebMainBench_1827_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl"
    
    # 检查命令行参数
    if len(sys.argv) >= 3:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
    else:
        file1 = file1_default
        file2 = file2_default
    
    print("=" * 80)
    print("🔍 比较JSONL文件中的track_id差异")
    print("=" * 80)
    print(f"📁 文件1 (源文件): {file1}")
    print(f"📁 文件2 (对比文件): {file2}")
    print(f"🎯 目标: 找出在文件1中存在但在文件2中不存在的track_id数据")
    print()
    
    # 步骤1: 加载文件1的所有track_id
    print("🔸 步骤1: 加载文件1的track_id...")
    track_ids_file1 = load_track_ids(file1)
    
    if not track_ids_file1:
        print("❌ 文件1中没有找到有效的track_id")
        return
    
    print()
    
    # 步骤2: 加载文件2的所有track_id
    print("🔸 步骤2: 加载文件2的track_id...")
    track_ids_file2 = load_track_ids(file2)
    
    if not track_ids_file2:
        print("❌ 文件2中没有找到有效的track_id")
        return
    
    print()
    
    # 步骤3: 计算差集
    print("🔸 步骤3: 计算差集...")
    diff_track_ids = track_ids_file1 - track_ids_file2
    common_track_ids = track_ids_file1 & track_ids_file2
    
    print(f"  📊 文件1中的track_id数量: {len(track_ids_file1):,}")
    print(f"  📊 文件2中的track_id数量: {len(track_ids_file2):,}")
    print(f"  📊 共同的track_id数量: {len(common_track_ids):,}")
    print(f"  ⭐ 差异的track_id数量: {len(diff_track_ids):,}")
    
    if not diff_track_ids:
        print("\n🎉 没有发现差异！文件1中的所有track_id在文件2中都存在。")
        return
    
    print()
    
    # 步骤4: 提取差异数据
    print("🔸 步骤4: 提取差异数据...")
    diff_data = load_data_with_track_ids(file1, diff_track_ids)
    
    if not diff_data:
        print("❌ 没有找到差异数据")
        return
    
    print()
    
    # 步骤5: 保存结果
    print("🔸 步骤5: 保存差异数据...")
    output_file = "data/track_id_diff_result.jsonl"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for data in diff_data:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"✅ 已保存 {len(diff_data)} 条差异数据到: {output_file}")
        
        # 显示前几个差异的track_id作为示例
        print(f"\n📋 差异track_id示例 (前10个):")
        for i, track_id in enumerate(list(diff_track_ids)[:10], 1):
            print(f"  {i}. {track_id}")
        
        if len(diff_track_ids) > 10:
            print(f"  ... 还有 {len(diff_track_ids) - 10} 个")
            
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")
        return
    
    print("\n" + "=" * 80)
    print("🎉 比较完成!")
    print("=" * 80)

if __name__ == "__main__":
    main()
