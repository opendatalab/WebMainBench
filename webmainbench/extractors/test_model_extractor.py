"""
Test Model Extractor for WebMainBench
"""

from typing import Dict, Any, Optional
from .base import BaseExtractor, ExtractionResult
from .factory import extractor

@extractor("test-model")
class TestModelExtractor(BaseExtractor):
    """
    A test extractor that does not perform actual extraction; returns the content and content_list fields directly from the dataset.
    Suitable for validating the evaluation pipeline and baseline testing.
    """

    version = "1.0.0"
    description = "Test extractor that returns groundtruth content/content_list for evaluation baseline"

    def _setup(self) -> None:
        """No special initialization needed for test model."""
        pass

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        """
        Read the content and content_list fields directly from the input html parameter (assumed to be a dataset sample dict or JSON string).
        """
        pass
