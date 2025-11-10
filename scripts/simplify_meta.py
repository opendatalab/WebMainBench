#!/usr/bin/env python3
"""
简化meta字段工具
只保留指定的meta字段，移除其他复杂的统计信息
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List

class MetaSimplifier:
    """Meta字段简化器"""
    
    def __init__(self):
        """初始化简化器"""
        self.processed_count = 0
        self.error_count = 0
        
    def simplify_meta(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        简化meta字段
        
        Args:
            data: 原始数据记录
            
        Returns:
            简化后的数据记录
        """
        if 'meta' not in data:
            return data
            
        original_meta = data['meta']
        
        # 构建简化的meta字段
        simplified_meta = {}
        
        # 保留指定字段
        if 'language' in original_meta:
            simplified_meta['language'] = original_meta['language']
            
        if 'table' in original_meta:
            simplified_meta['table'] = original_meta['table']
        else:
            simplified_meta['table'] = []
            
        if 'code' in original_meta:
            simplified_meta['code'] = original_meta['code']
        else:
            simplified_meta['code'] = []
            
        if 'equation' in original_meta:
            simplified_meta['equation'] = original_meta['equation']
        else:
            simplified_meta['equation'] = []
            
        if 'level' in original_meta:
            simplified_meta['level'] = original_meta['level']
            
        # 处理style字段 - 只保留category值作为style
        if 'style' in original_meta and isinstance(original_meta['style'], dict):
            style_category = original_meta['style'].get('category', 'Other')
            simplified_meta['style'] = style_category
        elif 'style' in original_meta and isinstance(original_meta['style'], str):
            # 如果style已经是字符串，直接使用
            simplified_meta['style'] = original_meta['style']
        else:
            simplified_meta['style'] = 'Other'
        
        # 更新数据记录
        data['meta'] = simplified_meta
        return data
    
    def process_file(self, input_file: str, output_file: str) -> None:
        """
        处理文件，简化meta字段
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
        """
        print(f"📄 正在处理文件: {input_file}")
        print(f"📄 输出文件: {output_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8') as outfile:
                
                for line_num, line in enumerate(infile, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # 简化meta字段
                        simplified_data = self.simplify_meta(data)
                        
                        # 写入输出文件
                        outfile.write(json.dumps(simplified_data, ensure_ascii=False) + '\n')
                        
                        self.processed_count += 1
                        
                        if line_num % 1000 == 0:
                            print(f"  已处理 {line_num:,} 条数据...")
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️  第{line_num}行JSON解析错误: {e}")
                        self.error_count += 1
                        continue
                    except Exception as e:
                        print(f"⚠️  第{line_num}行处理错误: {e}")
                        self.error_count += 1
                        continue
                        
        except FileNotFoundError:
            print(f"❌ 文件未找到: {input_file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 处理文件时出错: {e}")
            sys.exit(1)
    
    def print_summary(self) -> None:
        """打印处理统计摘要"""
        print(f"\n📊 处理统计摘要:")
        print(f"   成功处理记录数: {self.processed_count:,}")
        print(f"   错误记录数: {self.error_count:,}")
        
        if self.processed_count > 0:
            success_rate = (self.processed_count / (self.processed_count + self.error_count)) * 100
            print(f"   成功率: {success_rate:.2f}%")


def show_before_after_example(input_file: str) -> None:
    """
    显示简化前后的示例对比
    
    Args:
        input_file: 输入文件路径
    """
    print("\n📋 简化前后对比示例:")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # 读取第一条记录
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    
                    if 'meta' in data:
                        print("\n🔍 简化前的meta字段:")
                        print(json.dumps(data['meta'], ensure_ascii=False, indent=2)[:500] + "...")
                        
                        # 简化
                        simplifier = MetaSimplifier()
                        simplified_data = simplifier.simplify_meta(data.copy())
                        
                        print("\n✨ 简化后的meta字段:")
                        print(json.dumps(simplified_data['meta'], ensure_ascii=False, indent=2))
                        
                    break
                    
    except Exception as e:
        print(f"⚠️  无法显示示例: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="简化meta字段，只保留指定的字段",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
简化后的meta字段包含:
  - language: str - 语言标识
  - table: list[str] - 表格相关信息
  - code: list[str] - 代码相关信息  
  - equation: list[str] - 公式相关信息
  - level: str - 复杂度级别
  - style: str - 网页类型(原meta.style.category)

示例用法:
  # 基本简化
  python scripts/simplify_meta.py \\
    data/WebMainBench_7887_with_meta.jsonl \\
    --output data/WebMainBench_7887_simplified.jsonl
    
  # 显示简化示例
  python scripts/simplify_meta.py \\
    data/WebMainBench_7887_with_meta.jsonl \\
    --output data/WebMainBench_7887_simplified.jsonl \\
    --show-example
        """
    )
    
    parser.add_argument(
        "input_file",
        help="输入JSONL文件路径"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出简化后的JSONL文件路径"
    )
    
    parser.add_argument(
        "--show-example",
        action="store_true",
        help="显示简化前后的示例对比"
    )
    
    args = parser.parse_args()
    
    # 验证输入文件
    if not Path(args.input_file).exists():
        print(f"❌ 输入文件不存在: {args.input_file}")
        sys.exit(1)
    
    # 显示示例
    if args.show_example:
        show_before_after_example(args.input_file)
        print("\n" + "="*60)
    
    # 创建简化器
    simplifier = MetaSimplifier()
    
    # 处理文件
    simplifier.process_file(args.input_file, args.output)
    
    # 打印统计摘要
    simplifier.print_summary()
    
    print(f"\n✅ 简化完成! 输出文件: {args.output}")


if __name__ == "__main__":
    main()

