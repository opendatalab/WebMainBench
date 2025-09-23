import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from .base_extractor import ContentExtractor


class TableExtractor(ContentExtractor):
    """从文本中提取表格"""

    def extract(self, text: str, field_name: str = None) -> str:
        """提取表格"""
        tables = self.extract_basic(text)

        if self.should_use_llm(field_name):
            table_parts = self.enhance_with_llm(tables)
        else:
            table_parts = tables

        return '\n'.join(table_parts)

    def extract_basic(self, text: str) -> List[str]:
        """基本表格提取方法"""
        table_parts = []

        # HTML表格提取
        soup = BeautifulSoup(text, "html.parser")
        for table in soup.find_all("table"):
            if not table.find_parent(["td", "tr", "tbody", "table"]):
                table_parts.append(str(table))

        # Markdown表格提取
        lines = text.split('\n')
        table_lines = []
        in_markdown_table = False

        def is_md_table_line(line):
            """判断是否可能是 Markdown 表格行"""
            if line.count("|") < 1:
                return False
            return True

        def is_md_separator_line(line):
            """判断是否为 Markdown 分隔行"""
            parts = [p.strip() for p in line.split("|")]
            for p in parts:
                if p and not re.match(r"^:?\-{3,}:?$", p):
                    return False
            return True

        def save_table():
            """保存当前表格并清空缓存"""
            nonlocal table_lines
            if len(table_lines) >= 2 and is_md_separator_line(table_lines[1]):
                md_table = '\n'.join(table_lines)
                table_parts.append(md_table)

        for line in lines:
            if is_md_table_line(line):
                table_lines.append(line)
                in_markdown_table = True
            else:
                if in_markdown_table:
                    save_table()
                    table_lines = []
                    in_markdown_table = False

        # 处理文档末尾的 Markdown 表格
        if in_markdown_table:
            save_table()

        return table_parts

    def _llm_enhance(self, basic_results: List[str]) -> List[str]:
        """使用LLM增强表格提取结果（未实现）"""
        print(f"[DEBUG] 表格LLM增强功能尚未实现，返回原始结果")
        return basic_results
