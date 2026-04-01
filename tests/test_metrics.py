#!/usr/bin/env python
"""Test new content type metrics"""

import unittest
from webmainbench.metrics import MetricCalculator


class TestContentMetrics(unittest.TestCase):
    """Test content type metrics"""

    def setUp(self):
        """Test setup"""
        self.calculator = MetricCalculator()

        # Test data
        self.predicted_content = """# Title

This is a paragraph of text.

```python
def hello():
    print("Hello World")
```

This is a formula: $E = mc^2$

And a block formula:
$$\\int_{0}^{\\infty} e^{-x} dx = 1$$

| Col1 | Col2 |
|-----|-----|
| Data1 | Data2 |
| Data3 | Data4 |

Finally more text content.
"""

        self.groundtruth_content = """# Title

This is a paragraph of correct text.

```python
def hello():
    print("Hello, World!")
```

This is the correct formula: $E = mc^2$

Correct block formula:
$$\\int_{0}^{\\infty} e^{-x} dx = 1$$

| Col1 | Col2 |
|-----|-----|
| Correct Data1 | Correct Data2 |
| Correct Data3 | Correct Data4 |

Finally correct text content.
"""

    def test_available_metrics(self):
        """Test the list of available metrics"""
        metrics = self.calculator.list_available_metrics()

        # Verify all required metrics exist
        expected_metrics = ['code_edit', 'formula_edit', 'table_edit', 'table_TEDS', 'text_edit']
        for metric in expected_metrics:
            self.assertIn(metric, metrics, f"Missing metric: {metric}")

    def test_metric_calculation_success(self):
        """Test successful metric calculation"""
        results = self.calculator.calculate_all(
            predicted_content=self.predicted_content,
            groundtruth_content=self.groundtruth_content
        )

        # Verify all metrics were calculated successfully
        expected_metrics = ['code_edit', 'formula_edit', 'table_edit', 'table_TEDS', 'text_edit', 'overall']
        for metric_name in expected_metrics:
            self.assertIn(metric_name, results, f"Missing metric result: {metric_name}")
            self.assertTrue(results[metric_name].success,
                            f"Metric {metric_name} calculation failed: {results[metric_name].error_message}")

    def test_code_edit_metric(self):
        """Test code edit distance metric"""
        results = self.calculator.calculate_all(
            predicted_content=self.predicted_content,
            groundtruth_content=self.groundtruth_content
        )

        code_result = results['code_edit']
        self.assertTrue(code_result.success)
        self.assertIsInstance(code_result.score, float)
        # Verify deterministic score for fixed content
        self.assertAlmostEqual(code_result.score, 0.9487179487179487, places=5,
                               msg=f"code_edit score should be 0.9487179487179487, actual: {code_result.score}")

        # Verify details
        self.assertEqual(code_result.details['content_type'], 'code')
        self.assertIn('distance', code_result.details)
        self.assertIn('predicted_code_length', code_result.details)
        self.assertIn('groundtruth_code_length', code_result.details)

    def test_formula_edit_metric(self):
        """Test formula edit distance metric"""
        results = self.calculator.calculate_all(
            predicted_content=self.predicted_content,
            groundtruth_content=self.groundtruth_content
        )

        formula_result = results['formula_edit']
        self.assertTrue(formula_result.success)
        self.assertIsInstance(formula_result.score, float)
        # Verify deterministic score for fixed content
        self.assertAlmostEqual(formula_result.score, 1.000000, places=5,
                               msg=f"formula_edit score should be 1.000000, actual: {formula_result.score}")

        # Verify details
        self.assertEqual(formula_result.details['content_type'], 'formula')
        self.assertIn('distance', formula_result.details)

    def test_table_edit_metric(self):
        """Test table edit distance metric"""
        results = self.calculator.calculate_all(
            predicted_content=self.predicted_content,
            groundtruth_content=self.groundtruth_content
        )

        table_result = results['table_edit']
        self.assertTrue(table_result.success)
        self.assertIsInstance(table_result.score, float)
        # Verify deterministic score for fixed content
        self.assertAlmostEqual(table_result.score, 0.9333333333333333, places=5,
                               msg=f"table_edit score should be 0.9333333333333333, actual: {table_result.score}")

        # Verify details
        self.assertEqual(table_result.details['content_type'], 'table')
        self.assertIn('distance', table_result.details)

    def test_table_teds_metric(self):
        """Test table TEDS metric"""
        results = self.calculator.calculate_all(
            predicted_content=self.predicted_content,
            groundtruth_content=self.groundtruth_content
        )

        teds_result = results['table_TEDS']
        self.assertTrue(teds_result.success)
        self.assertIsInstance(teds_result.score, float)
        # Verify deterministic score for fixed content
        self.assertAlmostEqual(teds_result.score, 0.97857, places=5,
                               msg=f"table_TEDS score should be 0.97857, actual: {teds_result.score}")

        # Verify details
        self.assertEqual(teds_result.details['content_type'], 'table')

    def test_text_edit_metric(self):
        """Test plain text edit distance metric"""
        results = self.calculator.calculate_all(
            predicted_content=self.predicted_content,
            groundtruth_content=self.groundtruth_content
        )

        text_result = results['text_edit']
        self.assertTrue(text_result.success)
        self.assertIsInstance(text_result.score, float)
        # Verify deterministic score for fixed content
        self.assertAlmostEqual(text_result.score, 0.8904109589041096, places=5,
                               msg=f"text_edit score should be 0.8904109589041096, actual: {text_result.score}")

        # Verify details
        self.assertEqual(text_result.details['content_type'], 'text')
        self.assertIn('distance', text_result.details)

    def test_overall_metric_calculation(self):
        """Test that overall metric is the average of other metrics"""
        results = self.calculator.calculate_all(
            predicted_content=self.predicted_content,
            groundtruth_content=self.groundtruth_content
        )

        # Get individual metric scores
        individual_metrics = ['code_edit', 'formula_edit', 'table_edit', 'table_TEDS', 'text_edit']
        individual_scores = []

        for metric_name in individual_metrics:
            self.assertIn(metric_name, results)
            self.assertTrue(results[metric_name].success)
            individual_scores.append(results[metric_name].score)

        # Calculate expected overall score
        expected_overall = sum(individual_scores) / len(individual_scores)

        # Verify overall score
        overall_result = results['overall']
        self.assertTrue(overall_result.success)
        self.assertAlmostEqual(overall_result.score, expected_overall, places=5,
                               msg="overall score should be the average of all other metrics")

        # Verify overall details
        self.assertEqual(overall_result.details['source'], 'average_of_all_metrics')
        self.assertEqual(overall_result.details['successful_metrics'], len(individual_metrics))

    def test_identical_content(self):
        """Test the case with identical content"""
        # Use identical content
        results = self.calculator.calculate_all(
            predicted_content=self.groundtruth_content,
            groundtruth_content=self.groundtruth_content
        )

        # Identical content should get a perfect score
        for metric_name in ['code_edit', 'formula_edit', 'table_edit', 'text_edit']:
            if metric_name in results and results[metric_name].success:
                self.assertAlmostEqual(results[metric_name].score, 1.0, places=5,
                                       msg=f"Identical content {metric_name} should get a perfect score, actual: {results[metric_name].score}")

    def test_empty_content(self):
        """Test the case with empty content"""
        results = self.calculator.calculate_all(
            predicted_content="",
            groundtruth_content=""
        )

        # Empty content should be handled correctly without errors
        for metric_name, result in results.items():
            if metric_name != 'overall':  # overall may have special handling
                self.assertTrue(result.success or result.score == 0.0,
                                f"Empty content {metric_name} should be handled correctly")


