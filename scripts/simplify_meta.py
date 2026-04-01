#!/usr/bin/env python3
"""
Meta field simplification tool
Keeps only specified meta fields, removing other complex statistics
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List

class MetaSimplifier:
    """Meta field simplifier."""
    
    def __init__(self):
        """Initialize simplifier."""
        self.processed_count = 0
        self.error_count = 0
        
    def simplify_meta(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplify meta fields.
        
        Args:
            data: Original data record
            
        Returns:
            Simplified data record
        """
        if 'meta' not in data:
            return data
            
        original_meta = data['meta']
        
        # Build simplified meta fields
        simplified_meta = {}
        
        # Keep specified fields
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
            
        # Process style field - keep only category value as style
        if 'style' in original_meta and isinstance(original_meta['style'], dict):
            style_category = original_meta['style'].get('category', 'Other')
            simplified_meta['style'] = style_category
        elif 'style' in original_meta and isinstance(original_meta['style'], str):
            # If style is already a string, use it directly
            simplified_meta['style'] = original_meta['style']
        else:
            simplified_meta['style'] = 'Other'
        
        # Update data record
        data['meta'] = simplified_meta
        return data
    
    def process_file(self, input_file: str, output_file: str) -> None:
        """
        Process file, simplifying meta fields.
        
        Args:
            input_file: Input file path
            output_file: Output file path
        """
        print(f"📄 Processing file: {input_file}")
        print(f"📄 Output file: {output_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8') as outfile:
                
                for line_num, line in enumerate(infile, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Simplify meta field
                        simplified_data = self.simplify_meta(data)
                        
                        # Write to output file
                        outfile.write(json.dumps(simplified_data, ensure_ascii=False) + '\n')
                        
                        self.processed_count += 1
                        
                        if line_num % 1000 == 0:
                            print(f"  Processed {line_num:,} records...")
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON parse error at line {line_num}: {e}")
                        self.error_count += 1
                        continue
                    except Exception as e:
                        print(f"⚠️  Processing error at line {line_num}: {e}")
                        self.error_count += 1
                        continue
                        
        except FileNotFoundError:
            print(f"❌ File not found: {input_file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            sys.exit(1)
    
    def print_summary(self) -> None:
        """Print processing statistics summary."""
        print(f"\n📊 Processing Statistics Summary:")
        print(f"   Successfully processed records: {self.processed_count:,}")
        print(f"   Error records: {self.error_count:,}")
        
        if self.processed_count > 0:
            success_rate = (self.processed_count / (self.processed_count + self.error_count)) * 100
            print(f"   Success rate: {success_rate:.2f}%")


def show_before_after_example(input_file: str) -> None:
    """
    Show before/after simplification example.
    
    Args:
        input_file: Input file path
    """
    print("\n📋 Before/After Simplification Example:")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Read the first record
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    
                    if 'meta' in data:
                        print("\n🔍 meta field before simplification:")
                        print(json.dumps(data['meta'], ensure_ascii=False, indent=2)[:500] + "...")
                        
                        # Simplify
                        simplifier = MetaSimplifier()
                        simplified_data = simplifier.simplify_meta(data.copy())
                        
                        print("\n✨ meta field after simplification:")
                        print(json.dumps(simplified_data['meta'], ensure_ascii=False, indent=2))
                        
                    break
                    
    except Exception as e:
        print(f"⚠️  Cannot show example: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Simplify meta fields, keeping only specified fields",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Simplified meta fields include:
  - language: str - Language identifier
  - table: list[str] - Table-related information
  - code: list[str] - Code-related information
  - equation: list[str] - Formula-related information
  - level: str - Complexity level
  - style: str - Web page type (from original meta.style.category)

Examples:
  # Basic simplification
  python scripts/simplify_meta.py \\
    data/WebMainBench_7887_with_meta.jsonl \\
    --output data/WebMainBench_7887_simplified.jsonl
    
  # Show simplification example
  python scripts/simplify_meta.py \\
    data/WebMainBench_7887_with_meta.jsonl \\
    --output data/WebMainBench_7887_simplified.jsonl \\
    --show-example
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Input JSONL file path"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output simplified JSONL file path"
    )
    
    parser.add_argument(
        "--show-example",
        action="store_true",
        help="Show before/after simplification example"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"❌ Input file does not exist: {args.input_file}")
        sys.exit(1)
    
    # Show example
    if args.show_example:
        show_before_after_example(args.input_file)
        print("\n" + "="*60)
    
    # Create simplifier
    simplifier = MetaSimplifier()
    
    # Process file
    simplifier.process_file(args.input_file, args.output)
    
    # Print statistics summary
    simplifier.print_summary()
    
    print(f"\n✅ Simplification complete! Output file: {args.output}")


if __name__ == "__main__":
    main()

