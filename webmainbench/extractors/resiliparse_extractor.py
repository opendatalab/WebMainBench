"""
resiliparse extractor implementation.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .base import BaseExtractor, ExtractionResult
from .factory import extractor
from resiliparse.extract.html2text import extract_plain_text
import re

@dataclass
class ResiliparseInferenceConfig:
    """Configuration for Resiliparse extractor."""
    main_content: bool = True # 是否提取主要内容,默认开启.(丢弃<nav>（导航列表）、<footer>（版权信息) 、<aside>（侧边栏）、<footer>（页脚）等)
    alt_texts: bool = True  # 是否提取 <img> 的 alt 属性文本,默认开启
    links: bool = False  # 是否提取超链接,默认关闭
    form_fields: bool = False  # 是否提取表单控件,默认关闭
    noscript: bool = False  # 是否提取 <noscript> 标签的内容,默认关闭
    list_bullets: bool = True # 是否用 • 标记列表项,默认开启
    preserve_formatting: bool = True  ## 控制格式保留：True（默认）：保留列表、换行等基础格式,False：完全压缩（无换行、无列表，所有文本连在一起）
    comments: bool = True # 是否保留用户评论,默认开启
    post_meta: bool = True  # 是否保留文章元信息,默认开启
    hidden_elements: bool = False  # 是否保留CSS隐藏元素,默认关闭
    


    # 可根据需要添加更多resiliparse支持的参数


@extractor("resiliparse")
class ResiliparseExtractor(BaseExtractor):
    """Extractor using Resiliparse."""

    version = "0.14.5"
    description = "Resiliparse based content extractor"

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.inference_config = ResiliparseInferenceConfig()

        # 应用用户配置
        if config:
            for key, value in config.items():
                if hasattr(self.inference_config, key):
                    setattr(self.inference_config, key, value)

    def _setup(self) -> None:
        """Set up the Resiliparse extractor."""
        # 初始化操作
        pass

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        """
        Extract content using Resiliparse.

        Args:
            html: HTML content to extract from
            url: Optional URL of the page

        Returns:
            ExtractionResult instance
        """
        try:
            # 使用配置参数进行内容抽取
            content = extract_plain_text(
                html,
                main_content=self.inference_config.main_content,
                alt_texts=self.inference_config.alt_texts,
                links=self.inference_config.links,
                form_fields=self.inference_config.form_fields,
                noscript=self.inference_config.noscript,
                list_bullets=self.inference_config.list_bullets,
                preserve_formatting=self.inference_config.preserve_formatting,
                comments=self.inference_config.comments
            )

            # 创建 content_list（简单分割段落）
            content_list = []
            if content:
                paragraphs = content.split('\n\n')
                for i, para in enumerate(paragraphs):
                    if para.strip():
                        content_list.append({
                            "type": "paragraph",
                            "content": para.strip(),
                            "index": i
                        })

            return ExtractionResult(
                content=content,
                # content_list=content_list,
                title=self._extract_title(html),
                language=self._detect_language(content),
                success=True
            )

        except Exception as e:
            return ExtractionResult.create_error_result(
                f"Resiliparse extraction failed: {str(e)}"
            )

    def _extract_title(self, html: str) -> Optional[str]:
        """提取页面标题."""
        try:
            import re
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                return title_match.group(1).strip()
        except:
            pass
        return None

    def _detect_language(self, content: str) -> Optional[str]:
        """检测内容语言."""
        if not content:
            return None

        # 简单的语言检测逻辑
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))

        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > 0:
            return "en"
        else:
            return None

