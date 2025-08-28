"""
Main evaluator for WebMainBench.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import html2text

from ..data import BenchmarkDataset, DataSample
from ..extractors import BaseExtractor, ExtractorFactory
from ..metrics import  MainHTMLMetricCalculator
from .evaluator import EvaluationResult, Evaluator
from ..utils import extract_main_html

class MainHTMLEvaluator(Evaluator):
    """Main html evaluator for web content extraction benchmarks."""
    
    def __init__(self, metric_config: Dict[str, Any] = None):
        """
        Initialize the evaluator.
        
        Args:
            metric_config: Configuration for metrics
        """
        self.metric_calculator = MainHTMLMetricCalculator(metric_config)
        self.metric_config = metric_config or {}
        self.html2text = html2text.HTML2Text(bodywidth=0)
        self.html2text.ignore_links = True
        self.html2text.ignore_images = True
    
    
    def evaluate(self, 
                dataset: BenchmarkDataset,
                extractor: Union[BaseExtractor, str],
                extractor_config: Dict[str, Any] = None,
                max_samples: Optional[int] = None,
                categories: Optional[List[str]] = None) -> EvaluationResult:
        """
        Evaluate an extractor on a dataset.
        
        Args:
            dataset: BenchmarkDataset to evaluate on
            extractor: BaseExtractor instance or name
            extractor_config: Configuration for the extractor
            max_samples: Maximum number of samples to evaluate (for testing)
            categories: Specific categories to evaluate
            
        Returns:
            EvaluationResult instance
        """
        # Create extractor if string name provided
        if isinstance(extractor, str):
            extractor = ExtractorFactory.create(extractor, extractor_config)
        
        # Filter samples if needed (避免不必要的副本)
        samples_iter = dataset.samples
        
        # 只有在需要过滤时才创建副本
        if categories:
            samples_iter = [
                s for s in samples_iter 
                if s.content_type in categories
            ]
        
        # 如果有max_samples限制，使用itertools.islice避免完整列表
        if max_samples:
            import itertools
            samples_to_evaluate = list(itertools.islice(samples_iter, max_samples))
        else:
            # 如果没有任何过滤，直接使用原始列表避免副本
            samples_to_evaluate = samples_iter if not categories else samples_iter
        
        # Run evaluation
        sample_results = []
        extraction_errors = []
        
        print(f"Evaluating {len(samples_to_evaluate)} samples...")
        
        for i, sample in enumerate(samples_to_evaluate):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(samples_to_evaluate)}")
            
            try:
                sample_result = self._evaluate_sample(sample, extractor)
                sample_results.append(sample_result)
                
                # Track extraction errors
                if not sample_result.get('extraction_success', True):
                    extraction_errors.append({
                        'sample_id': sample.id,
                        'error': sample_result.get('extraction_error', 'Unknown error')
                    })
                    
            except Exception as e:
                print(f"Error evaluating sample {sample.id}: {e}")
                # Create error result
                error_result = {
                    'sample_id': sample.id,
                    'extraction_success': False,
                    'extraction_error': str(e),
                    'metrics': {},
                }
                sample_results.append(error_result)
                extraction_errors.append({
                    'sample_id': sample.id,
                    'error': str(e)
                })
        
        # Aggregate results
        overall_metrics = self._aggregate_metrics(sample_results)
        category_metrics = self._calculate_category_metrics(sample_results, samples_to_evaluate)
        error_analysis = self._analyze_errors(extraction_errors, sample_results)
        
        # Create evaluation result
        evaluation_result = EvaluationResult(
            dataset_name=dataset.name,
            extractor_name=extractor.name,
            timestamp=datetime.now().isoformat(),
            total_samples=len(samples_to_evaluate),
            overall_metrics=overall_metrics,
            sample_results=sample_results,
            category_metrics=category_metrics,
            error_analysis=error_analysis,
            extractor_config=extractor.get_config(),
            metric_config=self.metric_config,
        )
        
        return evaluation_result
    

    def _evaluate_sample(self, sample: DataSample, extractor: BaseExtractor) -> Dict[str, Any]:
        """Evaluate a single sample."""
        if extractor.__class__.__name__ == 'TestModelExtractor':
            extraction_result = extractor.extract_from_sample(sample)
        else:
            # Extract content
            extraction_result = extractor.extract(sample.html, sample.url)
        
        # Prepare result
        sample_result = {
            'sample_id': sample.id,
            'extraction_success': extraction_result.success,
            'extraction_time': extraction_result.extraction_time,
            'extracted_main_html': extraction_result.main_html if extraction_result.success else None,
            'extracted_content': extraction_result.content if extraction_result.success else None,
            'extracted_content_list': extraction_result.content_list if extraction_result.success else None,
        }
        
        if not extraction_result.success:
            sample_result['extraction_error'] = extraction_result.error_message
            sample_result['metrics'] = {}
            return sample_result
        
        main_html = extract_main_html(sample.html)
        self.html2text.baseurl = sample.url
        convert_gt_main_content = self.html2text.handle(main_html)
        sample_result['groundtruth_content'] = sample.groundtruth_content
        sample_result['gt_main_html'] = main_html
        sample_result['convert_gt_main_content'] = convert_gt_main_content
        
        # Calculate metrics
        metrics = self.metric_calculator.calculate_all(
            predicted_content=extraction_result.content,
            convert_gt_main_content=convert_gt_main_content,
            groundtruth_content=sample.groundtruth_content,
        )
        
        # Convert metrics to dict
        metrics_dict = {}
        for metric_name, metric_result in metrics.items():
            metrics_dict[metric_name] = {
                'score': metric_result.score,
                'success': metric_result.success,
                'details': metric_result.details,
            }
            if not metric_result.success:
                metrics_dict[metric_name]['error'] = metric_result.error_message
        
        sample_result['metrics'] = metrics_dict
        
        # Add sample metadata
        sample_result['sample_metadata'] = {
            'url': sample.url,
            'domain': sample.domain,
            'language': sample.language,
            'content_type': sample.content_type,
            'difficulty': sample.difficulty,
        }
        
        return sample_result
    
    def _aggregate_metrics(self, sample_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
            聚合所有样本的指标，计算全局平均值（每个指标单独聚合）
            """
        if not sample_results:
            return {}

        # 初始化每个指标的总分和样本数
        metric_totals = {
            "human_rouge_n": 0.0,
            "convert_rouge_n": 0.0,
        }
        metric_counts = {k: 0 for k in metric_totals.keys()}  # 记录每个指标有效样本数

        # 累加所有样本的指标分数
        for sample in sample_results:
            metrics = sample.get("metrics", {})
            for metric_name in metric_totals.keys():
                if metric_name in metrics and metrics[metric_name].get("success", False):
                    metric_totals[metric_name] += metrics[metric_name]["score"]
                    metric_counts[metric_name] += 1

        # 计算每个指标的平均值（全局overall为5个单项指标的平均值）
        overall_metrics = {}
        for metric_name in metric_totals.keys():
            if metric_counts[metric_name] > 0:
                overall_metrics[metric_name] = metric_totals[metric_name] / metric_counts[metric_name]
            else:
                overall_metrics[metric_name] = 0.0  # 无有效样本时默认为0

        return overall_metrics

    def _calculate_category_metrics(self, sample_results: List[Dict[str, Any]], 
                                  samples: List[DataSample]) -> Optional[Dict[str, Dict[str, float]]]:
        """Calculate metrics by category."""
        # Group samples by content type
        category_samples = {}
        for i, sample in enumerate(samples):
            if i >= len(sample_results):
                break
                
            content_type = sample.content_type or 'unknown'
            if content_type not in category_samples:
                category_samples[content_type] = []
            category_samples[content_type].append(sample_results[i])
        
        # Calculate metrics for each category
        category_metrics = {}
        for category, category_sample_results in category_samples.items():
            if len(category_sample_results) >= 3:  # Only calculate if enough samples
                category_metrics[category] = self._aggregate_metrics(category_sample_results)
        
        return category_metrics if category_metrics else None

    def _analyze_errors(self, extraction_errors: List[Dict[str, str]], 
                       sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze extraction errors."""
        total_samples = len(sample_results)
        failed_samples = len(extraction_errors)
        success_rate = (total_samples - failed_samples) / total_samples if total_samples > 0 else 0.0
        
        # Count error types
        error_types = {}
        for error in extraction_errors:
            error_msg = error['error']
            # Simple error categorization
            if 'timeout' in error_msg.lower():
                error_type = 'timeout'
            elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                error_type = 'network'
            elif 'parse' in error_msg.lower() or 'parsing' in error_msg.lower():
                error_type = 'parsing'
            elif 'empty' in error_msg.lower():
                error_type = 'empty_input'
            else:
                error_type = 'other'
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_samples': total_samples,
            'failed_count': failed_samples,
            'success_rate': success_rate,
            'common_errors': error_types,
            'sample_errors': extraction_errors[:10]  # Keep first 10 for debugging
        }

    def compare_extractors(self, 
                          dataset: BenchmarkDataset,
                          extractors: List[Union[BaseExtractor, str]],
                          extractor_configs: Optional[List[Dict[str, Any]]] = None,
                          **kwargs) -> Dict[str, EvaluationResult]:
        """
        Compare multiple extractors on the same dataset.
        
        Args:
            dataset: BenchmarkDataset to evaluate on
            extractors: List of extractors to compare
            extractor_configs: List of configs for each extractor
            **kwargs: Additional arguments for evaluate()
            
        Returns:
            Dictionary mapping extractor names to EvaluationResult
        """
        if extractor_configs is None:
            extractor_configs = [None] * len(extractors)
        
        results = {}
        
        for extractor, config in zip(extractors, extractor_configs):
            print(f"\nEvaluating extractor: {extractor if isinstance(extractor, str) else extractor.name}")
            
            try:
                result = self.evaluate(
                    dataset=dataset,
                    extractor=extractor,
                    extractor_config=config,
                    **kwargs
                )
                
                extractor_name = result.extractor_name
                results[extractor_name] = result
                
            except Exception as e:
                extractor_name = extractor if isinstance(extractor, str) else extractor.name
                print(f"Error evaluating {extractor_name}: {e}")
                continue
        
        return results 