"""
Model Providers Package
Provides interfaces to various LLM providers
"""

import os
import sys
import logging
import importlib
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

# Import server manager
try:
    from .server_manager import get_server_manager
except ImportError:
    logger.warning("Server manager not found, local model management may not be available")

# Providers dictionary
_providers = {}

def get_provider(provider_name: str = None):
    """
    Get a provider instance by name
    
    Args:
        provider_name: Name of the provider (claude, openai, deepseek)
        
    Returns:
        Provider instance or None if not found
    """
    global _providers
    
    # Default to Claude if not specified
    if provider_name is None:
        provider_name = 'claude'
    
    provider_name = provider_name.lower()
    
    # Return cached provider if available
    if provider_name in _providers:
        return _providers[provider_name]
    
    try:
        # Import the provider module
        if provider_name == 'claude':
            from .claude_provider import ClaudeProvider
            _providers[provider_name] = ClaudeProvider()
        elif provider_name == 'openai':
            from .openai_provider import OpenAIProvider
            _providers[provider_name] = OpenAIProvider()
        elif provider_name == 'deepseek':
            from .deepseek_provider import DeepSeekProvider
            _providers[provider_name] = DeepSeekProvider()
        else:
            logger.error(f"Unknown provider: {provider_name}")
            return None
        
        return _providers[provider_name]
    except ImportError as e:
        logger.error(f"Failed to import provider {provider_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error initializing provider {provider_name}: {e}")
        return None

async def get_available_models():
    """
    Get available models from all providers
    
    Returns:
        dict: Dictionary of models by provider
    """
    models = {}
    
    # Claude models
    try:
        from .claude_provider import ClaudeProvider
        claude = ClaudeProvider()
        claude_models = await claude.list_models()
        models['claude'] = claude_models
    except Exception as e:
        logger.error(f"Error getting Claude models: {e}")
        models['claude'] = []
    
    # OpenAI models
    try:
        from .openai_provider import OpenAIProvider
        openai = OpenAIProvider()
        openai_models = await openai.list_models()
        models['openai'] = openai_models
    except Exception as e:
        logger.error(f"Error getting OpenAI models: {e}")
        models['openai'] = []
    
    # DeepSeek models
    try:
        from .deepseek_provider import DeepSeekProvider
        deepseek = DeepSeekProvider()
        deepseek_models = await deepseek.list_models()
        models['deepseek'] = deepseek_models
    except Exception as e:
        logger.error(f"Error getting DeepSeek models: {e}")
        models['deepseek'] = []
    
    # Ollama models (local)
    try:
        from .ollama_provider import OllamaProvider
        ollama = OllamaProvider()
        ollama_models = await ollama.list_models()
        models['ollama'] = ollama_models
    except Exception as e:
        logger.error(f"Error getting Ollama models: {e}")
        models['ollama'] = []
    
    return models