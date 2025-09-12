"""
LLM-WebKit extractor implementation with advanced LLM inference.
"""

import json
import re
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import torch

from .base import BaseExtractor, ExtractionResult
from .factory import extractor


@dataclass
class LLMInferenceConfig:
    """Configuration for LLM inference."""
    model_path: str = "/path/to/your/model"
    use_logits_processor: bool = True
    max_tokens: int = 32768         # 最大输入token数
    temperature: float = 0.0
    top_p: float = 0.95
    max_output_tokens: int = 8192   # 最大输出token数
    tensor_parallel_size: int = 1   # 张量并行大小
    dtype: str = "bfloat16"         # 数据类型
    max_item_count: int = 1000      # 最大item数量
    gpu_memory_utilization: float = 0.8  # GPU内存利用率
    enforce_eager: bool = True      # 使用eager模式
    use_preprocessed_html: bool = False  # 是否使用预处理的HTML（跳过HTML简化步骤）
    preprocessed_html_field: str = "llm_webkit_html"  # 预处理HTML字段名


class TokenState(Enum):
    """Token states for JSON format enforcement."""
    Left_bracket = 0
    Right_bracket = 1
    Space_quote = 2
    Quote_colon_quote = 3
    Quote_comma = 4
    Main_other = 5
    Number = 6


class TokenStateManager:
    """Manages token states to ensure valid JSON output."""
    
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        token_id_map = {
            TokenState.Left_bracket: ["{"],
            TokenState.Right_bracket: ["}"],
            TokenState.Space_quote: [' "'],
            TokenState.Quote_colon_quote: ['":"'],
            TokenState.Quote_comma: ['",'],
            TokenState.Main_other: ["main", "other"],
            TokenState.Number: ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
        }
        self.token_id_map = {k: [self.tokenizer.encode(v)[0] for v in token_id_map[k]] for k in token_id_map}
    
    def mask_other_logits(self, logits: torch.Tensor, remained_ids: List[int]):
        """Mask logits to only allow specific token IDs."""
        remained_logits = {ids: logits[ids].item() for ids in remained_ids}
        new_logits = torch.ones_like(logits) * -float('inf')
        for id in remained_ids:
            new_logits[id] = remained_logits[id]
        return new_logits
        
    def calc_max_count(self, prompt_token_ids: List[int]):
        """Calculate maximum count of items from prompt."""
        pattern_list = [716, 1203, 842, 428]
        for idx in range(len(prompt_token_ids) - len(pattern_list), -1, -1):
            if all(prompt_token_ids[idx + i] == pattern_list[i] for i in range(len(pattern_list))):
                num_idx = idx + len(pattern_list)
                num_ids = []
                while num_idx < len(prompt_token_ids) and prompt_token_ids[num_idx] in self.token_id_map[TokenState.Number]:
                    num_ids.append(prompt_token_ids[num_idx])
                    num_idx += 1
                return int(self.tokenizer.decode(num_ids)) 
        return 1
        
    def find_last_complete_number(self, input_ids: List[int]):
        """Find the last complete number in input IDs."""
        if not input_ids:
            return -1, "null", -1
        
        tail_number_ids = []
        last_idx = len(input_ids) - 1
        while last_idx >= 0 and input_ids[last_idx] in self.token_id_map[TokenState.Number]:
            tail_number_ids.insert(0, input_ids[last_idx])
            last_idx -= 1
        
        tail_number = int(self.tokenizer.decode(tail_number_ids)) if tail_number_ids else -1
        
        while last_idx >= 0 and input_ids[last_idx] not in self.token_id_map[TokenState.Number]:
            last_idx -= 1
        
        if last_idx < 0:
            return tail_number, "tail", tail_number
        
        last_number_ids = []
        while last_idx >= 0 and input_ids[last_idx] in self.token_id_map[TokenState.Number]:
            last_number_ids.insert(0, input_ids[last_idx])
            last_idx -= 1
        
        last_number = int(self.tokenizer.decode(last_number_ids))
        
        if tail_number == last_number + 1:
            return tail_number, "tail", tail_number
        return last_number, "non_tail", tail_number
            
    def process_logit(self, prompt_token_ids: List[int], input_ids: List[int], logits: torch.Tensor):
        """Process logits to enforce JSON format."""
        if not input_ids:
            return self.mask_other_logits(logits, self.token_id_map[TokenState.Left_bracket])
        
        last_token = input_ids[-1]
        
        if last_token == self.token_id_map[TokenState.Right_bracket][0]:
            return self.mask_other_logits(logits, [151645])
        elif last_token == self.token_id_map[TokenState.Left_bracket][0]:
            return self.mask_other_logits(logits, self.token_id_map[TokenState.Space_quote])
        elif last_token == self.token_id_map[TokenState.Space_quote][0]:
            last_number, _, _ = self.find_last_complete_number(input_ids)
            if last_number == -1:
                next_char = '1'
            else:
                next_char = str(last_number + 1)[0]
            return self.mask_other_logits(logits, self.tokenizer.encode(next_char))
        elif last_token in self.token_id_map[TokenState.Number]:
            last_number, state, tail_number = self.find_last_complete_number(input_ids)
            if state == "tail":
                return self.mask_other_logits(logits, self.token_id_map[TokenState.Quote_colon_quote])
            else:
                next_str = str(last_number + 1)
                next_char = next_str[len(str(tail_number))]
                return self.mask_other_logits(logits, self.tokenizer.encode(next_char))
        elif last_token == self.token_id_map[TokenState.Quote_colon_quote][0]:
            return self.mask_other_logits(logits, self.token_id_map[TokenState.Main_other])
        elif last_token in self.token_id_map[TokenState.Main_other]:
            return self.mask_other_logits(logits, self.token_id_map[TokenState.Quote_comma])
        elif last_token == self.token_id_map[TokenState.Quote_comma][0]:
            last_number, _, _ = self.find_last_complete_number(input_ids)
            max_count = self.calc_max_count(prompt_token_ids)
            if last_number >= max_count:
                return self.mask_other_logits(logits, self.token_id_map[TokenState.Right_bracket])
            else:
                return self.mask_other_logits(logits, self.token_id_map[TokenState.Space_quote])
        
        return logits


