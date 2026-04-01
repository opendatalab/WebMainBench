"""
Text-based metrics for WebMainBench.
"""

from typing import Dict, Any, List
import jieba
import difflib
import re
from .base import BaseMetric, MetricResult
from rapidfuzz.distance import Levenshtein

class EditDistanceMetric(BaseMetric):
    """Edit distance (Levenshtein distance) metric."""
    
    version = "1.0.0"
    description = "Character-level edit distance metric"
    
    def _setup(self) -> None:
        """Setup the edit distance metric."""
        self.normalize = self.config.get('normalize', True)
    
    def _calculate_score(self, predicted: str, groundtruth: str, **kwargs) -> MetricResult:
        """
        Calculate edit distance between predicted and ground truth text.
        
        Args:
            predicted: Predicted text
            groundtruth: Ground truth text
            
        Returns:
            MetricResult with edit distance score
        """
        if not isinstance(predicted, str) or not isinstance(groundtruth, str):
            return MetricResult.create_error_result(
                self.name, "Both inputs must be strings"
            )
        
        # Calculate edit distance using difflib
        distance = self._levenshtein_distance(predicted, groundtruth)
        
        # Normalize by the length of the longer string
        if self.normalize:
            max_len = max(len(predicted), len(groundtruth))
            # if max_len == 0:
            #     score = 1.0  # Both strings are empty
            # else:
            #     score = 1.0 - (distance / max_len)
            if max_len == 0:
                # Mark as failed when both are empty
                return MetricResult.create_error_result(
                    self.name,
                    "Both predicted and groundtruth are empty"
                )

            score = 1.0 - (distance / max_len)
            return MetricResult(
                metric_name=self.name,
                score=score,
                details={
                    "distance": distance,
                    "predicted_length": len(predicted),
                    "groundtruth_length": len(groundtruth),
                    "normalized": True
                }
            )
        else:
            score = distance



        details = {
            "distance": distance,
            "predicted_length": len(predicted),
            "groundtruth_length": len(groundtruth),
            "normalized": self.normalize,
        }


        return MetricResult(
            metric_name=self.name,
            score=score,
            details=details
        )
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""

        return Levenshtein.distance(s1, s2)



class BLEUMetric(BaseMetric):
    """BLEU score metric for text similarity."""
    
    version = "1.0.0"
    description = "BLEU score for text similarity evaluation"
    
    def _setup(self) -> None:
        """Setup the BLEU metric."""
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            self._sentence_bleu = sentence_bleu
            self._smoothing = SmoothingFunction()
        except ImportError:
            raise RuntimeError("NLTK is required for BLEU metric")
        
        self.max_n = self.config.get('max_n', 4)
        self.smoothing_method = self.config.get('smoothing_method', 'method1')
    
    def _calculate_score(self, predicted: str, groundtruth: str, **kwargs) -> MetricResult:
        """
        Calculate BLEU score between predicted and ground truth text.
        
        Args:
            predicted: Predicted text
            groundtruth: Ground truth text
            
        Returns:
            MetricResult with BLEU score
        """
        if not isinstance(predicted, str) or not isinstance(groundtruth, str):
            return MetricResult.create_error_result(
                self.name, "Both inputs must be strings"
            )
        
        # Tokenize texts (simple whitespace tokenization)
        predicted_tokens = predicted.split()
        groundtruth_tokens = groundtruth.split()
        
        if not predicted_tokens and not groundtruth_tokens:
            score = 1.0  # Both are empty
        elif not predicted_tokens or not groundtruth_tokens:
            score = 0.0  # One is empty
        else:
            # Calculate BLEU score
            smoothing_func = getattr(self._smoothing, self.smoothing_method)
            score = self._sentence_bleu(
                [groundtruth_tokens], 
                predicted_tokens,
                smoothing_function=smoothing_func
            )
        
        details = {
            "predicted_tokens": len(predicted_tokens),
            "groundtruth_tokens": len(groundtruth_tokens),
            "max_n": self.max_n,
            "smoothing_method": self.smoothing_method,
        }
        
        return MetricResult(
            metric_name=self.name,
            score=score,
            details=details
        )


