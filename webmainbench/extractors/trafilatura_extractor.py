
"""
trafilatura extractor implementation.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .base import BaseExtractor, ExtractionResult
from .factory import extractor
from trafilatura import extract,html2txt
import re


@dataclass
class TrafilaturaInferenceConfig:
    """Configuration for Trafilatura extractor."""
    favor_precision: bool = True  # 优先精度：只提取最核心的内容，过滤更多冗余（如侧边栏、广告）,默认开启
    favor_recall: bool = True  # 优先召回：尽可能提取所有潜在有效内容，减少遗漏,默认开启
    include_comments: bool = False  # 是否保留评论,默认关闭
    include_tables: bool = True  # 是否保留提取html表格,默认开启
    include_images: bool = False  # 是否保留提取图片信息,默认开启
    include_links: bool = False  # 是否保留链接,默认关闭
    with_metadata: bool = False  # 是否保留元信息,默认关闭
    skip_elements: bool = False  # 是否保留CSS隐藏元素,默认关闭
    output_format: str = "markdown"  # 支持多种格式输出:"csv", "json", "html", "markdown", "txt", "xml"等


@extractor("trafilatura")
class TrafilaturaExtractor(BaseExtractor):
    """Extractor using Trafilatura."""

    version = "2.0.0"
    description = "Trafilatura based content extractor"

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.inference_config = TrafilaturaInferenceConfig()

        # 应用用户配置
        if config:
            for key, value in config.items():
                if hasattr(self.inference_config, key):
                    setattr(self.inference_config, key, value)

    def _setup(self) -> None:
        """Set up the Trafilatura extractor."""
        # 初始化操作
        pass

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        """
        Extract content using Trafilatura.

        Args:
            html: HTML content to extract from
            url: Optional URL of the page

        Returns:
            ExtractionResult instance
        """
        try:
            # 使用配置参数进行内容抽取
            content = extract(
                html,
                url=url,
                favor_precision=self.inference_config.favor_precision,
                favor_recall=self.inference_config.favor_recall,
                include_comments=self.inference_config.include_comments,
                include_tables=self.inference_config.include_tables,
                include_images=self.inference_config.include_images,
                include_links=self.inference_config.include_links,
                with_metadata=self.inference_config.with_metadata,
                output_format=self.inference_config.output_format  # 传入输出格式

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
                f"Trafilatura extraction failed: {str(e)}"
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
