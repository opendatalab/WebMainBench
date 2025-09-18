#!/usr/bin/env python3
"""
语言分类工具
用于为数据集中的文本内容添加语言标签（ISO 639-1 标准）
"""

import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import os
from collections import Counter
import time

class LanguageClassifier:
    """语言分类器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5", base_url: str = "https://api.deepseek.com/v1"):
        """
        初始化语言分类器
        
        Args:
            api_key: OpenAI API密钥（如果使用LLM）
            model: 使用的模型名称
            base_url: 模型请求的基础URL地址
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.supported_languages = self._get_supported_languages()
        
    def _get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表（ISO 639-1 标准）"""
        return {
            # 主要语言
            'en': 'English',
            'zh': 'Chinese',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian',
            'ar': 'Arabic',
            'pt': 'Portuguese',
            'it': 'Italian',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ur': 'Urdu',
            'fa': 'Persian',
            'he': 'Hebrew',
            'cs': 'Czech',
            'sk': 'Slovak',
            'hu': 'Hungarian',
            'ro': 'Romanian',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sr': 'Serbian',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'uk': 'Ukrainian',
            'be': 'Belarusian',
            'ka': 'Georgian',
            'hy': 'Armenian',
            'az': 'Azerbaijani',
            'kk': 'Kazakh',
            'ky': 'Kyrgyz',
            'uz': 'Uzbek',
            'tg': 'Tajik',
            'mn': 'Mongolian',
            'my': 'Burmese',
            'km': 'Khmer',
            'lo': 'Lao',
            'si': 'Sinhala',
            'ne': 'Nepali',
            'ml': 'Malayalam',
            'kn': 'Kannada',
            'gu': 'Gujarati',
            'or': 'Odia',
            'pa': 'Punjabi',
            'as': 'Assamese',
            'mt': 'Maltese',
            'is': 'Icelandic',
            'ga': 'Irish',
            'cy': 'Welsh',
            'eu': 'Basque',
            'ca': 'Catalan',
            'gl': 'Galician',
            'af': 'Afrikaans',
            'sq': 'Albanian',
            'mk': 'Macedonian',
            'bs': 'Bosnian',
            'me': 'Montenegrin',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Filipino',
            'sw': 'Swahili',
            'am': 'Amharic',
            'ti': 'Tigrinya',
            'so': 'Somali',
            'zu': 'Zulu',
            'xh': 'Xhosa',
            'st': 'Southern Sotho',
            'tn': 'Tswana',
            'ss': 'Swazi',
            've': 'Venda',
            'ts': 'Tsonga',
            'nr': 'Southern Ndebele'
        }
    
    def get_language_detection_prompt(self, text: str) -> str:
        """
        生成语言检测的prompt
        
        Args:
            text: 需要检测语言的文本
            
        Returns:
            格式化的prompt
        """
        # 构建支持的语言列表字符串
        lang_list = ", ".join([f"{code} ({name})" for code, name in sorted(self.supported_languages.items())])
        
        prompt = f"""Please identify the primary language of the following text and return ONLY the ISO 639-1 two-letter language code.

SUPPORTED LANGUAGES:
{lang_list}

RULES:
1. Return ONLY the two-letter ISO 639-1 code (e.g., "en", "zh", "es")
2. If the text contains multiple languages, return the code for the DOMINANT language
3. If the text is empty or contains only symbols/numbers, return "en" as default
4. If the language is not in the supported list, return the closest supported language
5. For Chinese text, return "zh" regardless of Traditional/Simplified variant
6. Do not include any explanation, punctuation, or additional text

TEXT TO ANALYZE:
{text[:2000]}{"..." if len(text) > 2000 else ""}

