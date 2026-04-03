#!/usr/bin/env python3
"""
Add llm_webkit430_main_html field to the dataset
Builds main_html from existing fields following llm_webkit_extractor.py logic
Usage:
    python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl
"""

import json
import argparse
from pathlib import Path


def process_single_item(data: dict, verbose: bool = False) -> dict:
    """
    Add llm_webkit430_main_html field to a single JSON object.
    
    See llm_webkit_extractor.py:665-670 for the reference logic.
    """
    try:
        # Import necessary modules
        from llm_web_kit.input.pre_data_json import PreDataJson, PreDataJsonKey
        from llm_web_kit.main_html_parser.parser.tag_mapping import MapItemToHtmlTagsParser

        # Get fields from data
        typical_raw_tag_html = data.get('typical_raw_tag_html', '')  # Preprocessed HTML
        llm_response = data.get('llm_response_html', '')  # LLM response HTML

        # Check required fields
        if not typical_raw_tag_html:
            if verbose:
print("  ⚠️  llm_webkit_html field is empty, skipping")
            data['llm_webkit430_main_html'] = ""
            return data

        # Build pre_data (see llm_webkit_extractor.py:665)
        pre_data = {
            'typical_raw_tag_html': typical_raw_tag_html,
            'typical_raw_html': typical_raw_tag_html,
            'llm_response': llm_response,
            'html_source': typical_raw_tag_html
        }

        # Convert to PreDataJson object
        pre_data = PreDataJson(pre_data)

        # Mapping - use MapItemToHtmlTagsParser
        parser = MapItemToHtmlTagsParser({})
        pre_data = parser.parse(pre_data)

        # Extract main_html
        main_html = pre_data.get(PreDataJsonKey.TYPICAL_MAIN_HTML, "")

        # Add new field
        data['llm_webkit430_main_html'] = main_html

        return data

    except ImportError as e:
        if verbose:
print(f"\n❌ Import error: {e}")
print("   Please make sure llm_web_kit is installed: pip install llm-webkit")
        data['llm_webkit430_main_html'] = ""
        return data
    except Exception as e:
        if verbose:
            import traceback
print(f"\n⚠️  Processing failed: {e}")
print(f"   Error details: {traceback.format_exc()}")
        # Add empty field on failure
        data['llm_webkit430_main_html'] = ""
        return data


def process_dataset(input_file: str, output_file: str = None, verbose: bool = False, test_first: int = None):
    """
    Process the entire dataset.
    
    Args:
        input_file: Input JSONL file path
        output_file: Output JSONL file path (default: input_filename_with_main_html.jsonl)
        verbose: Whether to show detailed information
        test_first: Only process first N records (for testing)
    """
    input_path = Path(input_file)

    if not input_path.exists():
print(f"❌ File does not exist: {input_file}")
        return

    # Determine output file name
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_with_main_html.jsonl")

print(f"📄 Input file: {input_file}")
print(f"📄 Output file: {output_file}")
    if test_first:
print(f"🧪 Test mode: processing only the first {test_first} records")

    # Check dependencies
print("\n🔍 Checking dependencies...")
    try:
        from llm_web_kit.input.pre_data_json import PreDataJson, PreDataJsonKey
        from llm_web_kit.main_html_parser.parser.tag_mapping import MapItemToHtmlTagsParser
print("✅ llm_web_kit module available")
    except ImportError as e:
print(f"❌ llm_web_kit module not installed: {e}")
        print("   Please run: pip install llm-webkit")
        return

    # Statistics
    total = 0
    success = 0
    failed = 0

    # Count total lines first (for progress bar)
print("\n📊 Counting total lines...")
    with open(input_file, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)

    if test_first:
        total_lines = min(total_lines, test_first)

print(f"📦 Total {total_lines:,} records\n")

    # Process data
print("🔄 Starting processing...\n")
    try:
        with open(input_file, 'r', encoding='utf-8') as fin, \
             open(output_file, 'w', encoding='utf-8') as fout:

            for idx, line in enumerate(fin, 1):
                # Test mode: only process first N records
                if test_first and idx > test_first:
                    break

                if not line.strip():
                    continue

                try:
                    # Parse JSON
                    data = json.loads(line)
                    total += 1

                    # Show progress every 100 records
                    if total % 100 == 0:
print(f"  Progress: {total}/{total_lines} ({total/total_lines*100:.1f}%)")

                    # Process single record
                    if verbose and idx <= 3:
print(f"\nProcessing record {idx}...")

                    processed_data = process_single_item(data, verbose=(verbose and idx <= 3))

                    # Check if field was successfully added
                    if processed_data.get('llm_webkit430_main_html'):
                        success += 1
                    else:
                        failed += 1

                    # Write to output file
                    fout.write(json.dumps(processed_data, ensure_ascii=False) + '\n')

                except json.JSONDecodeError as e:
print(f"\n⚠️  JSON parse error at line {idx}: {e}")
                    failed += 1
                    # Write original line
                    fout.write(line)
                except Exception as e:
print(f"\n❌ Processing error at line {idx}: {e}")
                    if verbose:
                        import traceback
                        print(traceback.format_exc())
                    failed += 1
                    # Write original data
                    try:
                        data['llm_webkit430_main_html'] = ""
                        fout.write(json.dumps(data, ensure_ascii=False) + '\n')
                    except:
                        fout.write(line)

    except Exception as e:
print(f"\n❌ Critical error during processing: {e}")
        import traceback
        print(traceback.format_exc())
        return

    # Output statistics
    print("\n" + "="*60)
print("✅ Processing complete!")
    print("="*60)
print(f"Total processed: {total:,}")
print(f"Success: {success:,} ({success/total*100:.1f}%)" if total > 0 else "Success: 0")
print(f"Failed: {failed:,} ({failed/total*100:.1f}%)" if total > 0 else "Failed: 0")
print(f"\nOutput file: {output_file}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Add llm_webkit430_main_html field to the dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl
  
  # Specify output file
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl \\
    --output data/WebMainBench_7887_with_main_html.jsonl
  
  # Test on first 10 records
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl \\
    --test-first 10 --verbose
  
  # Verbose mode (show details for first 3 records)
  python scripts/process_dataset.py data/WebMainBench_7887_within_formula_code.jsonl \\
    --verbose
        '''
    )

    parser.add_argument(
        'input_file',
        help='Input JSONL file path'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Output JSONL file path (default: input_filename_with_main_html.jsonl)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show detailed processing information (first 3 records only)'
    )

    parser.add_argument(
        '--test-first',
        '-t',
        type=int,
        help='Process only the first N records (for testing)'
    )

    args = parser.parse_args()

    # Process dataset
    process_dataset(args.input_file, args.output, args.verbose, args.test_first)


if __name__ == '__main__':
    main()