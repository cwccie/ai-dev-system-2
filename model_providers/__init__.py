"""
Model Providers Module
Factory for getting appropriate model providers
"""

import os
import importlib
import logging
from typing import Optional, Any, Dict, List

from .server_manager import ServerManager

# Set up logging
logger = logging.getLogger(__name__)

# Define provider mapping
PROVIDERS = {
    'claude': 'model_providers.claude_provider',
    'openai': 'model_providers.openai_provider',
    'deepseek': 'model_providers.deepseek_provider',
    'ollama': 'model_providers.ollama_provider'
}

# Singleton instance of the server manager
_server_manager = None

def get_server_manager() -> ServerManager:
    """
    Get or create the singleton ServerManager instance
    
    Returns:
        The ServerManager instance
    """
    global _server_manager
    if _server_manager is None:
        _server_manager = ServerManager()
    return _server_manager

async def get_provider(provider_name: str, model_name: Optional[str] = None, 
                      task_type: Optional[str] = None, complexity: Optional[str] = None) -> Optional[Any]:
    """
    Factory function to get the appropriate model provider
    
    Args:
        provider_name: Name of the provider to instantiate
        model_name: Name of the specific model (optional)
        task_type: Type of task (for model recommendation)
        complexity: Complexity level of the task (high, medium, low)
    
    Returns:
        An instance of the requested provider or None if not available
    """
    if provider_name not in PROVIDERS:
        logger.error(f"Unknown provider: {provider_name}")
        return None
    
    # For Ollama provider, handle local model selection
    if provider_name == 'ollama':
        return await get_local_provider(model_name, task_type, complexity)
    
    # For cloud providers, handle as before
    # Check for API key
    api_key_env_vars = {
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY'
    }
    
    api_key = os.environ.get(api_key_env_vars.get(provider_name))
    if not api_key:
        logger.warning(f"No API key found for {provider_name}")
        return None
    
    try:
        # Import the module dynamically
        module_path = PROVIDERS[provider_name]
        module = importlib.import_module(module_path)
        
        # Get the provider class
        provider_classes = {
            'claude': 'ClaudeProvider',
            'openai': 'OpenAIProvider',
            'deepseek': 'DeepSeekProvider',
            'ollama': 'OllamaProvider'
        }
        
        provider_class = getattr(module, provider_classes[provider_name])
        
        # Instantiate the provider
        provider = provider_class(api_key=api_key)
        
        # Set specific model if provided
        if model_name and hasattr(provider, 'model'):
            provider.model = model_name
            
        return provider
    
    except (ImportError, AttributeError) as e:
        logger.error(f"Error initializing provider {provider_name}: {e}")
        return None

async def get_local_provider(model_name: Optional[str] = None, 
                           task_type: Optional[str] = None,
                           complexity: Optional[str] = None) -> Optional[Any]:
    """
    Get a provider for a local Ollama model
    
    Args:
        model_name: Name of the specific model (optional)
        task_type: Type of task (for model recommendation)
        complexity: Complexity level of the task (high, medium, low)
    
    Returns:
        An OllamaProvider instance or None if not available
    """
    try:
        # Get the server manager
        server_manager = get_server_manager()
        
        # If no model specified but task type is provided, recommend a model
        if not model_name and task_type:
            model_name = await recommend_local_model(task_type, complexity)
            if not model_name:
                logger.warning(f"No suitable model found for task type {task_type} with complexity {complexity}")
                return None
        
        # If still no model, use default
        if not model_name:
            model_name = "codellama:34b"  # Default model for coding tasks
        
        # Find best server for this model
        server_id = await server_manager.find_server_for_model(model_name)
        if not server_id:
            logger.warning(f"No available server found for model {model_name}")
            return None
        
        # Get server URL
        server_info = server_manager.get_server_info(server_id)
        server_url = server_info.get("info", {}).get("url")
        
        if not server_url:
            logger.warning(f"No URL found for server {server_id}")
            return None
        
        # Import the module dynamically
        module = importlib.import_module(PROVIDERS['ollama'])
        provider_class = getattr(module, 'OllamaProvider')
        
        # Instantiate the provider
        provider = provider_class(api_url=server_url, model=model_name, server_id=server_id)
        
        # Register task with server manager
        server_manager.register_task(server_id, f"task_{id(provider)}")
        
        logger.info(f"Created provider for model {model_name} on server {server_id}")
        return provider
        
    except Exception as e:
        logger.error(f"Error initializing local provider: {e}")
        return None