@extractor("llm-webkit")
class LlmWebkitExtractor(BaseExtractor):
    """Advanced LLM-WebKit extractor with intelligent content classification."""
    
    version = "4.0.1"
    description = "Advanced LLM-WebKit extractor with intelligent content classification"
    
    # 分类提示模板
    CLASSIFICATION_PROMPT = """As a front-end engineering expert in HTML, your task is to analyze the given HTML structure and accurately classify elements with the _item_id attribute as either "main" (primary content) or "other" (supplementary content). Your goal is to precisely extract the primary content of the page, ensuring that only the most relevant information is labeled as "main" while excluding navigation, metadata, and other non-essential elements. 

Guidelines for Classification:

Primary Content ("main")
Elements that constitute the core content of the page should be classified as "main". These typically include:
✅ For Articles, News, and Blogs:
The main text body of the article, blog post, or news content.
Images embedded within the main content that contribute to the article.
✅ For Forums & Discussion Threads:
The original post in the thread.
Replies and discussions that are part of the main conversation.
✅ For Q&A Websites:
The question itself posted by a user.
Answers to the question and replies to answers that contribute to the discussion.
✅ For Other Content-Based Pages:
Any rich text, paragraphs, or media that serve as the primary focus of the page.

Supplementary Content ("other")
Elements that do not contribute to the primary content but serve as navigation, metadata, or supporting information should be classified as "other". These include:
❌ Navigation & UI Elements:
Menus, sidebars, footers, breadcrumbs, and pagination links.
"Skip to content" links and accessibility-related text.
❌ Metadata & User Information:
Article titles, author names, timestamps, and view counts.
Like counts, vote counts, and other engagement metrics.
❌ Advertisements & Promotional Content:
Any section labeled as "Advertisement" or "Sponsored".
Social media sharing buttons, follow prompts, and external links.
❌ Related & Suggested Content:
"Read More", "Next Article", "Trending Topics", and similar sections.
Lists of related articles, tags, and additional recommendations.

Task Instructions:
You will be provided with a simplified HTML structure containing elements with an _item_id attribute. Your job is to analyze each element's function and determine whether it should be classified as "main" or "other".

Response Format:
Return a JSON object where each key is the _item_id value, and the corresponding value is either "main" or "other", as in the following example:
{{"1": "other","2": "main","3": "other"}}

🚨 Important Notes:
Do not include any explanations in the output—only return the JSON.
Ensure high accuracy by carefully distinguishing between primary content and supplementary content.
Err on the side of caution—if an element seems uncertain, classify it as "other" unless it clearly belongs to the main content.

Input HTML:
{alg_html}

Output format should be a JSON-formatted string representing a dictionary where keys are item_id strings and values are either 'main' or 'other'. Make sure to include ALL item_ids from the input HTML."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        # 先初始化inference_config，再调用父类初始化（因为父类会调用_setup()）
        self.inference_config = LLMInferenceConfig()
        self.model = None
        self.tokenizer = None
        self.token_state_manager = None
        
        # Override config if provided
        if config:
            for key, value in config.items():
                if hasattr(self.inference_config, key):
                    setattr(self.inference_config, key, value)
        
        # 现在可以安全地调用父类初始化（会调用_setup()）
        super().__init__(name, config)
    
    def _setup(self) -> None:
        """Setup the LLM-WebKit extractor with advanced inference capabilities."""
        # 初始化模块引用
        self._simplify_html = None
        self._PreDataJson = None
        self._PreDataJsonKey = None
        self._MapItemToHtmlTagsParser = None
        self._SamplingParams = None
        self._model_loaded = False
        
        # 检查各个依赖模块的可用性
        missing_modules = []
        
        # 如果使用预处理HTML模式，只需要检查llm_web_kit的基础功能
        if self.inference_config.use_preprocessed_html:
            # 预处理HTML模式：只检查内容提取相关的依赖
            try:
                from llm_web_kit.main_html_parser.parser.tag_mapping import MapItemToHtmlTagsParser
                self._MapItemToHtmlTagsParser = MapItemToHtmlTagsParser
            except ImportError as e:
                missing_modules.append(f"llm_web_kit (content extraction): {e}")
            
            # 设置可用性标志（预处理模式下不需要LLM）
            self._transformers_available = False
            self._vllm_available = False
        else:
            # 标准模式：检查完整的依赖
            # 检查 llm_web_kit
            try:
                from llm_web_kit.main_html_parser.simplify_html.simplify_html import simplify_html
                from llm_web_kit.input.pre_data_json import PreDataJson, PreDataJsonKey
                from llm_web_kit.main_html_parser.parser.tag_mapping import MapItemToHtmlTagsParser
                
                self._simplify_html = simplify_html
                self._PreDataJson = PreDataJson
                self._PreDataJsonKey = PreDataJsonKey
                self._MapItemToHtmlTagsParser = MapItemToHtmlTagsParser
                
            except ImportError as e:
                missing_modules.append(f"llm_web_kit: {e}")
            
            # 检查 transformers（延迟到实际使用时）
            self._transformers_available = False
            try:
                import transformers
                self._transformers_available = True
            except ImportError as e:
                missing_modules.append(f"transformers: {e}")
            
            # 检查 vllm（延迟到实际使用时）
            self._vllm_available = False
            try:
                import vllm
                from vllm import SamplingParams
                self._SamplingParams = SamplingParams
                self._vllm_available = True
            except ImportError as e:
                missing_modules.append(f"vllm: {e}")
        
        # 如果关键模块缺失，提供详细的错误信息
        if missing_modules:
            if self.inference_config.use_preprocessed_html:
                error_msg = "LLM-WebKit extractor (preprocessed HTML mode) requires:\n"
                error_msg += "\n".join([f"  • {module}" for module in missing_modules])
                error_msg += "\n\nTo install dependencies:\n"
                error_msg += "  pip install llm_web_kit"
            else:
                error_msg = "LLM-WebKit extractor requires additional dependencies:\n"
                error_msg += "\n".join([f"  • {module}" for module in missing_modules])
                error_msg += "\n\nTo install dependencies:\n"
                error_msg += "  pip install llm_web_kit transformers vllm torch\n"
                error_msg += "\nFor CPU-only usage (limited functionality):\n"
                error_msg += "  pip install llm_web_kit transformers torch --index-url https://download.pytorch.org/whl/cpu"
            
            raise RuntimeError(error_msg)
    
    def _load_model(self):
        """延迟加载LLM模型和tokenizer."""
        if self._model_loaded:
            return
        
        # 检查依赖是否可用
        if not self._transformers_available:
            raise RuntimeError("transformers library is not available. Please install it: pip install transformers")
        
        import torch
        
        # 检测运行环境
        is_apple_silicon = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        has_cuda = torch.cuda.is_available()
        
        print(f"🔍 检测到运行环境:")
        print(f"   CUDA: {has_cuda}")
        print(f"   Apple Silicon (MPS): {is_apple_silicon}")
        
        # 对于Apple Silicon，优先使用transformers而不是vLLM（避免兼容性问题）
        if is_apple_silicon and not has_cuda:
            print("🍎 Apple Silicon环境检测到，使用transformers模式以避免vLLM兼容性问题")
            self._load_transformers_model()
        else:
            # 其他环境尝试使用vLLM
            if not self._vllm_available:
                print("⚠️  vLLM不可用，回退到transformers模式")
                self._load_transformers_model()
            else:
                self._load_vllm_model()
    
    def _load_transformers_model(self):
        """使用transformers加载模型（兼容性更好）"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            print(f"📦 使用transformers加载模型: {self.inference_config.model_path}")
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.inference_config.model_path, 
                trust_remote_code=True
            )
            
            # 设置设备
            if torch.cuda.is_available():
                device = "cuda"
                torch_dtype = torch.bfloat16 if self.inference_config.dtype == "bfloat16" else torch.float16
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"
                torch_dtype = torch.float16  # MPS目前不支持bfloat16
            else:
                device = "cpu"
                torch_dtype = torch.float32
            
            print(f"🎯 使用设备: {device}, 数据类型: {torch_dtype}")
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.inference_config.model_path,
                trust_remote_code=True,
                torch_dtype=torch_dtype,
                device_map=device if device != "mps" else None  # MPS不支持device_map
            )
            
            if device == "mps":
                self.model = self.model.to(device)
            
            self.model.eval()
            
            # 标记为transformers模式
            self._use_transformers = True
            self._model_loaded = True
            
            print("✅ transformers模型加载成功!")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load transformers model: {e}")
    
    def _load_vllm_model(self):
        """使用vLLM加载模型（高性能但兼容性要求高）"""
        try:
            from transformers import AutoTokenizer
            from vllm import LLM
            
            print(f"⚡ 使用vLLM加载模型: {self.inference_config.model_path}")
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.inference_config.model_path, 
                trust_remote_code=True
            )
            
            # vLLM配置 - 参考ray_test_qa.py的简化配置
            model_kwargs = {
                "model": self.inference_config.model_path,
                "trust_remote_code": True,
                "dtype": self.inference_config.dtype,
                "tensor_parallel_size": self.inference_config.tensor_parallel_size,
            }
            
            print(f"🔧 vLLM配置: {model_kwargs}")
            
            self.model = LLM(**model_kwargs)
            
            # 初始化token状态管理器
            if self.inference_config.use_logits_processor:
                self.token_state_manager = TokenStateManager(self.tokenizer)
            
            # 标记为vLLM模式
            self._use_transformers = False
            self._model_loaded = True
            
            print("✅ vLLM模型加载成功!")
            
        except Exception as e:
            print(f"❌ vLLM加载失败: {e}")
            raise RuntimeError(f"vLLM模型加载失败: {e}")
    
    def _create_prompt(self, simplified_html: str) -> str:
        """创建分类提示."""
        return self.CLASSIFICATION_PROMPT.format(alg_html=simplified_html)
    
    def _add_template(self, prompt: str) -> str:
        """添加聊天模板."""
        messages = [
            {"role": "user", "content": prompt}
        ]
        chat_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True
        )
        return chat_prompt
    
    def _generate_with_transformers(self, prompt: str) -> str:
        """使用transformers生成文本"""
        try:
            import torch
            
            # Tokenize输入
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.inference_config.max_tokens)
            
            # 移动到正确的设备
            device = self.model.device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # 生成配置
            generation_config = {
                "max_new_tokens": self.inference_config.max_output_tokens,
                "temperature": self.inference_config.temperature,
                "top_p": self.inference_config.top_p,
                "do_sample": self.inference_config.temperature > 0,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }
            
            print(f"🔄 开始生成文本 (max_new_tokens: {generation_config['max_new_tokens']})")
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **generation_config
                )
            
            # 解码输出（只取新生成的部分）
            input_length = inputs['input_ids'].shape[1]
            generated_ids = outputs[0][input_length:]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            print(f"✅ 生成完成，输出长度: {len(generated_text)}")
            print(f"🔍 LLM原始输出: {repr(generated_text[:200])}")  # 显示前200字符用于调试
            
            # 提取JSON部分
            json_result = self._extract_json_from_text(generated_text)
            print(f"🔍 提取的JSON: {repr(json_result[:200])}")  # 显示JSON结果
            return json_result
            
        except Exception as e:
            print(f"⚠️  transformers生成失败: {e}")
            raise RuntimeError(f"transformers生成失败: {e}")
    
    def _extract_json_from_text(self, text: str) -> str:
        """从生成的文本中提取JSON"""
        # 查找JSON部分
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = text[start_idx:end_idx]
            # 清理JSON
            json_str = json_str.strip()
            json_str = re.sub(r',\s*}', '}', json_str)
            try:
                # 验证JSON
                json.loads(json_str)
                return json_str
            except:
                pass
        
        return "{}"

    def _clean_output(self, output) -> str:
        """清理LLM输出，提取JSON."""
        prediction = output[0].outputs[0].text
        
        # 提取JSON
        start_idx = prediction.rfind("{")
        end_idx = prediction.rfind("}") + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = prediction[start_idx:end_idx]
            json_str = re.sub(r',\s*}', '}', json_str)  # 清理JSON
            try:
                json.loads(json_str)  # 验证
                return json_str
            except:
                return "{}"
        else:
            return "{}"
    
    def _reformat_classification_result(self, json_str: str) -> Dict[str, int]:
        """重新格式化分类结果."""
        try:
            data = json.loads(json_str)
            return {"item_id " + k: 1 if v == "main" else 0 for k, v in data.items()}
        except json.JSONDecodeError:
            return {}
    
    def _reconstruct_content(self, original_html: str, classification_result: Dict[str, int], url: str = None) -> tuple:
        """根据分类结果重建主要内容."""
        try:
            # 按照ray_test_qa.py的正确流程
            # 第一步：使用MapItemToHtmlTagsParser生成main_html
            main_html = self._generate_main_html_with_parser(original_html, classification_result)
            print(f"🔧 MapItemToHtmlTagsParser生成的main_html长度: {len(main_html)}")
            
            if not main_html.strip():
                print("⚠️  没有生成main_html，返回空结果")
                return "", []
            
            # 第二步：使用llm-webkit的方法将main_html提取成content，传入URL
            content, content_list = self._extract_content_from_main_html(main_html, url)
            print(f"✅ content提取成功: {len(content)}字符, {len(content_list)}个内容块")
            
            return content, content_list
            
        except Exception as e:
            print(f"❌ Content reconstruction failed: {e}")
            return "", []
    
    def _generate_main_html_with_parser(self, original_html: str, classification_result: Dict[str, int]) -> str:
        """使用MapItemToHtmlTagsParser生成main_html（按照ray_test_qa.py的流程）"""
        try:
            # 获取typical_raw_tag_html (简化的HTML)
            simplified_html, typical_raw_tag_html, _ = self._simplify_html(original_html)
            print(f"🔧 simplified HTML长度: {len(simplified_html)}")
            print(f"🔧 typical_raw_tag_html长度: {len(typical_raw_tag_html)}")
            
            # 按照ray_test_qa.py的流程
            pre_data = self._PreDataJson({})
            pre_data[self._PreDataJsonKey.LLM_RESPONSE] = classification_result
            pre_data[self._PreDataJsonKey.TYPICAL_RAW_HTML] = original_html
            pre_data[self._PreDataJsonKey.TYPICAL_RAW_TAG_HTML] = typical_raw_tag_html
            
            print(f"🔧 PreDataJson设置完成，开始解析...")
            
            # 使用MapItemToHtmlTagsParser解析
            parser = self._MapItemToHtmlTagsParser({})
            pre_data = parser.parse_single(pre_data)
            
            # 获取生成的main_html
            main_html = pre_data.get(self._PreDataJsonKey.TYPICAL_MAIN_HTML, "")
            
            print(f"✅ MapItemToHtmlTagsParser完成，main_html长度: {len(main_html)}")
            return main_html
            
        except Exception as e:
            print(f"❌ MapItemToHtmlTagsParser失败: {e}")
            return ""
    
    def _extract_content_from_main_html(self, main_html: str, url: str = None) -> tuple:
        """使用llm-webkit的方法将main_html提取成content"""
        import traceback
        try:
            from llm_web_kit.simple import extract_content_from_main_html
            
            print(f"🔧 开始使用llm-webkit简单接口提取content...")
            
            # 使用简单接口提取markdown，传入URL
            content = extract_content_from_main_html(url or "", main_html)
            
            print(f"✅ llm-webkit提取完成: {len(content)}字符")
            
            # 暂不构建content_list，直接返回空列表
            return content.strip(), []
            
        except Exception as e:
            print(f"❌ llm-webkit提取失败: {e}")
            print(f"❌ 错误详情: {traceback.format_exc()}")
            raise RuntimeError(f"llm-webkit提取失败: {str(e)}") from e


    def extract(self, html_or_sample, url: str = None) -> ExtractionResult:
        """
        重写extract方法以支持预处理HTML模式
        
        Args:
            html_or_sample: HTML字符串或DataSample对象
            url: 可选的页面URL
            
        Returns:
            ExtractionResult实例
        """
        # 判断输入类型
        if type(html_or_sample).__name__ == 'DataSample':  # 这是一个DataSample对象
            sample = html_or_sample
            
            # 检查是否使用预处理的HTML
            try:
                if self.inference_config.use_preprocessed_html:
                    preprocessed_field = self.inference_config.preprocessed_html_field
                    
                    # 从sample中获取预处理的HTML内容
                    if hasattr(sample, preprocessed_field):
                        preprocessed_html = getattr(sample, preprocessed_field)
                        print(f"📥 使用预处理HTML字段: {preprocessed_field}")
                        return super().extract(preprocessed_html, sample.url)
            except Exception as e:
                return ExtractionResult.create_error_result(
                    f"访问预处理HTML字段 {preprocessed_field} 时发生异常: {str(e)}"
                )
        else:
            # 这是普通的HTML字符串，使用标准处理
            return super().extract(html_or_sample, url)

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
            # 检查是否使用预处理的HTML（跳过HTML简化步骤）
            if self.inference_config.use_preprocessed_html:
                # 传入的html已经是预处理的内容（由Evaluator从指定字段提取），直接用作main_html
                print(f"📥 使用预处理HTML，跳过HTML简化步骤")
                content, content_list = self._extract_content_from_main_html(html, url)
                
                extraction_time = time.time() - start_time
                
                # 创建结果对象
                result = ExtractionResult(
                    content=content,
                    # content_list=content_list,
                    title=self._extract_title(html),  # 从主内容提取标题
                    language=self._detect_language(content),
                    confidence_score=0.9,  # 预处理HTML的置信度设为0.9
                    extraction_time=extraction_time,
                    success=True
                )
                
                return result
            
            # 标准流程：HTML简化 + LLM推理
            # 步骤1: HTML简化处理
            simplified_html, typical_raw_tag_html, _ = self._simplify_html(html)
            
            # 步骤2: 检查长度限制
            item_count = simplified_html.count('_item_id')
            if item_count > self.inference_config.max_item_count:
                return ExtractionResult.create_error_result(
                    f"HTML too complex: {item_count} items > {self.inference_config.max_item_count} limit"
                )
            
            if item_count == 0:
                return ExtractionResult.create_error_result("No _item_id found in simplified HTML")
            
            # 步骤3: 延迟加载模型
            self._load_model()
            
            # 步骤4: 创建提示并进行LLM推理
            prompt = self._create_prompt(simplified_html)
            chat_prompt = self._add_template(prompt)
            
            # 配置采样参数
            if self.inference_config.use_logits_processor and self.token_state_manager:
                sampling_params = self._SamplingParams(
                    temperature=self.inference_config.temperature,
                    top_p=self.inference_config.top_p,
                    max_tokens=self.inference_config.max_output_tokens,
                    logits_processors=[self.token_state_manager.process_logit]
                )
            else:
                sampling_params = self._SamplingParams(
                    temperature=self.inference_config.temperature,
                    top_p=self.inference_config.top_p,
                    max_tokens=self.inference_config.max_output_tokens
                )
            
            # 根据模型类型选择生成方式
            if hasattr(self, '_use_transformers') and self._use_transformers:
                # 使用transformers生成
                json_result = self._generate_with_transformers(chat_prompt)
            else:
                # 使用vLLM生成
                output = self.model.generate(chat_prompt, sampling_params)
                json_result = self._clean_output(output)
            
            # 步骤5: 格式转换和内容重建
            print(f"🔄 开始格式转换...")
            classification_result = self._reformat_classification_result(json_result)
            print(f"🔍 格式转换结果: {len(classification_result)} 个分类项")
            
            print(f"🔄 开始重建内容...")
            main_content, content_list = self._reconstruct_content(html, classification_result, url)
            print(f"🔍 重建结果: 主内容长度={len(main_content)}, 内容块数量={len(content_list) if content_list else 0}")
            
            # 计算置信度
            confidence = self._calculate_confidence(main_content, content_list, item_count)
            
            extraction_time = time.time() - start_time
            
            # 创建结果对象
            result = ExtractionResult(
                content=main_content,
                # content_list=content_list,
                title=self._extract_title(html),
                language=self._detect_language(main_content),
                confidence_score=confidence,
                extraction_time=extraction_time,
                success=True
            )
            
            # 添加调试信息到错误消息字段（用于开发调试）
            debug_info = f"item_count: {item_count}, llm_output_length: {len(json_result)}"
            if not result.success:
                result.error_message = f"{result.error_message or ''} | {debug_info}".strip(' |')
            
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
    
    def _calculate_confidence(self, content: str, content_list: List[Dict], item_count: int) -> float:
        """计算提取置信度."""
        if not content:
            return 0.0
        
        # 基于内容长度的评分
        length_score = min(len(content) / 1000, 1.0)
        
        # 基于结构化内容的评分
        structure_score = min(len(content_list) / 10, 1.0) if content_list else 0.0
        
        # 基于处理复杂度的评分（item数量越多，置信度稍微降低）
        complexity_penalty = max(0, (item_count - 100) / 900)  # 100-1000范围内线性降低
        complexity_score = max(0.5, 1.0 - complexity_penalty)
        
        # 综合评分
        confidence = (length_score * 0.5 + structure_score * 0.3 + complexity_score * 0.2)
        return min(confidence, 1.0) 