import re
from typing import List
from .base_content_splitter import BaseContentSplitter, _metrics_debug


class FormulaSplitter(BaseContentSplitter):
    """Extract mathematical formulas from text"""

    DEFAULT_LLM_PROMPT = '''Task: From the content extracted by the following regular expressions, identify and keep genuine LaTeX mathematical formulas, and remove currency-formatted content.

    ### Identification Rules
    **Genuine mathematical formulas** (keep):
    - Contains mathematical symbols: + - × ÷ = < > ≤ ≥ ± ∞ ∑ ∫ ∂ √ ^ _ { } etc.
    - Contains Greek letters: α β γ δ θ λ μ π σ ω etc.
    - Contains LaTeX commands: \\frac \\sum \\int \\sqrt \\alpha \\beta \\sin \\cos etc.
    - Contains mathematical expressions: variables, functions, equations, etc.

    **Currency-formatted content** (remove):
    - Prices containing only digits, commas, and decimal points: e.g. 1,150.00
    - Pure monetary values: e.g. 25.99, 1,200, 5.50
    - Numbers without any mathematical operators or symbols

    ### Processing Requirements
    1. **Strict distinction**: Only keep genuine mathematical formulas, remove all currency prices
    2. **Format standardization**: Unify formula format, ensure correct LaTeX syntax
    3. **Preserve meaning**: Do not modify the content of mathematical formulas

    ### Output Format
    - Each valid mathematical formula occupies one line
    - Output only the formula content, without $ symbols or other wrappers
    - If the input is not a valid mathematical formula (e.g. currency), output <empty>
    - Output retained formulas in their original order

    ### Example 1 (valid formulas remain after removal)
    Input: 1,150.00 → remove (currency)
    Input: x^2 + y^2 = r^2 → keep (mathematical formula)
    Input: 25.99 → remove (currency)
    Input: \\frac{a}{b} + c → keep (mathematical formula)

    ### Example 2 (no valid formulas remain after removal)
    Input: 1,150.00 → remove (currency)
    Input: 25.99 → remove (currency)

    Output: <empty>

    Note: Do not add any explanations to the output!
    [Input content list begins]'''

    def extract(self, text: str, field_name: str = None) -> str:
        """Extract mathematical formulas"""
        regex_formulas = self.extract_basic(text)
        if self.should_use_llm(field_name):
            formula_parts = self.enhance_with_llm(regex_formulas)
        else:
            formula_parts = regex_formulas
            _metrics_debug("Skipping LLM enhancement; using regex-only results")
        return '\n'.join(formula_parts)

    def extract_basic(self, text: str) -> List[str]:
        """Extract formulas using regular expressions"""

        regex_formulas = []

        # Exclude Markdown code blocks (```code``` and `code`)
        # First remove multi-line code blocks
        text_without_blocks = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Remove inline code blocks
        text_without_code = re.sub(r'`[^`]*`', '', text_without_blocks)

        latex_patterns = [
            r'(?<!\\)\$\$(.*?)(?<!\\)\$\$',  # display math $$...$$
            r'(?<!\\)\\\[(.*?)(?<!\\)\\\]',  # display math \[...\]
            r'(?<!\\)\$(.*?)(?<!\\)\$',  # inline math $...$
            r'(?<!\\)\\\((.*?)(?<!\\)\\\)',  # inline math \(...\)
        ]

        for pattern in latex_patterns:
            for match in re.finditer(pattern, text_without_code, re.DOTALL):
                formula_content = match.group(1)
                if formula_content.strip():
                    regex_formulas.append(formula_content.strip())


        return regex_formulas

    def _llm_enhance(self, basic_results: List[str]) -> List[str]:
        """Use LLM to enhance formula extraction results"""
        if not self.client:
            _metrics_debug("OpenAI client not initialized; returning basic extraction results")
            return basic_results

        formulas_text = '\n'.join(basic_results)

        response = self.client.chat.completions.create(
            model=self.config.get('llm_model', "deepseek-chat"),
            temperature=0,
            messages=[
                {"role": "user", "content": self.DEFAULT_LLM_PROMPT + f"\n{formulas_text}\n" + '''[Input content list ends]
        ---
        Please identify and output genuine mathematical formulas as required, removing currency-formatted content.
        ---'''}
            ]
        )

        result_text = response.choices[0].message.content.strip()

        if '<empty>' in result_text or 'empty' in result_text.lower():
            return []
        elif not result_text:
            return []
        else:
            return [line.strip() for line in result_text.split('\n') if line.strip()]