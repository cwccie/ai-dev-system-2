"""
Model Providers Module
Factory for getting appropriate model providers
"""

import os
import importlib
from typing import Optional, Any

# Define provider mapping
PROVIDERS = {
    'claude': 'model_providers.claude_provider',
    'openai': 'model_providers.openai_provider',
    'deepseek': 'model_providers.deepseek_provider'
}

def get_provider(provider_name: str) -> Optional[Any]:
    """
    Factory function to get the appropriate model provider
    
    Args:
        provider_name: Name of the provider to instantiate
    
    Returns:
        An instance of the requested provider or None if not available
    """
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    # Check for API key
    api_key_env_vars = {
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY'
    }
    
    api_key = os.environ.get(api_key_env_vars.get(provider_name))
    if not api_key:
        print(f"Warning: No API key found for {provider_name}")
        return None
    
    try:
        # Import the module dynamically
        module_path = PROVIDERS[provider_name]
        module = importlib.import_module(module_path)
        
        # Get the provider class
        provider_classes = {
            'claude': 'ClaudeProvider',
            'openai': 'OpenAIProvider',
            'deepseek': 'DeepSeekProvider'
        }
        
        provider_class = getattr(module, provider_classes[provider_name])
        
        # Instantiate the provider
        return provider_class(api_key=api_key)
    
    except (ImportError, AttributeError) as e:
        print(f"Error initializing provider {provider_name}: {e}")
        return None
