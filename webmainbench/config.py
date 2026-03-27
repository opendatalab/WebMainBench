"""Package-wide configuration."""

# LLM settings for refinement of extractor outputs
LLM_CONFIG = {
    'llm_base_url': '',
    'llm_api_key': '',
    'llm_model': 'deepseek-chat',
    'use_llm': True,
}

# When True, print LLM enhancement / cache diagnostics (very noisy).
METRICS_DEBUG = False
