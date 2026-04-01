#!/usr/bin/env python3
"""
Comprehensive tests for TEDS (Tree-Edit Distance based Similarity) metrics.
"""

import re
import unittest
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from webmainbench.metrics.teds_metrics import TEDSMetric, StructureTEDSMetric
from webmainbench.metrics.base import MetricResult



class TestTEDSBasic(unittest.TestCase):
    """Basic TEDS functionality tests"""

    def setUp(self):
        """Set up test fixtures"""
        # self.teds = TEDSMetric("test_teds")
        self.teds_metric = TEDSMetric(name="table_TEDS")
        self.s_teds_metric = StructureTEDSMetric(name="s_teds")

        # Create a "success" status table_edit result (to satisfy dependency)
        self.valid_table_edit_result = MetricResult(
            metric_name="table_edit",
            score=1.0,
            success=True,
            details={
                "distance": 0,
                "predicted_length": 100,
                "groundtruth_length": 100
            }
        )

    def test_teds_identical_tables(self):
        """Test completely identical tables"""
        pred = "<table><tr><td>1</td></tr></table>"
        gt = "<table><tr><td>1</td></tr></table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertEqual(result.score, 1.0)

    def test_teds_different_tables(self):
        """Test completely different tables"""
        pred = "<table><tr><td>1</td></tr></table>"
        gt = "<table><tr><td>2</td></tr></table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertLess(result.score, 1.0)

    def test_teds_empty_tables(self):
        """Test empty tables"""
        pred = "<table></table>"
        gt = "<table></table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertEqual(result.score, 1.0)

    def test_teds_markdown_conversion(self):
        """Test Markdown table conversion"""
        pred = "| A | B |\n|-----|-----|\n| 1 | 2 |"
        gt = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertAlmostEqual(result.score, 1.0, places=3)

    def test_teds_list_conversion(self):
        """Test list conversion to table"""
        pred = [[1, 2], [3, 4]]
        gt = "<table><tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertAlmostEqual(result.score, 1.0, places=3)

    def test_teds_complex_table(self):
        """Test complex table (with merged cells)"""
        pred = """
        <table>
            <tr><th colspan="2">Header</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        """
        gt = """
        <table>
            <tr><th colspan="2">Header</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        """

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertEqual(result.score, 1.0)

    def test_s_teds_identical_structure(self):
        """Test tables with identical structure but different content (S-TEDS should ignore content)"""
        pred = "<table><tr><td>Content A</td></tr></table>"
        gt = "<table><tr><td>Content B</td></tr></table>"

        result = self.s_teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertEqual(result.score, 1.0)

    def test_s_teds_different_structure(self):
        """Test tables with different structure (S-TEDS should be sensitive)"""
        pred = "<table><tr><td>1</td></tr></table>"
        gt = "<table><tr><td>1</td><td>2</td></tr></table>"

        result = self.s_teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertLess(result.score, 1.0)

    def test_s_teds_colspan_sensitivity(self):
        """Test S-TEDS sensitivity to colspan"""
        pred = "<table><tr><th colspan='2'>Title</th></tr></table>"
        gt = "<table><tr><th>Title 1</th><th>Title 2</th></tr></table>"

        result = self.s_teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertLess(result.score, 1.0)

    def test_unicode_content(self):
        """Test tables containing Unicode characters"""
        pred = "<table><tr><td>Test text</td><td>Текст на русском</td></tr></table>"
        gt = "<table><tr><td>Test text</td><td>Текст на русском</td></tr></table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertEqual(result.score, 1.0)

    def test_very_large_table(self):
        """Test large table (performance test)"""
        pred_rows = []
        gt_rows = []
        for i in range(100):
            pred_rows.append(f"<tr><td>Row {i}</td><td>Value {i}</td></tr>")
            gt_rows.append(f"<tr><td>Row {i}</td><td>Value {i}</td></tr>")

        pred = f"<table>{''.join(pred_rows)}</table>"
        gt = f"<table>{''.join(gt_rows)}</table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result  # pass in dependency
        )

        self.assertTrue(result.success)
        self.assertEqual(result.score, 1.0)

    def test_teds_structure_same_content_different(self):
        """Test tables with identical structure but different content - verify fixed TEDS does not return 0"""
        pred = "<table><tr><td>I do not like you</td></tr></table>"
        gt = "<table><tr><td>I like you</td></tr></table>"

        result = self.teds_metric.calculate(
            predicted=pred,
            groundtruth=gt,
            table_edit_result=self.valid_table_edit_result
        )
        self.assertAlmostEqual(result.score, 0.96, places=6)


