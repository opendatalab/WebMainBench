from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os
import hashlib
import json
from openai import OpenAI


class BaseContentSplitter(ABC):
    """抽象基类，用于从文本中提取特定类型的内容"""

    # 默认的LLM提示词模板
    DEFAULT_LLM_PROMPT = """请处理以下内容：
    {content}
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化提取器"""
        self.config = config or {}

        # 保留这行代码，用于控制是否使用LLM
        self.use_llm = self.config.get('use_llm', True)

        # 初始化OpenAI客户端（如果配置了LLM）
        if self.use_llm and self.config.get('llm_base_url') and self.config.get('llm_api_key'):
            self.client = OpenAI(
                base_url=self.config.get('llm_base_url', ""),
                api_key=self.config.get('llm_api_key', "")
            )
        else:
            self.client = None

        self.cache_dir = self.config.get('cache_dir',
                                         os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                      '.cache'))
        os.makedirs(self.cache_dir, exist_ok=True)

    @abstractmethod
    def extract(self, text: str, field_name: str = None) -> str:
        """提取特定类型的内容"""
        pass

    @abstractmethod
    def extract_basic(self, text: str) -> List[str]:
        """使用基本方法提取内容（通常是正则表达式）"""
        pass

    def should_use_llm(self, field_name: str) -> bool:
        """判断是否应该使用LLM进行增强提取"""
        if not self.use_llm:
            return False

        # 默认逻辑：对groundtruth内容不使用LLM，对其他内容使用
        if field_name == "groundtruth_content":
            print(f"[DEBUG] 检测到groundtruth内容，不使用LLM")
            return False
        return True

    def enhance_with_llm(self, basic_results: List[str], cache_key: str = None) -> List[str]:
        """使用LLM增强基本提取结果"""
        if not basic_results:
            print(f"[DEBUG] 输入内容为空，跳过LLM增强")
            return []

        # 生成缓存键
        if cache_key is None:
            content_str = '\n'.join(basic_results)
            cache_key = hashlib.md5(content_str.encode('utf-8')).hexdigest()

        cache_file = os.path.join(self.cache_dir, f'{self.__class__.__name__.lower()}_cache_{cache_key}.json')

        # 检查缓存
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_result = json.load(f)
                    print(f"[DEBUG] 从缓存加载LLM增强结果: {len(cached_result)} 个")
                    return cached_result
            except Exception as e:
                print(f"[DEBUG] 缓存读取失败: {e}")

        # 实际的LLM增强逻辑
        try:
            enhanced_results = self._llm_enhance(basic_results)

            # 保存缓存
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_results, f, ensure_ascii=False, indent=2)
                print(f"[DEBUG] LLM增强结果已缓存到: {cache_file}")
            except Exception as e:
                print(f"[DEBUG] 缓存保存失败: {e}")

            return enhanced_results
        except Exception as e:
            print(f"[DEBUG] LLM增强失败: {type(e).__name__}: {e}")
            return basic_results

    @abstractmethod
    def _llm_enhance(self, basic_results: List[str]) -> List[str]:
        """使用LLM增强基本提取结果的具体实现"""
        pass
