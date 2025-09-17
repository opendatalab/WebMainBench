# webmainbench/metrics/formula_extractor.py
import json
import os
from openai import OpenAI

def correct_formulas_with_llm(regex_formulas, cache_file=None):
    """使用LLM API修正正则提取的公式"""

    if not regex_formulas:
        print(f"[DEBUG] 输入公式列表为空，跳过API修正")
        return []

    # 检查缓存
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_result = json.load(f)
                print(f"[DEBUG] 从缓存加载修正结果: {len(cached_result)} 个")
                return cached_result
        except Exception as e:
            print(f"[DEBUG] 缓存读取失败: {e}")

    # API配置
    client = OpenAI(
        base_url="",
        api_key=""
    )

    # 将正则提取的公式转换为文本
    formulas_text = '\n'.join(regex_formulas)

    CORRECTION_PROMPT = '''任务：请从以下正则表达式提取的内容中，识别并保留真正的LaTeX数学公式，剔除货币形式的内容。

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

    try:
        print(f"[DEBUG] 开始调用 OpenAI API 进行公式修正...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            temperature=0,
            messages=[
                {"role": "user", "content": CORRECTION_PROMPT + f"\n{formulas_text}\n" + '''[输入内容列表结束]
---
请按要求识别并输出真正的数学公式，剔除货币形式的内容。
---'''}
            ]
        )

        result_text = response.choices[0].message.content.strip()
        print(f"[DEBUG] API 返回修正结果: {repr(result_text)}")

        # 检测返回内容是否包含"空"字 - 如果包含则整个结果为空
        if '空' in result_text:
            print(f"[DEBUG] 检测到API返回包含'空'字，将整个结果设置为空列表")
            corrected_formulas = []
        elif not result_text:
            corrected_formulas = []
        else:
            # 正常解析返回的公式列表
            corrected_formulas = [line.strip() for line in result_text.split('\n') if line.strip()]

        print(f"[DEBUG] 修正后的公式列表: {corrected_formulas}")

        # 保存缓存
        if cache_file:
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(corrected_formulas, f, ensure_ascii=False, indent=2)
                print(f"[DEBUG] 修正结果已缓存到: {cache_file}")
            except Exception as e:
                print(f"[DEBUG] 缓存保存失败: {e}")

        return corrected_formulas

    except Exception as e:
        print(f"[DEBUG] API 修正异常: {type(e).__name__}: {e}")
        print(f"[DEBUG] 回退到原始正则结果")
        return regex_formulas