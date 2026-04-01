# webmainbench/metrics/extractors/table_extractor.py
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from .base_content_splitter import BaseContentSplitter, _metrics_debug


class TableSplitter(BaseContentSplitter):
    """Extract tables from text."""

    def extract(self, text: str, field_name: str = None) -> str:
        """Extract tables."""
        tables = self.extract_basic(text)
        return '\n'.join(tables)

    def extract_basic(self, text: str) -> List[str]:
        """Basic table extraction method."""
        table_parts = []

        # Remove code block content
        text_without_code = self._remove_code_blocks(text)

        # Extract HTML tables (from cleaned text)
        soup = BeautifulSoup(text_without_code, "html.parser")

        for table in soup.find_all("table"):
            if not table.find_parent(["td", "tr", "tbody", "table"]):
                table_parts.append(str(table))

        # Extract Markdown tables
        lines = text.split('\n')
        table_lines = []
        in_markdown_table = False

        def is_md_table_line(line):
            """Check if a line could be a Markdown table row."""
            if line.count("|") < 1:
                return False
            return True

        def is_md_separator_line(line):
            """Check if a line is a Markdown separator row."""
            parts = [p.strip() for p in line.split("|")]
            for p in parts:
                if p and not re.match(r"^:?\-{3,}:?$", p):
                    return False
            return True

        def save_table():
            """Save the current table and clear the buffer."""
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

        # Handle Markdown tables at the end of the document
        if in_markdown_table:
            save_table()

        return table_parts

    def _remove_code_blocks(self, text: str) -> str:
        """Remove Markdown code blocks."""
        # Remove multi-line fenced code blocks ```
        text_without_blocks = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Remove inline code blocks `
        text_without_code = re.sub(r'`[^`]*`', '', text_without_blocks)
        return text_without_code

    def _llm_enhance(self, basic_results: List[str]) -> List[str]:
        """Table extraction does not use LLM enhancement."""
        return basic_results
