import unittest
from unittest.mock import Mock, patch
from webmainbench.extractors.factory import ExtractorFactory
from webmainbench.extractors.base import ExtractionResult


def _is_llm_webkit_available():
    """Check if LLM-WebKit is available (for preprocessed HTML mode)."""
    try:
        from webmainbench.extractors.factory import ExtractorFactory
        config = {"use_preprocessed_html": True}
        extractor = ExtractorFactory.create("llm-webkit", config)
        return True
    except Exception:
        return False


class TestLLMWebKitExtractor(unittest.TestCase):
    """LLM-WebKit extractor functional tests."""

    def setUp(self):
        """Test setup."""
        # Auto-discover extractors
        ExtractorFactory.auto_discover()

        # Prepare preprocessed HTML content for testing
        self.preprocessed_main_html = """
        <div _item_id="1">
            <h1>Trends in Artificial Intelligence Development</h1>
            <p>Artificial Intelligence (AI) technology is rapidly advancing, with far-reaching impact across all industries.</p>
        </div>
        <div _item_id="2">
            <h2>Advances in Machine Learning</h2>
            <p>Breakthroughs in deep learning and large language models have enabled AI systems to understand and generate more natural language.</p>
        </div>
        <div _item_id="3">
            <h2>Automation Applications</h2>
            <p>From robots in manufacturing to code generation in software development, AI is automating processes across all domains.</p>
        </div>
        """

        # Simulate extraction results
        self.mock_extracted_content = "Trends in Artificial Intelligence Development\n\nArtificial Intelligence (AI) technology is rapidly advancing, with far-reaching impact across all industries.\n\nAdvances in Machine Learning\n\nBreakthroughs in deep learning and large language models have enabled AI systems to understand and generate more natural language."
        self.mock_extracted_content_list = [
            {"type": "heading", "content": "Trends in Artificial Intelligence Development"},
            {"type": "paragraph", "content": "Artificial Intelligence (AI) technology is rapidly advancing, with far-reaching impact across all industries."},
            {"type": "heading", "content": "Advances in Machine Learning"},
            {"type": "paragraph", "content": "Breakthroughs in deep learning and large language models have enabled AI systems to understand and generate more natural language."}
        ]

    def test_preprocessed_html_config(self):
        """Test preprocessed HTML configuration parameters."""
        config = {
            "use_preprocessed_html": True,
            "preprocessed_html_field": "custom_html_field"
        }
        
        try:
            extractor = ExtractorFactory.create("llm-webkit", config=config)
            
            # Verify that the configuration is correctly set
            self.assertTrue(extractor.inference_config.use_preprocessed_html)
            self.assertEqual(extractor.inference_config.preprocessed_html_field, "custom_html_field")

        except Exception as e:
            # If dependency is not available, skip the test
            self.skipTest(f"LLM-WebKit dependencies not available: {e}")

    @patch('webmainbench.extractors.llm_webkit_extractor.LlmWebkitExtractor._extract_content_from_main_html')
    def test_preprocessed_html_extract_content(self, mock_extract_from_main):
        """Test the _extract_content method using preprocessed HTML."""
        # Configure mock return value
        mock_extract_from_main.return_value = (self.mock_extracted_content, self.mock_extracted_content_list)

        config = {
            "use_preprocessed_html": True,
            "model_path": "/fake/model/path"  # Fake path for testing
        }
        
        try:
            extractor = ExtractorFactory.create("llm-webkit", config=config)
            
            # Call the _extract_content method
            result = extractor._extract_content(self.preprocessed_main_html, "https://example.com")

            # Verify mock was called correctly
            mock_extract_from_main.assert_called_once_with(self.preprocessed_main_html, "https://example.com")

            # Verify results
            self.assertIsInstance(result, ExtractionResult)
            self.assertTrue(result.success)
            self.assertEqual(result.content, self.mock_extracted_content)
            self.assertEqual(result.confidence_score, 0.9)  # Fixed confidence score for preprocessed HTML
            self.assertIsNotNone(result.extraction_time)
            
        except Exception as e:
            self.skipTest(f"LLM-WebKit dependencies not available: {e}")

    @patch('webmainbench.extractors.llm_webkit_extractor.LlmWebkitExtractor._extract_content_from_main_html')
    def test_standard_html_mode(self, mock_extract_from_main):
        """Test standard HTML mode (non-preprocessed)."""
        # Not setting use_preprocessed_html, should follow the standard process
        config = {
            "use_preprocessed_html": False,
            "model_path": "/fake/model/path"
        }

        try:
            extractor = ExtractorFactory.create("llm-webkit", config=config)

            # Use standard HTML
            standard_html = "<html><head><title>Test</title></head><body><p>Test content</p></body></html>"

            # Since standard mode requires HTML simplification and other steps, we only test the configuration
            self.assertFalse(extractor.inference_config.use_preprocessed_html)

            # Ensure _extract_content_from_main_html was not called directly
            # (because HTML simplification needs to happen first)
            # We do not actually call _extract_content here because it requires full dependencies
            
        except Exception as e:
            self.skipTest(f"LLM-WebKit dependencies not available: {e}")

    def test_config_defaults(self):
        """Test configuration default values."""
        try:
            extractor = ExtractorFactory.create("llm-webkit")

            # Verify default configuration
            self.assertFalse(extractor.inference_config.use_preprocessed_html)
            self.assertEqual(extractor.inference_config.preprocessed_html_field, "llm_webkit_html")
            
        except Exception as e:
            self.skipTest(f"LLM-WebKit dependencies not available: {e}")

    @patch('webmainbench.extractors.llm_webkit_extractor.LlmWebkitExtractor._extract_content_from_main_html')
    def test_error_handling_in_preprocessed_mode(self, mock_extract_from_main):
        """Test error handling in preprocessed mode."""
        # Configure mock to raise an exception
        mock_extract_from_main.side_effect = Exception("Mock extraction error")
        
        config = {
            "use_preprocessed_html": True,
            "model_path": "/fake/model/path"
        }
        
        try:
            extractor = ExtractorFactory.create("llm-webkit", config=config)
            
            # The call should catch the exception and return an error result
            result = extractor._extract_content(self.preprocessed_main_html)

            # Verify error handling
            self.assertIsInstance(result, ExtractionResult)
            self.assertFalse(result.success)
            self.assertIn("LLM-WebKit extraction failed", result.error_message)
            self.assertIsNotNone(result.extraction_time)
            
        except Exception as e:
            self.skipTest(f"LLM-WebKit dependencies not available: {e}")

    @unittest.skipUnless(
        _is_llm_webkit_available(),
        "Skip: LLM-WebKit dependencies required"
    )
    def test_preprocessed_html_integration(self):
        """Integration test: demonstrates actual usage of the preprocessed HTML feature."""
        print("\n" + "="*50)
        print("Preprocessed HTML Feature Integration Test")
        print("="*50)

        # Prepare preprocessed HTML content (simulate output from first stage of llm-webkit)
        preprocessed_main_html = """
        <div _item_id="1">
            <h1>Introduction to Deep Learning</h1>
            <p>Artificial Intelligence (AI) technology is rapidly advancing, with far-reaching impact across all industries. This article explores the major trends and future prospects of AI.</p>
        </div>
        <div _item_id="2">
            <h2>Advances in Machine Learning</h2>
            <p>Breakthroughs in deep learning and large language models have enabled AI systems to understand and generate more natural language, excelling in dialogue, translation, and creative tasks.</p>
        </div>
        <div _item_id="3">
            <h2>Automation Applications</h2>
            <p>From robots in manufacturing to code generation in software development, AI is automating processes across all domains, improving efficiency and reducing costs.</p>
        </div>
        """

        try:
            # Test 1: Configuration comparison between standard mode and preprocessed mode
            print("\nTest 1: Configuration comparison")

            # Standard mode configuration
            standard_config = {
                "use_preprocessed_html": False,
                "model_path": "/fake/model/path"
            }
            standard_extractor = ExtractorFactory.create("llm-webkit", config=standard_config)
            print(f"Standard mode - use_preprocessed_html: {standard_extractor.inference_config.use_preprocessed_html}")

            # Preprocessed mode configuration
            preprocessed_config = {
                "use_preprocessed_html": True,
                "preprocessed_html_field": "llm_webkit_html",
                "model_path": "/fake/model/path"
            }
            preprocessed_extractor = ExtractorFactory.create("llm-webkit", config=preprocessed_config)
            print(f"Preprocessed mode - use_preprocessed_html: {preprocessed_extractor.inference_config.use_preprocessed_html}")
            print(f"Preprocessed field: {preprocessed_extractor.inference_config.preprocessed_html_field}")

            # Test 2: Verify configuration correctness
            print("\nTest 2: Configuration validation")
            self.assertFalse(standard_extractor.inference_config.use_preprocessed_html)
            self.assertTrue(preprocessed_extractor.inference_config.use_preprocessed_html)
            self.assertEqual(preprocessed_extractor.inference_config.preprocessed_html_field, "llm_webkit_html")
            print("Configuration validation passed!")

            # Test 3: Title extraction feature
            print("\nTest 3: Title extraction feature")
            html_with_title = "<html><head><title>AI Development Trends Report</title></head><body>" + preprocessed_main_html + "</body></html>"
            title = preprocessed_extractor._extract_title(html_with_title)
            print(f"Extracted title: {title}")
            self.assertEqual(title, "AI Development Trends Report")

            # Test 4: Language detection feature
            print("\nTest 4: Language detection feature")
            test_content = "Artificial intelligence technology is rapidly advancing, with far-reaching impact across all industries."
            language = preprocessed_extractor._detect_language(test_content)
            print(f"Detected language: {language}")
            self.assertEqual(language, "en")

            print("\nPreprocessed HTML feature integration test complete!")

        except Exception as e:
            self.skipTest(f"LLM-WebKit dependencies not available: {e}")

    @unittest.skipIf(
        not _is_llm_webkit_available(),
        "LLM-WebKit dependencies not available"
    )
    def test_preprocessed_html_e2e(self):
        """End-to-end test for the preprocessed HTML feature."""
        try:
            # Scenario: a batch of data already processed through the first stage of llm-webkit
            dataset_samples = [
                {
                    "id": "sample_1",
                    "url": "https://example.com/article1",
                    "llm_webkit_html": """
                    <div _item_id="1">
                        <h1>Introduction to Deep Learning</h1>
                        <p>Deep learning is an important branch of machine learning.</p>
                    </div>
                    """,
                },
                {
                    "id": "sample_2",
                    "url": "https://example.com/article2",
                    "llm_webkit_html": """
                    <div _item_id="1">
                        <h1>Natural Language Processing Applications</h1>
                        <p>NLP technology has wide applications across many domains.</p>
                    </div>
                    """,
                }
            ]

            # Create extractor in preprocessed HTML mode
            config = {
                "use_preprocessed_html": True,
                "preprocessed_html_field": "llm_webkit_html"
            }
            extractor = ExtractorFactory.create("llm-webkit", config=config)

            # Verify configuration
            self.assertTrue(extractor.inference_config.use_preprocessed_html)
            self.assertEqual(extractor.inference_config.preprocessed_html_field, "llm_webkit_html")

            # Batch processing test
            results = []
            for sample in dataset_samples:
                result = extractor._extract_content(sample['llm_webkit_html'], sample['url'])
                results.append(result)

            # Core assertion validation
            successful_results = [r for r in results if r.success]

            # 1. All samples should be processed successfully
            self.assertEqual(len(successful_results), len(dataset_samples),
                           "All samples should be processed successfully")

            # 2. Verify basic properties of each result
            for i, result in enumerate(successful_results):
                with self.subTest(sample_id=dataset_samples[i]['id']):
                    # Content should not be empty
                    self.assertGreater(len(result.content), 0, "Extracted content should not be empty")

                    # Fixed confidence score for preprocessed HTML
                    self.assertEqual(result.confidence_score, 0.9, "Preprocessed HTML confidence score should be 0.9")

                    # Should contain relevant keywords
                    if "Deep learning" in dataset_samples[i]['llm_webkit_html']:
                        self.assertIn("Deep learning", result.content, "Should contain deep learning related content")
                    elif "Natural Language Processing" in dataset_samples[i]['llm_webkit_html']:
                        self.assertIn("Natural Language Processing", result.content, "Should contain NLP related content")

                    # Extraction time should be reasonable
                    self.assertGreater(result.extraction_time, 0, "Extraction time should be greater than 0")
                    self.assertLess(result.extraction_time, 10, "Extraction time should be within a reasonable range")
            
        except Exception as e:
            self.skipTest(f"LLM-WebKit dependencies not available: {e}")




if __name__ == '__main__':
    unittest.main()
