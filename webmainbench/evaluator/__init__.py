"""
Evaluator module for WebMainBench.

This module provides the main evaluation engine for running benchmarks.
"""

from .evaluator import Evaluator, EvaluationResult
from .main_html_evaluator import MainHTMLEvaluator
__all__ = [
    "Evaluator",
    "EvaluationResult",
    "MainHTMLEvaluator"
] 