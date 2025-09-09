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

        # 1. 提取原始表格内容
        pred_raw = self._extract_table_content(predicted, predicted_content_list)
        gt_raw = self._extract_table_content(groundtruth, groundtruth_content_list)

        # 2. 复用TEDSMetric的归一化方法，统一转换为HTML格式
        teds = TEDSMetric("temp_teds")  # 实例化TEDSMetric以调用其方法
        pred_html = teds._normalize_to_html(pred_raw)  # 调用TEDS的归一化方法
        gt_html = teds._normalize_to_html(gt_raw)

        # 3. 从归一化后的HTML中提取纯文本内容（保留表格结构）
        pred_text = self._extract_text_from_html(pred_html)
        gt_text = self._extract_text_from_html(gt_html)

        # 4. 基于归一化后的文本计算编辑距离
        result = super()._calculate_score(pred_text, gt_text, **kwargs)
        result.metric_name = self.name
        result.details.update({
            "predicted_table_length": len(pred_text),
            "groundtruth_table_length": len(gt_text),
            "content_type": "table",
            "normalization": "teds_based"  # 标记使用TEDS的归一化方法
        })
        
        return result
    
    def _extract_table_content(self, text: str, content_list: List[Dict[str, Any]] = None) -> str:
        """从文本和content_list中提取表格内容"""
        # 使用统一的内容分割方法
        content_parts = self.split_content(text, content_list)
        return content_parts.get('table', '')

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