class TestErrorHandling(unittest.TestCase):
    """Test error handling"""

    def setUp(self):
        self.calculator = MetricCalculator()

    def test_malformed_content(self):
        """Test malformed input"""
        # Should be able to handle various invalid inputs without crashing
        results = self.calculator.calculate_all(
            predicted_content="test",
            groundtruth_content="test"
        )

        # Should not have uncaught exceptions
        self.assertIsInstance(results, dict)

    def test_none_inputs(self):
        """Test None inputs"""
        results = self.calculator.calculate_all(
            predicted_content=None,
            groundtruth_content=None
        )

        # Should be able to handle None inputs
        self.assertIsInstance(results, dict)


class TestRealSampleMetrics(unittest.TestCase):
    """Test metric calculation based on actual LLM-WebKit extraction results"""

    def setUp(self):
        """Test setup"""
        self.calculator = MetricCalculator()

    def test_text_code_sample_edit_distance(self):
        """Test edit distance of text+code samples"""
        # Data based on actual debug results
        groundtruth = """# Python Programming Example

This is an introduction to Python programming.

```python
def hello_world():
    print("Hello, World!")
    return True
```

The above code demonstrates a simple Python function."""

        predicted = """# Python Programming Example

This is an introduction to Python programming.

```
def hello_world():
    print("Hello, World!")
    return True
```

The above code demonstrates a simple Python function."""

        # Calculate edit distance (based on actual debug results)
        results = self.calculator.calculate_all(
            predicted_content=predicted,
            groundtruth_content=groundtruth
        )

        # Verify text edit distance (fixed content should have a deterministic score)
        self.assertIn("text_edit", results)
        self.assertTrue(results["text_edit"].success)
        self.assertAlmostEqual(results["text_edit"].score, 0.9552238805970149, places=5,
                               msg=f"text_edit score should be 0.9552238805970149, actual: {results['text_edit'].score}")

        # Verify code edit distance (slight difference due to missing python identifier)
        self.assertIn("code_edit", results)
        self.assertTrue(results["code_edit"].success)
        self.assertAlmostEqual(results["code_edit"].score, 1.0, places=5,
                               msg=f"code_edit score should be 1.0, actual: {results['code_edit'].score}")

    def test_html_table_edit_distance(self):
        """Test edit distance for table samples"""
        groundtruth = """
        
        <table>
<caption>Harrisburg, Portsmouth, Mountjoy &amp; Lancaster Rail-Road</caption><tbody><tr><td colspan="2"><div>Route map, circa 1850</div></td></tr><tr><th colspan="2">Overview</th>
</tr>
<tr>
<th scope="row">Locale</th>
<td>Harrisburg, Pennsylvania</td>
</tr>
<tr>
<th scope="row">Dates of operation</th>
<td>1835–1917</td>
</tr>
<tr>
<th scope="row">Predecessor</th>
<td>Portsmouth and Lancaster Rail-Road</td>
</tr>
<tr>
<th scope="row">Successor</th>
<td>The Pennsylvania Railroad</td>
</tr>
<tr>
<th colspan="2">Technical</th>
</tr>
<tr>
<th scope="row">Length</th>
<td>52.57 miles (84.60 km) in 1917</td>
</tr>
<tr>
<td colspan="2">
<table>
<tbody>
<tr>
<th>Route map</th>
</tr>
<tr>
<td>
<table>
<tbody>
<tr>
<td>Susquehanna River</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>0 mi</td>
<td colspan="2">Harrisburg</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>3 mi</td>
<td colspan="2">Steelton</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>9 mi</td>
<td colspan="2">Middletown</td>
</tr>
<tr>
<td>Swatara Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>10 mi</td>
<td colspan="2">Royalton</td>
</tr>
<tr>
<td>Conewago Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Falmouth</td>
<td>14 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Bainbridge</td>
<td>18 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>18 mi</td>
<td colspan="2">Elizabethtown</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2">tunnel 850 feet (260 m)</td>
</tr>
<tr>
<td colspan="2">Marrietta</td>
<td>25 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>25 mi</td>
<td colspan="2">Mountjoy</td>
</tr>
<tr>
<td>Chiques Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td>tunnel 180 feet (55 m)</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Columbia</td>
<td>28.5 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>35.5 mi</td>
<td colspan="2">Lancaster</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table>
<tbody>
<tr>
<th>Route map</th>
</tr>
<tr>
<td>
<table>
<tbody>
<tr>
<td>Susquehanna River</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>0 mi</td>
<td colspan="2">Harrisburg</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>3 mi</td>
<td colspan="2">Steelton</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>9 mi</td>
<td colspan="2">Middletown</td>
</tr>
<tr>
<td>Swatara Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>10 mi</td>
<td colspan="2">Royalton</td>
</tr>
<tr>
<td>Conewago Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Falmouth</td>
<td>14 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Bainbridge</td>
<td>18 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>18 mi</td>
<td colspan="2">Elizabethtown</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2">tunnel 850 feet (260 m)</td>
</tr>
<tr>
<td colspan="2">Marrietta</td>
<td>25 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>25 mi</td>
<td colspan="2">Mountjoy</td>
</tr>
<tr>
<td>Chiques Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td>tunnel 180 feet (55 m)</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Columbia</td>
<td>28.5 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>35.5 mi</td>
<td colspan="2">Lancaster</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table>
<tbody>
<tr>
<td>Susquehanna River</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>0 mi</td>
<td colspan="2">Harrisburg</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>3 mi</td>
<td colspan="2">Steelton</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>9 mi</td>
<td colspan="2">Middletown</td>
</tr>
<tr>
<td>Swatara Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>10 mi</td>
<td colspan="2">Royalton</td>
</tr>
<tr>
<td>Conewago Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Falmouth</td>
<td>14 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Bainbridge</td>
<td>18 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>18 mi</td>
<td colspan="2">Elizabethtown</td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2">tunnel 850 feet (260 m)</td>
</tr>
<tr>
<td colspan="2">Marrietta</td>
<td>25 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>25 mi</td>
<td colspan="2">Mountjoy</td>
</tr>
<tr>
<td>Chiques Creek</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td>tunnel 180 feet (55 m)</td>
<td></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2">Columbia</td>
<td>28.5 mi</td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td></td>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2"></td>
<td></td>
<td>
<div></div>
<div></div>
<div></div>
</td>
<td>35.5 mi</td>
<td colspan="2">Lancaster</td>
</tr>
</tbody>
</table>
        
        """

        predicted = """

<table><caption>Harrisburg, Portsmouth, Mountjoy &amp; Lancaster Rail-Road</caption><tbody><tr><td colspan="2"><a></a><div></div><div>Wikimedia | © OpenStreetMap</div><div>Route map, circa 1850</div></td></tr><tr><th colspan="2">Overview</th></tr><tr><th>Locale</th><td>Harrisburg, Pennsylvania</td></tr><tr><th>Dates of operation</th><td><marked-text>1835</marked-text><span>( 1835 )</span><marked-tail>–1917</marked-tail><span>( 1917 )</span></td></tr><tr><th>Predecessor</th><td>Portsmouth and Lancaster Rail-Road</td></tr><tr><th>Successor</th><td><marked-text>The</marked-text><a>Pennsylvania Railroad</a></td></tr><tr><th colspan="2">Technical</th></tr><tr><th>Length</th><td>52.57 miles (84.60 km) in 1917</td></tr><tr><td colspan="2"><table><tbody><tr><th><div>Route map</div></th></tr><tr><td><p></p><table><tbody><tr><td><div>Legend</div></td></tr><tr><td><table><tbody><tr><td><div>Susquehanna River</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td><div>0 mi</div></td><td colspan="2">Harrisburg</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>3 mi</div></td><td colspan="2">Steelton</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>9 mi</div></td><td colspan="2">Middletown</td></tr><tr><td><div>Swatara Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>10 mi</div></td><td colspan="2">Royalton</td></tr><tr><td><div>Conewago Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Falmouth</td><td><div>14 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Bainbridge</td><td><div>18 mi</div></td><td><div></div><div></div><div></div></td><td><div>18 mi</div></td><td colspan="2">Elizabethtown</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"><div>tunnel 850 feet (260 m)</div></td></tr><tr><td colspan="2">Marrietta</td><td><div>25 mi</div></td><td><div></div><div></div><div></div></td><td><div>25 mi</div></td><td colspan="2">Mountjoy</td></tr><tr><td><div>Chiques Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td><div>tunnel 180 feet (55 m)</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Columbia</td><td><div>28.5 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>35.5 mi</div></td><td colspan="2">Lancaster</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table>
<table><tbody><tr><th><div>Route map</div></th></tr><tr><td><p></p><table><tbody><tr><td><div>Legend</div></td></tr><tr><td><table><tbody><tr><td><div>Susquehanna River</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td><div>0 mi</div></td><td colspan="2">Harrisburg</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>3 mi</div></td><td colspan="2">Steelton</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>9 mi</div></td><td colspan="2">Middletown</td></tr><tr><td><div>Swatara Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>10 mi</div></td><td colspan="2">Royalton</td></tr><tr><td><div>Conewago Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Falmouth</td><td><div>14 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Bainbridge</td><td><div>18 mi</div></td><td><div></div><div></div><div></div></td><td><div>18 mi</div></td><td colspan="2">Elizabethtown</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"><div>tunnel 850 feet (260 m)</div></td></tr><tr><td colspan="2">Marrietta</td><td><div>25 mi</div></td><td><div></div><div></div><div></div></td><td><div>25 mi</div></td><td colspan="2">Mountjoy</td></tr><tr><td><div>Chiques Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td><div>tunnel 180 feet (55 m)</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Columbia</td><td><div>28.5 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>35.5 mi</div></td><td colspan="2">Lancaster</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table>
<table><tbody><tr><td><div>Legend</div></td></tr><tr><td><table><tbody><tr><td><div>Susquehanna River</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td><div>0 mi</div></td><td colspan="2">Harrisburg</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>3 mi</div></td><td colspan="2">Steelton</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>9 mi</div></td><td colspan="2">Middletown</td></tr><tr><td><div>Swatara Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>10 mi</div></td><td colspan="2">Royalton</td></tr><tr><td><div>Conewago Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Falmouth</td><td><div>14 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Bainbridge</td><td><div>18 mi</div></td><td><div></div><div></div><div></div></td><td><div>18 mi</div></td><td colspan="2">Elizabethtown</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"><div>tunnel 850 feet (260 m)</div></td></tr><tr><td colspan="2">Marrietta</td><td><div>25 mi</div></td><td><div></div><div></div><div></div></td><td><div>25 mi</div></td><td colspan="2">Mountjoy</td></tr><tr><td><div>Chiques Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td><div>tunnel 180 feet (55 m)</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Columbia</td><td><div>28.5 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>35.5 mi</div></td><td colspan="2">Lancaster</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tbody></table></td></tr></tbody></table>
<table><tbody><tr><td><div>Susquehanna River</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td><div>0 mi</div></td><td colspan="2">Harrisburg</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>3 mi</div></td><td colspan="2">Steelton</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>9 mi</div></td><td colspan="2">Middletown</td></tr><tr><td><div>Swatara Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>10 mi</div></td><td colspan="2">Royalton</td></tr><tr><td><div>Conewago Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Falmouth</td><td><div>14 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Bainbridge</td><td><div>18 mi</div></td><td><div></div><div></div><div></div></td><td><div>18 mi</div></td><td colspan="2">Elizabethtown</td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"><div>tunnel 850 feet (260 m)</div></td></tr><tr><td colspan="2">Marrietta</td><td><div>25 mi</div></td><td><div></div><div></div><div></div></td><td><div>25 mi</div></td><td colspan="2">Mountjoy</td></tr><tr><td><div>Chiques Creek</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td><div>tunnel 180 feet (55 m)</div></td><td></td><td></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2">Columbia</td><td><div>28.5 mi</div></td><td><div></div><div></div><div></div></td><td></td><td colspan="2"></td></tr><tr><td colspan="2"></td><td></td><td><div></div><div></div><div></div></td><td><div>35.5 mi</div></td><td colspan="2">Lancaster</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tbody></table>
"""

        results = self.calculator.calculate_all(
            predicted_content=predicted,
            groundtruth_content=groundtruth
        )

        # Verify table edit distance (fixed score due to separator length difference)
        self.assertIn("table_edit", results)
        self.assertTrue(results["table_edit"].success)
        self.assertAlmostEqual(results["table_edit"].score, 0.5935733724094621, places=5,
                               msg=f"table_edit score should be 0.5935733724094621, actual: {results['table_edit'].score}")

        # Verify TEDS metric (identical table structure, perfect score)
        self.assertIn("table_TEDS", results)
        self.assertTrue(results["table_TEDS"].success)
        self.assertAlmostEqual(results["table_TEDS"].score, 0.9984520490180891, places=5,
                               msg=f"table_TEDS score should be 0.0.9984520490180891, actual: {results['table_TEDS'].score}")

    def test_table_sample_edit_distance(self):
        """Test edit distance for tables with consistent rendering but inconsistent style"""
        groundtruth = """
| Product | Sales | Revenue |
|------|------|------|
| Product A | 100 | 1000 |
| Product B | 200 | 3000 |
"""

        predicted = """
<table><tr><th>Product</th><th>Sales</th><th>Revenue</th></tr><tr><td>Product A</td><td>100</td><td>1000</td></tr><tr><td>Product B</td><td>200</td><td>3000</td></tr></table>"""

        results = self.calculator.calculate_all(
            predicted_content=predicted,
            groundtruth_content=groundtruth
        )

        # Verify table edit distance (fixed score due to separator length difference)
        self.assertIn("table_edit", results)
        self.assertTrue(results["table_edit"].success)
        self.assertAlmostEqual(results["table_edit"].score, 1.0, places=5,
                               msg=f"table_edit score should be 1.0, actual: {results['table_edit'].score}")

        # Verify TEDS metric (identical table structure, perfect score)
        self.assertIn("table_TEDS", results)
        self.assertTrue(results["table_TEDS"].success)
        self.assertAlmostEqual(results["table_TEDS"].score, 1.0, places=5,
                               msg=f"table_TEDS score should be 1.0, actual: {results['table_TEDS'].score}")

    def test_formula_sample_edit_distance(self):
        """Test edit distance for formula samples"""
        groundtruth = """## Math Formula Examples

This is an inline formula: $E = mc^2$

This is a block formula:

$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$"""

        predicted = """## Math Formula Examples

This is an inline formula: \\$E = mc^2\\$

This is a block formula:

\\$\\$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}\\$"""

        results = self.calculator.calculate_all(
            predicted_content=predicted,
            groundtruth_content=groundtruth
        )

        # Verify formula edit distance (fixed low score due to symbol escaping)
        self.assertIn("formula_edit", results)
        self.assertTrue(results["formula_edit"].success)
        self.assertAlmostEqual(results["formula_edit"].score, 0.0, places=5,
                               msg=f"formula_edit score should be 0.0, actual: {results['formula_edit'].score}")

        # Verify text edit distance (plain text after removing formulas, also affected by symbol escaping)
        self.assertIn("text_edit", results)
        self.assertTrue(results["text_edit"].success)
        self.assertAlmostEqual(results["text_edit"].score, 0.95, places=5,
                               msg=f"text_edit score should be 0.95, actual: {results['text_edit'].score}")

    def test_overall_score_calculation(self):
        """Test overall score calculation"""
        # Use the first sample to test overall score
        groundtruth = """# Python Programming Example

This is an introduction to Python programming.

```python
def hello_world():
    print("Hello, World!")
    return True
```

The above code demonstrates a simple Python function."""

        predicted = """# Python Programming Example

This is an introduction to Python programming.

```
def hello_world():
    print("Hello, World!")
    return True
```

The above code demonstrates a simple Python function."""

        results = self.calculator.calculate_all(
            predicted_content=predicted,
            groundtruth_content=groundtruth
        )

        # Verify overall score exists and is reasonable
        self.assertIn("overall", results)
        self.assertTrue(results["overall"].success)

        # overall should be the average of all successful metrics
        successful_scores = []
        for metric_name, result in results.items():
            if metric_name != "overall" and result.success:
                successful_scores.append(result.score)

        if successful_scores:
            expected_overall = sum(successful_scores) / len(successful_scores)
            actual_overall = results["overall"].score

            # Allow small calculation errors
            self.assertAlmostEqual(actual_overall, expected_overall, places=3)

    def test_all_metrics_coverage(self):
        """Test that all 6 metrics are calculated"""
        groundtruth = """# Comprehensive Example

This is text content.

```python
def test():
    return True
```

This is a formula: $x = y$

| A | B |
|---|---|
| 1 | 2 |

More text."""

        predicted = groundtruth  # Use identical content for testing

        results = self.calculator.calculate_all(
            predicted_content=predicted,
            groundtruth_content=groundtruth
        )

        # Verify all 6 metrics exist
        expected_metrics = ["overall", "text_edit", "code_edit", "table_edit", "table_TEDS", "formula_edit"]

        print(f"\n=== Metric test results for identical content ===")

        for metric in expected_metrics:
            self.assertIn(metric, results, f"Metric {metric} is missing")
            self.assertTrue(results[metric].success, f"Metric {metric} calculation failed")

            score = results[metric].score
            print(f"{metric}: {score:.6f}")

            # Completely identical content should get a perfect score of 1.0
            self.assertAlmostEqual(score, 1.0,
                                   places=4,
                                   msg=f"Identical content {metric} should get a perfect score, actual score: {score}")

        print("All metrics correctly received a perfect score!")


