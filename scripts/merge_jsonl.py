#!/usr/bin/env python3
"""
Merge multiple JSONL files and deduplicate based on the track_id field
"""
import json
import sys
from pathlib import Path
from collections import OrderedDict

def load_jsonl_with_dedup(jsonl_files):
    """
    Load multiple JSONL files and deduplicate based on track_id

    Args:
        jsonl_files: List of JSONL file paths

    Returns:
        dict: Ordered dictionary of {track_id: data}
    """
    merged_data = OrderedDict()
    total_loaded = 0
    duplicates_found = 0
    
    for file_path in jsonl_files:
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"⚠️ File does not exist, skipping: {file_path}")
            continue
            
        print(f"📖 Reading file: {file_path.name}")
        
        line_count = 0
        file_loaded = 0
        file_duplicates = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    line_count += 1
                    
                    # Show progress every 1000 lines processed
                    if line_count % 1000 == 0:
                        print(f"  📊 Processed {line_count} lines...")
                    
                    try:
                        data = json.loads(line)
                        track_id = data.get('track_id')
                        
                        if not track_id:
                            print(f"  ⚠️ Line {line_num} is missing the track_id field, skipping")
                            continue
                        
                        if track_id in merged_data:
                            # Duplicate track_id found
                            file_duplicates += 1
                            duplicates_found += 1
                            print(f"  🔄 Duplicate track_id found: {track_id} (line {line_num})")
                        else:
                            # New track_id, add to merged data
                            merged_data[track_id] = data
                            file_loaded += 1
                            total_loaded += 1
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Line {line_num} JSON parse error: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
            continue
        
        print(f"  ✅ File processing complete:")
        print(f"    📄 Total lines: {line_count}")
        print(f"    ➕ New entries: {file_loaded}")
        print(f"    🔄 Duplicates: {file_duplicates}")
        print()
    
    print(f"📊 Merge statistics:")
    print(f"  📄 Total entries processed: {total_loaded + duplicates_found}")
    print(f"  ✅ Unique entries: {len(merged_data)}")
    print(f"  🔄 Duplicates removed: {duplicates_found}")
    
    return merged_data

def save_merged_data(merged_data, output_file):
    """
    Save merged data to a JSONL file

    Args:
        merged_data: Dictionary of merged data
        output_file: Output file path
    """
    output_path = Path(output_file)
    
    print(f"💾 Saving merged results to: {output_path}")
    
    try:
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for track_id, data in merged_data.items():
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"✅ Successfully saved {len(merged_data)} entries to: {output_path}")
        print(f"📁 File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def main():
    """Main function"""
    # Default input files
    default_files = [
        "data/filtered_normal_data_1883.jsonl",
        "data/track_id_diff_result_56.jsonl"
    ]
    
    # Check command-line arguments
    if len(sys.argv) > 2:
        input_files = sys.argv[1:-1]  # All arguments except the last are input files
        output_file = sys.argv[-1]    # The last argument is the output file
    elif len(sys.argv) == 2:
        input_files = default_files
        output_file = sys.argv[1]
    else:
        input_files = default_files
        output_file = "data/merged_data.jsonl"
    
    print("=" * 80)
    print("🔗 Merge JSONL files and deduplicate based on track_id")
    print("=" * 80)
    print("📁 Input files:")
    for i, file in enumerate(input_files, 1):
        print(f"  {i}. {file}")
    print(f"📄 Output file: {output_file}")
    print()
    
    # Check if input files exist
    existing_files = []
    for file_path in input_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            # Try some common filename variants
            base_name = Path(file_path).stem
            parent_dir = Path(file_path).parent
            
            # If the filename contains numbers, try different numbers
            if "track_id_diff_result" in base_name:
                # Try to find the actual diff result file
                potential_files = list(parent_dir.glob("track_id_diff_result*.jsonl"))
                if potential_files:
                    actual_file = potential_files[0]
                    print(f"🔍 Found similar file: {actual_file}")
                    existing_files.append(str(actual_file))
                    continue
            
            print(f"⚠️ File does not exist: {file_path}")
    
    if not existing_files:
        print("❌ No valid input files found")
        return
    
    # Perform merge
    print("🔸 Step 1: Loading and deduplicating data...")
    merged_data = load_jsonl_with_dedup(existing_files)
    
    if not merged_data:
        print("❌ No valid data found")
        return
    
    print()
    print("🔸 Step 2: Saving merged results...")
    save_merged_data(merged_data, output_file)
    
    print()
    print("=" * 80)
    print("🎉 Merge complete!")
    print("=" * 80)
    
    # Display some statistics
    if merged_data:
        print("📋 Merge result statistics:")
        print(f"  🎯 Unique track_id count: {len(merged_data):,}")

        # Display first few track_ids as examples
        sample_track_ids = list(merged_data.keys())[:5]
        print(f"  📝 Sample track_ids:")
        for i, track_id in enumerate(sample_track_ids, 1):
            print(f"    {i}. {track_id}")
        
        if len(merged_data) > 5:
            print(f"    ... and {len(merged_data) - 5:,} more")

if __name__ == "__main__":
    main()
