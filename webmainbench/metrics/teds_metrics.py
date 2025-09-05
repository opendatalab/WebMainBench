"""
TEDS (Tree-Edit Distance based Similarity) metrics for WebMainBench.

Based on the paper:
"Image-based table recognition: data, model, and evaluation" by IBM Research.

The TEDS algorithm represents tables as tree structures and calculates
similarity using tree edit distance.
"""

from typing import Dict, Any, List, Optional
import re
from bs4 import BeautifulSoup
from rapidfuzz.distance import Levenshtein
from apted import APTED, Config
from .base import BaseMetric, MetricResult


class TableConfig(Config):
    def delete(self, node):
        return 1

    def insert(self, node):
        return 1

    def rename(self, node1, node2):
        # 解析节点标签，格式为 "tag:text"
        tag1, text1 = self._parse_node(node1)
        tag2, text2 = self._parse_node(node2)

        if tag1 != tag2:
            return 1

        if text1 == text2:
            return 0

        # 计算文本编辑距离
        return self._levenshtein(text1, text2)

    def _parse_node(self, node_str):
        """解析节点字符串，格式为 'tag:text' 或 'tag'"""
        if ':' in node_str:
            tag, text = node_str.split(':', 1)
            return tag, text
        else:
            return node_str, ""

    def _levenshtein(self, a, b):
        """计算文本编辑距离"""
        if not a and not b:
            return 0
        if not a:
            return len(b)  # 空字符串到非空字符串，成本为字符串长度
        if not b:
            return len(a)  # 非空字符串到空字符串，成本为字符串长度

        # 计算原始编辑距离
        raw_distance = Levenshtein.distance(a, b)

        # 使用与text_metrics.py相同的归一化方式：基于较长字符串的长度
        max_len = max(len(a), len(b))
        if max_len == 0:
            return 0

        # 归一化到0-1范围
        return raw_distance / max_len