LANGUAGE CODE:"""
        
        return prompt
    
    
    def detect_language_llm(self, text: str) -> str:
        """
        使用LLM进行语言检测
        
        Args:
            text: 需要检测的文本
            
        Returns:
            ISO 639-1 语言代码
        """
        try:
            from openai import OpenAI
            
            if not self.api_key:
                raise ValueError("API key is required for LLM detection")
            
            # 配置OpenAI客户端
            client = OpenAI(
                base_url = self.base_url,
                api_key = self.api_key
            )
            
            prompt = self.get_language_detection_prompt(text)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # 验证返回的语言代码
            if result in self.supported_languages:
                return result
            else:
                print(f"⚠️  LLM返回了无效的语言代码: {result}，返回默认语言")
                return "en"
                
        except Exception as e:
            print(f"⚠️  LLM检测失败: {e}，返回默认语言")
            return "en"
    
    def detect_language(self, text: str) -> str:
        """
        使用LLM检测文本语言
        
        Args:
            text: 需要检测的文本
            
        Returns:
            ISO 639-1 语言代码
        """
        return self.detect_language_llm(text)
    
    def process_jsonl(self, input_file: str, output_file: str, 
                     batch_size: int = 100) -> None:
        """
        处理JSONL文件，添加语言标签
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            batch_size: 批处理大小
        """
        print(f"🔄 开始处理语言分类...")
        print(f"📄 输入文件: {input_file}")
        print(f"📄 输出文件: {output_file}")
        print(f"🧠 检测方法: LLM")
        print(f"🌐 模型地址: {self.base_url}")
        print(f"🤖 使用模型: {self.model}")
        
        # 统计信息
        total_count = 0
        processed_count = 0
        language_stats = Counter()
        
        try:
            with open(input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8') as outfile:
                
                batch = []
                
                for line_num, line in enumerate(infile, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        total_count += 1
                        batch.append(data)
                        
                        if len(batch) >= batch_size:
                            self._process_batch(batch, outfile, language_stats)
                            processed_count += len(batch)
                            batch = []
                            
                            print(f"  📊 已处理 {processed_count:,} 条数据...")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  第{line_num}行JSON解析错误: {e}")
                        continue
                
                # 处理最后一批
                if batch:
                    self._process_batch(batch, outfile, language_stats)
                    processed_count += len(batch)
        
        except FileNotFoundError:
            print(f"❌ 文件未找到: {input_file}")
            return
        except Exception as e:
            print(f"❌ 处理过程中出错: {e}")
            return
        
        # 输出统计结果
        print(f"\n✅ 处理完成!")
        print(f"📊 总计处理: {processed_count:,} 条数据")
        print(f"📊 语言分布:")
        
        for lang_code, count in language_stats.most_common():
            lang_name = self.supported_languages.get(lang_code, "Unknown")
            percentage = (count / processed_count) * 100 if processed_count > 0 else 0
            print(f"   {lang_code} ({lang_name}): {count:,} ({percentage:.1f}%)")

    def analyze_language_statistics(self, input_file: str, output_csv: str = None) -> None:
        """
        分析JSONL文件中的语言统计信息并保存到CSV文件
        
        Args:
            input_file: 输入JSONL文件路径
            output_csv: 输出CSV文件路径，默认为输入文件名_language_stats.csv
        """
        if output_csv is None:
            input_path = Path(input_file)
            output_csv = str(input_path.parent / f"{input_path.stem}_language_stats.csv")
        
        print(f"🔍 开始分析语言统计信息...")
        print(f"📄 输入文件: {input_file}")
        print(f"📄 输出CSV: {output_csv}")
        
        # 统计信息
        total_count = 0
        processed_count = 0
        language_stats = Counter()
        
        try:
            with open(input_file, 'r', encoding='utf-8') as infile:
                for line_num, line in enumerate(infile, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        total_count += 1
                        
                        # 从meta字段中获取language信息
                        language = None
                        if 'meta' in data and isinstance(data['meta'], dict):
                            language = data['meta'].get('language')
                        
                        if language:
                            language_stats[language] += 1
                            processed_count += 1
                        else:
                            # 如果没有language字段，记录为未知
                            language_stats['unknown'] += 1
                            processed_count += 1
                            
                        if line_num % 1000 == 0:
                            print(f"  📊 已分析 {line_num:,} 行数据...")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  第{line_num}行JSON解析错误: {e}")
                        continue
        
        except FileNotFoundError:
            print(f"❌ 文件未找到: {input_file}")
            return
        except Exception as e:
            print(f"❌ 分析过程中出错: {e}")
            return
        
        # 生成统计数据
        stats_data = []
        for lang_code, count in language_stats.most_common():
            lang_name = self.supported_languages.get(lang_code, "Unknown" if lang_code != 'unknown' else "未检测到语言")
            percentage = (count / processed_count) * 100 if processed_count > 0 else 0
            stats_data.append({
                'language_code': lang_code,
                'language_name': lang_name,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # 保存到CSV文件
        try:
            import csv
            with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['language_code', 'language_name', 'count', 'percentage']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in stats_data:
                    writer.writerow(row)
            
            print(f"\n✅ 语言统计分析完成!")
            print(f"📊 总计分析: {processed_count:,} 条数据")
            print(f"📊 语言分布:")
            
            for row in stats_data:
                print(f"   {row['language_code']} ({row['language_name']}): {row['count']:,} ({row['percentage']:.1f}%)")
            
            print(f"\n💾 统计结果已保存到: {output_csv}")
            
        except Exception as e:
            print(f"❌ 保存CSV文件时出错: {e}")
            return
    
    def _process_batch(self, batch: List[Dict], outfile, language_stats: Counter) -> None:
        """
        处理一批数据
        
        Args:
            batch: 数据批次
            outfile: 输出文件对象
            language_stats: 语言统计计数器
        """
        for data in batch:
            # 获取文本内容
            text = data.get('convert_main_content', '')
            
            # 如果没有convert_main_content，尝试其他字段
            if not text:
                text = data.get('groundtruth_content', '')
            if not text:
                text = data.get('content', '')
            
            # 检测语言
            if text:
                language = self.detect_language(text)
            else:
                language = "en"  # 默认英语
            
            # 更新数据
            if 'meta' not in data:
                data['meta'] = {}
            data['meta']['language'] = language
            
            # 统计
            language_stats[language] += 1
            
            # 写入输出文件
            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            # 添加延迟避免速率限制
            time.sleep(0.1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="为JSONL数据集添加语言标签 (ISO 639-1 标准) 或统计语言分布",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用LLM进行语言检测
  python scripts/language_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY
  
  # 指定自定义模型地址和批处理大小
  python scripts/language_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --base-url http://custom-url:8080/ --batch-size 50
  
  # 使用默认地址和指定模型
  python scripts/language_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --model gpt-4
  
  # 统计已有文件的语言分布
  python scripts/language_classify.py data/WebMainBench_7887_language_output.jsonl --analyze-only --output-csv data/language_stats.csv
        """
    )
    
    parser.add_argument(
        "input_file",
        help="输入JSONL文件路径"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出JSONL文件路径（仅在非分析模式下必需）"
    )
    
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="仅分析语言统计信息，不进行语言检测"
    )
    
    parser.add_argument(
        "--output-csv",
        help="语言统计结果CSV输出文件路径（仅在分析模式下使用）"
    )
    
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API密钥（仅在语言检测模式下需要）"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-5",
        help="LLM模型名称 (默认: gpt-5)"
    )
    
    parser.add_argument(
        "--base-url",
        default="https://api.deepseek.com/v1/",
        help="模型请求的基础URL地址"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="批处理大小 (默认: 100)"
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if not Path(args.input_file).exists():
        print(f"❌ 输入文件不存在: {args.input_file}")
        sys.exit(1)
    
    # 创建分类器
    classifier = LanguageClassifier(
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url
    )
    
    if args.analyze_only:
        # 仅进行语言统计分析
        classifier.analyze_language_statistics(
            input_file=args.input_file,
            output_csv=args.output_csv
        )
    else:
        # 进行语言检测和分类
        if not args.output:
            print("❌ 在语言检测模式下，--output 参数是必需的")
            sys.exit(1)
        
        if not args.api_key:
            print("❌ 在语言检测模式下，--api-key 参数是必需的")
            sys.exit(1)
        
        classifier.process_jsonl(
            input_file=args.input_file,
            output_file=args.output,
            batch_size=args.batch_size
        )


if __name__ == "__main__":
    main()
