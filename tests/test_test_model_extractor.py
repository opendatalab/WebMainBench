import unittest
from webmainbench.extractors.test_model_extractor import TestModelExtractor

class TestTestModelExtractor(unittest.TestCase):
    """Tests basic functionality of TestModelExtractor"""

    def setUp(self):
        """Initialize the extractor instance for testing"""
        self.extractor = TestModelExtractor("test-model")

        # Use test_model.jsonl in the data directory as test data
        import json
        from pathlib import Path

        # Read the first sample as a test case
        data_path = Path(__file__).parent.parent / "data" / "test_model.jsonl"
        with open(data_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            sample_dict = json.loads(first_line)

        # Since TestModelExtractor expects sample to support attribute access, wrap it with SimpleNamespace
        from types import SimpleNamespace
        self.sample_data = SimpleNamespace(**sample_dict)

    def test_extract_from_sample(self):
        """Test the extract_from_sample method"""
        result = self.extractor.extract_from_sample(self.sample_data)
        self.assertTrue(result.success)
        self.assertEqual(result.content, self.sample_data.llm_webkit_md)
        self.assertEqual(result.content_list, self.sample_data.content_list)
        self.assertEqual(result.language, self.sample_data.language)
        self.assertEqual(result.confidence_score, 1.0)

    def test_extract_with_empty_html(self):
        """Test the extract method when given empty html"""
        result = self.extractor.extract("")
        self.assertFalse(result.success)
        self.assertIn("Empty HTML input", result.error_message)

if __name__ == "__main__":
    unittest.main()