class ROUGEMetric(BaseMetric):
    """ROUGE score metric for text similarity."""
    
    version = "1.0.0"
    description = "ROUGE score for text similarity evaluation"
    
    def _setup(self) -> None:
        """Setup the ROUGE metric."""
        try:
            import rouge
            self._rouge = rouge.Rouge()
        except ImportError:
            raise RuntimeError("rouge-score package is required for ROUGE metric")
        
        self.rouge_types = self.config.get('rouge_types', ['rouge-1', 'rouge-2', 'rouge-l'])
        self.use_stemmer = self.config.get('use_stemmer', True)
    
    def _calculate_score(self, predicted: str, groundtruth: str, **kwargs) -> MetricResult:
        """
        Calculate ROUGE score between predicted and ground truth text.
        
        Args:
            predicted: Predicted text
            groundtruth: Ground truth text
            
        Returns:
            MetricResult with ROUGE scores
        """
        if not isinstance(predicted, str) or not isinstance(groundtruth, str):
            return MetricResult.create_error_result(
                self.name, "Both inputs must be strings"
            )
        
        if not predicted.strip() and not groundtruth.strip():
            # Both are empty
            score = 1.0
            details = {"rouge-1": {"f": 1.0}, "rouge-2": {"f": 1.0}, "rouge-l": {"f": 1.0}}
        elif not predicted.strip() or not groundtruth.strip():
            # One is empty
            score = 0.0
            details = {"rouge-1": {"f": 0.0}, "rouge-2": {"f": 0.0}, "rouge-l": {"f": 0.0}}
        else:
            # Calculate ROUGE scores
            try:
                scores = self._rouge.get_scores(predicted, groundtruth)[0]
                # Use ROUGE-L F1 as the main score
                score = scores['rouge-l']['f']
                details = scores
            except Exception as e:
                return MetricResult.create_error_result(
                    self.name, f"ROUGE calculation failed: {str(e)}"
                )
        
        return MetricResult(
            metric_name=self.name,
            score=score,
            details=details
        ) 


class CodeEditMetric(EditDistanceMetric):
    """Code edit distance metric"""

    version = "1.0.0"
    description = "Code block edit distance metric"

    def _calculate_score(self, predicted: str, groundtruth: str,
                        predicted_content_list: List[Dict[str, Any]] = None,
                        groundtruth_content_list: List[Dict[str, Any]] = None,
                        **kwargs) -> MetricResult:
        """Calculate edit distance for code blocks"""

        # Extract code content from content_list
        pred_code = self._extract_code_content(predicted, predicted_content_list)
        gt_code = self._extract_code_content(groundtruth, groundtruth_content_list)

        # Calculate edit distance
        result = super()._calculate_score(pred_code, gt_code, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "predicted_code_length": len(pred_code),
            "groundtruth_code_length": len(gt_code),
            "content_type": "code"
        })

        return result

    def _extract_code_content(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """Extract code content from text and content_list"""
        # Use the unified content splitting method
        content_parts = self.split_content(text, content_list)
        return content_parts.get('code', '')

    def _extract_codes_from_content_list(self, content_list: List[Dict[str, Any]]) -> List[str]:
        """Recursively extract code content from content_list"""
        codes = []

        def _recursive_extract(items):
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, dict):
                    continue

                # Check if the current item is code
                item_type = item.get('type', '')
                if item_type in ['code']:
                    content = item.get('content', '')
                    if content:
                        codes.append(content)

                # Recursively check the children field
                children = item.get('children')
                if children:
                    _recursive_extract(children)

                # Recursively check the items field
                items_field = item.get('items')
                if items_field:
                    _recursive_extract(items_field)

        _recursive_extract(content_list)
        return codes


