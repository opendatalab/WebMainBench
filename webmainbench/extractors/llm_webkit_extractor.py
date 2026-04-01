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
    max_tokens: int = 32768         # Maximum input token count
    temperature: float = 0.0
    top_p: float = 0.95
    max_output_tokens: int = 8192   # Maximum output token count
    tensor_parallel_size: int = 1   # Tensor parallel size
    dtype: str = "bfloat16"         # Data type
    max_item_count: int = 1000      # Maximum item count
    gpu_memory_utilization: float = 0.8  # GPU memory utilization
    enforce_eager: bool = True      # Use eager mode
    use_preprocessed_html: bool = False  # Whether to use preprocessed HTML (skip HTML simplification step)
    preprocessed_html_field: str = "llm_webkit_html"  # Preprocessed HTML field name


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
    
    # Classification prompt template
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
        # Initialize inference_config first, then call parent initialization (since parent calls _setup())
        self.inference_config = LLMInferenceConfig()
        self.model = None
        self.tokenizer = None
        self.token_state_manager = None
        
        # Override config if provided
        if config:
            for key, value in config.items():
                if hasattr(self.inference_config, key):
                    setattr(self.inference_config, key, value)
        
        # Now it is safe to call parent initialization (which calls _setup())
        super().__init__(name, config)

    def _setup(self) -> None:
        """Setup the LLM-WebKit extractor with advanced inference capabilities."""
        # Initialize module references
        self._simplify_html = None
        self._PreDataJson = None
        self._PreDataJsonKey = None
        self._MapItemToHtmlTagsParser = None
        self._SamplingParams = None
        self._model_loaded = False

        # Check availability of each dependency module
        missing_modules = []

        # If using preprocessed HTML mode, only need to check llm_web_kit basic functionality
        if self.inference_config.use_preprocessed_html:
            # Preprocessed HTML mode: only check content extraction related dependencies
            try:
                from llm_web_kit.main_html_parser.parser.tag_mapping import MapItemToHtmlTagsParser
                self._MapItemToHtmlTagsParser = MapItemToHtmlTagsParser
            except ImportError as e:
                missing_modules.append(f"llm_web_kit (content extraction): {e}")
            
            # Set availability flags (LLM not required in preprocessed mode)
            self._transformers_available = False
            self._vllm_available = False
        else:
            # Standard mode: check full dependencies
            # Check llm_web_kit
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
            
            # Check transformers (deferred until actual use)
            self._transformers_available = False
            try:
                import transformers
                self._transformers_available = True
            except ImportError as e:
                missing_modules.append(f"transformers: {e}")

            # Check vllm (deferred until actual use)
            self._vllm_available = False
            try:
                import vllm
                from vllm import SamplingParams
                self._SamplingParams = SamplingParams
                self._vllm_available = True
            except ImportError as e:
                missing_modules.append(f"vllm: {e}")
        
        # If critical modules are missing, provide detailed error messages
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
        """Lazily load the LLM model and tokenizer."""
        if self._model_loaded:
            return

        # Check if dependencies are available
        if not self._transformers_available:
            raise RuntimeError("transformers library is not available. Please install it: pip install transformers")
        
        import torch

        # Detect runtime environment
        is_apple_silicon = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        has_cuda = torch.cuda.is_available()

        print(f"Detected runtime environment:")
        print(f"   CUDA: {has_cuda}")
        print(f"   Apple Silicon (MPS): {is_apple_silicon}")

        # For Apple Silicon, prefer transformers over vLLM (to avoid compatibility issues)
        if is_apple_silicon and not has_cuda:
            print("Apple Silicon environment detected, using transformers mode to avoid vLLM compatibility issues")
            self._load_transformers_model()
        else:
            # Other environments: attempt to use vLLM
            if not self._vllm_available:
                print("vLLM not available, falling back to transformers mode")
                self._load_transformers_model()
            else:
                self._load_vllm_model()
    
    def _load_transformers_model(self):
        """Load model using transformers (better compatibility)."""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            print(f"Loading model with transformers: {self.inference_config.model_path}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.inference_config.model_path, 
                trust_remote_code=True
            )
            
            # Set device
            if torch.cuda.is_available():
                device = "cuda"
                torch_dtype = torch.bfloat16 if self.inference_config.dtype == "bfloat16" else torch.float16
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"
                torch_dtype = torch.float16  # MPS does not currently support bfloat16
            else:
                device = "cpu"
                torch_dtype = torch.float32

            print(f"Using device: {device}, dtype: {torch_dtype}")

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.inference_config.model_path,
                trust_remote_code=True,
                torch_dtype=torch_dtype,
                device_map=device if device != "mps" else None  # MPS does not support device_map
            )
            
            if device == "mps":
                self.model = self.model.to(device)
            
            self.model.eval()

            # Mark as transformers mode
            self._use_transformers = True
            self._model_loaded = True

            print("Transformers model loaded successfully!")

        except Exception as e:
            raise RuntimeError(f"Failed to load transformers model: {e}")

    def _load_vllm_model(self):
        """Load model using vLLM (high performance but strict compatibility requirements)."""
        try:
            from transformers import AutoTokenizer
            from vllm import LLM

            print(f"Loading model with vLLM: {self.inference_config.model_path}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.inference_config.model_path, 
                trust_remote_code=True
            )
            
            # vLLM configuration - simplified config based on ray_test_qa.py
            model_kwargs = {
                "model": self.inference_config.model_path,
                "trust_remote_code": True,
                "dtype": self.inference_config.dtype,
                "tensor_parallel_size": self.inference_config.tensor_parallel_size,
            }
            
            print(f"vLLM configuration: {model_kwargs}")

            self.model = LLM(**model_kwargs)

            # Initialize token state manager
            if self.inference_config.use_logits_processor:
                self.token_state_manager = TokenStateManager(self.tokenizer)

            # Mark as vLLM mode
            self._use_transformers = False
            self._model_loaded = True

            print("vLLM model loaded successfully!")

        except Exception as e:
            print(f"vLLM loading failed: {e}")
            raise RuntimeError(f"vLLM model loading failed: {e}")
    
    def _create_prompt(self, simplified_html: str) -> str:
        """Create the classification prompt."""
        return self.CLASSIFICATION_PROMPT.format(alg_html=simplified_html)

    def _add_template(self, prompt: str) -> str:
        """Add the chat template."""
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
        """Generate text using transformers."""
        try:
            import torch

            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.inference_config.max_tokens)
            
            # Move to the correct device
            device = self.model.device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Generation configuration
            generation_config = {
                "max_new_tokens": self.inference_config.max_output_tokens,
                "temperature": self.inference_config.temperature,
                "top_p": self.inference_config.top_p,
                "do_sample": self.inference_config.temperature > 0,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }
            
            print(f"Starting text generation (max_new_tokens: {generation_config['max_new_tokens']})")

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **generation_config
                )
            
            # Decode output (only take newly generated portion)
            input_length = inputs['input_ids'].shape[1]
            generated_ids = outputs[0][input_length:]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            print(f"Generation complete, output length: {len(generated_text)}")
            print(f"LLM raw output: {repr(generated_text[:200])}")  # Show first 200 chars for debugging

            # Extract JSON part
            json_result = self._extract_json_from_text(generated_text)
            print(f"Extracted JSON: {repr(json_result[:200])}")  # Show JSON result
            return json_result

        except Exception as e:
            print(f"transformers generation failed: {e}")
            raise RuntimeError(f"transformers generation failed: {e}")
    
    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from generated text."""
        # Find JSON portion
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1

        if start_idx != -1 and end_idx != 0:
            json_str = text[start_idx:end_idx]
            # Clean up JSON
            json_str = json_str.strip()
            json_str = re.sub(r',\s*}', '}', json_str)
            try:
                # Validate JSON
                json.loads(json_str)
                return json_str
            except:
                pass

        return "{}"

    def _clean_output(self, output) -> str:
        """Clean LLM output and extract JSON."""
        prediction = output[0].outputs[0].text

        # Extract JSON
        start_idx = prediction.rfind("{")
        end_idx = prediction.rfind("}") + 1

        if start_idx != -1 and end_idx != -1:
            json_str = prediction[start_idx:end_idx]
            json_str = re.sub(r',\s*}', '}', json_str)  # Clean up JSON
            try:
                json.loads(json_str)  # Validate
                return json_str
            except:
                return "{}"
        else:
            return "{}"

    def _reformat_classification_result(self, json_str: str) -> Dict[str, int]:
        """Reformat classification result."""
        try:
            data = json.loads(json_str)
            return {"item_id " + k: 1 if v == "main" else 0 for k, v in data.items()}
        except json.JSONDecodeError:
            return {}
    
    def _reconstruct_content(self, original_html: str, classification_result: Dict[str, int], url: str = None) -> tuple:
        """Reconstruct main content based on classification results."""
        try:
            # Follow the correct flow from ray_test_qa.py
            # Step 1: Use MapItemToHtmlTagsParser to generate main_html
            main_html = self._generate_main_html_with_parser(original_html, classification_result)
            print(f"MapItemToHtmlTagsParser generated main_html length: {len(main_html)}")

            if not main_html.strip():
                print("No main_html generated, returning empty result")
                return "", []

            # Step 2: Use llm-webkit method to extract content from main_html, pass in URL
            content, content_list = self._extract_content_from_main_html(main_html, url)
            print(f"Content extraction successful: {len(content)} chars, {len(content_list)} content blocks")
            
            return content, content_list
            
        except Exception as e:
            print(f"❌ Content reconstruction failed: {e}")
            return "", []
    
    def _generate_main_html_with_parser(self, original_html: str, classification_result: Dict[str, int]) -> str:
        """Generate main_html using MapItemToHtmlTagsParser (following ray_test_qa.py flow)."""
        try:
            # Get typical_raw_tag_html (simplified HTML)
            simplified_html, typical_raw_tag_html, _ = self._simplify_html(original_html)
            print(f"Simplified HTML length: {len(simplified_html)}")
            print(f"typical_raw_tag_html length: {len(typical_raw_tag_html)}")

            # Follow the flow from ray_test_qa.py
            pre_data = self._PreDataJson({})
            pre_data[self._PreDataJsonKey.LLM_RESPONSE] = classification_result
            pre_data[self._PreDataJsonKey.TYPICAL_RAW_HTML] = original_html
            pre_data[self._PreDataJsonKey.TYPICAL_RAW_TAG_HTML] = typical_raw_tag_html

            print(f"PreDataJson setup complete, starting parsing...")

            # Parse using MapItemToHtmlTagsParser
            parser = self._MapItemToHtmlTagsParser({})
            pre_data = parser.parse_single(pre_data)

            # Get generated main_html
            main_html = pre_data.get(self._PreDataJsonKey.TYPICAL_MAIN_HTML, "")

            print(f"MapItemToHtmlTagsParser complete, main_html length: {len(main_html)}")
            return main_html

        except Exception as e:
            print(f"MapItemToHtmlTagsParser failed: {e}")
            return ""

    def _extract_content_from_main_html(self, main_html: str, url: str = None) -> tuple:
        """Extract content from main_html using llm-webkit method."""
        import traceback
        try:
            from llm_web_kit.simple import extract_content_from_main_html

            print(f"Starting content extraction using llm-webkit simple interface...")

            # Use simple interface to extract markdown, pass in URL
            content = extract_content_from_main_html(url or "", main_html)

            print(f"llm-webkit extraction complete: {len(content)} chars")

            # content_list construction deferred; return empty list for now
            return content.strip(), []

        except Exception as e:
            print(f"llm-webkit extraction failed: {e}")
            print(f"Error details: {traceback.format_exc()}")
            raise RuntimeError(f"llm-webkit extraction failed: {str(e)}") from e


    def extract(self, html_or_sample, url: str = None) -> ExtractionResult:
        """
        Override extract method to support preprocessed HTML mode.

        Args:
            html_or_sample: HTML string or DataSample object
            url: Optional page URL

        Returns:
            ExtractionResult instance
        """
        # Determine input type
        if type(html_or_sample).__name__ == 'DataSample':  # This is a DataSample object
            sample = html_or_sample

            # Check whether to use preprocessed HTML
            try:
                if self.inference_config.use_preprocessed_html:
                    preprocessed_field = self.inference_config.preprocessed_html_field

                    # Get preprocessed HTML content from sample
                    if hasattr(sample, preprocessed_field):
                        preprocessed_html = getattr(sample, preprocessed_field)
                        print(f"Using preprocessed HTML field: {preprocessed_field}")
                        return super().extract(preprocessed_html, sample.url)
            except Exception as e:
                return ExtractionResult.create_error_result(
                    f"Exception while accessing preprocessed HTML field {preprocessed_field}: {str(e)}"
                )
        else:
            # This is a plain HTML string, use standard processing
            return super().extract(html_or_sample, url)

    def _extract_content(self, html: str, url: str = None) -> ExtractionResult:
        """
        Extract content using advanced LLM inference.

        Args:
            html: HTML content. If use_preprocessed_html=True is configured, the Evaluator passes in preprocessed HTML content.
            url: Optional page URL

        Returns:
            ExtractionResult instance
        """
        start_time = time.time()

        try:
            # Check whether to use preprocessed HTML (skip HTML simplification step)
            if self.inference_config.use_preprocessed_html:
                # The passed-in html is already preprocessed content (extracted from the specified field by Evaluator), use it directly as main_html
                print(f"Using preprocessed HTML, skipping HTML simplification step")
                content, content_list = self._extract_content_from_main_html(html, url)
                
                extraction_time = time.time() - start_time

                # Create result object
                result = ExtractionResult(
                    content=content,
                    # content_list=content_list,
                    title=self._extract_title(html),  # Extract title from main content
                    language=self._detect_language(content),
                    confidence_score=0.9,  # Confidence score for preprocessed HTML is set to 0.9
                    extraction_time=extraction_time,
                    success=True
                )

                return result

            # Standard flow: HTML simplification + LLM inference
            # Step 1: HTML simplification
            simplified_html, typical_raw_tag_html, _ = self._simplify_html(html)

            # Step 2: Check length limit
            item_count = simplified_html.count('_item_id')
            if item_count > self.inference_config.max_item_count:
                return ExtractionResult.create_error_result(
                    f"HTML too complex: {item_count} items > {self.inference_config.max_item_count} limit"
                )
            
            if item_count == 0:
                return ExtractionResult.create_error_result("No _item_id found in simplified HTML")
            
            # Step 3: Lazy load model
            self._load_model()

            # Step 4: Create prompt and perform LLM inference
            prompt = self._create_prompt(simplified_html)
            chat_prompt = self._add_template(prompt)

            # Configure sampling parameters
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
            
            # Choose generation method based on model type
            if hasattr(self, '_use_transformers') and self._use_transformers:
                # Use transformers for generation
                json_result = self._generate_with_transformers(chat_prompt)
            else:
                # Use vLLM for generation
                output = self.model.generate(chat_prompt, sampling_params)
                json_result = self._clean_output(output)

            # Step 5: Format conversion and content reconstruction
            print(f"Starting format conversion...")
            classification_result = self._reformat_classification_result(json_result)
            print(f"Format conversion result: {len(classification_result)} classification items")

            print(f"Starting content reconstruction...")
            main_content, content_list = self._reconstruct_content(html, classification_result, url)
            print(f"Reconstruction result: main content length={len(main_content)}, content block count={len(content_list) if content_list else 0}")
            
            # Calculate confidence
            confidence = self._calculate_confidence(main_content, content_list, item_count)
            
            extraction_time = time.time() - start_time

            # Create result object
            result = ExtractionResult(
                content=main_content,
                # content_list=content_list,
                title=self._extract_title(html),
                language=self._detect_language(main_content),
                confidence_score=confidence,
                extraction_time=extraction_time,
                success=True
            )

            # Add debug info to error message field (for development debugging)
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
        """Extract page title."""
        try:
            import re
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                return title_match.group(1).strip()
        except:
            pass
        return None
    
    def _detect_language(self, content: str) -> Optional[str]:
        """Detect content language."""
        if not content:
            return None

        # Simple language detection logic
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        
        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > 0:
            return "en"
        else:
            return None
    
    def _calculate_confidence(self, content: str, content_list: List[Dict], item_count: int) -> float:
        """Calculate extraction confidence."""
        if not content:
            return 0.0

        # Score based on content length
        length_score = min(len(content) / 1000, 1.0)

        # Score based on structured content
        structure_score = min(len(content_list) / 10, 1.0) if content_list else 0.0

        # Score based on processing complexity (more items slightly reduce confidence)
        complexity_penalty = max(0, (item_count - 100) / 900)  # Linear decrease in range 100-1000
        complexity_score = max(0.5, 1.0 - complexity_penalty)

        # Combined score
        confidence = (length_score * 0.5 + structure_score * 0.3 + complexity_score * 0.2)
        return min(confidence, 1.0)