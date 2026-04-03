#!/usr/bin/env python3
"""
Compare two JSONL files and find records whose track_id exists in file 1 but not in file 2
"""
import json
import sys
from pathlib import Path

def load_track_ids(jsonl_file):
    """
    Load all track_ids from a JSONL file

    Args:
        jsonl_file: Path to the JSONL file

    Returns:
        set: Set of track_ids
    """
    track_ids = set()
    file_path = Path(jsonl_file)
    
    if not file_path.exists():
        print(f"❌ File does not exist: {file_path}")
        return track_ids
    
    print(f"📖 Reading file: {file_path.name}")
    
    line_count = 0
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
                    
                    if track_id:
                        track_ids.add(track_id)
                        
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ Line {line_num} JSON parse error: {e}")
                    continue

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return set()

    print(f"  ✅ Found {len(track_ids)} unique track_ids")
    return track_ids

def load_data_with_track_ids(jsonl_file, target_track_ids):
    """
    Load records with specified track_ids from a JSONL file

    Args:
        jsonl_file: Path to the JSONL file
        target_track_ids: Set of target track_ids

    Returns:
        list: List of matching records
    """
    matched_data = []
    file_path = Path(jsonl_file)
    
    if not file_path.exists():
        print(f"❌ File does not exist: {file_path}")
        return matched_data
    
    print(f"📖 Extracting target records from {file_path.name}...")
    
    line_count = 0
    found_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                line_count += 1
                
                # Show progress every 1000 lines processed
                if line_count % 1000 == 0:
                    print(f"  📊 Processed {line_count} lines, found {found_count} target records...")
                
                try:
                    data = json.loads(line)
                    track_id = data.get('track_id')
                    
                    if track_id in target_track_ids:
                        matched_data.append(data)
                        found_count += 1
                        
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ Line {line_num} JSON parse error: {e}")
                    continue

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []

    print(f"  ✅ Found {len(matched_data)} target records")
    return matched_data

def main():
    """Main function"""
    # Default input files
    file1_default = "data/filtered_normal_data_1883.jsonl"
    file2_default = "data/WebMainBench_1827_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl"
    
    # Check command-line arguments
    if len(sys.argv) >= 3:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
    else:
        file1 = file1_default
        file2 = file2_default
    
    print("=" * 80)
    print("🔍 Compare track_id differences between JSONL files")
    print("=" * 80)
    print(f"📁 File 1 (source): {file1}")
    print(f"📁 File 2 (comparison): {file2}")
    print(f"🎯 Goal: Find track_ids that exist in file 1 but not in file 2")
    print()
    
    # Step 1: Load all track_ids from file 1
    print("🔸 Step 1: Loading track_ids from file 1...")
    track_ids_file1 = load_track_ids(file1)
    
    if not track_ids_file1:
        print("❌ No valid track_ids found in file 1")
        return
    
    print()
    
    # Step 2: Load all track_ids from file 2
    print("🔸 Step 2: Loading track_ids from file 2...")
    track_ids_file2 = load_track_ids(file2)
    
    if not track_ids_file2:
        print("❌ No valid track_ids found in file 2")
        return
    
    print()
    
    # Step 3: Compute difference
    print("🔸 Step 3: Computing difference...")
    diff_track_ids = track_ids_file1 - track_ids_file2
    common_track_ids = track_ids_file1 & track_ids_file2
    
    print(f"  📊 track_id count in file 1: {len(track_ids_file1):,}")
    print(f"  📊 track_id count in file 2: {len(track_ids_file2):,}")
    print(f"  📊 Common track_id count: {len(common_track_ids):,}")
    print(f"  ⭐ Different track_id count: {len(diff_track_ids):,}")
    
    if not diff_track_ids:
        print("\n🎉 No differences found! All track_ids in file 1 exist in file 2.")
        return
    
    print()
    
    # Step 4: Extract different records
    print("🔸 Step 4: Extracting different records...")
    diff_data = load_data_with_track_ids(file1, diff_track_ids)
    
    if not diff_data:
        print("❌ No different records found")
        return
    
    print()
    
    # Step 5: Save results
    print("🔸 Step 5: Saving differential data...")
    output_file = "data/track_id_diff_result.jsonl"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for data in diff_data:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"✅ Saved {len(diff_data)} differential records to: {output_file}")
        
        # Display first few different track_ids as examples
        print(f"\n📋 Sample differential track_ids (first 10):")
        for i, track_id in enumerate(list(diff_track_ids)[:10], 1):
            print(f"  {i}. {track_id}")
        
        if len(diff_track_ids) > 10:
            print(f"  ... and {len(diff_track_ids) - 10} more")
            
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return
    
    print("\n" + "=" * 80)
    print("🎉 Comparison complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
