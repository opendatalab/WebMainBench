import time
from webmainbench.extractors import ExtractorFactory

# Configure Resiliparse extractor
config = {
    "main_content": True,
    "alt_texts": True,
    "links": False,
    "form_fields": False,
    "noscript": False,
    "list_bullets": True,
    "preserve_formatting": True,
    "comments": True
}

try:
    # Create Resiliparse extractor instance
    extractor = ExtractorFactory.create("resiliparse", config=config)
    print(f"✅ Extractor created successfully: {extractor.description}")
    print(f"📋 Version: {extractor.version}")
    print(f"⚙️ Config: {extractor.get_config()}\n")
except Exception as e:
    print(f"❌ Failed to create extractor: {e}")


# Test HTML
test_html = """
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

print("🔍 Starting content extraction...")
start_time = time.time()

try:
    result = extractor.extract(test_html)
    end_time = time.time()

    print(f"⏱️ Extraction time: {end_time - start_time:.2f}s\n")

    # Display extraction results
    if result.success:
        print("✅ Content extracted successfully!\n")

        print("📄 Extracted main content:")
        print("=" * 50)
        print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
        print("=" * 50)

        print(f"\n📊 Extraction statistics:")
        print(f"  • Content length: {len(result.content)} characters")
        print(f"  • Title: {result.title}")
        print(f"  • Language: {result.language}")
        print(f"  • Extraction time: {result.extraction_time:.3f}s")

        if result.content_list:
            print(f"  • Structured content blocks: {len(result.content_list)}")
            for i, item in enumerate(result.content_list[:3]):  # Show first 3
                print(f"    [{i + 1}] {item.get('type', 'unknown')}: {item.get('content', '')[:50]}...")
    else:
        print("❌ Content extraction failed")
        print(f"Error message: {result.error_message}")
        if result.error_traceback:
            print(f"Error details:\n{result.error_traceback}")

except Exception as e:
    print(f"❌ Exception during extraction: {e}")