class TextEditMetric(EditDistanceMetric):
    """Pure text edit distance metric (excluding code, tables, and formulas)"""

    version = "1.0.0"
    description = "Pure text edit distance metric (excluding code, tables, formulas)"

    def _calculate_score(self, predicted: str, groundtruth: str,
                        predicted_content_list: List[Dict[str, Any]] = None,
                        groundtruth_content_list: List[Dict[str, Any]] = None,
                        **kwargs) -> MetricResult:
        """Calculate edit distance for pure text"""

        # Remove code, tables, and formulas from text
        pred_text = self._extract_pure_text(predicted, predicted_content_list)
        gt_text = self._extract_pure_text(groundtruth, groundtruth_content_list)

        # Calculate edit distance
        result = super()._calculate_score(pred_text, gt_text, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "predicted_text_length": len(pred_text),
            "groundtruth_text_length": len(gt_text),
            "content_type": "text"
        })

        return result

    def _extract_pure_text(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """Extract pure text content (excluding code, tables, and formulas)"""
        # Use the unified content splitting method
        content_parts = self.split_content(text, content_list)
        return content_parts.get('text', '')

    def _extract_text_from_content_list(self, content_list: List[Dict[str, Any]]) -> List[str]:
        """Recursively extract pure text content from content_list (excluding code, tables, formulas)"""
        texts = []

        def _recursive_extract(items):
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, dict):
                    continue

                # Check if the current item is pure text content
                item_type = item.get('type', '')
                # Exclude special content types such as code, tables, and formulas
                if item_type in ['paragraph', 'heading', 'text', 'list_item', 'list-item']:
                    content = item.get('content', '')
                    if content:
                        texts.append(content)

                # Recursively check the children field
                children = item.get('children')
                if children:
                    _recursive_extract(children)

                # Recursively check the items field
                items_field = item.get('items')
                if items_field:
                    _recursive_extract(items_field)

        _recursive_extract(content_list)
        return texts


class TextRougeNgramMetric(BaseMetric):
    """Text Rouge-Ngram similarity metric"""
    
    version = "1.0.0"
    description = "Text Rouge-Ngram similarity metric"

    
    def _setup(self) -> None:
        self.ngram = self.config.get('ngram', 5)
        try:
            from rouge_score.rouge_scorer import _create_ngrams, _score_ngrams
            self._create_ngrams = _create_ngrams
            self._score_ngrams = _score_ngrams
        except ImportError:
            raise RuntimeError("rouge package is required for TextRouge metric")
            
    
    def _calculate_score(self, predicted: Any, groundtruth: Any, **kwargs) -> MetricResult:
        try:
            rouge_score_result = self.calc_rouge_n_score(
                target_input=groundtruth,
                prediction_input=predicted,
                n=self.ngram
            )
            return MetricResult(
                metric_name="rouge_n",
                score=rouge_score_result['f1'],
                details=rouge_score_result,
                success=True
            )
        except Exception as e:
            return MetricResult.create_error_result(
                metric_name="rouge_n",
                error_message=str(e)
            )

    def calc_rouge_n_score(self, target_input: str, prediction_input: str, n: int = 5) -> dict:
        """
        Calculate the ROUGE-N score between the target and prediction inputs.

        Args:
            target_input (str): The ground truth text.
            prediction_input (str): The predicted text.
            n (int, optional): The n-gram size. Defaults to 5.

        Returns:
            dict: A dictionary containing the precision, recall, and F1 score.
        """
        target = target_input.strip()
        prediction = prediction_input.strip()

        # When both target and prediction are empty
        # we consider the prediction to be perfect
        if len(target) == 0 and len(prediction) == 0:
            return {'prec': 1.0, 'rec': 1.0, 'f1': 1.0}

        target_tokens_list = [x for x in jieba.lcut(target_input)]
        target_ngrams = self._create_ngrams(target_tokens_list, n)

        prediction_tokens_list = [x for x in jieba.lcut(prediction_input)]
        prediction_ngrams = self._create_ngrams(prediction_tokens_list, n)

        score = self._score_ngrams(target_ngrams, prediction_ngrams)

        # Convert scores to precision, recall, f1-score in ROUGE-L format
        result = {'prec': score.precision, 'rec': score.recall, 'f1': score.fmeasure}
        return result

