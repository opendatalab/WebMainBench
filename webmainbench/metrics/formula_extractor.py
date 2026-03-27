import re
from typing import List
from .base_content_splitter import BaseContentSplitter, _metrics_debug


class FormulaSplitter(BaseContentSplitter):
    """从文本中提取数学公式"""

    DEFAULT_LLM_PROMPT = '''任务：请从以下正则表达式提取的内容中，识别并保留真正的LaTeX数学公式，剔除货币形式的内容。

    ### 识别规则
    **真正的数学公式**（保留）：
    - 包含数学符号：+ - × ÷ = < > ≤ ≥ ± ∞ ∑ ∫ ∂ √ ^ _ { } 等
    - 包含希腊字母：α β γ δ θ λ μ π σ ω 等
    - 包含LaTeX命令：\\frac \\sum \\int \\sqrt \\alpha \\beta \\sin \\cos 等
    - 包含数学表达式：变量、函数、方程等

    **货币形式内容**（剔除）：
    - 仅包含数字、逗号、小数点的价格：如 1,150.00
    - 纯粹的金额数值：如 25.99、1,200、5.50
    - 不包含任何数学运算符或数学符号的数字

    ### 处理要求
    1. **严格区分**：只保留真正的数学公式，剔除所有货币价格
    2. **格式标准化**：统一公式格式，确保LaTeX语法正确
    3. **保持原意**：不修改数学公式内容

    ### 输出格式
    - 每个有效的数学公式独占一行
    - 只输出公式内容，不包含$符号或其他包装
    - 如果输入不是有效的数学公式（如货币），则输出<空>
    - 按原顺序输出保留的公式

    ### 示例 1 (剔除后有有效公式)
    输入：1,150.00 → 剔除（货币）
    输入：x^2 + y^2 = r^2 → 保留（数学公式）
    输入：25.99 → 剔除（货币）
    输入：\\frac{a}{b} + c → 保留（数学公式）

    ### 示例 2 (剔除后无有效公式)
    输入：1,150.00 → 剔除（货币）
    输入：25.99 → 剔除（货币）

    输出：<空>

    注意，输出结果中不要添加任何解释！。
    [输入内容列表开始]'''

    def extract(self, text: str, field_name: str = None) -> str:
        """提取数学公式"""
        regex_formulas = self.extract_basic(text)
        if self.should_use_llm(field_name):
            _metrics_debug("Using LLM-enhanced formula extraction")
            formula_parts = self.enhance_with_llm(regex_formulas)
            if not formula_parts:
                _metrics_debug("No valid formulas after LLM enhancement")
        else:
            formula_parts = regex_formulas
            _metrics_debug("Skipping LLM enhancement; using regex-only results")
        return '\n'.join(formula_parts)

    def extract_basic(self, text: str) -> List[str]:
        """使用正则表达式提取公式"""

        regex_formulas = []

        # 排除Markdown代码块（```code```和`code`）
        # 首先移除多行代码块
        text_without_blocks = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # 移除内联代码块
        text_without_code = re.sub(r'`[^`]*`', '', text_without_blocks)

        latex_patterns = [
            r'(?<!\\)\$\$(.*?)(?<!\\)\$\$',  # 行间 $$...$$
            r'(?<!\\)\\\[(.*?)(?<!\\)\\\]',  # 行间 \[...\]
            r'(?<!\\)\$(.*?)(?<!\\)\$',  # 行内 $...$
            r'(?<!\\)\\\((.*?)(?<!\\)\\\)',  # 行内 \(...\)
        ]

        for pattern in latex_patterns:
            for match in re.finditer(pattern, text_without_code, re.DOTALL):
                formula_content = match.group(1)
                if formula_content.strip():
                    regex_formulas.append(formula_content.strip())


        return regex_formulas

    def _llm_enhance(self, basic_results: List[str]) -> List[str]:
        """使用LLM增强公式提取结果"""
        if not self.client:
            _metrics_debug("OpenAI client not initialized; returning basic extraction results")
            return basic_results

        formulas_text = '\n'.join(basic_results)

        response = self.client.chat.completions.create(
            model=self.config.get('llm_model', "deepseek-chat"),
            temperature=0,
            messages=[
                {"role": "user", "content": self.DEFAULT_LLM_PROMPT + f"\n{formulas_text}\n" + '''[输入内容列表结束]
        ---
        请按要求识别并输出真正的数学公式，剔除货币形式的内容。
        ---'''}
            ]
        )

        result_text = response.choices[0].message.content.strip()

        if '空' in result_text:
            return []
        elif not result_text:
            return []
        else:
            return [line.strip() for line in result_text.split('\n') if line.strip()]