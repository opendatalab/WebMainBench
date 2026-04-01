#!/usr/bin/env python3
"""
LLM-WebKit Extractor Usage Example

This example demonstrates how to use the LLM-WebKit extractor integrated with VLLM inference capabilities.
"""

import time
from webmainbench.extractors import ExtractorFactory


def main():
    print("LLM-WebKit Extractor Usage Example\n")

    # 1. Create extractor with custom configuration
    config = {
        "model_path": "/Users/chupei/model/checkpoint-3296",  # Replace with your model path
        "use_logits_processor": True,  # Enable JSON format constraint
        "temperature": 0.0,  # Deterministic output
        "max_item_count": 500,  # Maximum number of items to process
        "max_output_tokens": 4096,  # Maximum output tokens
        "dtype": "bfloat16",  # Model precision
        "tensor_parallel_size": 1  # Tensor parallel size
    }

    try:
        extractor = ExtractorFactory.create("llm-webkit", config=config)
        print(f"Extractor created successfully: {extractor.description}")
        print(f"Version: {extractor.version}")
        print(f"Config: {extractor.inference_config.__dict__}\n")

    except Exception as e:
        print(f"Extractor creation failed: {e}")
        print("Please ensure the required dependencies are installed:")
        print("   pip install vllm transformers torch llm_web_kit")
        return

    # 2. Prepare test HTML (structured HTML with _item_id attributes)
    test_html = """
    <html>
    <head>
        <title>Test Article - AI Development Trends</title>
    </head>
    <body>
        <nav _item_id="1">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/news">News</a></li>
                <li><a href="/tech">Tech</a></li>
            </ul>
        </nav>

        <header _item_id="2">
            <h1>AI Development Trends</h1>
            <p class="meta">Author: John Doe | Published: 2024-01-15 | Views: 1,234</p>
        </header>

        <main _item_id="3">
            <article>
                <p>Artificial Intelligence (AI) technology is rapidly advancing, with far-reaching impacts across all industries. This article explores the major development trends and future prospects of AI.</p>

                <h2>1. Advances in Machine Learning</h2>
                <p>Breakthroughs in deep learning and large language models have enabled AI systems to understand and generate more natural language, excelling in dialogue, translation, and creative tasks.</p>

                <h2>2. Automation Applications</h2>
                <p>From robots in manufacturing to code generation in software development, AI is automating processes across domains, improving efficiency and reducing costs.</p>

                <h2>3. Personalized Services</h2>
                <p>Personalized recommendations and services based on user data are becoming increasingly precise, providing better user experiences.</p>
            </article>
        </main>

        <aside _item_id="4">
            <h3>Related Articles</h3>
            <ul>
                <li><a href="/article1">Introduction to Machine Learning</a></li>
                <li><a href="/article2">Deep Learning Application Cases</a></li>
                <li><a href="/article3">AI Ethics and Safety</a></li>
            </ul>
        </aside>

        <footer _item_id="5">
            <p>&copy; 2024 Tech News. All rights reserved.</p>
            <div class="social-links">
                <a href="#">Twitter</a> | <a href="#">LinkedIn</a> | <a href="#">GitHub</a>
            </div>
        </footer>
    </body>
    </html>
    """

    # 3. Execute content extraction
    print("Starting content extraction...")
    start_time = time.time()
    
    try:
        result = extractor.extract(test_html)
        end_time = time.time()
        
        print(f"⏱️ Extraction time: {end_time - start_time:.2f}s\n")

        # 4. Display extraction results
        if result.success:
            print("✅ Content extracted successfully!\n")

            print("📄 Extracted main content:")
            print("=" * 50)
            print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
            print("=" * 50)

            print(f"\n📊 Extraction statistics:")
            print(f"  • Content length: {len(result.content)} characters")
            print(f"  • Confidence: {result.confidence_score:.3f}")
            print(f"  • Title: {result.title}")
            print(f"  • Language: {result.language}")
            print(f"  • Extraction time: {result.extraction_time:.3f}s")

            if result.content_list:
                print(f"  • Structured content blocks: {len(result.content_list)}")
                for i, item in enumerate(result.content_list[:3]):  # Show first 3
                    print(f"    [{i+1}] {item.get('type', 'unknown')}: {item.get('content', '')[:50]}...")

        else:
            print("❌ Content extraction failed")
            print(f"Error message: {result.error_message}")
            if result.error_traceback:
                print(f"Error details:\n{result.error_traceback}")

    except Exception as e:
        print(f"❌ Exception during extraction: {e}")

    print("\n🎯 Advanced feature notes:")
    print("• Smart classification: Uses LLM to understand HTML element semantics, accurately distinguishing main content from auxiliary content")
    print("• Format constraint: Uses logits processor to ensure valid JSON output from the LLM")
    print("• Performance optimization: Automatically skips overly complex HTML, supports lazy model loading")
    print("• Detailed feedback: Provides classification results, confidence scores, and performance metrics")


if __name__ == "__main__":
    main()

    print("\n💡 Usage tips:")
    print("1. Ensure required dependencies are installed: vllm, transformers, torch, llm_web_kit")
    print("2. Set the correct model path")
    print("3. Adjust tensor_parallel_size and dtype based on hardware resources")
    print("4. For large-scale HTML, adjust max_item_count accordingly")
    print("5. Use use_logits_processor=True to ensure reliable output format") 