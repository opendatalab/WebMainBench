"""
Dataset classes for WebMainBench.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
import json
from pathlib import Path


@dataclass
class DataSample:
    """Single data sample in the benchmark dataset."""
    
    # Required fields
    id: str
    html: str  # HTML with cc-select=true annotations
    groundtruth_content: str  # Groundtruth markdown content
    # Optional fields with defaults
    groundtruth_content_list: Optional[List[Dict[str, Any]]] = None  # Groundtruth content_list from llm-webkit
    content_list: List[Dict[str, Any]] = None # Content_list from llm-webkit
    content: str = None  # Content from llm-webkit
    # Optional metadata
    url: Optional[str] = None
    domain: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None  # article, forum, blog, etc.
    difficulty: Optional[str] = None  # easy, medium, hard
    tags: Optional[List[str]] = None
    llm_webkit_md: Optional[str] = None
    llm_webkit_html: Optional[str] = None  # Pre-processed HTML field
    main_html: Optional[str] = None  # Main HTML content field
    
    # Extracted results (populated during evaluation)
    extracted_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "id": self.id,
            "html": self.html,
            "groundtruth_content": self.groundtruth_content,
            "groundtruth_content_list": self.groundtruth_content_list,
            "content_list": self.content_list,
            "content": self.content,
            "llm_webkit_md": self.llm_webkit_md,
            "llm_webkit_html": self.llm_webkit_html,
            "main_html": self.main_html,
            "url": self.url,
            "domain": self.domain,
            "language": self.language,
            "content_type": self.content_type,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "extracted_results": self.extracted_results,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSample":
        """Create from dictionary, ignoring unknown fields and supporting field mapping."""
        # Get all field names of the class
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(cls)}
        
        # Define field name mappings (external field name -> internal field name)
        field_mapping = {
            "track_id": "id",  # track_id maps to id
            "content": "groundtruth_content",  # content maps to groundtruth_content
            "convert_main_content": "groundtruth_content",  # convert_main_content maps to groundtruth_content
            "content_list": "groundtruth_content_list",  # content_list maps to groundtruth_content_list
        }
        
        # Only extract defined fields, ignore others
        filtered_data = {}
        for key, value in data.items():
            # First check if field mapping is needed
            mapped_key = field_mapping.get(key, key)
            
            # If the mapped field name is in the class fields, add it
            if mapped_key in field_names:
                filtered_data[mapped_key] = value
            # Ignore undefined fields such as layout_id, max_layer_n, etc.
        
        return cls(**filtered_data)


class BenchmarkDataset:
    """Main dataset class for WebMainBench."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.samples: List[DataSample] = []
        self._metadata: Dict[str, Any] = {}
    
    def add_sample(self, sample: DataSample) -> None:
        """Add a data sample to the dataset."""
        self.samples.append(sample)
    
    def get_sample(self, sample_id: str) -> Optional[DataSample]:
        """Get a sample by ID."""
        for sample in self.samples:
            if sample.id == sample_id:
                return sample
        return None
    
    def filter_by_criteria(self, **kwargs) -> List[DataSample]:
        """Filter samples by criteria (e.g., language='en', difficulty='hard')."""
        filtered = self.samples
        for key, value in kwargs.items():
            filtered = [s for s in filtered if getattr(s, key, None) == value]
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        stats = {
            "total_samples": len(self.samples),
            "languages": {},
            "content_types": {},
            "difficulties": {},
            "domains": {},
        }
        
        for sample in self.samples:
            # Count languages
            lang = sample.language or "unknown"
            stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
            
            # Count content types
            ctype = sample.content_type or "unknown"
            stats["content_types"][ctype] = stats["content_types"].get(ctype, 0) + 1
            
            # Count difficulties
            diff = sample.difficulty or "unknown"
            stats["difficulties"][diff] = stats["difficulties"].get(diff, 0) + 1
            
            # Count domains
            domain = sample.domain or "unknown"
            stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
        
        return stats
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set dataset metadata."""
        self._metadata[key] = value
    
    def get_metadata(self, key: str = None) -> Union[Any, Dict[str, Any]]:
        """Get dataset metadata."""
        if key:
            return self._metadata.get(key)
        return self._metadata.copy()
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __iter__(self):
        return iter(self.samples)
    
    def __getitem__(self, index: int) -> DataSample:
        return self.samples[index] 