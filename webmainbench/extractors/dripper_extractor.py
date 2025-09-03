"""
LLM-WebKit extractor implementation with advanced LLM inference.
"""

import json
import re
import time
from typing import Dict, Any, Optional, List

from dripper.api import Dripper
from dripper.base import DripperInput, DripperOutput
from .base import BaseExtractor, ExtractionResult
from .factory import extractor

from ..utils import HTML2TextWrapper



@extractor("dripper")
class DripperExtractor(BaseExtractor):
    """Extractor using dripper."""

    version = "1.0.0"
    description = "Extractor using dripper."


    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        # 先初始化inference_config，再调用父类初始化（因为父类会调用_setup()）
        self.dripper = Dripper(config)
        self.html2text = HTML2TextWrapper()

        # 现在可以安全地调用父类初始化（会调用_setup()）
        super().__init__(name, config)
    
    def _setup(self) -> None:
        self.dripper.get_llm()
        self.dripper.get_tokenizer()

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        """
        使用高级LLM推理提取内容.
        
        Args:
            html: HTML内容。如果配置了use_preprocessed_html=True，则由Evaluator传入预处理的HTML内容
            url: 可选的页面URL
            
        Returns:
            ExtractionResult实例
        """
        start_time = time.time()
        
        try:
            dripper_input = DripperInput(raw_html=html, url=url, case_id=None)
            dripper_output : DripperOutput = self.dripper.process([dripper_input])[0]
            
            main_html = dripper_output.main_html
            main_content = self.html2text(main_html, url)

            extraction_time = time.time() - start_time
            
            # 创建结果对象
            result = ExtractionResult(
                content=main_content,
                main_html=main_html,
                # content_list=content_list,
                title=self._extract_title(html),
                confidence_score=1.0,
                extraction_time=extraction_time,
                success=True
            )
            
            # 添加调试信息到错误消息字段（用于开发调试）
            return result
            
        except Exception as e:
            extraction_time = time.time() - start_time
            import traceback
            return ExtractionResult.create_error_result(
                f"LLM-WebKit extraction failed: {str(e)}",
                traceback.format_exc(),
                extraction_time
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
