#!/usr/bin/env python
"""测试Markdown表格提取功能"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from webmainbench.metrics.base import BaseMetric, MetricResult


class TestTableExtractionMetric(BaseMetric):
    """测试用的具体实现类"""
    
    def _setup(self) -> None:
        pass
    
    def _calculate_score(self, predicted: str, groundtruth: str, **kwargs) -> MetricResult:
        return MetricResult(
            metric_name=self.name,
            score=1.0,
            details={"test": True}
        )


class TestTableExtraction(unittest.TestCase):
    """测试Markdown表格提取功能"""

    def setUp(self):
        self.metric = TestTableExtractionMetric("test_metric")

    def test_basic_table_extraction(self):
        """测试基本表格提取"""
        text = """文字内容

| 列1 | 列2 |
|-----|-----|
| 数据1 | 数据2 |

更多文字"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证表格被提取
        self.assertIn('| 列1 | 列2 |', result['table'])
        self.assertIn('|-----|-----|', result['table'])
        self.assertIn('| 数据1 | 数据2 |', result['table'])
        
        # 验证文本中表格被移除
        # self.assertNotIn('| 列1 | 列2 |', result['text'])

    def test_no_name_error(self):
        """测试修复后的代码不会出现 'name table_lines is not defined' 错误"""
        text = """| A | B |
|-----|-----|
| 1 | 2 |"""

        try:
            result = self.metric._extract_from_markdown(text)
            self.assertIsInstance(result, dict)
            self.assertIn('table', result)
            print(f"✅ 表格提取成功: {repr(result['table'])}")
        except NameError as e:
            if 'table_lines' in str(e):
                self.fail(f"仍然存在table_lines未定义的错误: {e}")
            else:
                raise

    def test_html_table_extraction(self):
        """测试HTML表格提取"""
        text = """这是HTML表格：
<table>
<tr><th>标题1</th><th>标题2</th></tr>
<tr><td>数据1</td><td>数据2</td></tr>
</table>
这是普通文本。"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证HTML表格被提取
        expected_table = """<table>
<tr><th>标题1</th><th>标题2</th></tr>
<tr><td>数据1</td><td>数据2</td></tr>
</table>"""
        self.assertIn(expected_table, result['table'])
        
        # 验证文本中HTML表格被移除
        # self.assertNotIn('<table>', result['text'])

    def test_complex_markdown_table(self):
        """测试复杂Markdown表格"""
        text = """复杂表格：

| 姓名 | 年龄 | 职业 | 薪资 |
|:-----|:----:|-----:|------|
| 张三 | 25   | 工程师 | 15k |
| 李四 | 30   | 设计师 | 18k |
| 王五 | 28   | 产品经理 | 20k |

表格结束"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证复杂表格被完整提取
        expected_table = """| 姓名 | 年龄 | 职业 | 薪资 |
|:-----|:----:|-----:|------|
| 张三 | 25   | 工程师 | 15k |
| 李四 | 30   | 设计师 | 18k |
| 王五 | 28   | 产品经理 | 20k |"""
        self.assertIn(expected_table, result['table'])
        
        # 验证文本中表格被移除
        # self.assertNotIn('| 姓名 | 年龄 | 职业 | 薪资 |', result['text'])


    def test_table_with_alignment(self):
        """测试带对齐的表格"""
        text = """对齐表格：
| 左对齐 | 居中 | 右对齐 |
|:-------|:----:|-------:|
| 内容1  | 内容2 | 内容3  |"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证对齐表格被提取
        expected_table = """| 左对齐 | 居中 | 右对齐 |
|:-------|:----:|-------:|
| 内容1  | 内容2 | 内容3  |"""
        self.assertIn(expected_table, result['table'])

    def test_invalid_table_ignored(self):
        """测试无效表格被忽略"""
        text = """这不是表格：| 列1 | 列2 |
这也不是：|-----|
这也不是：| 数据 |"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证无效表格不被提取
        self.assertEqual(result['table'], '')
        
        # 验证原始文本保持不变
        self.assertIn('| 列1 | 列2 |', result['text'])

    def test_table_with_escaped_pipes(self):
        """测试包含转义管道的表格"""
        text = """转义管道表格：
| 列1 | 列2 \| 列3 | 列4 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证包含转义管道的表格被提取
        expected_table = """| 列1 | 列2 \\| 列3 | 列4 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |"""
        self.assertIn(expected_table, result['table'])

    def test_table_at_document_end(self):
        """测试文档末尾的表格"""
        text = """开始内容
