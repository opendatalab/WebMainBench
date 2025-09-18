#!/usr/bin/env python3
"""
网页类型分类工具
用于为数据集中的网页内容添加类型标签
"""

import json
import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from collections import Counter
import time

class StyleClassifier:
    """网页类型分类器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5", base_url: str = "https://api.deepseek.com/v1"):
        """
        初始化网页类型分类器
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
            base_url: 模型请求的基础URL地址
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.supported_categories = self._get_supported_categories()
        
    def _get_supported_categories(self) -> Dict[str, List[str]]:
        """获取支持的网页类型分类"""
        return {
            "Article": [
                "Blog", "News", "Tutorial", "Multiple data article", 
                "Product page", "other article"
            ],
            "Forum_or_Article_with_commentsection": [
                "Forum", "Article_with_commentsection"
            ],
            "Content Listing": [
                "navigation listing", "irrelevant content listing"
            ],
            "Other": [
                "login", "register", "error", "paywall", "truncated", "other"
            ]
        }
    
    def get_style_classification_prompt(self, url: str, html_content: str) -> str:
        """
        生成网页类型分类的prompt
        
        Args:
            url: 网页URL
            html_content: 网页HTML内容
            
        Returns:
            格式化的prompt
        """
        prompt = f"""You are an expert in web page classification with a strong focus on web page layout, content analysis, and user interaction. Your task is to accurately classify the provided simplified HTML source code into one of the main categories listed below, while also identifying an appropriate subcategory if applicable. Pay attention to html tag name and significant structural elements.

When faced with multiple classifications, choose the one that best represents the overall purpose and structure of the page. **Key distinctions include**:
- **Article**: 
   - These pages feature in-depth narratives or detailed discussions without comment section, also includes product detail page.
   - subcategory: Blog, News, Tutorial, Multiple data article, Product page, other article.
   - Examples: wikipedia, bbc news, product detail page.
   - Note: Some article pages may have advertiment or posts in the middle, but it is not the primary focus.

- **Forum_or_Article_with_commentsection**: 
   - This page must have comment section. The main content includes tree-like discussion forum or Article around a topic with multiple posts or comments from different users at the end, except for mailing list archive pages. Some pages set comment section but with no comments temporarily.
   - subcategory: Forum, Article_with_commentsection
   - Example: Forum like reddit, stackoverflow, quora, etc. Article_with_commentsection like weibo, zhihu, etc.
   - Note: Forum homepage is intend to navigation, so it is classified as **Content Listing**. Some forum use article tag to display topic, but it is intend to discussion, classify as **Forum_or_Article_with_commentsection**.

- **Content Listing**: 
   - Pages primarily serving as navigation tools with minimal content on irrelevant topics(e.g., product catalogs or sitemaps) fall into this category.
   - subcategory: navigation listing, irrelevant content listing
   - Example: product catalogs, news listings with short snippets of articles, Forum Topic Listing Page.
   - Note: If the content is relevant, it cannot count in this category, such as different parts in an article.

- **Other**:
   - Any pages with incomplete, generic, or non-informative content (e.g., error pages, login forms) that do not fit the above categories.
   - subcategory: login, register, error, paywall, truncated, other

**Instructions for Classification**:
1. Identify the main content of the page by looking at the HTML structure and the presence of significant tags like `<article>`, `<section>`, `<div>`, etc.
2. Determine if the page contains a discussion forum or a comment section by checking for <div class> or <div id> elements like `<form>`, `<textarea>`, `<user-comment>`and `<input type="submit">`. If have comment section or comments, classify it as "Forum_or_Article_with_commentsection", and explanation should include "has_commentsection=true/false" and "has_comments=true/false" in the response.
3. Analyze the overall purpose and structure of the page to determine if it is a content listing, article, or other.
4. If the page contains multiple classifications, choose the one that best represents the overall purpose and structure of the page.

Start your response with Cateory name and subcategory name followed by an brief explanation in 50 words.Separate cateory name, subcategory, explanation with a vertical bar |, do not use other symbols.

Example:
URL: https://lists.swift.org/pipermail/swift-evolution/Week-of-Mon-20170918/039878.html
HTML Text:
<html>\\n <body>\\n  <h1>\\n   [swift-evolution] (core library) modern URL types\\n  </h1>\\n  <b>\\n   Taylor Swift kelvin13ma at gmail.com Thu Sep 21 12:52:43 CDT 2017\\n  </b>\\n  <ul>\\n   <li>\\n    Previous message: [swift-evolution] (core library) modern URL types\\n   </li>\\n   <li>\\n    Next message: [swift-evolution] Retroactive protocol inheritance\\n   </li>\\n   <li>\\n    <b>\\n     Messages sorted by: [ date ] [ thread ] [ subject ] [ author ]\\n    </b>\\n   </li>\\n  </ul>\\n  <pre>great work! it looks like there is quite a lot of duplicated work going on\\nhere though which is unfortunate. how do we reconcile these 2\\nimplementations?\\n\\nOn Thu, Sep 21, 2017 at 12:16 PM, Aleksey Mashanov &lt; aleksey.mashanov at gmail.com &gt; wrote:\\n\\n&gt; I have an alternative implementation of a URI (a superset of URL).  As I said, this is still really early on and not a mature library at all &gt;&gt; but everyone is invited to observe, provide feedback, or contribute! &gt;&gt; &gt;&gt; _______________________________________________ &gt;&gt; swift-evolution mailing list &gt;&gt; swift-evolution at swift.org &gt;&gt; https://lists.swift.org/mailman/listinfo/swift-evolution &gt;&gt; &gt;&gt; &gt; -------------- next part --------------\\nAn HTML attachment was scrubbed...\\nURL: &lt; https://lists.swift.org/pipermail/swift-evolution/attachments/20170921/f1c65353/attachment.html &gt;</pre>\\n  <ul>\\n   <li>\\n    Previous message: [swift-evolution] (core library) modern URL types\\n   </li>\\n   <li>\\n    Next message: [swift-evolution] Retroactive protocol inheritance\\n   </li>\\n   <li>\\n    <b>\\n     Messages sorted by: [ date ] [ thread ] [ subject ] [ author ]\\n    </b>\\n   </li>\\n  </ul>\\n  <a>\\n   More information about the swift-evolution\\nmailing list\\n  </a>\\n </body>\\n</html>\\n

[Answer]: Article | other Article | has_commentsection=false, has_comments=false, This page is mailing list archives, belong to "Article", 


URL: {url}
HTML Text:
{html_content[:8000]}{"..." if len(html_content) > 8000 else ""}
[Answer]: """
        
        return prompt
    
    def detect_style_llm(self, url: str, html_content: str) -> str:
        """
        使用LLM进行网页类型检测
        
        Args:
            url: 网页URL
            html_content: 网页HTML内容
            
        Returns:
            网页类型分类结果
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
            
            prompt = self.get_style_classification_prompt(url, html_content)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            
            # 解析结果格式: Category | subcategory | explanation
            parts = result.split('|')
            if len(parts) >= 3:
                category = parts[0].strip()
                subcategory = parts[1].strip()
                explanation = parts[2].strip()
                
                # 验证分类是否在支持列表中
                if category in self.supported_categories:
                    return f"{category}|{subcategory}|{explanation}"
                else:
                    print(f"⚠️  LLM返回了无效的分类: {category}，返回默认分类")
                    return "Other|other|LLM returned invalid category"
            else:
                print(f"⚠️  LLM返回了格式错误的结果: {result}，返回默认分类")
                return "Other|other|LLM returned malformed result"
                
        except Exception as e:
            print(f"⚠️  LLM检测失败: {e}，返回默认分类")
            return "Other|other|LLM detection failed"
    
    def detect_style(self, url: str, html_content: str) -> str:
        """
        检测网页类型
        
        Args:
            url: 网页URL
            html_content: 网页HTML内容
            
        Returns:
            网页类型分类结果
        """
        return self.detect_style_llm(url, html_content)
    
    def process_jsonl(self, input_file: str, output_file: str, 
                     batch_size: int = 100) -> None:
        """
        处理JSONL文件，添加网页类型标签
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            batch_size: 批处理大小
        """
        print(f"🔄 开始处理网页类型分类...")
        print(f"📄 输入文件: {input_file}")
        print(f"📄 输出文件: {output_file}")
        print(f"🧠 检测方法: LLM")
        print(f"🌐 模型地址: {self.base_url}")
        print(f"🤖 使用模型: {self.model}")
        
        # 统计信息
        total_count = 0
        processed_count = 0
        style_stats = Counter()
        
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
                            self._process_batch(batch, outfile, style_stats)
                            processed_count += len(batch)
                            batch = []
                            
                            print(f"  📊 已处理 {processed_count:,} 条数据...")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  第{line_num}行JSON解析错误: {e}")
                        continue
                
                # 处理最后一批
                if batch:
                    self._process_batch(batch, outfile, style_stats)
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
        print(f"📊 网页类型分布:")
        
        for style_result, count in style_stats.most_common():
            percentage = (count / processed_count) * 100 if processed_count > 0 else 0
            # 解析分类结果
            parts = style_result.split('|')
            category = parts[0] if len(parts) > 0 else "Unknown"
            subcategory = parts[1] if len(parts) > 1 else "Unknown"
            print(f"   {category} -> {subcategory}: {count:,} ({percentage:.1f}%)")
    
    def _process_batch(self, batch: List[Dict], outfile, style_stats: Counter) -> None:
        """
        处理一批数据
        
        Args:
            batch: 数据批次
            outfile: 输出文件对象
            style_stats: 网页类型统计计数器
        """
        for data in batch:
            # 获取URL和HTML内容
            url = data.get('url', '')
            html_content = data.get('main_html', '')
            
            # 如果没有main_html，尝试其他字段
            if not html_content:
                html_content = data.get('html', '')
            
            # 检测网页类型
            if url and html_content:
                style_result = self.detect_style(url, html_content)
            else:
                style_result = "Other|other|Missing URL or HTML content"
            
            # 解析分类结果
            parts = style_result.split('|')
            category = parts[0].strip() if len(parts) > 0 else "Other"
            subcategory = parts[1].strip() if len(parts) > 1 else "other"
            
            # 更新数据
            if 'meta' not in data:
                data['meta'] = {}
            data['meta']['style'] = {
                'category': category,
                'subcategory': subcategory,
                'full_result': style_result
            }
            
            # 统计
            style_stats[style_result] += 1
            
            # 写入输出文件
            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            # 添加延迟避免速率限制
            time.sleep(0.1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="为JSONL数据集添加网页类型标签",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用LLM进行网页类型分类
  python scripts/style_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY
  
  # 指定自定义模型地址和批处理大小
  python scripts/style_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --base-url https://custom-url/v1 --batch-size 50
  
  # 使用默认地址和指定模型
  python scripts/style_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --model gpt-4
        """
    )
    
    parser.add_argument(
        "input_file",
        help="输入JSONL文件路径"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出JSONL文件路径"
    )
    
    parser.add_argument(
        "--api-key",
        required=True,
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API密钥（必需）"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-5",
        help="LLM模型名称 (默认: gpt-5)"
    )
    
    parser.add_argument(
        "--base-url",
        required=True,
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
    classifier = StyleClassifier(
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url
    )
    
    # 处理数据
    classifier.process_jsonl(
        input_file=args.input_file,
        output_file=args.output,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
