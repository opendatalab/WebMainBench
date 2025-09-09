"""
Table extraction metrics for WebMainBench.
"""

from typing import Dict, Any, List
import re
from .base import BaseMetric, MetricResult
from .teds_metrics import TEDSMetric, StructureTEDSMetric
from .text_metrics import EditDistanceMetric
from bs4 import BeautifulSoup

class TableEditMetric(EditDistanceMetric):
    """表格编辑距离指标"""
    
    version = "1.0.0"
    description = "Table content edit distance metric"
    
    def _calculate_score(self, predicted: str, groundtruth: str,
                        predicted_content_list: List[Dict[str, Any]] = None,
                        groundtruth_content_list: List[Dict[str, Any]] = None,
                        **kwargs) -> MetricResult:
        """计算表格内容的编辑距离"""
        
        # 从content_list中提取表格内容
        pred_table = self._extract_table_content(predicted, predicted_content_list)
        gt_table = self._extract_table_content(groundtruth, groundtruth_content_list)

        # 统一转换为HTML格式（复用TEDSMetric的归一化逻辑）
        pred_html = self._normalize_to_html(pred_table)
        gt_html = self._normalize_to_html(gt_table)

        # 从HTML中提取纯文本内容（忽略标签，仅保留表格数据）
        pred_text = self._extract_text_from_html(pred_html)
        gt_text = self._extract_text_from_html(gt_html)
        
        # 计算编辑距离
        result = super()._calculate_score(pred_text, gt_text, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "predicted_table_length": len(pred_text),
            "groundtruth_table_length": len(gt_text),
            "content_type": "table"
        })
        
        return result
    
    def _extract_table_content(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """从文本和content_list中提取表格内容"""
        # 使用统一的内容分割方法
        content_parts = self.split_content(text, content_list)
        return content_parts.get('table', '')

    def _normalize_to_html(self, table_data: str) -> str:
        """复用TEDSMetric的表格格式归一化逻辑，统一转换为HTML"""
        # 若输入为空，直接返回空字符串
        if not table_data.strip():
            return ""
        # 若已为HTML表格，直接返回
        if '<table' in table_data.lower():
            return table_data
        # 若为Markdown表格，转换为HTML
        if '|' in table_data:
            return self._markdown_to_html(table_data)
        # 其他格式视为纯文本表格，简单包裹为HTML
        return f"<table><tr><td>{table_data}</td></tr></table>"

    def _markdown_to_html(self, markdown: str) -> str:
        """将Markdown表格转换为HTML（复用TEDSMetric逻辑）"""
        lines = [line.strip() for line in markdown.split('\n') if line.strip()]
        table_lines = [line for line in lines if '|' in line]
        if not table_lines:
            return ""
        html_parts = ["<table>"]
        # 过滤分隔线（如 |---|）
        data_lines = [line for line in table_lines if not re.match(r'^[\s\|\-:]+$', line)]
        for i, line in enumerate(data_lines):
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                # 首行视为表头（th），其余为单元格（td）
                tag = "th" if i == 0 else "td"
                html_parts.append(f"<tr>{''.join(f'<{tag}>{cell}</{tag}>' for cell in cells)}</tr>")
        html_parts.append("</table>")
        return ''.join(html_parts)

    def _extract_text_from_html(self, html: str) -> str:
        """从HTML表格中提取纯文本内容（忽略标签，保留数据结构）"""
        if not html.strip():
            return ""
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        if not table:
            return ""
        # 按行提取文本，用换行分隔行，用空格分隔单元格
        text_parts = []
        for row in table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
            if row_text:
                text_parts.append(row_text)
        return '\n'.join(text_parts)

    def _extract_tables_from_content_list(self, content_list: List[Dict[str, Any]]) -> List[str]:
        """递归从content_list中提取表格内容"""
        tables = []
        
        def _recursive_extract(items):
            if not isinstance(items, list):
                return
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                # 检查当前项是否为表格
                item_type = item.get('type', '')
                if item_type in ['table']:
                    content = item.get('content', '')
                    if content:
                        tables.append(content)
                
                # 递归检查children字段
                children = item.get('children')
                if children:
                    _recursive_extract(children)
                
                # 递归检查items字段
                items_field = item.get('items')
                if items_field:
                    _recursive_extract(items_field)
        
        _recursive_extract(content_list)
        return tables


class TableTEDSMetric(TEDSMetric):
    """表格TEDS指标"""
    
    version = "1.0.0"
    description = "Table TEDS (Tree-Edit Distance based Similarity) metric"
    
    def _calculate_score(self, predicted: str, groundtruth: str,
                        predicted_content_list: List[Dict[str, Any]] = None,
                        groundtruth_content_list: List[Dict[str, Any]] = None,
                        **kwargs) -> MetricResult:
        """计算表格的TEDS分数"""
        
        # 从content_list中提取表格内容
        pred_table = self._extract_table_content(predicted, predicted_content_list)
        gt_table = self._extract_table_content(groundtruth, groundtruth_content_list)
        
        # 使用父类的TEDS计算
        result = super()._calculate_score(pred_table, gt_table, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "content_type": "table",
            "algorithm": "TEDS"
        })
        
        return result
    
    def _extract_table_content(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """从文本和content_list中提取表格内容"""
        # 使用统一的内容分割方法
        content_parts = self.split_content(text, content_list)
        return content_parts.get('table', '') 