#!/usr/bin/env python3
"""
过滤JSONL文件中marked_type为normal的数据
"""
import json
import sys
from pathlib import Path

def filter_normal_data(input_file):
    """
    过滤marked_type为normal的数据
    
    Args:
        input_file: 输入的JSONL文件路径
        
    Returns:
        tuple: (normal_data_list, total_count, normal_count)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        return [], 0, 0
    
    normal_data = []
    total_count = 0
    normal_count = 0
    
    print(f"📖 正在读取文件: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                total_count += 1
                
                # 每处理1000行显示进度
                if total_count % 1000 == 0:
                    print(f"📊 已处理 {total_count} 行...")
                
                try:
                    data = json.loads(line)
                    marked_type = data.get('marked_type', '')
                    
                    if marked_type == 'normal':
                        normal_count += 1
                        normal_data.append(data)
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ 第 {line_num} 行JSON解析错误: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return [], 0, 0
    
    return normal_data, total_count, normal_count

def main():
    """主函数"""
    # 默认输入文件
    default_input = "data/WebMainBench_dataset_merge_2549_llm_webkit.jsonl"
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input
    
    print("=" * 60)
    print("🔍 过滤 marked_type 为 'normal' 的数据")
    print("=" * 60)
    
    # 执行过滤
    normal_data, total_count, normal_count = filter_normal_data(input_file)
    
    # 输出统计结果
    print("\n" + "=" * 60)
    print("📊 统计结果")
    print("=" * 60)
    print(f"📁 输入文件: {input_file}")
    print(f"📄 总数据条数: {total_count:,}")
    print(f"✅ normal类型数据: {normal_count:,}")
    
    if total_count > 0:
        percentage = (normal_count / total_count) * 100
        print(f"📈 normal类型占比: {percentage:.2f}%")
    
    # 显示其他统计信息
    other_count = total_count - normal_count
    if other_count > 0:
        other_percentage = (other_count / total_count) * 100
        print(f"📊 其他类型数据: {other_count:,} ({other_percentage:.2f}%)")
    
    # 询问是否保存过滤结果
    if normal_count > 0:
        print(f"\n💾 是否保存过滤结果? 将保存到 filtered_normal_data.jsonl")
        user_input = input("输入 'y' 保存，其他键跳过: ").strip().lower()
        
        if user_input == 'y':
            output_file = "filtered_normal_data.jsonl"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    for data in normal_data:
                        f.write(json.dumps(data, ensure_ascii=False) + '\n')
                print(f"✅ 已保存 {normal_count} 条normal类型数据到: {output_file}")
            except Exception as e:
                print(f"❌ 保存文件时出错: {e}")
    
    print("\n🎉 处理完成!")

if __name__ == "__main__":
    main()
