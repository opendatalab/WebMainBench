# webmainbench/extractors/magic_html_extractor.py
"""
Magic HTML extractor implementation.
"""

from typing import Dict, Any, Optional, List
from .base import BaseExtractor, ExtractionResult
from .factory import extractor
from magic_html import GeneralExtractor
import re
import html2text
from ..utils import HTML2TextWrapper


@extractor("magic-html")
class MagicHtmlExtractor(BaseExtractor):
    """Extractor using Magic HTML."""

    version = "0.1.5"
    description = "Magic HTML based content extractor"

    def _setup(self) -> None:
        """Set up the Magic HTML extractor."""
        try:
            self.extractor = GeneralExtractor()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Magic HTML extractor: {e}")

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        try:
            # Use Magic HTML for extraction
            data = self.extractor.extract(html)

            # Extract required information from output
            extracted_html = data.get('html', '')
            # Use internal HTML2Text method to generate markdown
            h = HTML2TextWrapper()
            markdown = h(extracted_html)
            # markdown = html2text.html2text(extracted_html)
            title = data.get('title', '')
            # Use extracted HTML as content
            content = markdown
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
                title=title,
                language=self._detect_language(content),
                success=True
            )

        except Exception as e:
            return ExtractionResult.create_error_result(
                f"Magic HTML extraction failed: {str(e)}"
            )


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

