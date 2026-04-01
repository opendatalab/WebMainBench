"""
Data saver for WebMainBench.
"""

import json
import jsonlines
from pathlib import Path
from typing import Union, List, Dict, Any, TYPE_CHECKING

from .dataset import BenchmarkDataset, DataSample

if TYPE_CHECKING:
    from ..evaluator import EvaluationResult
    from ..metrics import MetricResult


class DataSaver:
    """Data saver for various output formats."""
    
    @staticmethod
    def save_jsonl(dataset: BenchmarkDataset, 
                   file_path: Union[str, Path],
                   include_results: bool = True) -> None:
        """
        Save dataset to JSONL file.
        
        Args:
            dataset: BenchmarkDataset to save
            file_path: Output file path
            include_results: Whether to include extraction results
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with jsonlines.open(file_path, 'w') as writer:
            for sample in dataset.samples:
                sample_dict = sample.to_dict()
                if not include_results:
                    sample_dict.pop('extracted_results', None)
                writer.write(sample_dict)
    
    @staticmethod
    def save_json(dataset: BenchmarkDataset, 
                  file_path: Union[str, Path],
                  include_metadata: bool = True,
                  include_results: bool = True,
                  indent: int = 2) -> None:
        """
        Save dataset to JSON file.
        
        Args:
            dataset: BenchmarkDataset to save
            file_path: Output file path
            include_metadata: Whether to include dataset metadata
            include_results: Whether to include extraction results
            indent: JSON indentation level
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "name": dataset.name,
            "description": dataset.description,
            "samples": []
        }
        
        if include_metadata:
            data["metadata"] = dataset.get_metadata()
            data["statistics"] = dataset.get_statistics()
        
        for sample in dataset.samples:
            sample_dict = sample.to_dict()
            if not include_results:
                sample_dict.pop('extracted_results', None)
            data["samples"].append(sample_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def save_evaluation_results(results: Union["EvaluationResult", Dict[str, Any]], 
                              file_path: Union[str, Path],
                              format: str = "json") -> None:
        """
        Save evaluation results.
        
        Args:
            results: EvaluationResult instance or evaluation results dictionary
            file_path: Output file path
            format: Output format ("json" or "jsonl")
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert EvaluationResult to dict if needed
        if hasattr(results, 'to_dict'):
            results_dict = results.to_dict()
        else:
            results_dict = results
        
        # Remove extracted_content and extracted_content_list fields to reduce file size
        results_dict = DataSaver._remove_content_fields(results_dict)
        
        if format.lower() == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2, ensure_ascii=False)
        elif format.lower() == "jsonl":
            with jsonlines.open(file_path, 'w') as writer:
                if isinstance(results_dict, dict) and 'samples' in results_dict:
                    for sample_result in results_dict['samples']:
                        writer.write(sample_result)
                else:
                    writer.write(results_dict)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def save_summary_report(results: Union["EvaluationResult", List["EvaluationResult"], Dict[str, Any], List[Dict[str, Any]]], 
                          file_path: Union[str, Path]) -> None:
        """
        Save evaluation results as a CSV leaderboard.
        
        Args:
            results: Single EvaluationResult instance, list of EvaluationResult instances, 
                    or their dictionary representations
            file_path: Output CSV file path
        """
        import csv
        from importlib import metadata as importlib_metadata

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert results to list of dicts
        def to_dict_if_needed(item):
            return item.to_dict() if hasattr(item, 'to_dict') else item

        if isinstance(results, list):
            results_list = [to_dict_if_needed(item) for item in results]
        else:
            results_list = [to_dict_if_needed(results)]

        csv_data = []
        for result in results_list:
            metadata = result.get('metadata', {})
            error_analysis = result.get('error_analysis', {})

            # Get extractor version
            extractor_name = metadata.get('extractor_name', 'unknown')
            try:
                # Map extractor name to package name
                package_mapping = {
                    'llm-webkit': 'llm_web_kit',
                    'magic-html': 'magic_html',
                    'trafilatura': 'trafilatura',
                    'trafilatura_txt': 'trafilatura',
                    'resiliparse': 'resiliparse'
                }
                package_name = package_mapping.get(extractor_name, extractor_name)
                extractor_version = importlib_metadata.version(package_name)
            except importlib_metadata.PackageNotFoundError:
                extractor_version = 'unknown'
            row = {
                'extractor': metadata.get('extractor_name', 'unknown'),
                'dataset': metadata.get('dataset_name', 'unknown'),
                'total_samples': metadata.get('total_samples', 0),
                'success_rate': error_analysis.get('success_rate', 0.0),
                 'extractor_version': extractor_version,
            }
            
            # Add all available metrics from overall_metrics
            if 'overall_metrics' in result:
                for metric_name, value in result['overall_metrics'].items():
                        row[metric_name] = round(value, 4) if isinstance(value, (int, float)) else value
            
            csv_data.append(row)
        
        # Sort by overall score (descending)
        def get_sort_key(row):
            return row.get('overall', 0)
        
        csv_data.sort(key=get_sort_key, reverse=True)
        
        # Write CSV file
        if csv_data:
            # Define field order: basic info first, then overall, then other metrics alphabetically
            basic_fields = ['extractor','extractor_version', 'dataset', 'total_samples', 'success_rate']
            
            # Get all metric fields from the data
            all_fields = set()
            for row in csv_data:
                all_fields.update(row.keys())
            
            # Remove basic fields from metrics
            metric_fields = all_fields - set(basic_fields)
            
            # Sort metrics: overall first, then alphabetically
            sorted_metrics = []
            if 'overall' in metric_fields:
                sorted_metrics.append('overall')
                metric_fields.remove('overall')
            sorted_metrics.extend(sorted(metric_fields))
            
            # Final field order
            fieldnames = basic_fields + sorted_metrics
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
    

    @staticmethod
    def save_dataset_with_extraction(results: Union["EvaluationResult", Dict[str, Any], List[Dict[str, Any]]], 
                                   dataset: "BenchmarkDataset",
                                   file_path: Union[str, Path],
                                   extractor_name: str = None) -> None:
        """
        Save original dataset with extracted content added for manual review.
        
        Args:
            results: EvaluationResult instance, its dictionary representation, or list of evaluation results
            dataset: Original dataset
            file_path: Output JSONL file path
            extractor_name: Name of the extractor (used for field naming)
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle different input formats
        if isinstance(results, list):
            # Handle list of evaluation results (multi-extractor scenario)
            all_extraction_maps = {}
            extractor_names = []
            
            for result_item in results:
                # Convert EvaluationResult to dict if needed
                if hasattr(result_item, 'to_dict'):
                    results_dict = result_item.to_dict()
                else:
                    results_dict = result_item
                
                # Get extractor name for this result
                current_extractor_name = results_dict.get('metadata', {}).get('extractor_name', 'extracted')
                extractor_names.append(current_extractor_name)
                
                # Create mapping from sample_id to extraction result for this extractor
                sample_results = results_dict.get('sample_results', [])
                extraction_map = {}
                for sample_result in sample_results:
                    sample_id = sample_result.get('sample_id')
                    if sample_id:
                        extraction_map[sample_id] = sample_result
                
                all_extraction_maps[current_extractor_name] = extraction_map
        else:
            # Handle single evaluation result
            # Convert EvaluationResult to dict if needed
            if hasattr(results, 'to_dict'):
                results_dict = results.to_dict()
            else:
                results_dict = results
            
            # Get extractor name
            if not extractor_name:
                extractor_name = results_dict.get('metadata', {}).get('extractor_name', 'extracted')
            
            # Create mapping from sample_id to extraction result
            sample_results = results_dict.get('sample_results', [])
            extraction_map = {}
            for sample_result in sample_results:
                sample_id = sample_result.get('sample_id')
                if sample_id:
                    extraction_map[sample_id] = sample_result
            
            all_extraction_maps = {extractor_name: extraction_map}
            extractor_names = [extractor_name]
        
        # Process each sample and add extracted content
        enriched_samples = []
        from webmainbench.metrics.base import BaseMetric
        
        for sample in dataset.samples:
            # Convert sample to dict
            sample_dict = sample.to_dict()
            
            # Add extraction results for each extractor
            for current_extractor_name in extractor_names:
                extraction_map = all_extraction_maps.get(current_extractor_name, {})
                extraction_result = extraction_map.get(sample.id)
                
                if extraction_result:
                    # Add extracted content with extractor name prefix
                    sample_dict[f'{current_extractor_name}_content'] = extraction_result.get('extracted_content', '')
                    sample_dict[f'{current_extractor_name}_content_list'] = extraction_result.get('extracted_content_list', [])
                    sample_dict[f'{current_extractor_name}_success'] = extraction_result.get('extraction_success', False)
                    sample_dict[f'{current_extractor_name}_time'] = extraction_result.get('extraction_time', 0)
                    
                    # Add metric scores for quick review
                    metrics = extraction_result.get('metrics', {})
                    for metric_name, metric_data in metrics.items():
                        if isinstance(metric_data, dict) and metric_data.get('success', False):
                            sample_dict[f'{current_extractor_name}_{metric_name}_score'] = metric_data.get('score', 0)

                    # Parse predicted values
                    predicted_content = extraction_result.get('extracted_content', '')
                    predicted_parts = BaseMetric._extract_from_markdown(predicted_content, field_name="llm_webkit_md")  # Key: parse predicted content
                    for part_type in ['code', 'formula', 'table', 'text']:
                        sample_dict[f'{current_extractor_name}_predicted_{part_type}'] = predicted_parts.get(part_type, '')

            # Parse groundtruth values - only needs to be parsed once
            if extractor_names:  # Only parse when extractors exist
                groundtruth_content = sample_dict.get('groundtruth_content', '')
                groundtruth_parts = BaseMetric._extract_from_markdown(groundtruth_content, field_name="groundtruth_content")  # Key: parse groundtruth content
                for part_type in ['code', 'formula', 'table', 'text']:
                    # Use the first extractor name as prefix, or use a generic prefix
                    prefix = extractor_names[0] if len(extractor_names) == 1 else 'groundtruth'
                    sample_dict[f'{prefix}_groundtruth_{part_type}'] = groundtruth_parts.get(part_type, '')

            enriched_samples.append(sample_dict)
        
        # Save as JSONL
        DataSaver._save_jsonl_list(enriched_samples, file_path)
    
    @staticmethod
    def _save_jsonl_list(data_list: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
        """Save list of dictionaries as JSONL file."""
        import json
        
        file_path = Path(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in data_list:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
    
    @staticmethod
    def _remove_content_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove extracted_content and extracted_content_list fields to reduce saved file size."""
        import copy
        
        cleaned_data = copy.deepcopy(data)
        
        def remove_fields(obj):
            if isinstance(obj, dict):
                # Remove extracted_content and extracted_content_list fields
                obj.pop('extracted_content', None)
                obj.pop('extracted_content_list', None)
                # Recursively process nested dicts and lists
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        remove_fields(value)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        remove_fields(item)
        
        remove_fields(cleaned_data)
        return cleaned_data
    
    @staticmethod
    def append_intermediate_results(results: List[Dict[str, Any]], 
                                  file_path: Union[str, Path]) -> None:
        """
        Append and save intermediate results, used for releasing memory during batch processing.

        Args:
            results: List of results to save
            file_path: Output file path
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append mode write to JSONL
        with open(file_path, 'a', encoding='utf-8') as f:
            for result in results:
                json.dump(result, f, ensure_ascii=False)
                f.write('\n')
    
    @staticmethod
    def save_streaming_results(results_iterator,
                             file_path: Union[str, Path],
                             batch_size: int = 100) -> int:
        """
        Stream and save evaluation results, suitable for large dataset processing.

        Args:
            results_iterator: Results iterator
            file_path: Output file path
            batch_size: Batch save size

        Returns:
            int: Number of saved results
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        saved_count = 0
        batch = []
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for result in results_iterator:
                batch.append(result)
                saved_count += 1
                
                # Write when batch size is reached
                if len(batch) >= batch_size:
                    for item in batch:
                        json.dump(item, f, ensure_ascii=False)
                        f.write('\n')
                    batch = []
            
            # Save the last batch
            if batch:
                for item in batch:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')
        
        return saved_count
    
    @staticmethod
    def create_streaming_writer(file_path: Union[str, Path]):
        """
        Create a streaming writer for saving results one by one.

        Args:
            file_path: Output file path

        Returns:
            StreamingResultWriter: Streaming writer instance
        """
        return StreamingResultWriter(file_path)


class StreamingResultWriter:
    """Streaming result writer for saving evaluation results one by one."""
    
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = None
        self.count = 0
    
    def __enter__(self):
        self.file_handle = open(self.file_path, 'w', encoding='utf-8')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            self.file_handle.close()
    
    def write_result(self, result: Dict[str, Any]) -> None:
        """Write a single result."""
        if self.file_handle:
            json.dump(result, self.file_handle, ensure_ascii=False)
            self.file_handle.write('\n')
            self.file_handle.flush()  # Ensure immediate write
            self.count += 1
    
    def get_count(self) -> int:
        """Get the number of results written."""
        return self.count
    
    @staticmethod
    def export_for_analysis(dataset: BenchmarkDataset,
                           file_path: Union[str, Path],
                           extractor_name: str = None) -> None:
        """
        Export dataset in a format suitable for analysis tools.
        
        Args:
            dataset: BenchmarkDataset to export
            file_path: Output file path
            extractor_name: Name of the extractor (for filtering results)
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        analysis_data = []
        
        for sample in dataset.samples:
            row = {
                'sample_id': sample.id,
                'url': sample.url,
                'domain': sample.domain,
                'language': sample.language,
                'content_type': sample.content_type,
                'difficulty': sample.difficulty,
                'groundtruth_length': len(sample.groundtruth_content) if sample.groundtruth_content else 0,
                'groundtruth_blocks': len(sample.groundtruth_content_list),
            }
            
            # Add extraction results if available
            if sample.extracted_results and extractor_name:
                if extractor_name in sample.extracted_results:
                    result = sample.extracted_results[extractor_name]
                    row.update({
                        'extracted_length': len(result.get('content', '')),
                        'extracted_blocks': len(result.get('content_list', [])),
                        'extraction_time': result.get('extraction_time'),
                        'extraction_success': result.get('success', False),
                    })
            
            analysis_data.append(row)
        
        # Save as JSON for easy loading into analysis tools
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False) 