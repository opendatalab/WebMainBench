"""
Base metric interface for WebMainBench.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class MetricResult:
    """Result of metric calculation."""
    
    metric_name: str
    score: float
    details: Dict[str, Any] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "metric_name": self.metric_name,
            "score": self.score,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricResult":
        """Create from dictionary."""
        return cls(**data)
    
    @classmethod
    def create_error_result(cls, metric_name: str, error_message: str) -> "MetricResult":
        """Create an error result."""
        return cls(
            metric_name=metric_name,
            score=0.0,
            success=False,
            error_message=error_message
        )


class BaseMetric(ABC):
    """Base class for all evaluation metrics."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize the metric.
        
        Args:
            name: Name of the metric
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._setup()
    
    @abstractmethod
    def _setup(self) -> None:
        """Setup the metric (load models, initialize components, etc.)."""
        pass
    
    @abstractmethod
    def _calculate_score(self, predicted: Any, groundtruth: Any, **kwargs) -> MetricResult:
        """
        Calculate the metric score.
        
        Args:
            predicted: Predicted/extracted content
            groundtruth: Ground truth content
            **kwargs: Additional arguments
            
        Returns:
            MetricResult instance
        """
        pass
    
    def calculate(self, predicted: Any, groundtruth: Any, **kwargs) -> MetricResult:
        """
        Calculate metric with error handling.
        
        Args:
            predicted: Predicted/extracted content
            groundtruth: Ground truth content
            **kwargs: Additional arguments
            
        Returns:
            MetricResult instance
        """
        try:
            return self._calculate_score(predicted, groundtruth, **kwargs)
        except Exception as e:
            error_message = f"Metric calculation failed: {str(e)}"
            return MetricResult.create_error_result(self.name, error_message)
    
    def batch_calculate(self, predicted_list: List[Any], 
                       groundtruth_list: List[Any],
                       **kwargs) -> List[MetricResult]:
        """
        Calculate metrics for multiple samples.
        
        Args:
            predicted_list: List of predicted/extracted content
            groundtruth_list: List of ground truth content
            **kwargs: Additional arguments
            
        Returns:
            List of MetricResult instances
        """
        results = []
        for pred, gt in zip(predicted_list, groundtruth_list):
            result = self.calculate(pred, gt, **kwargs)
            results.append(result)
        return results

    def split_content(self, text: str, content_list: List[Dict[str, Any]] = None, field_name: str = None) -> Dict[str, str]:
        """
        Unified content splitting method that divides text into 4 parts: code, formula, table, and remaining text.

        Args:
            text: Raw markdown text
            content_list: Structured content list (from llm-webkit etc.)
            field_name: Name of the current field being processed, passed to _extract_from_markdown
        Returns:
            Dict with keys: 'code', 'formula', 'table', 'text'
        """
        # Prefer extraction from content_list
        if content_list:
            extracted_content = BaseMetric._extract_from_content_list(content_list)
            if any(extracted_content.values()):
                return extracted_content

        # Extract from markdown text, passing the field name
        return BaseMetric._extract_from_markdown(text or "", field_name=field_name, config=self.config)

    @staticmethod
    def _extract_from_content_list(content_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """Recursively extract various types of content from content_list"""
        extracted = {
            'code': [],
            'formula': [],
            'table': [],
            'text': []
        }

        def _recursive_extract(items):
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, dict):
                    continue

                item_type = item.get('type', '').lower()
                content = item.get('content', '').strip()

                # Classify content by type
                if item_type in ['code', 'code_block', 'inline_code']:
                    if content:
                        extracted['code'].append(content)
                elif item_type in ['formula', 'math', 'equation', 'latex']:
                    if content:
                        extracted['formula'].append(content)
                elif item_type in ['table', 'table_content', 'html_table', 'table_row', 'table_cell']:
                    if content:
                        extracted['table'].append(content)
                elif item_type in ['text', 'paragraph', 'heading']:
                    if content:
                        extracted['text'].append(content)

                # Recursively process child elements
                for child_key in ['children', 'items', 'content_list']:
                    if child_key in item and isinstance(item[child_key], list):
                        _recursive_extract(item[child_key])

        _recursive_extract(content_list)

        # Convert lists to strings
        return {
            'code': '\n'.join(extracted['code']),
            'formula': '\n'.join(extracted['formula']),
            'table': '\n'.join(extracted['table']),
            'text': '\n'.join(extracted['text'])
        }

    @staticmethod
    def _extract_from_markdown(text: str, field_name: str = None, config: Dict[str, Any] = None) -> Dict[str, str]:
        """Extract various types of content from markdown text"""
        if not text:
            return {'code': '', 'formula': '', 'table': '', 'text': ''}

        # Load LLM config
        from ..config import LLM_CONFIG
        splitter_config = {**LLM_CONFIG, **(config or {})}

        # Directly create concrete extractor instances
        from .code_extractor import CodeSplitter
        from .formula_extractor import FormulaSplitter
        from .table_extractor import TableSplitter

        code_extractor = CodeSplitter(splitter_config)
        formula_extractor = FormulaSplitter(splitter_config)
        table_extractor = TableSplitter(splitter_config)

        # Extract each type of content
        code_content = code_extractor.extract(text, field_name)
        formula_content = formula_extractor.extract(text, field_name)
        table_content = table_extractor.extract(text, field_name)

        return {
            'code': code_content,
            'formula': formula_content,
            'table': table_content,
            'text': text  # Retain the original full text
        }

    def aggregate_results(self, results: List[MetricResult]) -> MetricResult:
        """
        Aggregate multiple metric results.
        
        Args:
            results: List of MetricResult instances
            
        Returns:
            Aggregated MetricResult
        """
        if not results:
            return MetricResult.create_error_result(self.name, "No results to aggregate")
        
        # Filter successful results
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return MetricResult.create_error_result(self.name, "All calculations failed")
        
        # Calculate aggregate score (mean by default)
        scores = [r.score for r in successful_results]
        avg_score = sum(scores) / len(scores)
        
        # Aggregate details
        aggregate_details = {
            "num_samples": len(results),
            "num_successful": len(successful_results),
            "num_failed": len(results) - len(successful_results),
            "scores": scores,
            "min_score": min(scores),
            "max_score": max(scores),
            "std_score": self._calculate_std(scores),
        }
        
        return MetricResult(
            metric_name=f"{self.name}_aggregate",
            score=avg_score,
            details=aggregate_details,
            success=True
        )
    
    def _calculate_std(self, scores: List[float]) -> float:
        """Calculate standard deviation."""
        if len(scores) <= 1:
            return 0.0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
        return variance ** 0.5
    
    def get_config(self) -> Dict[str, Any]:
        """Get metric configuration."""
        return self.config.copy()
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Update metric configuration."""
        self.config.update(config)
    
    def get_info(self) -> Dict[str, Any]:
        """Get metric information."""
        return {
            "name": self.name,
            "config": self.get_config(),
            "version": getattr(self, 'version', 'unknown'),
            "description": getattr(self, 'description', ''),
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        return self.__str__()
