"""
Utility functions for WebMainBench.
"""

from .helpers import setup_logging, validate_config, format_results
from .main_html import extract_main_html, HTML2TextWrapper
from .html_cleaner import clean_browser_annotation_artifacts

__all__ = [
    "setup_logging",
    "validate_config", 
    "format_results",
    "extract_main_html",
    "HTML2TextWrapper",
    "clean_browser_annotation_artifacts",
]
