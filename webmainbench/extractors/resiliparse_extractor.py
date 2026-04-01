"""
resiliparse extractor implementation.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .base import BaseExtractor, ExtractionResult
from .factory import extractor
from resiliparse.extract.html2text import extract_plain_text
import re

@dataclass
class ResiliparseInferenceConfig:
    """Configuration for Resiliparse extractor."""
    main_content: bool = True # Whether to extract main content, enabled by default. (Discards <nav> (navigation lists), <footer> (copyright info), <aside> (sidebars), <footer> (page footer), etc.)
    alt_texts: bool = True  # Whether to extract alt attribute text from <img>, enabled by default
    links: bool = False  # Whether to extract hyperlinks, disabled by default
    form_fields: bool = False  # Whether to extract form controls, disabled by default
    noscript: bool = False  # Whether to extract content of <noscript> tags, disabled by default
    list_bullets: bool = True # Whether to mark list items with •, enabled by default
    preserve_formatting: bool = True  ## Controls format preservation: True (default): preserve basic formatting like lists and line breaks, False: fully compress (no line breaks, no lists, all text concatenated)
    comments: bool = True # Whether to keep user comments, enabled by default
    post_meta: bool = True  # Whether to keep article metadata, enabled by default
    hidden_elements: bool = False  # Whether to keep CSS-hidden elements, disabled by default
    


    # Additional resiliparse-supported parameters can be added here as needed


@extractor("resiliparse")
class ResiliparseExtractor(BaseExtractor):
    """Extractor using Resiliparse."""

    version = "0.14.5"
    description = "Resiliparse based content extractor"

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.inference_config = ResiliparseInferenceConfig()

        # Apply user configuration
        if config:
            for key, value in config.items():
                if hasattr(self.inference_config, key):
                    setattr(self.inference_config, key, value)

    def _setup(self) -> None:
        """Set up the Resiliparse extractor."""
        # Initialization operations
        pass

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        """
        Extract content using Resiliparse.

        Args:
            html: HTML content to extract from
            url: Optional URL of the page

        Returns:
            ExtractionResult instance
        """
        try:
            # Extract content using configuration parameters
            content = extract_plain_text(
                html,
                main_content=self.inference_config.main_content,
                alt_texts=self.inference_config.alt_texts,
                links=self.inference_config.links,
                form_fields=self.inference_config.form_fields,
                noscript=self.inference_config.noscript,
                list_bullets=self.inference_config.list_bullets,
                preserve_formatting=self.inference_config.preserve_formatting,
                comments=self.inference_config.comments
            )

            # Create content_list (simple paragraph splitting)
            content_list = []
            if content:
                paragraphs = content.split('\n\n')
                for i, para in enumerate(paragraphs):
                    if para.strip():
                        content_list.append({
                            "type": "paragraph",
                            "content": para.strip(),
                            "index": i
                        })

            return ExtractionResult(
                content=content,
                # content_list=content_list,
                title=self._extract_title(html),
                language=self._detect_language(content),
                success=True
            )

        except Exception as e:
            return ExtractionResult.create_error_result(
                f"Resiliparse extraction failed: {str(e)}"
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

    def _detect_language(self, content: str) -> Optional[str]:
        """Detect content language."""
        if not content:
            return None

        # Simple language detection logic
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))

        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > 0:
            return "en"
        else:
            return None

