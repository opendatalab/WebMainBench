#!/usr/bin/env python3
"""
Dataset statistics and filtering tool
Analyzes data distribution in the WebMainBench dataset
"""
import json
import sys
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import argparse

from llm_web_kit.simple import extract_content_from_html_with_magic_html, extract_content_from_main_html
from llm_web_kit.input.datajson import ContentList



class DatasetStatistics:
    """Dataset statistics and analysis class"""
    
    def __init__(self, jsonl_file: str, output_file: str):
        self.jsonl_file = Path(jsonl_file)
        self.output_file = Path(output_file)
        self.data = []
        self.stats = {}
        
    def load_data(self):
        """Load JSONL data"""
        print(f"📖 Loading data file: {self.jsonl_file}")
        
        if not self.jsonl_file.exists():
            raise FileNotFoundError(f"File does not exist: {self.jsonl_file}")
        
        line_count = 0
        try:
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        self.data.append(data)
                        line_count += 1
                        
                        # Show progress every 10000 lines
                        if line_count % 10000 == 0:
                            print(f"  📊 Loaded {line_count:,} lines...")
                            
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️ Line {line_num} JSON parse error: {e}")
                        continue
                        
        except Exception as e:
            raise RuntimeError(f"Error reading file: {e}")
        
        print(f"✅ Successfully loaded {len(self.data):,} records")
        return self
    
    def generate_content_list(self, data):
        """Generate content_list field using llm_web_kit to extract content"""
        try:                   
            html_content = data.get("html", "")
            url = data.get("url", "")
            
            # Validate required fields
            if not html_content:
                data["content_list"] = []
                return data
            
            # Extract content
            result = extract_content_from_html_with_magic_html(url, html_content, 'json')
            
            # Parse JSON
            try:
                result_json = json.loads(result)
                data["content_list"] = result_json.get("content_list", [])
                    
            except json.JSONDecodeError as e:
                data["content_list"] = []
            
            return data
            
        except Exception as e:
            # Ensure content_list field exists even on error
            data["content_list"] = []
            return data

    # Calculate DOM_WIDTH and DOM_DEPTH of HTML
    def calculate_DOM_WIDTH_DEPTH(self, data):
        """Calculate DOM tree depth and width."""
        try:
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
                
            html_content = data.get("html", "")
            if not html_content:
                data["meta"]["DOM_WIDTH"] = 0
                data["meta"]["DOM_DEPTH"] = 0
                return data
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find actual root elements (usually the html tag)
            root_elements = [child for child in soup.children if child.name]
            
            if not root_elements:
                data["meta"]["DOM_WIDTH"] = 0
                data["meta"]["DOM_DEPTH"] = 0
                return data
            
            # Calculate max depth and width across all root elements
            max_depth = 0
            max_width = 0
            
            for root in root_elements:
                depth = self._calculate_dom_depth(root)
                width = self._calculate_dom_width(root)
                max_depth = max(max_depth, depth)
                max_width = max(max_width, width)
            
            data["meta"]["DOM_WIDTH"] = max_width
            data["meta"]["DOM_DEPTH"] = max_depth
            
            return data
            
        except Exception as e:
            # If parsing fails, set default values
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["DOM_WIDTH"] = 0
            data["meta"]["DOM_DEPTH"] = 0
            return data
    
    def _calculate_dom_depth(self, element):
        """Recursively calculate maximum DOM tree depth."""
        if not element or not hasattr(element, 'name') or not element.name:
            return 0
        
        # Get all direct child elements (ignore text nodes)
        children = [child for child in element.children if hasattr(child, 'name') and child.name]
        
        if not children:
            return 1
        
        # Recursively calculate depth of all child elements, take max
        max_child_depth = max(self._calculate_dom_depth(child) for child in children)
        return 1 + max_child_depth
    
    def _calculate_dom_width(self, element):
        """Recursively calculate maximum DOM tree width (max child count at any level)."""
        if not element or not hasattr(element, 'name') or not element.name:
            return 0
        
        # Get all direct child elements (ignore text nodes)
        children = [child for child in element.children if hasattr(child, 'name') and child.name]
        current_width = len(children)
        
        # Recursively calculate max width of all child elements
        max_child_width = 0
        for child in children:
            child_width = self._calculate_dom_width(child)
            max_child_width = max(max_child_width, child_width)
        
        # Return the larger of current-level width and max child-level width
        return max(current_width, max_child_width)

    # Calculate link text to total text ratio in HTML and update data
    def calculate_and_update_text_linktext_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # Add ratio to meta field
                data["meta"]["text_linktext_ratio"] = 0.0
                return data
                
            # Use html.parser
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all text
            all_text = soup.get_text()
            all_text_len = len(all_text)
            
            if all_text_len == 0:
                data["meta"]["text_linktext_ratio"] = 0.0
                return data
            
            # Extract all link text
            link_text_len = sum(len(link.get_text()) for link in soup.find_all('a'))
            
            # Calculate ratio (non-link text / link text)
            if link_text_len <= 0:
                ratio = 1.0  # Use a large value to represent infinity
            else:
                ratio = link_text_len / all_text_len
                ratio = min(float(ratio), 1.0)  # Cap maximum value
            
            # Add ratio to meta field
            data["meta"]["text_linktext_ratio"] = ratio
            
            # Return updated data
            return data
            
        except Exception as e:
            # If parsing fails, at least add default values
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["text_linktext_ratio"] = 0.0
            return data

    # Calculate non-link text to link count ratio in HTML and update data
    def calculate_and_update_text_linknum_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # Add ratio to meta field
                data["meta"]["text_linknum_ratio"] = 0.0
                return data
                
            # Use html.parser
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all text
            all_text = soup.get_text()
            all_text_len = len(all_text)
            
            if all_text_len == 0:
                data["meta"]["text_linknum_ratio"] = 0.0
                return data
            
            # Count links
            links = soup.find_all('a')
            link_count = len(links)
            
            # Calculate total link text length
            link_text_len = sum(len(link.get_text()) for link in links)
            
            # Calculate non-link text length
            non_link_text_len = all_text_len - link_text_len
            
            # Calculate ratio (non-link text length / link count)
            if link_count <= 0:
                ratio = 10000.0  # Use a large value to represent infinity (not too extreme)
            else:
                ratio = non_link_text_len / link_count
                ratio = min(float(ratio), 10000.0)  # Cap maximum value
            
            # Add ratio to meta field
            data["meta"]["text_linknum_ratio"] = ratio
            
            # Return updated data
            return data
            
        except Exception as e:
            # If parsing fails, at least add default values
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["text_linknum_ratio"] = 0.0
            return data

    # Calculate table content to total content ratio in HTML and update data
    def calculate_and_update_table_html_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # Add ratio to meta field
                data["meta"]["table_html_source_ratio"] = 0.0
                return data
                
            # Use html.parser
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get total HTML content length
            total_html_length = len(html_content)
            
            if total_html_length == 0:
                data["meta"]["table_html_source_ratio"] = 0.0
                return data
            
            # Extract all table elements
            tables = soup.find_all(['table'])
            
            # Calculate total HTML length of all table elements
            table_html_length = sum(len(str(table)) for table in tables)
            
            # Calculate table content ratio of total HTML content
            ratio = table_html_length / total_html_length
            
            # Ensure ratio is between 0 and 1
            ratio = max(0.0, min(1.0, ratio))
            
            # Add ratio to meta field
            data["meta"]["table_html_source_ratio"] = ratio
            
            # Return updated data
            return data
            
        except Exception as e:
            # If parsing fails, at least add default values
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table_html_source_ratio"] = 0.0
            return data

    # Calculate table text to total text ratio in HTML and update data
    def calculate_and_update_table_text_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # Add ratio to meta field
                data["meta"]["table_text_ratio"] = 0.0
                return data
                
            # Use html.parser
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get all text from the entire document
            all_text = soup.get_text()
            total_text_length = len(all_text)
            
            if total_text_length == 0:
                data["meta"]["table_text_ratio"] = 0.0
                return data
            
            # Extract all table elements
            tables = soup.find_all(['table'])
            
            # Calculate total text length within all tables
            table_text_length = sum(len(table.get_text()) for table in tables)
            
            # Calculate table text ratio of total text content
            ratio = table_text_length / total_text_length
            
            # Ensure ratio is between 0 and 1
            ratio = max(0.0, min(1.0, ratio))
            
            # Add ratio to meta field
            data["meta"]["table_text_ratio"] = ratio
            
            # Return updated data
            return data
            
        except Exception as e:
            # If parsing fails, at least add default values
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table_text_ratio"] = 0.0
            return data

    # Calculate DOM depth of the first table in HTML and update data
    def calculate_and_update_table_depth(self, data):
        try:
            html_content = data.get("html", "")
            
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # Add depth to meta field, -1 means no table
                data["meta"]["table_dom_depth"] = -1
                return data
                
            # Use html.parser
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the first table element
            first_table = soup.find('table')
            
            # If no table found
            if not first_table:
                data["meta"]["table_dom_depth"] = -1
                return data
            
            # Calculate DOM depth of the table
            depth = 0
            parent = first_table.parent
            while parent and parent.name != '[document]':
                depth += 1
                parent = parent.parent
            
            # Add depth to meta field
            data["meta"]["table_dom_depth"] = depth
            
            # Return updated data
            return data
            
        except Exception as e:
            # If parsing fails, at least add default values
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table_dom_depth"] = -1
            return data
    
    # Detect equation types in HTML
    def detect_equations(self, data: dict) -> dict:
        """Detect and mark equation types in the page; returns meta.equation field as a string list."""
        try:
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            # Initialize code list
            equation_types = []
            
            # Check if content_list field exists
            if 'content_list' not in data:
                data["meta"]["equation"] = equation_types
                return data
            
            # Get JSON text of content_list
            text = ContentList(data['content_list']).to_json()
            
            # Detect inline equations
            inline_matches = re.findall("equation-inline", text)
            if len(inline_matches) > 0:
                equation_types.append("inline")
            
            # Detect interline equations
            interline_matches = re.findall("equation-interline", text)
            if len(interline_matches) > 0:
                equation_types.append("interline")
            
            # Store result in meta.equation field
            data["meta"]["equation"] = equation_types
            
            return data
            
        except Exception as e:
            # If parsing fails, return empty list
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["equation"] = []
            return data

    # Detect code types in HTML
    def detect_code(self, data: dict) -> dict:
        """Detect and mark code types in the page; returns meta.code field as a string list."""
        try:
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            # Initialize code list
            code_types = []
            
            # Check if content_list field exists
            if 'content_list' not in data:
                data["meta"]["code"] = code_types
                return data
            
            # Get JSON text of content_list
            text = ContentList(data['content_list']).to_json()
            
            # Detect inline equations
            inline_matches = re.findall("code-inline", text)
            if len(inline_matches) > 0:
                code_types.append("inline")
            
            # Detect interline equations
            target_str = r'"type": "code"'
            interline_matches = re.findall(target_str, text)
            if len(interline_matches) > 0:
                code_types.append("interline")
            
            # Store result in meta.code field
            data["meta"]["code"] = code_types
            
            return data
            
        except Exception as e:
            # If parsing fails, return empty list
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["code"] = []
            return data

    def classify_tables(self, data):
        """Classify table types based on DOM depth and other features."""
        try:
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            # Initialize table type list
            table_types = []
            
            # Get table-related meta information
            table_dom_depth = data["meta"].get("table_dom_depth", -1)
            table_text_ratio = data["meta"].get("table_text_ratio", 0)
            table_html_ratio = data["meta"].get("table_html_source_ratio", 0)
            
            # If no table, return empty list
            if table_dom_depth == -1:
                data["meta"]["table"] = table_types
                return data
            
            # Determine table type based on DOM depth and content ratio
            
            # Layout table heuristic:
            # 1. Shallow DOM depth (typically used for page layout)
            # 2. High table HTML ratio but low text ratio (mainly structural tags)
            if (table_dom_depth <= 3 and table_html_ratio > 0.1 and table_text_ratio < 0.3) or \
               (table_dom_depth <= 2):
                table_types.append("layout")
            
            # Data table heuristic:
            # 1. Deep DOM depth (nested in content area)
            # 2. High table text ratio (contains actual data content)
            # 3. Or moderate table HTML ratio but high text ratio
            if (table_dom_depth >= 3 and table_text_ratio >= 0.1) or \
               (table_text_ratio >= 0.3) or \
               (table_html_ratio > 0.05 and table_text_ratio >= 0.15):
                table_types.append("data")
            
            # If no type matched but table exists, default to data type
            if not table_types and table_dom_depth > -1:
                table_types.append("data")
            
            # Deduplicate and sort
            table_types = sorted(list(set(table_types)))
            
            data["meta"]["table"] = table_types
            return data
            
        except Exception as e:
            # If parsing fails, return empty list
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table"] = []
            return data

    # Calculate dispersion of text distribution in DOM linear sequence
    def calculate_text_DOM_distribution(self, data):
        """Linearize DOM tree and calculate dispersion of text distribution."""
        try:
            # Ensure meta field exists
            if "meta" not in data:
                data["meta"] = {}
            
            html_content = data.get("html", "")
            if not html_content:
                data["meta"]["text_distribution_dispersion"] = 0.0
                return data
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Linearize DOM tree into a 1D list
            dom_sequence = self._linearize_dom_tree(soup)
            
            if not dom_sequence:
                data["meta"]["text_distribution_dispersion"] = 0.0
                return data
            
            # Find positions of all text nodes in the sequence
            text_positions = []
            for i, node_info in enumerate(dom_sequence):
                if node_info['has_text']:
                    text_positions.append({
                        'position': i,
                        'text_length': node_info['text_length'],
                        'relative_position': i / len(dom_sequence)  # relative position 0-1
                    })
            
            if not text_positions:
                data["meta"]["text_distribution_dispersion"] = 0.0
                return data
            
            # Calculate dispersion of text distribution
            dispersion = self._calculate_text_dispersion(text_positions, len(dom_sequence))
            
            data["meta"]["text_distribution_dispersion"] = dispersion
            
            return data
            
        except Exception as e:
            # If parsing fails, return default value
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["text_distribution_dispersion"] = 0.0
            return data
    
    def _linearize_dom_tree(self, soup):
        """Linearize DOM tree into a 1D sequence (depth-first traversal)."""
        dom_sequence = []
        
        def traverse(element):
            if not element or not hasattr(element, 'name'):
                return
            
            # Skip document node
            if element.name == '[document]':
                # Process children of root node
                if hasattr(element, 'children'):
                    for child in element.children:
                        if hasattr(child, 'name') and child.name:
                            traverse(child)
                return
            
            # Process current element - only get direct text content
            text_content = ""
            text_length = 0
            has_text = False
            
            # Only collect direct text content (exclude child element text)
            if hasattr(element, 'contents'):
                for content in element.contents:
                    # Only process direct text nodes, skip child elements
                    if isinstance(content, str) and content.strip():
                        text_content += content.strip() + " "
                        
            text_length = len(text_content.strip())
            has_text = text_length > 0
            
            # Add to sequence
            node_info = {
                'tag': element.name,
                'has_text': has_text,
                'text_length': text_length,
                'text_content': text_content.strip()[:100] if has_text else ""  # Truncate to first 100 chars
            }
            dom_sequence.append(node_info)
            
            # Recursively process child elements
            if hasattr(element, 'children'):
                for child in element.children:
                    if hasattr(child, 'name') and child.name:
                        traverse(child)
        
        # Start traversal
        traverse(soup)
        return dom_sequence
    
    def _calculate_text_dispersion(self, text_positions, total_nodes):
        """Calculate dispersion of text distribution in 1D sequence based on state flip count."""
        if total_nodes < 2:
            return 0.0
        
        # Create text state sequence: 1=has text, 0=no text
        text_states = [0] * total_nodes
        for pos_info in text_positions:
            text_states[pos_info['position']] = 1
        
        # Count state flips (0->1 or 1->0)
        flips = 0
        for i in range(1, len(text_states)):
            if text_states[i] != text_states[i-1]:
                flips += 1
        
        # Normalize: flip count divided by total node count
        dispersion_score = flips / total_nodes
        
        return round(dispersion_score, 4)

    def calculate_level_score(self, data):
        """Calculate page content complexity score."""
        # Ensure meta field exists
        if "meta" not in data:
            data["meta"] = {}
        
        meta = data["meta"]
        
        # Collect complexity indicators
        complexity_score = 0.0
        
        # 1. Table complexity
        table_text_ratio = meta.get("table_text_ratio", 0)
        table_complexity = min(table_text_ratio, 1.0)  # Normalized to 0-1
        # complexity_score += 0.20 * table_complexity
        data["meta"]["table_complexity_score"] = round(table_complexity, 4) 
        
        # 2. DOM structure complexity
        dom_depth = meta.get("DOM_DEPTH", 0)
        dom_width = meta.get("DOM_WIDTH", 0)
        # Adjust normalization based on actual data distribution:
        # - 90th percentile depth ~104, use 120 as normalization base
        # - 90th percentile width ~1283, use 1500 as normalization base
        # - Use power function to reduce effect of large values for better discrimination
        depth_norm = min(dom_depth / 20, 1.0) ** 0.7  # Use 0.7 power for smoother curve
        width_norm = min(dom_width / 300, 1.0) ** 0.7
        dom_complexity = (depth_norm + width_norm) / 2  # Take average
        complexity_score += 0.25 * dom_complexity
        data["meta"]["dom_complexity_score"] = round(dom_complexity, 4) 
        
        # 3. Text distribution dispersion
        text_distribution_dispersion = meta.get("text_distribution_dispersion", 0)
        
        # Text distribution complexity score (simplified)
        text_dispersion_score = min(text_distribution_dispersion, 1.0)  # Normalized to 0-1
        complexity_score += 0.25 * text_dispersion_score
        data["meta"]["text_dispersion_score"] = round(text_dispersion_score, 4) 

        # 4. Content type diversity
        content_diversity = 0.0
        equation_types = meta.get("equation", [])
        code_types = meta.get("code", [])
        table_types = meta.get("table", [])
        
        # Score based on number of content types
        if equation_types:
            content_diversity += 0.3 * len(equation_types) / 2  # Up to 2 equation types
        if code_types:
            content_diversity += 0.3 * len(code_types) / 2      # Up to 2 code types
        if table_types:
            content_diversity += 0.4 * len(table_types) / 2     # Up to 2 table types
        
        content_diversity = min(content_diversity, 1.0)
        complexity_score += 0.25 * content_diversity
        data["meta"]["content_diversity_score"] = round(content_diversity, 4) 
        
        # 5. Link text ratio
        text_linktext_ratio = meta.get("text_linktext_ratio", 0)
        # Both high and low link ratios can increase complexity
        link_complexity = min(text_linktext_ratio, 1.0)
        complexity_score += 0.25 * link_complexity
        data["meta"]["link_complexity_score"] = round(link_complexity, 4) 
        
        data["meta"]["overall_complexity_score"] = round(complexity_score, 4)  # Save composite score for analysis
      
        return data

    def calculate_level(self, data, threshold_30=None, threshold_70=None):
        """Calculate page content difficulty level based on dynamic thresholds: simple, mid, hard."""
        # If no thresholds provided, use defaults
        if threshold_30 is None or threshold_70 is None:
            threshold_30 = 0.35
            threshold_70 = 0.65
        
        complexity_score = data["meta"]["overall_complexity_score"]
        if complexity_score >= threshold_70:
            level = 'hard'
        elif complexity_score >= threshold_30:
            level = 'mid'
        else:
            level = 'simple'
        data["meta"]["level"] = level
        return data
    
    def _calculate_dynamic_thresholds(self):
        """Calculate dynamic thresholds based on overall_complexity_score distribution."""
        complexity_scores = []
        for data in self.data:
            if "meta" in data and "overall_complexity_score" in data["meta"]:
                complexity_scores.append(data["meta"]["overall_complexity_score"])
        
        if not complexity_scores:
            print("⚠️  Warning: No overall_complexity_score data found, using default thresholds")
            return 0.35, 0.65  # Return default thresholds
        
        # Sort and calculate percentiles
        complexity_scores.sort()
        n = len(complexity_scores)
        
        # Calculate 30th and 70th percentiles
        percentile_30_idx = int(n * 0.3)
        percentile_70_idx = int(n * 0.7)
        
        # Ensure indices are within valid range
        percentile_30_idx = min(percentile_30_idx, n - 1)
        percentile_70_idx = min(percentile_70_idx, n - 1)
        
        threshold_30 = complexity_scores[percentile_30_idx]
        threshold_70 = complexity_scores[percentile_70_idx]
        
        print(f"📊 Complexity distribution threshold calculation:")
        print(f"   Total samples: {n:,}")
        print(f"   30th percentile (simple/mid boundary): {threshold_30:.4f}")
        print(f"   70th percentile (mid/hard boundary): {threshold_70:.4f}")
        print(f"   Complexity score range: {min(complexity_scores):.4f} - {max(complexity_scores):.4f}")
        
        return threshold_30, threshold_70
    
    def _print_level_distribution(self):
        """Count and print difficulty level classification results."""
        simple_count = mid_count = hard_count = 0
        for data in self.data:
            level = data.get("meta", {}).get("level", "unknown")
            if level == "simple":
                simple_count += 1
            elif level == "mid":
                mid_count += 1
            elif level == "hard":
                hard_count += 1
        
        total = len(self.data)
        print(f"📊 Difficulty level classification results:")
        print(f"   Simple: {simple_count:,} ({simple_count/total*100:.1f}%)")
        print(f"   Mid:    {mid_count:,} ({mid_count/total*100:.1f}%)")
        print(f"   Hard:   {hard_count:,} ({hard_count/total*100:.1f}%)")

    def update_data(self):
        """Update statistics in data."""
        print("🔄 Phase 1: Calculating base statistics and complexity scores...")
        
        # Phase 1: Calculate all base statistics and complexity scores
        for i, data in enumerate(self.data):
            # Append fields directly to original data
            self.generate_content_list(data)
            self.calculate_DOM_WIDTH_DEPTH(data)  # DOM structure analysis
            self.calculate_and_update_text_linktext_ratio(data)
            # self.calculate_and_update_text_linknum_ratio(data)
            # self.calculate_and_update_table_html_ratio(data)
            self.calculate_and_update_table_text_ratio(data)
            self.calculate_and_update_table_depth(data)
            self.classify_tables(data)  # Table classification must come after table statistics
            self.calculate_text_DOM_distribution(data)  # Text DOM distribution analysis
            self.detect_equations(data)
            self.detect_code(data)
            self.calculate_level_score(data)  # Only calculate complexity score, do not classify
            # Delete content_list field
            if 'content_list' in data:
                del data['content_list']

            # Show progress
            if (i + 1) % 100 == 0:
                print(f"  📊 Processed {i + 1:,} records...")
        
        print("🔄 Phase 2: Calculating dynamic thresholds and difficulty level classification...")
        
        # Phase 2: Calculate dynamic thresholds based on all complexity scores
        threshold_30, threshold_70 = self._calculate_dynamic_thresholds()
        
        # Phase 3: Apply dynamic thresholds for difficulty level classification
        for data in self.data:
            self.calculate_level(data, threshold_30, threshold_70)
        
        # Count final classification results
        self._print_level_distribution()
    
    def write_data(self):
        """Write data."""
        print(f"📝 Writing data to: {self.output_file}")
        with open(self.output_file, "w", encoding="utf-8") as f:
            for data in self.data:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"✅ Successfully wrote {len(self.data):,} records")
    
    def calculate_meta_statistics(self):
        """Calculate meta field statistics."""
        if not self.data:
            return {}
        
        stats = {
            'total_count': len(self.data),
            'numerical_stats': {},
            'categorical_stats': {},
            'correlation_stats': {}
        }
        
        # Numerical field statistics
        numerical_fields = [
            'text_linktext_ratio', 'text_linknum_ratio', 
            'table_html_source_ratio', 'table_text_ratio', 'table_dom_depth',
            'DOM_WIDTH', 'DOM_DEPTH',
            'text_distribution_dispersion',
            'table_complexity_score',
            'dom_complexity_score',
            'text_dispersion_score',
            'content_diversity_score',
            'link_complexity_score',
            'overall_complexity_score'
        ]
        
        for field in numerical_fields:
            values = []
            for data in self.data:
                if 'meta' in data and field in data['meta']:
                    value = data['meta'][field]
                    if isinstance(value, (int, float)) and value != -1:  # Exclude special value -1
                        values.append(value)
            
            if values:
                stats['numerical_stats'][field] = {
                    'count': len(values),
                    'mean': sum(values) / len(values),
                    'median': sorted(values)[len(values)//2],
                    'min': min(values),
                    'max': max(values),
                    'std': (sum((x - sum(values)/len(values))**2 for x in values) / len(values))**0.5
                }
        
        # Categorical field statistics - equation
        equation_combinations = {}
        for data in self.data:
            if 'meta' in data and 'equation' in data['meta']:
                eq_list = data['meta']['equation']
                eq_key = ','.join(sorted(eq_list)) if eq_list else 'none'
                equation_combinations[eq_key] = equation_combinations.get(eq_key, 0) + 1
        
        stats['categorical_stats']['equation'] = equation_combinations
        
        # Categorical field statistics - code
        code_combinations = {}
        for data in self.data:
            if 'meta' in data and 'code' in data['meta']:
                code_list = data['meta']['code']
                code_key = ','.join(sorted(code_list)) if code_list else 'none'
                code_combinations[code_key] = code_combinations.get(code_key, 0) + 1
        
        stats['categorical_stats']['code'] = code_combinations

        # Categorical field statistics - level
        level_combinations = {}
        for data in self.data:
            if 'meta' in data and 'level' in data['meta']:
                level_value = data['meta']['level']
                # level is a string, use directly
                level_key = level_value if level_value else 'none'
                level_combinations[level_key] = level_combinations.get(level_key, 0) + 1
        stats['categorical_stats']['level'] = level_combinations
        
        # Categorical field statistics - table
        table_combinations = {}
        for data in self.data:
            if 'meta' in data and 'table' in data['meta']:
                table_list = data['meta']['table']
                table_key = ','.join(sorted(table_list)) if table_list else 'none'
                table_combinations[table_key] = table_combinations.get(table_key, 0) + 1
        stats['categorical_stats']['table_types'] = table_combinations

        # Cross-tabulation - equation and code combination
        equation_code_cross = {}
        for data in self.data:
            if 'meta' in data:
                eq_list = data['meta'].get('equation', [])
                code_list = data['meta'].get('code', [])
                eq_key = ','.join(sorted(eq_list)) if eq_list else 'none'
                code_key = ','.join(sorted(code_list)) if code_list else 'none'
                cross_key = f"eq:{eq_key}|code:{code_key}"
                equation_code_cross[cross_key] = equation_code_cross.get(cross_key, 0) + 1
        
        stats['correlation_stats']['equation_code_cross'] = equation_code_cross
        
        # Table-related statistics
        table_stats = {
            'has_table': 0,
            'no_table': 0,
            'high_table_ratio': 0  # table_text_ratio > 0.5
        }
        
        for data in self.data:
            if 'meta' in data:
                table_depth = data['meta'].get('table_dom_depth', -1)
                table_text_ratio = data['meta'].get('table_text_ratio', 0)
                
                if table_depth > -1:
                    table_stats['has_table'] += 1
                    if table_text_ratio > 0.5:
                        table_stats['high_table_ratio'] += 1
                else:
                    table_stats['no_table'] += 1
        
        stats['categorical_stats']['table'] = table_stats
        
        self.stats = stats
        return stats

    def print_summary(self):
        """Print statistics summary."""
        print("\n" + "=" * 80)
        print("📊 WebMainBench Dataset Statistics Summary")
        print("=" * 80)
        print(f"📄 Total records: {len(self.data):,}")
        
        if hasattr(self, 'stats') and self.stats:
            stats = self.stats
            
            # Numerical field statistics
            print(f"\n📈 Numerical field statistics:")
            print("-" * 60)
            for field, field_stats in stats['numerical_stats'].items():
                print(f"  {field}:")
                print(f"    Sample count: {field_stats['count']:,}")
                print(f"    Mean: {field_stats['mean']:.4f}")
                print(f"    Median: {field_stats['median']:.4f}")
                print(f"    Min: {field_stats['min']:.4f}")
                print(f"    Max: {field_stats['max']:.4f}")
                print(f"    Std dev: {field_stats['std']:.4f}")
                print()
            
            # Equation type distribution
            print(f"📐 Equation type distribution:")
            print("-" * 60)
            equation_stats = stats['categorical_stats'].get('equation', {})
            total_with_meta = sum(equation_stats.values())
            for eq_type, count in sorted(equation_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {eq_type}: {count:,} ({percentage:.1f}%)")
            
            # Code type distribution
            print(f"\n💻 Code type distribution:")
            print("-" * 60)
            code_stats = stats['categorical_stats'].get('code', {})
            total_with_meta = sum(code_stats.values())
            for code_type, count in sorted(code_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {code_type}: {count:,} ({percentage:.1f}%)")
            
            # Table statistics
            print(f"\n📋 Table statistics:")
            print("-" * 60)
            table_stats = stats['categorical_stats'].get('table', {})
            total = table_stats.get('has_table', 0) + table_stats.get('no_table', 0)
            if total > 0:
                print(f"  Has table: {table_stats.get('has_table', 0):,} ({table_stats.get('has_table', 0)/total*100:.1f}%)")
                print(f"  No table: {table_stats.get('no_table', 0):,} ({table_stats.get('no_table', 0)/total*100:.1f}%)")
                print(f"  High table ratio (>50%): {table_stats.get('high_table_ratio', 0):,}")
            
            # Table type distribution
            print(f"\n📊 Table type distribution:")
            print("-" * 60)
            table_type_stats = stats['categorical_stats'].get('table_types', {})
            total_with_meta = sum(table_type_stats.values())
            for table_type, count in sorted(table_type_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {table_type}: {count:,} ({percentage:.1f}%)")
            
            # Difficulty level distribution
            print(f"\n🔍 Difficulty level distribution:")
            print("-" * 60)
            level_stats = stats['categorical_stats'].get('level', {})
            total_with_meta = sum(level_stats.values())
            for level, count in sorted(level_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {level}: {count:,} ({percentage:.1f}%)")
            
            # Equation-code cross-tabulation (show top 10 most common combinations)
            print(f"\n🔗 Equation-code combination distribution (Top 10):")
            print("-" * 60)
            cross_stats = stats['correlation_stats'].get('equation_code_cross', {})
            sorted_cross = sorted(cross_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            for combo, count in sorted_cross:
                percentage = (count / len(self.data) * 100) if len(self.data) > 0 else 0
                print(f"  {combo}: {count:,} ({percentage:.1f}%)")
        
        print("\n" + "=" * 80)
        

    

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Dataset statistics and filtering tool")
    # data/sample_dataset.jsonl
    # data/WebMainBench_1827_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl
    parser.add_argument("--input", "-i", required=True, type=str, help="Input JSONL file path")
    parser.add_argument("--output", "-o", required=True, type=str, help="Output file path")

    args = parser.parse_args()
    
    print("🔍 Dataset statistics and filtering tool")
    print("="*60)
    
    try:
        # Initialize and load data
        stats_tool = DatasetStatistics(args.input, args.output)       
        stats_tool.load_data()
        
        # Calculate statistics
        stats_tool.update_data()

        # Calculate meta field statistics
        stats_tool.calculate_meta_statistics()
            
        # Display statistics summary
        stats_tool.print_summary()
        
        # Write data
        stats_tool.write_data()
        
        print(f"\n🎉 Task complete!")
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
 