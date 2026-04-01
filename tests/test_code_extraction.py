# tests/test/test_code_extraction.py
# !/usr/bin/env python
"""Test code extraction functionality"""

import unittest
import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from webmainbench.metrics.base import BaseMetric, MetricResult


class TestCodeExtractionMetric(BaseMetric):
    """Concrete implementation class for testing"""

    def _setup(self) -> None:
        pass

    def _calculate_score(self, predicted: str, groundtruth: str, **kwargs) -> MetricResult:
        return MetricResult(
            metric_name=self.name,
            score=1.0,
            details={"test": True}
        )


class TestCodeExtraction(unittest.TestCase):
    """Test code extraction functionality"""

    def setUp(self):
        self.metric = TestCodeExtractionMetric("test_metric")

    def test_empty_text(self):
        """Test empty text"""
        result = BaseMetric._extract_from_markdown("")
        self.assertEqual(result['code'], '')
        self.assertEqual(result['text'], '')

    # def test_inline_code(self):
    #     """Test inline code"""
    #     text = "This is an example of `inline code`"
    #     result = BaseMetric._extract_from_markdown(text)
    #     print(result)
    #     self.assertEqual(result['code'], 'inline code')
    #     self.assertEqual(result['text'], text)

    def test_code_block(self):
        """Test code block"""
        text = """
I have the following string: `"aaaabbbb"`
How can I get the last four characters and store them in a string using Python?
Like this:
```python
>>> mystr = "abcdefghijkl"
>>> mystr[-4:]
'ijkl'
```
        """

        result = BaseMetric._extract_from_markdown(text)

        # Verify extracted code
        expected_code = ("""
>>> mystr = "abcdefghijkl"
>>> mystr[-4:]
'ijkl'
        """)
        self.assertEqual(result['code'], expected_code.strip())
        self.assertEqual(result['formula'], '')

    # def test_code_with_leading_trailing_spaces(self):
    #     """Test code with leading/trailing spaces"""
    #     text = "before `  code  ` after"
    #     result = BaseMetric._extract_from_markdown(text)
    #     self.assertEqual(result['code'], 'code')  # should strip spaces
    #     self.assertEqual(result['text'], text)

    # def test_multiline_inline_code(self):
    #     """Test multiline inline code (should not match)"""
    #     text = "`line1\nline2`"
    #     result = BaseMetric._extract_from_markdown(text)
    #     self.assertEqual(result['code'], '')  # should not match multiline inline code
    #     self.assertEqual(result['text'], text)  # preserve as-is

    def test_indent_code_block(self):
        """Test indented code block"""
        text = """
I have the following string: `"aaaabbbb"`
How can I get the last four characters and store them in a string using Python?
Like this:
    
    print("hello world")
    print("hi")

        """

        result = BaseMetric._extract_from_markdown(text)

        # Verify extracted code
        expected_code = ("""
print("hello world")
print("hi")
        """)
        self.assertEqual(result['code'], expected_code.strip())
        self.assertEqual(result['formula'], '')


if __name__ == '__main__':
    unittest.main()