async def recommend_local_model(task_type: str, complexity: Optional[str] = "medium") -> Optional[str]:
    """
    Recommend a local model based on task type and complexity
    
    Args:
        task_type: Type of task (code_generation, script_orchestration, etc.)
        complexity: Complexity level (high, medium, low)
    
    Returns:
        Recommended model name or None if no suitable model found
    """
    try:
        # Get server configuration
        server_manager = get_server_manager()
        
        # Load server config to get task mappings
        servers_info = server_manager.get_all_servers()
        if not servers_info:
            logger.warning("No servers configured")
            return None
        
        # Get first server's info to access the shared config
        first_server = next(iter(servers_info.values()))
        
        # Check if config is available
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "config",
            "server_config.json"
        )
        
        if not os.path.exists(config_path):
            logger.warning(f"Server config file not found: {config_path}")
            
            # Fallback defaults
            if task_type == "code_generation":
                return "codellama:34b"
            elif task_type in ["script_orchestration", "script_planning"]:
                return "llama2:70b"
            else:
                return "codellama:13b"
        
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get task model mapping
        task_mapping = config.get("task_model_matching", {}).get(task_type)
        if not task_mapping:
            logger.warning(f"No task mapping found for {task_type}")
            return None
        
        # Get primary role for this task
        primary_role = task_mapping.get("primary_role")
        
        # Get models for the given complexity
        complexity = complexity or "medium"
        models = task_mapping.get("complexity_mapping", {}).get(complexity, [])
        
        if not models:
            logger.warning(f"No models found for {task_type} with complexity {complexity}")
            return None
        
        # Check each model's availability
        for model in models:
            # Get servers that have this model
            model_servers = server_manager.get_model_servers(model)
            if model_servers:
                # Find least loaded server
                for server_id in model_servers:
                    server_status = server_manager.server_status.get(server_id, {})
                    if server_status.get("status") == "online":
                        return model
        
        # If no model is available, return None
        logger.warning(f"No available models found for {task_type} with complexity {complexity}")
        return None
        
    except Exception as e:
        logger.error(f"Error recommending local model: {e}")
        return None

async def get_available_models() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get a list of all available models across servers
    
    Returns:
        Dictionary mapping provider names to lists of available models
    """
    try:
        # Get cloud models
        cloud_models = {
            "claude": [
                {"name": "claude-3-opus-20240229", "provider": "claude"},
                {"name": "claude-3-7-sonnet-20250219", "provider": "claude"},
                {"name": "claude-3-5-sonnet-20240620", "provider": "claude"},
                {"name": "claude-3-haiku-20240307", "provider": "claude"},
                {"name": "claude-3-5-haiku-20240620", "provider": "claude"}
            ],
            "openai": [
                {"name": "gpt-4o", "provider": "openai"},
                {"name": "gpt-4-turbo", "provider": "openai"},
                {"name": "gpt-4", "provider": "openai"},
                {"name": "gpt-3.5-turbo", "provider": "openai"}
            ],
            "deepseek": [
                {"name": "deepseek-coder", "provider": "deepseek"}
            ]
        }
        
        # Check which cloud providers are available
        for provider in list(cloud_models.keys()):
            api_key_env_vars = {
                'claude': 'ANTHROPIC_API_KEY',
                'openai': 'OPENAI_API_KEY',
                'deepseek': 'DEEPSEEK_API_KEY'
            }
            
            if not os.environ.get(api_key_env_vars.get(provider)):
                del cloud_models[provider]
        
        # Get local models
        server_manager = get_server_manager()
        await server_manager.check_all_servers()
        
        local_models = []
        for model, servers in server_manager.model_availability.items():
            # Get model details from ranking if available
            model_info = {"name": model, "provider": "ollama", "servers": servers}
            
            # Try to get model ranking and details
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "config",
                "server_config.json"
            )
            
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check coding models
                for ranked_model in config.get("model_rankings", {}).get("coding", []):
                    if ranked_model.get("model") == model:
                        model_info.update({
                            "rank": ranked_model.get("rank"),
                            "parameter_count": ranked_model.get("parameter_count"),
                            "strengths": ranked_model.get("strengths"),
                            "role": "coding"
                        })
                        break
                
                # Check orchestration models if not found in coding
                if "rank" not in model_info:
                    for ranked_model in config.get("model_rankings", {}).get("orchestration", []):
                        if ranked_model.get("model") == model:
                            model_info.update({
                                "rank": ranked_model.get("rank"),
                                "parameter_count": ranked_model.get("parameter_count"),
                                "strengths": ranked_model.get("strengths"),
                                "role": "orchestration"
                            })
                            break
            
            local_models.append(model_info)
        
        # Sort local models by rank if available
        local_models.sort(key=lambda m: m.get("rank", 999))
        
        # Add local models to result
        result = cloud_models.copy()
        result["ollama"] = local_models
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return {}
