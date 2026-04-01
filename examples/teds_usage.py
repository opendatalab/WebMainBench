#!/usr/bin/env python3
"""
WebMainBench TEDS Algorithm Usage Example

Demonstrates how to use the TEDS (Tree-Edit Distance based Similarity) algorithm
for table evaluation in assessments.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from webmainbench import (
    DataLoader, Evaluator, EvaluationResult,
    TEDSMetric, StructureTEDSMetric
)
from webmainbench.extractors import LLMWebkitExtractor
from webmainbench.data import DataSample, ExtractionResult


def demo_teds_configuration():
    """Demonstrate how to configure the TEDS algorithm"""
    print("=== TEDS Configuration Example ===\n")

    # Method 1: Use the TableTEDSMetric metric
    print("**Method 1: Use the dedicated TableTEDSMetric metric**")
    evaluation_config = {
        "metrics": {
            "table_extraction": {
                "use_teds": True,  # Enable TEDS algorithm
                "structure_only": False  # Consider both structure and content
            }
        }
    }
    print("Config:", evaluation_config)
    print()

    # Method 2: Use TEDS metric directly
    print("**Method 2: Use the standalone TEDS metric directly**")
    teds_config = {
        "metrics": {
            "teds": {
                "structure_only": False,
                "ignore_nodes": ["tbody", "thead", "tfoot"]
            },
            "s_teds": {  # Structural TEDS
                "structure_only": True
            }
        }
    }
    print("Config:", teds_config)
    print()


def demo_teds_comparison():
    """Demonstrate comparison of TEDS vs simple algorithm"""
    print("=== TEDS vs Simple Algorithm Comparison ===\n")

    # Prepare test data
    test_cases = [
        {
            "name": "Perfectly matching table",
            "extracted": """
            <table>
                <tr><th>Product</th><th>Price</th></tr>
                <tr><td>Apple</td><td>$5</td></tr>
                <tr><td>Orange</td><td>$3</td></tr>
            </table>
            """,
            "groundtruth": """
            <table>
                <tr><th>Product</th><th>Price</th></tr>
                <tr><td>Apple</td><td>$5</td></tr>
                <tr><td>Orange</td><td>$3</td></tr>
            </table>
            """
        },
        {
            "name": "Table with missing row",
            "extracted": """
            <table>
                <tr><th>Product</th><th>Price</th></tr>
                <tr><td>Apple</td><td>$5</td></tr>
            </table>
            """,
            "groundtruth": """
            <table>
                <tr><th>Product</th><th>Price</th></tr>
                <tr><td>Apple</td><td>$5</td></tr>
                <tr><td>Orange</td><td>$3</td></tr>
                <tr><td>Banana</td><td>$4</td></tr>
            </table>
            """
        },
        {
            "name": "Table with different structure",
            "extracted": """
            <table>
                <tr><th>Product</th><th>Price</th></tr>
                <tr><td>Apple</td><td>$5</td></tr>
            </table>
            """,
            "groundtruth": """
            <table>
                <tr><th>Product</th><th>Price</th><th>Stock</th></tr>
                <tr><td>Apple</td><td>$5</td><td>100</td></tr>
            </table>
            """
        }
    ]

    print("| Test case | Simple | TEDS | S-TEDS | Diff |")
    print("|---------|---------|---------|--------|------|")

    for case in test_cases:
        # Simple algorithm evaluation
        simple_evaluator = Evaluator(task_config={
            "metrics": {
                "table_extraction": {"use_teds": False}
            }
        })

        # TEDS algorithm evaluation
        teds_evaluator = Evaluator(task_config={
            "metrics": {
                "table_extraction": {"use_teds": True}
            }
        })

        # Create mock data
        sample = DataSample(
            id=f"test_{case['name']}",
            html="<div>Test HTML</div>",
            content="Test content",
            content_list=[{"table": case["groundtruth"]}]
        )

        extraction_result = ExtractionResult(
            extractor_name="test",
            extracted_content="Test content",
            extracted_content_list=[{"table": case["extracted"]}]
        )

        # Calculate scores
        try:
            simple_result = simple_evaluator.evaluate_single(sample, extraction_result)
            teds_result = teds_evaluator.evaluate_single(sample, extraction_result)

            simple_score = simple_result.overall_metrics.get("table_extraction", 0.0)
            teds_score = teds_result.overall_metrics.get("table_extraction", 0.0)

            # S-TEDS (structure-only) evaluation
            s_teds = StructureTEDSMetric("s_teds")
            s_teds_result = s_teds.calculate(case["extracted"], case["groundtruth"])
            s_teds_score = s_teds_result.score

            diff = abs(simple_score - teds_score)

            print(f"| {case['name'][:10]}... | {simple_score:.4f} | {teds_score:.4f} | {s_teds_score:.4f} | {diff:.4f} |")

        except Exception as e:
            print(f"| {case['name'][:10]}... | Error | Error | Error | - |")
            print(f"  Error message: {e}")

    print()


def demo_advanced_teds_features():
    """Demonstrate advanced TEDS features"""
    print("=== TEDS Advanced Feature Demo ===\n")

    # 1. Handle Markdown tables
    print("**1. Markdown Table Support**")
    teds = TEDSMetric("teds")

    markdown_table = """
    | Name | Age | Occupation |
    |------|------|------|
    | Alice | 25   | Engineer |
    | Bob   | 30   | Designer |
    """

    html_table = """
    <table>
        <tr><th>Name</th><th>Age</th><th>Occupation</th></tr>
        <tr><td>Alice</td><td>25</td><td>Engineer</td></tr>
        <tr><td>Bob</td><td>30</td><td>Designer</td></tr>
    </table>
    """

    result = teds.calculate(markdown_table, html_table)
    print(f"Markdown vs HTML table TEDS score: {result.score:.4f}")
    print(f"Details: {result.details}")
    print()

    # 2. Complex table structure
    print("**2. Complex Table Structure Support (colspan, rowspan)**")
    complex_table1 = """
    <table>
        <tr><th colspan="2">Student Info</th></tr>
        <tr><th>Name</th><th>Score</th></tr>
        <tr><td>Alice</td><td>95</td></tr>
        <tr><td>Bob</td><td>87</td></tr>
    </table>
    """

    complex_table2 = """
    <table>
        <tr><th>Category</th><th>Details</th></tr>
        <tr><th>Name</th><th>Score</th></tr>
        <tr><td>Alice</td><td>95</td></tr>
        <tr><td>Bob</td><td>87</td></tr>
    </table>
    """

    result = teds.calculate(complex_table1, complex_table2)
    print(f"Complex table structure TEDS score: {result.score:.4f}")
    print(f"Edit distance: {result.details.get('edit_distance')}")
    print(f"Node count: predicted={result.details.get('predicted_nodes')}, groundtruth={result.details.get('groundtruth_nodes')}")
    print()

    # 3. Structure-only vs content-sensitive evaluation
    print("**3. Structure-only vs Content-sensitive Evaluation Comparison**")
    content_teds = TEDSMetric("content_teds", {"structure_only": False})
    structure_teds = StructureTEDSMetric("structure_teds")

    table_diff_content = """
    <table>
        <tr><th>A</th><th>B</th></tr>
        <tr><td>Data1</td><td>Data2</td></tr>
    </table>
    """

    table_same_structure = """
    <table>
        <tr><th>X</th><th>Y</th></tr>
        <tr><td>Value1</td><td>Value2</td></tr>
    </table>
    """

    content_result = content_teds.calculate(table_diff_content, table_same_structure)
    structure_result = structure_teds.calculate(table_diff_content, table_same_structure)

    print(f"Content-sensitive TEDS score: {content_result.score:.4f}")
    print(f"Structure-only S-TEDS score: {structure_result.score:.4f}")
    print(f"Note: S-TEDS ignores text content differences and only focuses on table structure")
    print()


def demo_evaluation_workflow():
    """Demonstrate the complete evaluation workflow"""
    print("=== Complete Evaluation Workflow ===\n")

    print("**Step 1: Prepare data**")
    # Simulated evaluation data
    sample_data = DataSample(
        id="sample_001",
        html="""
        <div>
            <h1>Product Price List</h1>
            <table>
                <tr><th>Product</th><th>Price</th><th>Stock</th></tr>
                <tr><td>iPhone</td><td>$599</td><td>50</td></tr>
                <tr><td>iPad</td><td>$399</td><td>30</td></tr>
                <tr><td>MacBook</td><td>$1299</td><td>10</td></tr>
            </table>
        </div>
        """,
        content="Product Price List\n\n| Product | Price | Stock |\n|------|------|------|\n| iPhone | $599 | 50 |\n| iPad | $399 | 30 |\n| MacBook | $1299 | 10 |",
        content_list=[
            {
                "type": "title",
                "content": "Product Price List"
            },
            {
                "type": "table",
                "content": "| Product | Price | Stock |\n|------|------|------|\n| iPhone | $599 | 50 |\n| iPad | $399 | 30 |\n| MacBook | $1299 | 10 |"
            }
        ]
    )
    print("Data preparation complete")

    print("\n**Step 2: Configure TEDS evaluator**")
    evaluation_config = {
        "metrics": {
            "overall": "edit_distance",
            "table_extraction": {
                "use_teds": True,
                "structure_only": False
            }
        }
    }

    evaluator = Evaluator(task_config=evaluation_config)
    print("Evaluator configuration complete")

    print("\n**Step 3: Simulate extraction results**")
    # Simulate extraction result with minor errors
    extraction_result = ExtractionResult(
        extractor_name="TestExtractor",
        extracted_content="Product Price List\n\n| Product | Price |\n|------|------|\n| iPhone | $599 |\n| iPad | $399 |",  # Missing stock column and MacBook row
        extracted_content_list=[
            {
                "type": "title",
                "content": "Product Price List"
            },
            {
                "type": "table",
                "content": "| Product | Price |\n|------|------|\n| iPhone | $599 |\n| iPad | $399 |"
            }
        ]
    )
    print("Simulated extraction result generated")

    print("\n**Step 4: Run evaluation**")
    evaluation_result = evaluator.evaluate_single(sample_data, extraction_result)

    print(f"Evaluation results:")
    print(f"  - Overall score: {evaluation_result.overall_metrics.get('overall', 'N/A'):.4f}")
    print(f"  - Table extraction (TEDS): {evaluation_result.overall_metrics.get('table_extraction', 'N/A'):.4f}")
    print(f"  - Success rate: {evaluation_result.metadata.get('success_rate', 'N/A'):.2%}")

    # Display detailed TEDS information
    if evaluation_result.detailed_metrics:
        for metric_name, metric_result in evaluation_result.detailed_metrics.items():
            if 'teds' in metric_name.lower():
                print(f"\n{metric_name} details:")
                details = metric_result.details
                print(f"  - Algorithm: {details.get('algorithm', 'N/A')}")
                print(f"  - Edit distance: {details.get('edit_distance', 'N/A')}")
                print(f"  - Node count (predicted/groundtruth): {details.get('predicted_nodes', 'N/A')}/{details.get('groundtruth_nodes', 'N/A')}")

    print("\nEvaluation complete")


if __name__ == "__main__":
    print("WebMainBench TEDS Algorithm Usage Example\n")
    print("=" * 60)

    try:
        demo_teds_configuration()
        print("=" * 60)

        demo_teds_comparison()
        print("=" * 60)

        demo_advanced_teds_features()
        print("=" * 60)

        demo_evaluation_workflow()

        print("\nAll demos complete!")
        print("\nKey takeaways:")
        print("  1. TEDS algorithm provides more academically rigorous table evaluation")
        print("  2. Supports multiple table formats including HTML and Markdown")
        print("  3. Configurable structure-only evaluation (S-TEDS) or content-sensitive evaluation")
        print("  4. Accurately identifies table structure differences and content differences")
        print("  5. Fully compatible with existing evaluation workflows")

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()