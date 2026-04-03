"""
Table extraction metrics for WebMainBench.
"""

from typing import Dict, Any, List
import re
from .base import BaseMetric, MetricResult
from .teds_metrics import TEDSMetric, StructureTEDSMetric
from .text_metrics import EditDistanceMetric
from bs4 import BeautifulSoup

class TableEditMetric(EditDistanceMetric):
    """Table edit distance metric."""

    version = "1.0.0"
    description = "Table content edit distance metric"

    def _calculate_score(self, predicted: str, groundtruth: str,
                        predicted_content_list: List[Dict[str, Any]] = None,
                        groundtruth_content_list: List[Dict[str, Any]] = None,
                        **kwargs) -> MetricResult:
        """Calculate edit distance for table content."""

        # 1. Extract raw table content
        pred_raw = self._extract_table_content(predicted, predicted_content_list)
        gt_raw = self._extract_table_content(groundtruth, groundtruth_content_list)

        # 2. Reuse TEDSMetric's normalization method to convert to HTML format uniformly
        teds = TEDSMetric("temp_teds")  # Instantiate TEDSMetric to call its methods
        pred_html = teds._normalize_to_html(pred_raw)  # Call TEDS normalization
        gt_html = teds._normalize_to_html(gt_raw)

        # 3. Calculate edit distance based on normalized text
        result = super()._calculate_score(pred_html, gt_html, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "predicted_table_length": len(pred_html),
            "groundtruth_table_length": len(gt_html),
            "content_type": "table",
            "normalization": "teds_based"  # Mark as using TEDS normalization method
        })

        return result

    def _extract_table_content(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """Extract table content from text and content_list."""
        # Use unified content splitting method
        content_parts = self.split_content(text, content_list)
        return content_parts.get('table', '')

    def _extract_tables_from_content_list(self, content_list: List[Dict[str, Any]]) -> List[str]:
        """Recursively extract table content from content_list."""
        tables = []

        def _recursive_extract(items):
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, dict):
                    continue

                # Check if current item is a table
                item_type = item.get('type', '')
                if item_type in ['table']:
                    content = item.get('content', '')
                    if content:
                        tables.append(content)

                # Recursively check children field
                children = item.get('children')
                if children:
                    _recursive_extract(children)

                # Recursively check items field
                items_field = item.get('items')
                if items_field:
                    _recursive_extract(items_field)

        _recursive_extract(content_list)
        return tables


class TableTEDSMetric(TEDSMetric):
    """Table TEDS metric."""

    version = "1.0.0"
    description = "Table TEDS (Tree-Edit Distance based Similarity) metric"

    def _calculate_score(self, predicted: str, groundtruth: str,
                        predicted_content_list: List[Dict[str, Any]] = None,
                        groundtruth_content_list: List[Dict[str, Any]] = None,
                        **kwargs) -> MetricResult:
        """Calculate TEDS score for tables."""

        # Extract table content from content_list
        pred_table = self._extract_table_content(predicted, predicted_content_list)
        gt_table = self._extract_table_content(groundtruth, groundtruth_content_list)

        # Use parent class TEDS calculation
        result = super()._calculate_score(pred_table, gt_table, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "content_type": "table",
            "algorithm": "TEDS"
        })

        return result

    def _extract_table_content(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """Extract table content from text and content_list."""
        # Use unified content splitting method
        content_parts = self.split_content(text, content_list)
        return content_parts.get('table', '')