| 列1 | 列2 |
|-----|-----|
| 数据1 | 数据2 |"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证文档末尾的表格被提取
        expected_table = """| 列1 | 列2 |
|-----|-----|
| 数据1 | 数据2 |"""
        self.assertIn(expected_table, result['table'])



    def test_empty_and_whitespace_handling(self):
        """测试空内容和空白处理"""
        # 测试空字符串
        result = self.metric._extract_from_markdown("")
        self.assertEqual(result['table'], '')
        self.assertEqual(result['text'], '')
        
        # 测试只有空白字符
        result = self.metric._extract_from_markdown("   \n\n  ")
        self.assertEqual(result['table'], '')
        self.assertEqual(result['text'], '   \n\n  ')

    def test_table_with_complex_content(self):
        """测试包含复杂内容的表格"""
        text = """复杂内容表格：
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 包含**粗体** | 包含`代码` | 包含[链接](url) |
| 包含*斜体* | 包含$公式$ | 包含>引用 |"""

        result = self.metric._extract_from_markdown(text)
        
        # 验证复杂内容表格被提取
        expected_table = """| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 包含**粗体** | 包含`代码` | 包含[链接](url) |
| 包含*斜体* | 包含$公式$ | 包含>引用 |"""
        self.assertIn(expected_table, result['table'])

    def test_abnormal_html_table(self):
        """测试复杂html表格,不要重复抽取"""
        text = """<table><tbody><tr><td><table><tbody><tr><td><table><tbody><tr><td><strong>Better Management of /$800 Bln Forex Reserves Urged</strong></td></tr></tbody></table></td></tr><tr><td><p>A number of political advisors on Sunday called for more rationally managing China's massive foreign exchange reserves, which doubled over the 2004-05 period to an equivalent of US/$818.9 billion, second only to Japan.</p><p>The quick buildup is largely a result of China's booming exports and foreign exchange controls by the government, as well as speculation on the yuan's rise, industry watchers agree.</p><p>A big part of China's foreign exchange reserves are US dollar-denominated assets, including bonds issued by the US government. "Risks in the international foreign exchange market should be lowered when China manages its reserves," said Professor Guo Guoqing of a business school of the People's University of China.</p><p>Guo, a member of the National Committee of the Chinese People's Political Consultative Conference (CPPCC), the country's top advisory body, urged the government to cut back on subsidies for exports and take other measures to reduce foreign trade surpluses appropriately and achieve the balance in international payments.</p><p>Part of the reserves should be channeled into the imports of more high-tech machinery, equipment and other products, he suggested on the sidelines of the CPPCC's annual session.</p><p>The United States has been contending that the value of yuan, also known as renminbi or RMB, is too low, giving Chinese exporters an "unfair" advantage. But China said its huge trade surpluses are also a result of the US reluctance to export goods involving state-of-the-art technologies.</p><p>Fu Rui, also a CPPCC member, said with ample foreign exchange reserves, China could intentionally bulk up the reserves of strategic resources.</p><p>The international consensus is a country's rational foreign exchange reserves should equal to its imports demand for a full quarter. Also taking into consideration of payments for foreign debts, returns for foreign investors and other demands in China, many believe it is enough for the country to retain US/$300 billion.</p><p>But Lin Yifu, a popular economist, underscored China's per capita foreign exchange reserves remains not large - less than one-tenth of Japan's and far below that of Hong Kong and Singapore.</p><p>The reserves were "tremendous fruits" from China's reform and opening-up drive, he said.</p><p>His remarks were echoed by Xiao Zhuoji, a well-known economics professor with Beijing University. "The rise of foreign exchange reserves reflects China's fast, sustained economic growth and sound international payments," he said.</p><p>"The reserves are of significant importance to upgrade the China image in the international economic arena, strengthen the nation's macro-control capabilities and guard against financial risks," added Xiao, a Standing Committee member of the CPPCC National Committee.</p><p>But as the People's Bank of China, or the central bank, has to buy foreign exchange reserves under the current foreign exchange control policies, the country's monetary base will be enlarged, increasing its inflationary pressure and difficulties on macro-economic controls, analysts acknowledge.</p><p>Another prevailing view is that China's hefty foreign exchange reserves actually "occupied" large amounts of fund resources that otherwise can be diverted for domestic investment and consumption.</p><p>Some CPPCC members said they believe it is already "meaningless" now to talk about whether China's foreign exchange reserves size is big or not. "The key lies on how to raise the reserves' yields."</p><p>"If the annual yields from foreign exchange reserves could reach a stable 5 percent, the nation will reap in 300 billion yuan a year. What a big fortune!" one advisor told Xinhua.</p><p>Central banker Zhou Xiaochuan reiterated earlier that China will "pay attention to and maintain the flexibility" of foreign reserves structure, which is unknown to the public.</p></td></tr></tbody></table></td></tr></tbody></table>"""

        result = self.metric._extract_from_markdown(text)

        # 验证复杂表格被完整提取
        expected_table = """<table><tbody><tr><td><table><tbody><tr><td><table><tbody><tr><td><strong>Better Management of /$800 Bln Forex Reserves Urged</strong></td></tr></tbody></table></td></tr><tr><td><p>A number of political advisors on Sunday called for more rationally managing China's massive foreign exchange reserves, which doubled over the 2004-05 period to an equivalent of US/$818.9 billion, second only to Japan.</p><p>The quick buildup is largely a result of China's booming exports and foreign exchange controls by the government, as well as speculation on the yuan's rise, industry watchers agree.</p><p>A big part of China's foreign exchange reserves are US dollar-denominated assets, including bonds issued by the US government. "Risks in the international foreign exchange market should be lowered when China manages its reserves," said Professor Guo Guoqing of a business school of the People's University of China.</p><p>Guo, a member of the National Committee of the Chinese People's Political Consultative Conference (CPPCC), the country's top advisory body, urged the government to cut back on subsidies for exports and take other measures to reduce foreign trade surpluses appropriately and achieve the balance in international payments.</p><p>Part of the reserves should be channeled into the imports of more high-tech machinery, equipment and other products, he suggested on the sidelines of the CPPCC's annual session.</p><p>The United States has been contending that the value of yuan, also known as renminbi or RMB, is too low, giving Chinese exporters an "unfair" advantage. But China said its huge trade surpluses are also a result of the US reluctance to export goods involving state-of-the-art technologies.</p><p>Fu Rui, also a CPPCC member, said with ample foreign exchange reserves, China could intentionally bulk up the reserves of strategic resources.</p><p>The international consensus is a country's rational foreign exchange reserves should equal to its imports demand for a full quarter. Also taking into consideration of payments for foreign debts, returns for foreign investors and other demands in China, many believe it is enough for the country to retain US/$300 billion.</p><p>But Lin Yifu, a popular economist, underscored China's per capita foreign exchange reserves remains not large - less than one-tenth of Japan's and far below that of Hong Kong and Singapore.</p><p>The reserves were "tremendous fruits" from China's reform and opening-up drive, he said.</p><p>His remarks were echoed by Xiao Zhuoji, a well-known economics professor with Beijing University. "The rise of foreign exchange reserves reflects China's fast, sustained economic growth and sound international payments," he said.</p><p>"The reserves are of significant importance to upgrade the China image in the international economic arena, strengthen the nation's macro-control capabilities and guard against financial risks," added Xiao, a Standing Committee member of the CPPCC National Committee.</p><p>But as the People's Bank of China, or the central bank, has to buy foreign exchange reserves under the current foreign exchange control policies, the country's monetary base will be enlarged, increasing its inflationary pressure and difficulties on macro-economic controls, analysts acknowledge.</p><p>Another prevailing view is that China's hefty foreign exchange reserves actually "occupied" large amounts of fund resources that otherwise can be diverted for domestic investment and consumption.</p><p>Some CPPCC members said they believe it is already "meaningless" now to talk about whether China's foreign exchange reserves size is big or not. "The key lies on how to raise the reserves' yields."</p><p>"If the annual yields from foreign exchange reserves could reach a stable 5 percent, the nation will reap in 300 billion yuan a year. What a big fortune!" one advisor told Xinhua.</p><p>Central banker Zhou Xiaochuan reiterated earlier that China will "pay attention to and maintain the flexibility" of foreign reserves structure, which is unknown to the public.</p></td></tr></tbody></table></td></tr></tbody></table>"""
        self.assertIn(expected_table, result['table'])

    def test_html_table_in_code(self):
        """测试代码块中的HTML表格不被提取"""
        text = """这是代码块中的HTML表格：

        ```
       
       <table> <tr><th>标题1</th><th>标题2</th></tr> <tr><td>数据1</td><td>数据2</td></tr> </table> 
       
       
       ```
        这是正常文本中的HTML表格（应该被提取）：
        
        <table> <tr><th>姓名</th><th>年龄</th></tr> <tr><td>张三</td><td>25</td></tr> </table>
        这是内联代码中的表格：`<table><tr><td>`不应该提取</td></tr></table>
        
        正常文本结束。"""

        result = self.metric._extract_from_markdown(text)

        # 验证代码块中的HTML表格没有被提取
        self.assertNotIn('<tr><th>标题1</th><th>标题2</th></tr>', result['table'])
        self.assertNotIn('<tr><td>数据1</td><td>数据2</td></tr>', result['table'])

        # 验证内联代码中的表格没有被提取
        self.assertNotIn('<table><tr><td>', result['table'])

        # 验证正常文本中的HTML表格被正确提取
        self.assertIn('<tr><th>姓名</th><th>年龄</th></tr>', result['table'])
        self.assertIn('<tr><td>张三</td><td>25</td></tr>', result['table'])

        # 验证只提取了一个表格
        table_count = result['table'].count('<table>')
        self.assertEqual(table_count, 1)



if __name__ == '__main__':
    unittest.main()
