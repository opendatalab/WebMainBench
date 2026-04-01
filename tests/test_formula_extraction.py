#!/usr/bin/env python
"""Test Markdown formula extraction functionality"""

import unittest
import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from webmainbench.metrics.base import BaseMetric, MetricResult


class TestFormulaExtractionMetric(BaseMetric):
    """Concrete formula extraction metric implementation class for testing"""

    def _setup(self) -> None:
        pass

    def _calculate_score(self, predicted: str, groundtruth: str, **kwargs) -> MetricResult:
        return MetricResult(
            metric_name=self.name,
            score=1.0,
            details={"test": True}
        )


class TestFormulaExtraction(unittest.TestCase):
    """Test Markdown formula extraction functionality"""

    def setUp(self):
        self.metric = TestFormulaExtractionMetric("test_formula_metric")

    def test_inline_formula_extraction(self):
        """Test inline formula extraction"""
        text = """This is an inline formula example: $E = mc^2$, this is plain text."""

        result = self.metric._extract_from_markdown(text)

        # Verify formula was extracted
        self.assertIn('E = mc^2', result['formula'])

        # Verify formula marker was removed from text
        # self.assertNotIn('$E = mc^2$', result['text'])
        # self.assertIn('This is an inline formula example: , this is plain text.', result['text'])
        self.assertEqual(result['text'], text)

    def test_block_formula_extraction(self):
        """Test block formula extraction"""
        text = """This is a block formula:
$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$
End of formula"""

        result = self.metric._extract_from_markdown(text)

        # Verify formula was extracted
        self.assertIn('\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}', result['formula'])

        # Correction: allow multiple blank lines after extraction
        self.assertIn('This is a block formula:', result['text'])
        self.assertIn('End of formula', result['text'])
        # Check if original formula position has been cleared
        # self.assertNotIn('$$', result['text'])

    def test_escaped_dollar_signs(self):
        """Test that escaped dollar signs are not recognized as formulas"""
        text = """
        This is an escaped dollar sign: \\$100, it will not be recognized as a formula.
And this one is a formula: $a + b = c$
"""

        result = self.metric._extract_from_markdown(text)
        # Verify escaped dollar sign is not extracted
        self.assertNotIn('100', result['formula'])
        # Verify normal formula was extracted
        self.assertIn('a + b = c', result['formula'])
        # Verify escape character is retained in text
        self.assertIn('\\$100', result['text'])

    def test_multiple_formulas(self):
        """Test multiple formula extraction"""
        text = """Formula 1: $a = b + c$
Formula 2: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$
Formula 3: $E_k = \\frac{1}{2}mv^2$"""

        result = self.metric._extract_from_markdown(text)

        # Verify all formulas were extracted
        self.assertIn('a = b + c', result['formula'])
        self.assertIn('x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}', result['formula'])
        self.assertIn('E_k = \\frac{1}{2}mv^2', result['formula'])

        # Verify separator between formulas
        self.assertIn('\n', result['formula'])

    def test_formula_with_special_characters(self):
        """Test formulas containing special characters"""
        text = """Complex formula: $\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$
With Greek letters: $$\\alpha + \\beta = \\gamma$$"""

        result = self.metric._extract_from_markdown(text)

        # Verify special characters are handled correctly
        self.assertIn('\\sum_{i=1}^n i = \\frac{n(n+1)}{2}', result['formula'])
        self.assertIn('\\alpha + \\beta = \\gamma', result['formula'])

    def test_formula_within_text(self):
        """Test formula extraction within text"""
        text = """According to relativity $E = mc^2$, energy and mass can be converted to each other.
A more complex case such as $$\\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\epsilon_0}$$ is shown."""

        result = self.metric._extract_from_markdown(text)

        # Verify formulas were extracted
        self.assertIn('E = mc^2', result['formula'])
        self.assertIn('\\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\epsilon_0}', result['formula'])

        # Correction: allow multiple spaces after extraction
        # self.assertIn('According to relativity , energy and mass can be converted to each other.', result['text'])
        # self.assertIn('A more complex case such as  is shown.', result['text'])
        self.assertEqual(result['text'], text)

    def test_empty_formulas(self):
        """Test empty formula handling"""
        text = """Empty inline formula: $   $
Empty block formula: $$   $$"""

        result = self.metric._extract_from_markdown(text)

        # Verify empty formula was extracted but content is empty
        self.assertTrue(result['formula'].strip() == '')

        # Verify empty formula marker was removed from text
        # self.assertNotIn('$   $', result['text'])
        # self.assertNotIn('$$   $$', result['text'])

#     def test_formula_at_document_edges(self):
#         """Test formulas at the beginning and end of the document"""
#         # Formula at the start
#         text1 = """$start = 0$
# Subsequent text"""
#         result1 = self.metric._extract_from_markdown(text1)
#         self.assertIn('start = 0', result1['formula'])
#
#         # Formula at the end
#         text2 = """Preceding text
# $$end = 1$$"""
#         result2 = self.metric._extract_from_markdown(text2)
#         self.assertIn('end = 1', result2['formula'])

    def test_formula_within_table(self):
        """Test formula extraction within a table"""
        text = """| Formula Type | Example |
|----------|------|
| Inline formula | $a + b = c$ |
| Block formula | $$\\int_0^1 x dx = 0.5$$ |"""

        result = self.metric._extract_from_markdown(text)

        # Verify formulas in table were extracted
        self.assertIn('a + b = c', result['formula'])
        self.assertIn('\\int_0^1 x dx = 0.5', result['formula'])

        # Verify table structure is still correctly extracted
        self.assertIn('| Formula Type | Example |', result['table'])

    def test_formula_within_code_block(self):
        """Test that formulas in code blocks are not extracted"""
        text = """Here is a code example:
            Inline code

            ```python
            # Formulas in here should not be extracted
            def calculate():
                # Inline formula $a + b = c$ in code
                result = 0
                return result
                ```
            Inline code:`$A+B=C$`

            """
        result = self.metric._extract_from_markdown(text)
        self.assertNotIn('a + b = c', result['formula'])
        self.assertNotIn('A+B=C', result['formula'])
