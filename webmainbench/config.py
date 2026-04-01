"""Package-wide configuration."""
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# LLM settings for refinement of extractor outputs
LLM_CONFIG = {
    'llm_base_url': os.getenv('LLM_BASE_URL', ''),
    'llm_api_key': os.getenv('LLM_API_KEY', ''),
    'llm_model': os.getenv('LLM_MODEL', 'deepseek-chat'),
    'use_llm': os.getenv('USE_LLM', 'True').lower() == 'true',
}

# When True, print LLM enhancement / cache diagnostics (very noisy).
METRICS_DEBUG = os.getenv('METRICS_DEBUG', 'False').lower() == 'true'