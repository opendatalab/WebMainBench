#!/usr/bin/env python
"""Test Markdown table extraction functionality"""

import unittest
import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from webmainbench.metrics.base import BaseMetric, MetricResult


class TestTableExtractionMetric(BaseMetric):
    """Concrete implementation class for testing"""
    
    def _setup(self) -> None:
        pass
    
    def _calculate_score(self, predicted: str, groundtruth: str, **kwargs) -> MetricResult:
        return MetricResult(
            metric_name=self.name,
            score=1.0,
            details={"test": True}
        )


class TestTableExtraction(unittest.TestCase):
    """Test Markdown table extraction functionality"""

    def setUp(self):
        self.metric = TestTableExtractionMetric("test_metric")

    def test_basic_table_extraction(self):
        """Test basic table extraction"""
        text = """Text content

| Col1 | Col2 |
|-----|-----|
| Data1 | Data2 |

More text"""

        result = self.metric._extract_from_markdown(text)

        # Verify table was extracted
        self.assertIn('| Col1 | Col2 |', result['table'])
        self.assertIn('|-----|-----|', result['table'])
        self.assertIn('| Data1 | Data2 |', result['table'])

        # Verify table was removed from text
        # self.assertNotIn('| Col1 | Col2 |', result['text'])

    def test_no_name_error(self):
        """Test that the fixed code does not raise 'name table_lines is not defined' error"""
        text = """| A | B |
|-----|-----|
| 1 | 2 |"""

        try:
            result = self.metric._extract_from_markdown(text)
            self.assertIsInstance(result, dict)
            self.assertIn('table', result)
            print(f"✅ Table extracted successfully: {repr(result['table'])}")
        except NameError as e:
            if 'table_lines' in str(e):
                self.fail(f"NameError for table_lines still exists: {e}")
            else:
                raise

    def test_html_table_extraction(self):
        """Test HTML table extraction"""
        text = """This is an HTML table:
<table>
<tr><th>Header1</th><th>Header2</th></tr>
<tr><td>Data1</td><td>Data2</td></tr>
</table>
This is plain text."""

        result = self.metric._extract_from_markdown(text)
        
        # Verify HTML table is extracted
        expected_table = """<table>
<tr><th>Header1</th><th>Header2</th></tr>
<tr><td>Data1</td><td>Data2</td></tr>
</table>"""
        self.assertIn(expected_table, result['table'])
        
        # Verify HTML table was removed from text
        # self.assertNotIn('<table>', result['text'])

    def test_complex_markdown_table(self):
        """Test complex Markdown table"""
        text = """Complex table:

| Name | Age | Role | Salary |
|:-----|:----:|-----:|------|
| Alice | 25   | Engineer | 15k |
| Bob   | 30   | Designer | 18k |
| Carol | 28   | PM       | 20k |

End of table"""

        result = self.metric._extract_from_markdown(text)
        
        # Verify complex table is completely extracted
        expected_table = """| Name | Age | Role | Salary |
|:-----|:----:|-----:|------|
| Alice | 25   | Engineer | 15k |
| Bob   | 30   | Designer | 18k |
| Carol | 28   | PM       | 20k |"""
        self.assertIn(expected_table, result['table'])
        
        # Verify table was removed from text
        # self.assertNotIn('| Name | Age | Role | Salary |', result['text'])


    def test_table_with_alignment(self):
        """Test table with alignment"""
        text = """Alignment table:
| Left | Center | Right |
|:-------|:----:|-------:|
| Item1  | Item2 | Item3  |"""

        result = self.metric._extract_from_markdown(text)
        
        # Verify alignment table is extracted
        expected_table = """| Left | Center | Right |
|:-------|:----:|-------:|
| Item1  | Item2 | Item3  |"""
        self.assertIn(expected_table, result['table'])

    def test_invalid_table_ignored(self):
        """Test that invalid tables are ignored"""
        text = """Not a table: | Col1 | Col2 |
Not this either: |-----|
Not this either: | Data |"""

        result = self.metric._extract_from_markdown(text)
        
        # Verify invalid tables are not extracted
        self.assertEqual(result['table'], '')
        
        # Verify original text is unchanged
        self.assertIn('| Col1 | Col2 |', result['text'])

    def test_table_with_escaped_pipes(self):
        """Test table containing escaped pipes"""
        text = """Escaped pipe table:
| Col1 | Col2 \| Col3 | Col4 |
|-----|-----|-----|
| Data1 | Data2 | Data3 |"""

        result = self.metric._extract_from_markdown(text)
        
        # Verify table with escaped pipes is extracted
        expected_table = """| Col1 | Col2 \\| Col3 | Col4 |
|-----|-----|-----|
| Data1 | Data2 | Data3 |"""
        self.assertIn(expected_table, result['table'])

    def test_table_at_document_end(self):
        """Test table at document end"""
        text = """Start content
| Col1 | Col2 |
|-----|-----|
| Data1 | Data2 |"""

        result = self.metric._extract_from_markdown(text)
        
        # Verify table at document end is extracted
        expected_table = """| Col1 | Col2 |
|-----|-----|
| Data1 | Data2 |"""
        self.assertIn(expected_table, result['table'])



    def test_empty_and_whitespace_handling(self):
        """Test empty content and whitespace handling"""
        # Test empty string
        result = self.metric._extract_from_markdown("")
        self.assertEqual(result['table'], '')
        self.assertEqual(result['text'], '')
        
        # Test whitespace only
        result = self.metric._extract_from_markdown("   \n\n  ")
        self.assertEqual(result['table'], '')
        self.assertEqual(result['text'], '   \n\n  ')

    def test_table_with_complex_content(self):
        """Test table containing complex content"""
        text = """Complex content table:
| Col1 | Col2 | Col3 |
|-----|-----|-----|
| contains **bold** | contains `code` | contains [link](url) |
| contains *italic* | contains $formula$ | contains >quote |"""

        result = self.metric._extract_from_markdown(text)
        
        # Verify table with complex content is extracted
        expected_table = """| Col1 | Col2 | Col3 |
|-----|-----|-----|
| contains **bold** | contains `code` | contains [link](url) |
| contains *italic* | contains $formula$ | contains >quote |"""
        self.assertIn(expected_table, result['table'])

    def test_abnormal_html_table(self):
        """Test complex HTML table, avoid duplicate extraction"""
        text = """<table><tbody><tr><td><table><tbody><tr><td><table><tbody><tr><td><strong>Better Management of /$800 Bln Forex Reserves Urged</strong></td></tr></tbody></table></td></tr><tr><td><p>A number of political advisors on Sunday called for more rationally managing China's massive foreign exchange reserves, which doubled over the 2004-05 period to an equivalent of US/$818.9 billion, second only to Japan.</p><p>The quick buildup is largely a result of China's booming exports and foreign exchange controls by the government, as well as speculation on the yuan's rise, industry watchers agree.</p><p>A big part of China's foreign exchange reserves are US dollar-denominated assets, including bonds issued by the US government. "Risks in the international foreign exchange market should be lowered when China manages its reserves," said Professor Guo Guoqing of a business school of the People's University of China.</p><p>Guo, a member of the National Committee of the Chinese People's Political Consultative Conference (CPPCC), the country's top advisory body, urged the government to cut back on subsidies for exports and take other measures to reduce foreign trade surpluses appropriately and achieve the balance in international payments.</p><p>Part of the reserves should be channeled into the imports of more high-tech machinery, equipment and other products, he suggested on the sidelines of the CPPCC's annual session.</p><p>The United States has been contending that the value of yuan, also known as renminbi or RMB, is too low, giving Chinese exporters an "unfair" advantage. But China said its huge trade surpluses are also a result of the US reluctance to export goods involving state-of-the-art technologies.</p><p>Fu Rui, also a CPPCC member, said with ample foreign exchange reserves, China could intentionally bulk up the reserves of strategic resources.</p><p>The international consensus is a country's rational foreign exchange reserves should equal to its imports demand for a full quarter. Also taking into consideration of payments for foreign debts, returns for foreign investors and other demands in China, many believe it is enough for the country to retain US/$300 billion.</p><p>But Lin Yifu, a popular economist, underscored China's per capita foreign exchange reserves remains not large - less than one-tenth of Japan's and far below that of Hong Kong and Singapore.</p><p>The reserves were "tremendous fruits" from China's reform and opening-up drive, he said.</p><p>His remarks were echoed by Xiao Zhuoji, a well-known economics professor with Beijing University. "The rise of foreign exchange reserves reflects China's fast, sustained economic growth and sound international payments," he said.</p><p>"The reserves are of significant importance to upgrade the China image in the international economic arena, strengthen the nation's macro-control capabilities and guard against financial risks," added Xiao, a Standing Committee member of the CPPCC National Committee.</p><p>But as the People's Bank of China, or the central bank, has to buy foreign exchange reserves under the current foreign exchange control policies, the country's monetary base will be enlarged, increasing its inflationary pressure and difficulties on macro-economic controls, analysts acknowledge.</p><p>Another prevailing view is that China's hefty foreign exchange reserves actually "occupied" large amounts of fund resources that otherwise can be diverted for domestic investment and consumption.</p><p>Some CPPCC members said they believe it is already "meaningless" now to talk about whether China's foreign exchange reserves size is big or not. "The key lies on how to raise the reserves' yields."</p><p>"If the annual yields from foreign exchange reserves could reach a stable 5 percent, the nation will reap in 300 billion yuan a year. What a big fortune!" one advisor told Xinhua.</p><p>Central banker Zhou Xiaochuan reiterated earlier that China will "pay attention to and maintain the flexibility" of foreign reserves structure, which is unknown to the public.</p></td></tr></tbody></table></td></tr></tbody></table>"""

        result = self.metric._extract_from_markdown(text)

        # Verify complex table is completely extracted
        expected_table = """<table><tbody><tr><td><table><tbody><tr><td><table><tbody><tr><td><strong>Better Management of /$800 Bln Forex Reserves Urged</strong></td></tr></tbody></table></td></tr><tr><td><p>A number of political advisors on Sunday called for more rationally managing China's massive foreign exchange reserves, which doubled over the 2004-05 period to an equivalent of US/$818.9 billion, second only to Japan.</p><p>The quick buildup is largely a result of China's booming exports and foreign exchange controls by the government, as well as speculation on the yuan's rise, industry watchers agree.</p><p>A big part of China's foreign exchange reserves are US dollar-denominated assets, including bonds issued by the US government. "Risks in the international foreign exchange market should be lowered when China manages its reserves," said Professor Guo Guoqing of a business school of the People's University of China.</p><p>Guo, a member of the National Committee of the Chinese People's Political Consultative Conference (CPPCC), the country's top advisory body, urged the government to cut back on subsidies for exports and take other measures to reduce foreign trade surpluses appropriately and achieve the balance in international payments.</p><p>Part of the reserves should be channeled into the imports of more high-tech machinery, equipment and other products, he suggested on the sidelines of the CPPCC's annual session.</p><p>The United States has been contending that the value of yuan, also known as renminbi or RMB, is too low, giving Chinese exporters an "unfair" advantage. But China said its huge trade surpluses are also a result of the US reluctance to export goods involving state-of-the-art technologies.</p><p>Fu Rui, also a CPPCC member, said with ample foreign exchange reserves, China could intentionally bulk up the reserves of strategic resources.</p><p>The international consensus is a country's rational foreign exchange reserves should equal to its imports demand for a full quarter. Also taking into consideration of payments for foreign debts, returns for foreign investors and other demands in China, many believe it is enough for the country to retain US/$300 billion.</p><p>But Lin Yifu, a popular economist, underscored China's per capita foreign exchange reserves remains not large - less than one-tenth of Japan's and far below that of Hong Kong and Singapore.</p><p>The reserves were "tremendous fruits" from China's reform and opening-up drive, he said.</p><p>His remarks were echoed by Xiao Zhuoji, a well-known economics professor with Beijing University. "The rise of foreign exchange reserves reflects China's fast, sustained economic growth and sound international payments," he said.</p><p>"The reserves are of significant importance to upgrade the China image in the international economic arena, strengthen the nation's macro-control capabilities and guard against financial risks," added Xiao, a Standing Committee member of the CPPCC National Committee.</p><p>But as the People's Bank of China, or the central bank, has to buy foreign exchange reserves under the current foreign exchange control policies, the country's monetary base will be enlarged, increasing its inflationary pressure and difficulties on macro-economic controls, analysts acknowledge.</p><p>Another prevailing view is that China's hefty foreign exchange reserves actually "occupied" large amounts of fund resources that otherwise can be diverted for domestic investment and consumption.</p><p>Some CPPCC members said they believe it is already "meaningless" now to talk about whether China's foreign exchange reserves size is big or not. "The key lies on how to raise the reserves' yields."</p><p>"If the annual yields from foreign exchange reserves could reach a stable 5 percent, the nation will reap in 300 billion yuan a year. What a big fortune!" one advisor told Xinhua.</p><p>Central banker Zhou Xiaochuan reiterated earlier that China will "pay attention to and maintain the flexibility" of foreign reserves structure, which is unknown to the public.</p></td></tr></tbody></table></td></tr></tbody></table>"""
        self.assertIn(expected_table, result['table'])

    def test_html_table_in_code(self):
        """Test that HTML tables in code blocks are not extracted"""
        text = """This is an HTML table in a code block:

        ```
       
       <table> <tr><th>Header1</th><th>Header2</th></tr> <tr><td>Data1</td><td>Data2</td></tr> </table> 
       
       
       ```
        This is an HTML table in normal text (should be extracted):
        
        <table> <tr><th>Name</th><th>Age</th></tr> <tr><td>Alice</td><td>25</td></tr> </table>
        This is a table in inline code: `<table><tr><td>`should not be extracted</td></tr></table>
        
        Normal text ends here."""

        result = self.metric._extract_from_markdown(text)

        # Verify HTML tables in code blocks are not extracted
        self.assertNotIn('<tr><th>Header1</th><th>Header2</th></tr>', result['table'])
        self.assertNotIn('<tr><td>Data1</td><td>Data2</td></tr>', result['table'])

        # Verify table in inline code is not extracted
        self.assertNotIn('<table><tr><td>', result['table'])

        # Verify HTML table in normal text is correctly extracted
        self.assertIn('<tr><th>Name</th><th>Age</th></tr>', result['table'])
        self.assertIn('<tr><td>Alice</td><td>25</td></tr>', result['table'])

        # Verify only one table was extracted
        table_count = result['table'].count('<table>')
        self.assertEqual(table_count, 1)



if __name__ == '__main__':
    unittest.main()
