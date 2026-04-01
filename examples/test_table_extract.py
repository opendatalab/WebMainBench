#!/usr/bin/env python3
"""
Script: Extract only table content from the WebMainBench dataset into table.md
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to sys.path for importing webmainbench
sys.path.append(str(Path(__file__).parent.parent))

from webmainbench.metrics.base import BaseMetric

def extract_only_tables_from_dataset():
    """Extract only table content from the WebMainBench dataset and output to table.md (items with empty tables are not recorded)"""

    # Path configuration
    dataset_path = "/home/zhangshuo/Desktop/vscodeworkspace/WebMainBench/data/WebMainBench_llm-webkit_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl"
    output_path = "table.md"

    # Check if the dataset file exists
    if not os.path.exists(dataset_path):
        print(f"Error: dataset file not found: {dataset_path}")
        return

    extracted_tables = []
    line_ids = []

    # Read JSONL file line by line
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())

                # Extract ID and content
                item_id = data.get('track_id', f'line_{line_num}')
                content = data.get('llm_webkit_md', '')

                # Use _extract_from_markdown to extract
                if content:
                    extracted = BaseMetric._extract_from_markdown(content)
                    table_content = extracted.get("table", "")
                    # Only record items with non-empty table
                    if table_content and table_content.strip():
                        extracted_tables.append(table_content)
                        line_ids.append((item_id, line_num))
            except json.JSONDecodeError as e:
                print(f"JSON parse error at line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
                continue

    # Write to table.md, output only the table field
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Extracted Table Content from WebMainBench Dataset\n\n")
        f.write(f"Total items processed: {len(extracted_tables)}\n\n")

        for idx, (table_content, (item_id, line_num)) in enumerate(zip(extracted_tables, line_ids), 1):
            f.write(f"## Item {idx}\n")
            f.write(f"- **ID**: {item_id}\n")
            f.write(f"- **Line Number**: {line_num}\n")
            f.write(f"- **Extracted Table**:\n\n")
            f.write("```\n")
            f.write(table_content)
            f.write("\n```\n\n")
            f.write("---\n\n")

    print(f"Table extraction complete! Processed {len(extracted_tables)} items.")
    print(f"Table content saved to: {output_path}")

if __name__ == "__main__":
    extract_only_tables_from_dataset()