class TestTEDSAdvanced(unittest.TestCase):
    """Advanced TEDS functionality tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.teds = TEDSMetric("teds")
        # Create a valid table_edit result as dependency
        self.valid_table_edit_result = MetricResult(
            metric_name="table_edit",
            score=1.0,
            success=True,
            details={
                "distance": 0,
                "predicted_length": 100,
                "groundtruth_length": 100
            }
        )

    def test_teds_markdown_conversion(self):
        """Test TEDS with markdown input"""
        markdown_table = """
        | Name | Age |
        |------|-----|
        | John | 25  |
        | Jane | 30  |
        """

        html_table = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>John</td><td>25</td></tr>
            <tr><td>Jane</td><td>30</td></tr>
        </table>
        """

        result = self.teds.calculate(
            markdown_table,
            html_table,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        self.assertTrue(result.success)
        self.assertGreater(result.score, 0.7)  # Should be quite similar

    def test_teds_list_conversion(self):
        """Test TEDS with list input"""
        list_data = [
            ["Name", "Age"],
            ["John", "25"],
            ["Jane", "30"]
        ]

        html_table = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>John</td><td>25</td></tr>
            <tr><td>Jane</td><td>30</td></tr>
        </table>
        """

        result = self.teds.calculate(
            list_data,
            html_table,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.score, 0.8)

    def test_teds_complex_table(self):
        """Test TEDS with complex table containing colspan"""
        table1 = """
        <table>
            <tr><th colspan="2">Header</th></tr>
            <tr><td>A</td><td>B</td></tr>
        </table>
        """

        table2 = """
        <table>
            <tr><th>Header1</th><th>Header2</th></tr>
            <tr><td>A</td><td>B</td></tr>
        </table>
        """

        result = self.teds.calculate(
            table1,
            table2,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        self.assertTrue(result.success)
        self.assertGreater(result.score, 0.0)
        self.assertLess(result.score, 1.0)

    def test_teds_content_similarity(self):
        """Test TEDS with similar content but different text"""
        table1 = "<table><tr><td>Apples are delicious</td><td>Bananas are also good</td></tr></table>"
        table2 = "<table><tr><td>Apples are tasty</td><td>Bananas are good too</td></tr></table>"

        result = self.teds.calculate(
            table1,
            table2,
            table_edit_result=self.valid_table_edit_result
        )

        self.assertAlmostEqual(result.score, 0.931818, places=6)

class TestStructureTEDS(unittest.TestCase):
    """Structure-only TEDS tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.s_teds = StructureTEDSMetric("s_teds")
        # Create a valid table_edit result as dependency
        self.valid_table_edit_result = MetricResult(
            metric_name="table_edit",
            score=1.0,
            success=True,
            details={
                "distance": 0,
                "predicted_length": 100,
                "groundtruth_length": 100
            }
        )

    def test_s_teds_identical_structure(self):
        """Test S-TEDS with identical structure but different content"""
        table1 = "<table><tr><th>Name</th><th>Age</th></tr><tr><td>John</td><td>25</td></tr></table>"
        table2 = "<table><tr><th>Product</th><th>Price</th></tr><tr><td>Apple</td><td>5</td></tr></table>"

        result = self.s_teds.calculate(
            table1,
            table2,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )

        self.assertTrue(result.success)
        self.assertEqual(result.score, 1.0)  # Structure is identical, content ignored
        self.assertEqual(result.details.get('algorithm'), 'TEDS')

    def test_s_teds_different_structure(self):
        """Test S-TEDS with different structure"""
        table1 = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>John</td><td>25</td></tr>
        </table>
        """

        table2 = """
        <table>
            <tr><th>Name</th><th>Age</th><th>City</th></tr>
            <tr><td>John</td><td>25</td><td>NYC</td></tr>
        </table>
        """

        result = self.s_teds.calculate(
            table1,
            table2,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        self.assertTrue(result.success)
        self.assertLess(result.score, 1.0)

    def test_s_teds_colspan_sensitivity(self):
        """Test S-TEDS sensitivity to colspan"""
        table1 = """
        <table>
            <tr><th colspan="2">Header</th></tr>
            <tr><td>A</td><td>B</td></tr>
        </table>
        """

        table2 = """
        <table>
            <tr><th>Header1</th><th>Header2</th></tr>
            <tr><td>A</td><td>B</td></tr>
        </table>
        """

        result = self.s_teds.calculate(
            table1,
            table2,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        self.assertTrue(result.success)
        self.assertLess(result.score, 1.0)  # Should detect structural difference


class TestTEDSEdgeCases(unittest.TestCase):
    """TEDS edge cases and error handling tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.teds = TEDSMetric("teds")
        self.s_teds = StructureTEDSMetric("s_teds")
        # Create a valid table_edit result as dependency
        self.valid_table_edit_result = MetricResult(
            metric_name="table_edit",
            score=1.0,
            success=True,
            details={
                "distance": 0,
                "predicted_length": 100,
                "groundtruth_length": 100
            }
        )

    def test_malformed_html(self):
        """Test TEDS with malformed HTML"""
        malformed_table = "<table><tr><th>Name<td>John</table>"
        good_table = "<table><tr><th>Name</th></tr><tr><td>John</td></tr></table>"

        result = self.teds.calculate(
            malformed_table,
            good_table,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        # Should handle gracefully without crashing
        self.assertTrue(result.success or not result.success)  # Either way is acceptable

    def test_unicode_content(self):
        """Test TEDS with Unicode content"""
        table1 = "<table><tr><th>Name</th><th>Age</th></tr><tr><td>Zhang San</td><td>25</td></tr></table>"
        table2 = "<table><tr><th>Name</th><th>Age</th></tr><tr><td>Li Si</td><td>30</td></tr></table>"

        result = self.teds.calculate(
            table1,
            table2,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        self.assertTrue(result.success)
        self.assertGreater(result.score, 0.0)

    def test_very_large_table(self):
        """Test TEDS with large table"""
        # Create a moderately large table
        rows = []
        for i in range(20):
            rows.append(f"<tr><td>Cell{i}_1</td><td>Cell{i}_2</td><td>Cell{i}_3</td></tr>")

        large_table1 = f"<table><tr><th>Col1</th><th>Col2</th><th>Col3</th></tr>{''.join(rows)}</table>"
        large_table2 = f"<table><tr><th>Col1</th><th>Col2</th><th>Col3</th></tr>{''.join(rows[:15])}</table>"

        result = self.teds.calculate(
            large_table1,
            large_table2,
            table_edit_result=self.valid_table_edit_result  # add dependency parameter
        )
        self.assertTrue(result.success)
        self.assertGreater(result.score, 0.0)
        self.assertLess(result.score, 1.0)


def run_all_teds_tests():
    """Run all TEDS tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        # Note: ensure TestTEDSBasic is defined or imported from another file
        TestTEDSBasic,
        TestTEDSAdvanced,
        TestStructureTEDS,
        TestTEDSEdgeCases
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("=== TEDS Algorithm Comprehensive Tests ===\n")

    success = run_all_teds_tests()

    if success:
        print("\nAll TEDS tests passed!")
    else:
        print("\nSome TEDS tests failed!")
        sys.exit(1)