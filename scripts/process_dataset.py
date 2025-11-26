#!/usr/bin/env python3
"""
为数据集添加 llm_webkit430_main_html 字段
根据 llm_webkit_extractor.py 的逻辑，从现有字段构建 main_html
使用方法:
    python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl
"""

import json
import argparse
from pathlib import Path


def process_single_item(data: dict, verbose: bool = False) -> dict:
    """
    为单个JSON对象添加 llm_webkit430_main_html 字段
    
    参考 llm_webkit_extractor.py:665-670 的逻辑
    """
    try:
        # 导入必要的模块
        from llm_web_kit.input.pre_data_json import PreDataJson, PreDataJsonKey
        from llm_web_kit.main_html_parser.parser.tag_mapping import MapItemToHtmlTagsParser

        # 从数据中获取字段
        typical_raw_tag_html = data.get('llm_webkit_html', '')  # 预处理HTML
        html = data.get('llm_webkit_html', '')  # 预处理HTML
        llm_response = data.get('llm_response_html', '')  # LLM响应HTML

        # 检查必要字段
        if not typical_raw_tag_html:
            if verbose:
                print("  ⚠️  llm_webkit_html 字段为空，跳过")
            data['llm_webkit430_main_html'] = ""
            return data

        # 构建 pre_data（参考 llm_webkit_extractor.py:665）
        pre_data = {
            'typical_raw_tag_html': typical_raw_tag_html,
            'typical_raw_html': html,
            'llm_response': llm_response,
            'html_source': typical_raw_tag_html
        }

        # 转换为 PreDataJson 对象
        pre_data = PreDataJson(pre_data)

        # 映射 - 使用 MapItemToHtmlTagsParser
        parser = MapItemToHtmlTagsParser({})
        pre_data = parser.parse(pre_data)

        # 提取 main_html
        main_html = pre_data.get(PreDataJsonKey.TYPICAL_MAIN_HTML, "")

        # 添加新字段
        data['llm_webkit430_main_html'] = main_html

        return data

    except ImportError as e:
        if verbose:
            print(f"\n❌ 导入错误: {e}")
            print("   请确保安装了 llm_web_kit: pip install llm-webkit")
        data['llm_webkit430_main_html'] = ""
        return data
    except Exception as e:
        if verbose:
            import traceback
            print(f"\n⚠️  处理失败: {e}")
            print(f"   错误详情: {traceback.format_exc()}")
        # 失败时添加空字段
        data['llm_webkit430_main_html'] = ""
        return data


def process_dataset(input_file: str, output_file: str = None, verbose: bool = False, test_first: int = None):
    """
    处理整个数据集
    
    Args:
        input_file: 输入JSONL文件路径
        output_file: 输出JSONL文件路径（默认为输入文件名_with_main_html.jsonl）
        verbose: 是否显示详细信息
        test_first: 仅处理前N条数据（用于测试）
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"❌ 文件不存在: {input_file}")
        return

    # 确定输出文件名
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_with_main_html.jsonl")

    print(f"📄 输入文件: {input_file}")
    print(f"📄 输出文件: {output_file}")
    if test_first:
        print(f"🧪 测试模式: 仅处理前 {test_first} 条数据")

    # 检查依赖
    print("\n🔍 检查依赖...")
    try:
        from llm_web_kit.input.pre_data_json import PreDataJson, PreDataJsonKey
        from llm_web_kit.main_html_parser.parser.tag_mapping import MapItemToHtmlTagsParser
        print("✅ llm_web_kit 模块可用")
    except ImportError as e:
        print(f"❌ llm_web_kit 模块未安装: {e}")
        print("   请运行: pip install llm-webkit")
        return

    # 统计信息
    total = 0
    success = 0
    failed = 0

    # 先统计总行数（用于进度条）
    print("\n📊 统计总行数...")
    with open(input_file, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)

    if test_first:
        total_lines = min(total_lines, test_first)

    print(f"📦 总共 {total_lines:,} 条数据\n")

    # 处理数据
    print("🔄 开始处理...\n")
    try:
        with open(input_file, 'r', encoding='utf-8') as fin, \
             open(output_file, 'w', encoding='utf-8') as fout:

            for idx, line in enumerate(fin, 1):
                # 测试模式：只处理前N条
                if test_first and idx > test_first:
                    break

                if not line.strip():
                    continue

                try:
                    # 解析JSON
                    data = json.loads(line)
                    total += 1

                    # 显示进度（每100条显示一次）
                    if total % 100 == 0:
                        print(f"  处理进度: {total}/{total_lines} ({total/total_lines*100:.1f}%)")

                    # 处理单条数据
                    if verbose and idx <= 3:
                        print(f"\n处理第 {idx} 条数据...")

                    processed_data = process_single_item(data, verbose=(verbose and idx <= 3))

                    # 检查是否成功添加字段
                    if processed_data.get('llm_webkit430_main_html'):
                        success += 1
                    else:
                        failed += 1

                    # 写入输出文件
                    fout.write(json.dumps(processed_data, ensure_ascii=False) + '\n')

                except json.JSONDecodeError as e:
                    print(f"\n⚠️  行 {idx} JSON解析错误: {e}")
                    failed += 1
                    # 写入原始行
                    fout.write(line)
                except Exception as e:
                    print(f"\n❌ 行 {idx} 处理错误: {e}")
                    if verbose:
                        import traceback
                        print(traceback.format_exc())
                    failed += 1
                    # 写入原始数据
                    try:
                        data['llm_webkit430_main_html'] = ""
                        fout.write(json.dumps(data, ensure_ascii=False) + '\n')
                    except:
                        fout.write(line)

    except Exception as e:
        print(f"\n❌ 处理过程中发生严重错误: {e}")
        import traceback
        print(traceback.format_exc())
        return

    # 输出统计信息
    print("\n" + "="*60)
    print("✅ 处理完成！")
    print("="*60)
    print(f"总处理数: {total:,}")
    print(f"成功: {success:,} ({success/total*100:.1f}%)" if total > 0 else "成功: 0")
    print(f"失败: {failed:,} ({failed/total*100:.1f}%)" if total > 0 else "失败: 0")
    print(f"\n输出文件: {output_file}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='为数据集添加 llm_webkit430_main_html 字段',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 基本使用
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl
  
  # 指定输出文件
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl \\
    --output data/WebMainBench_7887_with_main_html.jsonl
  
  # 测试前10条数据
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl \\
    --test-first 10 --verbose
  
  # 详细模式（显示前3条的处理细节）
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl \\
    --verbose
        '''
    )

    parser.add_argument(
        'input_file',
        help='输入JSONL文件路径'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='输出JSONL文件路径（默认：输入文件名_with_main_html.jsonl）'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='显示详细处理信息（仅显示前3条）'
    )

    parser.add_argument(
        '--test-first',
        '-t',
        type=int,
        help='仅处理前N条数据（用于测试）'
    )

    args = parser.parse_args()

    # 处理数据集
    process_dataset(args.input_file, args.output, args.verbose, args.test_first)


if __name__ == '__main__':
    main()