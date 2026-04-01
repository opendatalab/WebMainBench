# webmainbench/metrics/extractors/code_extractor.py
import re
from typing import List, Dict, Any

from .base_content_splitter import BaseContentSplitter, _metrics_debug


class CodeSplitter(BaseContentSplitter):
    """Extract code blocks from text."""

    def extract(self, text: str, field_name: str = None) -> str:
        """Extract code blocks."""
        code_blocks = self.extract_basic(text)
        return '\n'.join(code_blocks)

    def extract_basic(self, text: str) -> List[str]:
        """Extract code blocks using regular expressions."""
        code_parts = []

        # Handle fenced code blocks wrapped in triple backticks
        backtick_pattern = r'(```[\s\S]*?```)'
        for match in re.finditer(backtick_pattern, text):
            code_segment = match.group(0)
            if code_segment.startswith('```'):
                lines = code_segment.split('\n')
                content_lines = lines[1:-1]
                code_content = '\n'.join(content_lines)
                if code_content:
                    code_parts.append(code_content)

        # Handle indented code blocks
        indent_pattern = r'(?:\n\s*\n)((?:(?: {4,}|\t+)[^\n]*(?:\n|$)){2,})(?=\n\s*\n|$)'

        for match in re.finditer(indent_pattern, text, re.MULTILINE):
            code_segment = match.group(1)

            # Validate: ensure all lines are indented
            lines = code_segment.split('\n')
            all_indented = all(
                line.startswith('    ') or line.startswith('\t') or not line.strip()
                for line in lines
                if line.strip()
            )

            if not all_indented:
                continue

            # Further validate code characteristics
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            if len(non_empty_lines) < 2:
                continue

            # Check for obvious non-code features
            has_list_features = any(
                re.match(r'^[-•*]\s', line) or
                re.match(r'^\d+\.\s', line) or
                re.search(r'\$[\d,]', line) or
                re.search(r'\b(million|billion|thousand)\b', line, re.IGNORECASE)
                for line in non_empty_lines
            )

            if has_list_features:
                continue

            # Clean up the code segment
            cleaned_lines = []
            for line in code_segment.split('\n'):
                if line.strip():
                    if line.startswith('    '):
                        cleaned_lines.append(line[4:])
                    elif line.startswith('\t'):
                        cleaned_lines.append(line[1:])
                    else:
                        cleaned_lines.append(line)

            code_content = '\n'.join(cleaned_lines)
            if code_content.strip():
                code_parts.append(code_content)

        return code_parts

    def _llm_enhance(self, basic_results: List[str]) -> List[str]:
        """Code extraction does not use LLM enhancement."""
        return basic_results