class TEDSMetric(BaseMetric):
    """TEDS (Tree-Edit Distance based Similarity) metric for table evaluation."""

    version = "1.0.0"
    description = "Table evaluation using Tree-Edit Distance based Similarity (TEDS)"

    def _setup(self) -> None:
        self.structure_only = self.config.get('structure_only', False)
        self.ignore_nodes = self.config.get('ignore_nodes', ['tbody', 'thead', 'tfoot'])
        self.config_apted = TableConfig()

    def _calculate_score(self, predicted: Any, groundtruth: Any, **kwargs) -> MetricResult:
        try:
            table_edit_result = kwargs.get('table_edit_result')
            if table_edit_result is None:
                return MetricResult.create_error_result(
                    self.name, "Missing table_edit result in kwargs"
                )
            if not table_edit_result.success:
                return MetricResult.create_error_result(
                    self.name,
                    f"Skipped due to table_edit failure: {table_edit_result.details.get('error', 'unknown reason')}"
                )

            pred_html = self._normalize_to_html(predicted)
            gt_html = self._normalize_to_html(groundtruth)

            pred_tree = self._parse_html_table(pred_html)
            gt_tree = self._parse_html_table(gt_html)

            if pred_tree is None and gt_tree is None:
                return MetricResult(
                    metric_name=self.name,
                    score=1.0,
                    details={"note": "Both tables are empty or invalid"}
                )

            if pred_tree is None or gt_tree is None:
                return MetricResult(
                    metric_name=self.name,
                    score=0.0,
                    details={"note": "One table is empty or invalid"}
                )

            edit_distance = self._tree_edit_distance(pred_tree, gt_tree)
            max_nodes = max(self._count_nodes(pred_tree), self._count_nodes(gt_tree))

            # 使用归一化方式计算TEDS分数
            if max_nodes > 0:
                # 标准TEDS公式：1.0 - (edit_distance / max_nodes)
                teds_score = 1.0 - (edit_distance / max_nodes)
            else:
                teds_score = 1.0

            details = {
                "edit_distance": edit_distance,
                "predicted_nodes": self._count_nodes(pred_tree),
                "groundtruth_nodes": self._count_nodes(gt_tree),
                "max_nodes": max_nodes,
                "structure_only": self.structure_only,
                "algorithm": "TEDS"
            }

            return MetricResult(
                metric_name=self.name,
                score=max(0.0, min(1.0, teds_score)),
                details=details
            )

        except Exception as e:
            return MetricResult.create_error_result(
                self.name, f"TEDS calculation failed: {str(e)}"
            )

    def _normalize_to_html(self, table_data: Any) -> str:
        if table_data is None:
            return ""
        if isinstance(table_data, str):
            # 空字符串应该保持为空，不应该转换成默认HTML
            if not table_data.strip():
                return ""
            if '<table' in table_data.lower():
                return table_data
            if '|' in table_data:
                return self._markdown_to_html(table_data)
            return f"<table><tr><td>{table_data}</td></tr></table>"
        elif isinstance(table_data, list):
            return self._list_to_html(table_data)
        else:
            return f"<table><tr><td>{str(table_data)}</td></tr></table>"

    def _markdown_to_html(self, markdown: str) -> str:
        lines = [line.strip() for line in markdown.split('\n') if line.strip()]
        table_lines = [line for line in lines if '|' in line]
        if not table_lines:
            return ""
        html_parts = ["<table>"]
        data_lines = [line for line in table_lines if not re.match(r'^[\s\|\-:]+$', line)]
        for i, line in enumerate(data_lines):
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                tag = "th" if i == 0 else "td"
                html_parts.append(f"<tr>{''.join(f'<{tag}>{cell}</{tag}>' for cell in cells)}</tr>")
        html_parts.append("</table>")
        return ''.join(html_parts)

    def _list_to_html(self, data: List) -> str:
        if not data:
            return ""
        html_parts = ["<table>"]
        for item in data:
            if isinstance(item, dict):
                cells = list(item.values())
            elif isinstance(item, list):
                cells = item
            else:
                cells = [str(item)]
            html_parts.append(f"<tr>{''.join(f'<td>{cell}</td>' for cell in cells)}</tr>")
        html_parts.append("</table>")
        return ''.join(html_parts)

    def _parse_html_table(self, html_str: str) -> Optional[Dict]:
        if not html_str.strip():
            return None
        try:
            soup = BeautifulSoup(html_str, 'html.parser')
            table = soup.find('table')
            if table is None:
                return None
            return self._element_to_tree(table)
        except Exception:
            return None

    def _element_to_tree(self, element) -> Dict:
        tree = {
            'tag': element.name,
            'attrs': dict(element.attrs) if hasattr(element, 'attrs') else {},
            'text': element.get_text(strip=True) if not self.structure_only else "",
            'children': []
        }
        if element.name in self.ignore_nodes:
            for child in element.children:
                if hasattr(child, 'name') and child.name:
                    tree['children'].extend(self._element_to_tree(child)['children'])
        else:
            for child in element.children:
                if hasattr(child, 'name') and child.name:
                    tree['children'].append(self._element_to_tree(child))
        return tree

    def _tree_edit_distance(self, tree1: Dict, tree2: Dict) -> float:
        """使用APTED计算树编辑距离"""
        try:
            # 转换为APTED的括号表示法
            t1 = self._to_bracket_notation(tree1)
            t2 = self._to_bracket_notation(tree2)

            # 使用APTED计算编辑距离
            apted = APTED(t1, t2, self.config_apted)
            edit_distance = apted.compute_edit_distance()

            return float(edit_distance)
        except Exception as e:
            # 如果APTED失败，回退到简单的节点计数差异
            print(f"APTED calculation failed: {e}, falling back to simple distance")
            nodes1 = self._count_nodes(tree1)
            nodes2 = self._count_nodes(tree2)
            return abs(nodes1 - nodes2)

    def _to_bracket_notation(self, node: Dict) -> str:
        """将字典树转换为APTED的括号表示法"""
        # 构建节点标签
        tag = node['tag']
        text = node.get('text', '')

        # 在结构模式下，忽略文本内容
        if self.structure_only:
            label = tag
        else:
            # 在完整模式下，包含文本内容
            if text:
                # 处理文本中的特殊字符，避免APTED解析错误
                safe_text = text.replace('(', '[').replace(')', ']').replace(',', ';')
                label = f"{tag}:{safe_text}"
            else:
                label = tag

        # 如果没有子节点，返回标签
        if not node.get('children'):
            return label

        # 有子节点，递归处理
        children_str = ",".join([self._to_bracket_notation(c) for c in node['children']])
        return f"{label}({children_str})"

    def _count_nodes(self, tree: Dict) -> int:
        if tree is None:
            return 0
        return 1 + sum(self._count_nodes(c) for c in tree.get('children', []))


class StructureTEDSMetric(TEDSMetric):
    """Structure-only TEDS metric (S-TEDS)."""

    def _setup(self) -> None:
        super()._setup()
        self.structure_only = True
        self.name = "s_teds"
        self.description = "Structure-only Tree-Edit Distance based Similarity (S-TEDS)"