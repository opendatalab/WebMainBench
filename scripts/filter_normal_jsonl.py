#!/usr/bin/env python3
"""
Filter records with marked_type equal to 'normal' from a JSONL file
"""
import json
import sys
from pathlib import Path

def filter_normal_data(input_file):
    """
    Filter records where marked_type is 'normal'

    Args:
        input_file: Path to the input JSONL file

    Returns:
        tuple: (normal_data_list, total_count, normal_count)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ File does not exist: {input_path}")
        return [], 0, 0
    
    normal_data = []
    total_count = 0
    normal_count = 0
    
    print(f"📖 Reading file: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                total_count += 1
                
                # Show progress every 1000 lines processed
                if total_count % 1000 == 0:
                    print(f"📊 Processed {total_count} lines...")
                
                try:
                    data = json.loads(line)
                    marked_type = data.get('marked_type', '')
                    
                    if marked_type == 'normal':
                        normal_count += 1
                        normal_data.append(data)
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ Line {line_num} JSON parse error: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return [], 0, 0
    
    return normal_data, total_count, normal_count

def main():
    """Main function"""
    # Default input file
    default_input = "data/WebMainBench_dataset_merge_2549_llm_webkit.jsonl"
    
    # Check command-line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input
    
    print("=" * 60)
    print("🔍 Filter records with marked_type equal to 'normal'")
    print("=" * 60)
    
    # Perform filtering
    normal_data, total_count, normal_count = filter_normal_data(input_file)

    # Output statistics
    print("\n" + "=" * 60)
    print("📊 Statistics")
    print("=" * 60)
    print(f"📁 Input file: {input_file}")
    print(f"📄 Total records: {total_count:,}")
    print(f"✅ Normal-type records: {normal_count:,}")
    
    if total_count > 0:
        percentage = (normal_count / total_count) * 100
        print(f"📈 Normal-type percentage: {percentage:.2f}%")
    
    # Display other statistics
    other_count = total_count - normal_count
    if other_count > 0:
        other_percentage = (other_count / total_count) * 100
        print(f"📊 Other-type records: {other_count:,} ({other_percentage:.2f}%)")

    # Ask whether to save the filtered results
    if normal_count > 0:
        print(f"\n💾 Save filtered results? Will be saved to filtered_normal_data.jsonl")
        user_input = input("Enter 'y' to save, any other key to skip: ").strip().lower()
        
        if user_input == 'y':
            output_file = "filtered_normal_data.jsonl"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    for data in normal_data:
                        f.write(json.dumps(data, ensure_ascii=False) + '\n')
                print(f"✅ Saved {normal_count} normal-type records to: {output_file}")
            except Exception as e:
                print(f"❌ Error saving file: {e}")
    
    print("\n🎉 Processing complete!")

if __name__ == "__main__":
    main()
