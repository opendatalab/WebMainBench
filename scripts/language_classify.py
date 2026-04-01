#!/usr/bin/env python3
"""
Language classification tool
Adds language labels (ISO 639-1 standard) to text content in the dataset
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
    """Language classifier."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5", base_url: str = "https://api.deepseek.com/v1"):
        """
        Initialize language classifier.
        
        Args:
            api_key: OpenAI API key (if using LLM)
            model: Model name to use
            base_url: Base URL for model requests
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.supported_languages = self._get_supported_languages()
        
    def _get_supported_languages(self) -> Dict[str, str]:
        """Get the list of supported languages (ISO 639-1 standard)."""
        return {
            # Major languages
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
        Generate language detection prompt.
        
        Args:
            text: Text to detect language for
            
        Returns:
            Formatted prompt
        """
        # Build supported language list string
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
        Detect language using LLM.
        
        Args:
            text: Text to detect
            
        Returns:
            ISO 639-1 language code
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
            
            prompt = self.get_language_detection_prompt(text)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Validate returned language code
            if result in self.supported_languages:
                return result
            else:
                print(f"⚠️  LLM returned invalid language code: {result}, returning default language")
                return "en"
                
        except Exception as e:
            print(f"⚠️  LLM detection failed: {e}, returning default language")
            return "en"
    
    def detect_language(self, text: str) -> str:
        """
        Detect text language using LLM.
        
        Args:
            text: Text to detect
            
        Returns:
            ISO 639-1 language code
        """
        return self.detect_language_llm(text)
    
    def process_jsonl(self, input_file: str, output_file: str, 
                     batch_size: int = 100) -> None:
        """
        Process JSONL file, adding language labels.
        
        Args:
            input_file: Input file path
            output_file: Output file path
            batch_size: Batch size
        """
print(f"🔄 Starting language classification...")
print(f"📄 Input file: {input_file}")
print(f"📄 Output file: {output_file}")
print(f"🧠 Detection method: LLM")
print(f"🌐 Model URL: {self.base_url}")
print(f"🤖 Model: {self.model}")
        
        # Statistics
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
                            
    print(f"  📊 Processed {processed_count:,} records...")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON parse error at line {line_num}: {e}")
                        continue
                
                # Process the last batch
                if batch:
                    self._process_batch(batch, outfile, language_stats)
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
print(f"📊 Language distribution:")
        
        for lang_code, count in language_stats.most_common():
            lang_name = self.supported_languages.get(lang_code, "Unknown")
            percentage = (count / processed_count) * 100 if processed_count > 0 else 0
            print(f"   {lang_code} ({lang_name}): {count:,} ({percentage:.1f}%)")

    def analyze_language_statistics(self, input_file: str, output_csv: str = None) -> None:
        """
        Analyze language statistics in a JSONL file and save to CSV.
        
        Args:
            input_file: Input JSONL file path
            output_csv: Output CSV file path (default: input_filename_language_stats.csv)
        """
        if output_csv is None:
            input_path = Path(input_file)
            output_csv = str(input_path.parent / f"{input_path.stem}_language_stats.csv")
        
print(f"🔍 Starting language statistics analysis...")
print(f"📄 Input file: {input_file}")
print(f"📄 Output CSV: {output_csv}")
        
        # Statistics
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
                        
                        # Get language information from meta field
                        language = None
                        if 'meta' in data and isinstance(data['meta'], dict):
                            language = data['meta'].get('language')
                        
                        if language:
                            language_stats[language] += 1
                            processed_count += 1
                        else:
                            # If no language field, record as unknown
                            language_stats['unknown'] += 1
                            processed_count += 1
                            
                        if line_num % 1000 == 0:
                            print(f"  📊 Analyzed {line_num:,} lines...")
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON parse error at line {line_num}: {e}")
                        continue
        
        except FileNotFoundError:
            print(f"❌ File not found: {input_file}")
            return
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return
        
        # Generate statistics data
        stats_data = []
        for lang_code, count in language_stats.most_common():
            lang_name = self.supported_languages.get(lang_code, "Unknown" if lang_code != 'unknown' else "No language detected")
            percentage = (count / processed_count) * 100 if processed_count > 0 else 0
            stats_data.append({
                'language_code': lang_code,
                'language_name': lang_name,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Save to CSV file
        try:
            import csv
            with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['language_code', 'language_name', 'count', 'percentage']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in stats_data:
                    writer.writerow(row)
            
print(f"\n✅ Language statistics analysis complete!")
print(f"📊 Total analyzed: {processed_count:,} records")
    print(f"📊 Language distribution:")
            
            for row in stats_data:
                print(f"   {row['language_code']} ({row['language_name']}): {row['count']:,} ({row['percentage']:.1f}%)")
            
print(f"\n💾 Statistics saved to: {output_csv}")
            
        except Exception as e:
            print(f"❌ Error saving CSV file: {e}")
            return
    
    def _process_batch(self, batch: List[Dict], outfile, language_stats: Counter) -> None:
        """
        Process a batch of data.
        
        Args:
            batch: Data batch
            outfile: Output file object
            language_stats: Language statistics counter
        """
        for data in batch:
            # Get text content
            text = data.get('convert_main_content', '')
            
            # If no convert_main_content, try other fields
            if not text:
                text = data.get('groundtruth_content', '')
            if not text:
                text = data.get('content', '')
            
            # Detect language
            if text:
                language = self.detect_language(text)
            else:
                language = "en"  # Default to English
            
            # Update data
            if 'meta' not in data:
                data['meta'] = {}
            data['meta']['language'] = language
            
            # Statistics
            language_stats[language] += 1
            
            # Write to output file
            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            # Add delay to avoid rate limits
            time.sleep(0.1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Add language labels (ISO 639-1 standard) to JSONL dataset or analyze language distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use LLM for language detection
  python scripts/language_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY
  
  # Specify custom model URL and batch size
  python scripts/language_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --base-url http://custom-url:8080/ --batch-size 50
  
  # Use default URL with specified model
  python scripts/language_classify.py data/input.jsonl --output data/output.jsonl --api-key YOUR_API_KEY --model gpt-4
  
  # Analyze language distribution of an existing file
  python scripts/language_classify.py data/WebMainBench_7887_language_output.jsonl --analyze-only --output-csv data/language_stats.csv
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Input JSONL file path"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output JSONL file path (required only in non-analysis mode)"
    )
    
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze language statistics, skip language detection"
    )
    
    parser.add_argument(
        "--output-csv",
        help="CSV output file path for language statistics (used only in analysis mode)"
    )
    
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (required only in language detection mode)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-5",
        help="LLM model name (default: gpt-5)"
    )
    
    parser.add_argument(
        "--base-url",
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
    classifier = LanguageClassifier(
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url
    )
    
    if args.analyze_only:
        # Only perform language statistics analysis
        classifier.analyze_language_statistics(
            input_file=args.input_file,
            output_csv=args.output_csv
        )
    else:
        # Perform language detection and classification
        if not args.output:
print("❌ In language detection mode, --output parameter is required")
            sys.exit(1)
        
        if not args.api_key:
print("❌ In language detection mode, --api-key parameter is required")
            sys.exit(1)
        
        classifier.process_jsonl(
            input_file=args.input_file,
            output_file=args.output,
            batch_size=args.batch_size
        )


if __name__ == "__main__":
    main()
