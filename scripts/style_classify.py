#!/usr/bin/env python3
"""
Web page type classification tool
Adds type labels to web page content in the dataset
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
    """Web page type classifier."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5", base_url: str = "https://api.deepseek.com/v1"):
        """
        Initialize web page type classifier.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
            base_url: Base URL for model requests
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.supported_categories = self._get_supported_categories()
        
    def _get_supported_categories(self) -> Dict[str, List[str]]:
        """Get supported web page type categories."""
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
        Generate web page type classification prompt.
        
        Args:
            url: Web page URL
            html_content: Web page HTML content
            
        Returns:
            Formatted prompt
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
        Detect web page type using LLM.
        
        Args:
            url: Web page URL
            html_content: Web page HTML content
            
        Returns:
            Web page type classification result
        """
        try:
            from openai import OpenAI
            
            if not self.api_key:
                raise ValueError("API key is required for LLM detection")
            
            # Configure OpenAI client
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
            
            # Parse result format: Category | subcategory | explanation
            parts = result.split('|')
            if len(parts) >= 3:
                category = parts[0].strip()
                subcategory = parts[1].strip()
                explanation = parts[2].strip()
                
                # Validate category is in supported list
                if category in self.supported_categories:
                    return f"{category}|{subcategory}|{explanation}"
                else:
                    print(f"⚠️  LLM returned invalid category: {category}, returning default")
                    return "Other|other|LLM returned invalid category"
            else:
                print(f"⚠️  LLM returned malformed result: {result}, returning default")
                return "Other|other|LLM returned malformed result"
                
        except Exception as e:
            print(f"⚠️  LLM detection failed: {e}, returning default")
            return "Other|other|LLM detection failed"
    
    def detect_style(self, url: str, html_content: str) -> str:
        """
        Detect web page type.
        
        Args:
            url: Web page URL
            html_content: Web page HTML content
            
        Returns:
            Web page type classification result
        """
        return self.detect_style_llm(url, html_content)
    
    def process_jsonl(self, input_file: str, output_file: str, 
                     batch_size: int = 100) -> None:
        """
        Process JSONL file, adding web page type labels.
        
        Args:
            input_file: Input file path
            output_file: Output file path
            batch_size: Batch size
        """
print(f"🔄 Starting web page type classification...")
        print(f"📄 Input file: {input_file}")
        print(f"📄 Output file: {output_file}")
        print(f"🧠 Detection method: LLM")
        print(f"🌐 Model URL: {self.base_url}")
        print(f"🤖 Model: {self.model}")
        
        # Statistics
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
                            
    print(f"  📊 Processed {processed_count:,} records...")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON parse error at line {line_num}: {e}")
                        continue
                
                # Process the last batch
                if batch:
                    self._process_batch(batch, outfile, style_stats)
                    processed_count += len(batch)
        
        except FileNotFoundError:
            print(f"❌ File not found: {input_file}")
            return
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            return
        
        # Output statistics
        print(f"\n✅ Processing complete!")
        print(f"📊 Total processed: {processed_count:,} records")
print(f"📊 Web page type distribution:")
        
        for style_result, count in style_stats.most_common():
            percentage = (count / processed_count) * 100 if processed_count > 0 else 0
            # Parse classification result
            parts = style_result.split('|')
            category = parts[0] if len(parts) > 0 else "Unknown"
            subcategory = parts[1] if len(parts) > 1 else "Unknown"
            print(f"   {category} -> {subcategory}: {count:,} ({percentage:.1f}%)")
    
    def _process_batch(self, batch: List[Dict], outfile, style_stats: Counter) -> None:
        """
        Process a batch of data.
        
        Args:
            batch: Data batch
            outfile: Output file object
            style_stats: Web page type statistics counter
        """
        for data in batch:
            # Get URL and HTML content
            url = data.get('url', '')
            html_content = data.get('main_html', '')
            
            # If no main_html, try other fields
            if not html_content:
                html_content = data.get('html', '')
            
            # Detect web page type
            if url and html_content:
                style_result = self.detect_style(url, html_content)
            else:
                style_result = "Other|other|Missing URL or HTML content"
            
            # Parse classification result
            parts = style_result.split('|')
            category = parts[0].strip() if len(parts) > 0 else "Other"
            subcategory = parts[1].strip() if len(parts) > 1 else "other"
            
            # Update data
            if 'meta' not in data:
                data['meta'] = {}
            data['meta']['style'] = {
                'category': category,
                'subcategory': subcategory,
                'full_result': style_result
            }
            
            # Statistics
            style_stats[style_result] += 1
            
            # Write to output file
            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            # Add delay to avoid rate limits
            time.sleep(0.1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Add web page type labels to JSONL dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use LLM for web page type classification
  python scripts/style_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY
  
  # Specify custom model URL and batch size
  python scripts/style_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --base-url https://custom-url/v1 --batch-size 50
  
  # Use default URL with specified model
  python scripts/style_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --model gpt-4
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Input JSONL file path"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output JSONL file path"
    )
    
    parser.add_argument(
        "--api-key",
        required=True,
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (required)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-5",
        help="LLM model name (default: gpt-5)"
    )
    
    parser.add_argument(
        "--base-url",
        required=True,
        default="https://api.deepseek.com/v1/",
        help="Base URL for model requests"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size (default: 100)"
    )
    
    args = parser.parse_args()
    
    # Validate parameters
    if not Path(args.input_file).exists():
print(f"❌ Input file does not exist: {args.input_file}")
        sys.exit(1)
    
    # Create classifier
    classifier = StyleClassifier(
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url
    )
    
    # Process data
    classifier.process_jsonl(
        input_file=args.input_file,
        output_file=args.output,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
