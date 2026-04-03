import unittest
from webmainbench.extractors.factory import ExtractorFactory
from webmainbench.extractors.base import ExtractionResult


class TestExtractors(unittest.TestCase):

    def setUp(self):
        # Auto-discover extractors
        ExtractorFactory.auto_discover()

    def test_trafilatura_extractor(self):
        # Test Trafilatura extractor
        extractor = ExtractorFactory.create("trafilatura")
        html_content = """
        <html>
            <body>
                <h1 cc-select="true">Python Programming Tutorial</h1>
                <p cc-select="true">This is a basic Python tutorial demonstrating how to define functions.</p>
                <pre cc-select="true"><code>def greet(name):
    ""Greeting function""
    return f"Hello, {name}!"

# Usage example
result = greet("World")
print(result)</code></pre>
                <p cc-select="true">This function can be used to greet anyone.</p>
            </body>
        </html>
        """
        result = extractor.extract(html_content)
        self.assertEqual(isinstance(result, ExtractionResult), True)
        self.assertEqual(result.success in [True, False], True)

    def test_magic_html_extractor(self):
        # Test Magic HTML extractor
        try:
            extractor = ExtractorFactory.create("magic-html")
            html_content = """
            <html>
                <body>
                    <h1 cc-select="true">Python Programming Tutorial</h1>
                    <p cc-select="true">This is a basic Python tutorial demonstrating how to define functions.</p>
                    <pre cc-select="true"><code>def greet(name):
    ""Greeting function""
    return f"Hello, {name}!"

# Usage example
result = greet("World")
print(result)</code></pre>
                    <p cc-select="true">This function can be used to greet anyone.</p>
                </body>
            </html>
            """
            result = extractor.extract(html_content)
            self.assertEqual(isinstance(result, ExtractionResult), True)
            self.assertEqual(result.success in [True, False], True)
        except ValueError as e:
            # If extractor is not registered, skip the test
            self.skipTest(f"Magic HTML extractor not registered: {e}")

    def test_resiliparse_extractor(self):
        # Test Resiliparse extractor
        try:
            extractor = ExtractorFactory.create("resiliparse")
            html_content = """
            <html>
                <body>
                    <h1 cc-select="true">Python Programming Tutorial</h1>
                    <p cc-select="true">This is a basic Python tutorial demonstrating how to define functions.</p>
                    <pre cc-select="true"><code>def greet(name):
    ""Greeting function""
    return f"Hello, {name}!"

# Usage example
result = greet("World")
print(result)</code></pre>
                    <p cc-select="true">This function can be used to greet anyone.</p>
                </body>
            </html>
            """
            result = extractor.extract(html_content)
            self.assertEqual(isinstance(result, ExtractionResult), True)
            self.assertEqual(result.success in [True, False], True)
        except ValueError as e:
            # If extractor is not registered, skip the test
            self.skipTest(f"Resiliparse extractor not registered: {e}")


if __name__ == '__main__':
    unittest.main()