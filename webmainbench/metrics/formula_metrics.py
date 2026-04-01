"""
Formula extraction metrics for WebMainBench.
"""

from typing import Dict, Any, List
import re
from .base import BaseMetric, MetricResult
from .text_metrics import EditDistanceMetric


class FormulaEditMetric(EditDistanceMetric):
    """Formula edit distance metric (including inline and block formulas)"""

    version = "1.0.0"
    description = "Formula (inline and block) edit distance metric"

    def _calculate_score(self, predicted: str, groundtruth: str,
                        predicted_content_list: List[Dict[str, Any]] = None,
                        groundtruth_content_list: List[Dict[str, Any]] = None,
                        **kwargs) -> MetricResult:
        """Calculate edit distance for formulas"""

        # Extract formula content from content_list
        pred_formula = self._extract_formula_content(predicted, predicted_content_list)
        gt_formula = self._extract_formula_content(groundtruth, groundtruth_content_list)

        # Calculate edit distance
        result = super()._calculate_score(pred_formula, gt_formula, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "predicted_formula_length": len(pred_formula),
            "groundtruth_formula_length": len(gt_formula),
            "content_type": "formula"
        })

        return result

    def _extract_formula_content(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """Extract formula content from text and content_list"""
        # Use the unified content splitting method
        content_parts = self.split_content(text, content_list)
        return content_parts.get('formula', '')

    def _extract_formulas_from_content_list(self, content_list: List[Dict[str, Any]]) -> List[str]:
        """Recursively extract formula content from content_list"""
        formulas = []

        def _recursive_extract(items):
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, dict):
                    continue

                # Check if the current item is a formula
                item_type = item.get('type', '')
                if item_type in ['equation-interline', 'equation-inline']:
                    content = item.get('content', '')
                    if content:
                        formulas.append(content)

                # Recursively check the children field
                children = item.get('children')
                if children:
                    _recursive_extract(children)

                # Recursively check the items field (some implementations may use items)
                items_field = item.get('items')
                if items_field:
                    _recursive_extract(items_field)

        _recursive_extract(content_list)
        return formulas