def run_visual_test():
    """Run visual test (preserves original print functionality)"""
    print("=== New Metric Feature Test ===\n")

    calculator = MetricCalculator()

    # Display available metrics
    print("Available metrics:")
    metrics = calculator.list_available_metrics()
    for metric in metrics:
        print(f"  - {metric}")
    print()

    # Test data
    predicted_content = """# Title

This is a paragraph of text.

```python
def hello():
    print("Hello World")
```

This is a formula: $E = mc^2$

And a block formula:
$$\\int_{0}^{\\infty} e^{-x} dx = 1$$

| Col1 | Col2 |
|-----|-----|
| Data1 | Data2 |
| Data3 | Data4 |

Finally more text content.
"""

    groundtruth_content = """# Title

This is a paragraph of correct text.

```python
def hello():
    print("Hello, World!")
```

This is the correct formula: $E = mc^2$

Correct block formula:
$$\\int_{0}^{\\infty} e^{-x} dx = 1$$

| Col1 | Col2 |
|-----|-----|
| Correct Data1 | Correct Data2 |
| Correct Data3 | Correct Data4 |

Finally correct text content.
"""

    # Calculate all metrics
    print("Calculating metrics...")
    results = calculator.calculate_all(
        predicted_content=predicted_content,
        groundtruth_content=groundtruth_content
    )

    # Display results
    print("\n=== Evaluation Results ===")
    print("-" * 60)

    for metric_name, result in results.items():
        if result.success:
            print(f"{metric_name:15}: {result.score:.4f}")
            if "content_type" in result.details:
                content_type = result.details["content_type"]
                print(f"{'':15}  Type: {content_type}")
            print()
        else:
            print(f"{metric_name:15}: ERROR - {result.error_message}")
            print()

    # Display details
    print("\n=== Details ===")
    for metric_name in ["code_edit", "formula_edit", "table_edit", "text_edit"]:
        if metric_name in results and results[metric_name].success:
            details = results[metric_name].details
            print(f"\n{metric_name}:")
            print(f"  Predicted length: {details.get('predicted_' + details.get('content_type', '') + '_length', 'N/A')}")
            print(f"  Groundtruth length: {details.get('groundtruth_' + details.get('content_type', '') + '_length', 'N/A')}")
            print(f"  Edit distance: {details.get('distance', 'N/A')}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--visual":
        # Run visual test
        try:
            run_visual_test()
            print("\nNew metric test complete!")
        except Exception as e:
            print(f"\nTest failed: {e}")
            import traceback

            traceback.print_exc()
    else:
        # Run unit tests
        unittest.main(verbosity=2)