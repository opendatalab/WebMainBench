"""
Metric calculator for WebMainBench.
"""
from typing import Dict, Any
from .base import MetricResult
from .text_metrics import  TextRougeNgramMetric
from .calculator import MetricCalculator


class MainHTMLMetricCalculator(MetricCalculator):
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the metric calculator.
        
        Args:
            config: Configuration for metrics
        """
        super().__init__(config)

    def _setup_default_metrics(self) -> None:
        self.add_metric("rouge_n", TextRougeNgramMetric("rouge_n"))
    
    def calculate_all(self, predicted_content: str,
                      convert_gt_main_content: str,
                      groundtruth_content: str,
                      **kwargs) -> Dict[str, MetricResult]:
        """
        Calculate all available metrics.
        
        Args:
            predicted_content: Predicted markdown content
            groundtruth_content: Ground truth markdown content
            predicted_content_list: Predicted content list
            groundtruth_content_list: Ground truth content list
            **kwargs: Additional arguments for specific metrics
            
        Returns:
            Dictionary mapping metric names to MetricResult instances
        """
        results: Dict[str, MetricResult] = {}        
        for target_name, target_content in (("human", groundtruth_content), ("convert", convert_gt_main_content)):
            for metric_name in list(self.metrics.keys()):
                metric = self.metrics[metric_name]
                result = metric.calculate(
                    predicted=predicted_content,
                    groundtruth=target_content, **kwargs
                )
                results[f"{target_name}_{metric_name}"] = result
        
        return results