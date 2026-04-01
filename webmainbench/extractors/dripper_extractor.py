"""
LLM-WebKit extractor implementation with advanced LLM inference.
"""
import time
from typing import Dict, Any, Optional

from .base import BaseExtractor, ExtractionResult
from .factory import extractor

from ..utils import HTML2TextWrapper


@extractor("dripper")
class DripperExtractor(BaseExtractor):
    """Extractor using dripper."""

    version = "1.0.0"
    description = "Extractor using dripper."


    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        
        try:
            
            from dripper.api import Dripper
            from dripper.base import DripperInput, DripperOutput
        except ImportError:
            raise ImportError("Please install dripper package")
        
        # Initialize inference_config first, then call parent initialization (since parent calls _setup())
        self.dripper = Dripper(config)
        self.html2text = HTML2TextWrapper()

        # Now it is safe to call parent initialization (which calls _setup())
        super().__init__(name, config)
    
    def _setup(self) -> None:
        self.dripper.get_llm()
        self.dripper.get_tokenizer()

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        """
        Extract content using advanced LLM inference.
        
        Args:
            html: HTML content. If use_preprocessed_html=True is configured, preprocessed HTML is passed in by Evaluator.
            url: Optional page URL
            
        Returns:
            ExtractionResult instance
        """
        start_time = time.time()
        
        try:
            dripper_input = DripperInput(raw_html=html, url=url, case_id=None)
            dripper_output : DripperOutput = self.dripper.process([dripper_input])[0]
            
            main_html = dripper_output.main_html
            main_content = self.html2text(main_html, url)

            extraction_time = time.time() - start_time
            
            # Create result object
            result = ExtractionResult(
                content=main_content,
                main_html=main_html,
                # content_list=content_list,
                title=self._extract_title(html),
                confidence_score=1.0,
                extraction_time=extraction_time,
                success=True
            )
            
            # Add debug info to error message field (for development debugging)
            return result
            
        except Exception as e:
            extraction_time = time.time() - start_time
            import traceback
            return ExtractionResult.create_error_result(
                f"LLM-WebKit extraction failed: {str(e)}",
                traceback.format_exc(),
                extraction_time
            )
    
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title."""
        try:
            import re
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                return title_match.group(1).strip()
        except:
            pass
        return None
