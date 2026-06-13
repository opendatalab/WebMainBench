from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os
import hashlib
import json
from openai import OpenAI


def _metrics_debug(message: str) -> None:
    """Print diagnostics only when METRICS_DEBUG is True (see webmainbench/config.py)."""
    try:
        from ..config import METRICS_DEBUG
    except ImportError:
        METRICS_DEBUG = False
    if METRICS_DEBUG:
        print(f"[DEBUG] {message}")


class BaseContentSplitter(ABC):
    """Abstract base class for extracting specific types of content from text."""

    # Default LLM prompt template
    DEFAULT_LLM_PROMPT = """Please process the following content:
    {content}
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the extractor."""
        self.config = config or {}

        # Controls whether to use LLM
        self.use_llm = self.config.get('use_llm', True)

        # Initialize OpenAI client (if LLM is configured)
        if self.use_llm and self.config.get('llm_base_url') and self.config.get('llm_api_key'):
            self.client = OpenAI(
                base_url=self.config.get('llm_base_url', ""),
                api_key=self.config.get('llm_api_key', ""),
                timeout=self.config.get('llm_timeout', 60),
            )
        else:
            self.client = None

        self.cache_dir = self.config.get('cache_dir',
                                         os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                      '.cache'))
        os.makedirs(self.cache_dir, exist_ok=True)

    @abstractmethod
    def extract(self, text: str, field_name: str = None) -> str:
        """Extract specific types of content."""
        pass

    @abstractmethod
    def extract_basic(self, text: str) -> List[str]:
        """Extract content using basic methods (typically regular expressions)."""
        pass

    def should_use_llm(self, field_name: str) -> bool:
        """Determine whether to use LLM for enhanced extraction."""
        if not self.use_llm:
            return False

        # Default: do not use LLM for groundtruth content, use for others
        if field_name == "groundtruth_content":
            return False
        return True

    def enhance_with_llm(self, basic_results: List[str], cache_key: str = None) -> List[str]:
        """Enhance basic extraction results using LLM."""
        if not basic_results:
            return []

        # Generate cache key
        if cache_key is None:
            content_str = '\n'.join(basic_results)
            cache_key = hashlib.md5(content_str.encode('utf-8')).hexdigest()

        cache_file = os.path.join(self.cache_dir, f'{self.__class__.__name__.lower()}_cache_{cache_key}.json')

        # Check cache
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_result = json.load(f)
                    _metrics_debug(f"Loaded LLM-enhanced result from cache: {len(cached_result)} items")
                    return cached_result
            except Exception as e:
                _metrics_debug(f"Cache read failed: {e}")

        # Actual LLM enhancement logic
        try:
            enhanced_results = self._llm_enhance(basic_results)

            # Save to cache
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_results, f, ensure_ascii=False, indent=2)
                _metrics_debug(f"LLM-enhanced result cached at: {cache_file}")
            except Exception as e:
                _metrics_debug(f"Cache write failed: {e}")

            return enhanced_results
        except Exception as e:
            _metrics_debug(f"LLM enhancement failed: {type(e).__name__}: {e}")
            return basic_results

    @abstractmethod
    def _llm_enhance(self, basic_results: List[str]) -> List[str]:
        """Concrete implementation for enhancing basic extraction results with LLM."""
        pass
